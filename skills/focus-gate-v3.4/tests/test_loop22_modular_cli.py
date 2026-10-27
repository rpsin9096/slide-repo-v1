"""Tests for FocusGate v2.9 — Milestone 19 (Loop 22: Monolith CLI Decomposition & v2.9-prod Seal).

Covers:
1. Domain class extraction to core/gates (TracerGate, SpikeGate, SpikeValidator).
2. Compaction engine extraction to core/compaction (SmartZoneCompactor).
3. Grounding linter extraction to core/grounding (ConceptGroundingLinter, SpecToLedgerCompiler).
4. Backward compatibility in scripts/focus-gate.py re-exports.
5. Zero code cliche / shotgun exception suppression in extracted core modules.
6. Production checkpoint seal and wave verification.
"""

import unittest
import os
import sys
import subprocess
import json
import importlib.util
import tempfile

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SCRIPT = os.path.join(ROOT_DIR, "scripts", "focus-gate.py")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


class TestGateExtraction(unittest.TestCase):
    """Verifies core.gates modular extraction."""

    def test_imports_from_core_gates(self):
        from core.gates import TracerGate, SpikeGate, SpikeValidator
        gate = TracerGate("gate-test", "Test Gate", checked=False)
        self.assertEqual(gate.id, "gate-test")
        self.assertEqual(gate["title"], "Test Gate")
        self.assertEqual(gate.to_dict()["type"], "production")

        spike = SpikeGate("spike-logic-test", "Test Spike", checked=True)
        self.assertEqual(spike.branch, "logic")
        self.assertEqual(spike.to_dict()["type"], "spike")

    def test_spike_validator_logic_prototype(self):
        from core.gates import SpikeValidator
        with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as tf:
            tf.write("""<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<script id="core-logic">
function processState(state, action) {
    return state;
}
</script>
<div id="raw-state">Current State: Ready</div>
<button id="btn-run">Run</button>
<div id="scenario-1">Scenario Walkthrough</div>
</body>
</html>""")
            path = tf.name

        try:
            valid, errors = SpikeValidator.verify_logic_prototype(path)
            self.assertTrue(valid, f"Expected valid prototype, got errors: {errors}")
        finally:
            if os.path.exists(path):
                os.remove(path)


class TestCompactionExtraction(unittest.TestCase):
    """Verifies core.compaction modular extraction."""

    def test_smart_zone_compactor_tokens(self):
        from core.compaction import SmartZoneCompactor
        sample = "Short string for testing token estimation."
        tokens = SmartZoneCompactor.estimate_tokens(sample)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, len(sample))

    def test_smart_zone_compactor_empty_ledger_needs_no_compaction(self):
        from core.compaction import SmartZoneCompactor
        class DummyLedger:
            gates = []
            spikes = []
            raw_content = "# Gates"
        self.assertFalse(SmartZoneCompactor.needs_compaction(DummyLedger()))


class TestGroundingExtraction(unittest.TestCase):
    """Verifies core.grounding modular extraction."""

    def test_concept_grounding_linter(self):
        from core.grounding import ConceptGroundingLinter
        doc = "This paragraph introduces **NewConcept**: defined here.\n\nAnother paragraph references NewConcept cleanly."
        violations = ConceptGroundingLinter.lint_grounding(doc, set())
        self.assertEqual(len(violations), 0)

    def test_spec_to_ledger_compiler(self):
        from core.grounding import SpecToLedgerCompiler
        spec = "# Sample Spec\n1. As a developer, I want auth, so that users can log in."
        ledger = SpecToLedgerCompiler.compile_spec(spec)
        self.assertIn("gate-1-auth", ledger)
        self.assertIn("As developer, auth", ledger)


class TestBackwardCompatibilityReExports(unittest.TestCase):
    """Verifies scripts/focus-gate.py re-exports extracted classes for backward compatibility."""

    def setUp(self):
        spec = importlib.util.spec_from_file_location("focus_gate", SCRIPT)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_script_re_exports_tracer_and_spike(self):
        self.assertTrue(hasattr(self.mod, "TracerGate"))
        self.assertTrue(hasattr(self.mod, "SpikeGate"))
        self.assertTrue(hasattr(self.mod, "SpikeValidator"))

    def test_script_re_exports_compactor_and_grounding(self):
        self.assertTrue(hasattr(self.mod, "SmartZoneCompactor"))
        self.assertTrue(hasattr(self.mod, "ConceptGroundingLinter"))
        self.assertTrue(hasattr(self.mod, "SpecToLedgerCompiler"))


class TestCodeHygieneExtractedModules(unittest.TestCase):
    """Verifies zero code clichés and shotgun exception suppression in extracted packages."""

    def test_core_extracted_modules_clean(self):
        from core.oracles.code_cliche_oracle import CodeClicheOracle
        for subpkg in ["gates", "compaction", "grounding"]:
            pkg_path = os.path.join(ROOT_DIR, "core", subpkg)
            if os.path.exists(pkg_path):
                for root, _, files in os.walk(pkg_path):
                    for fn in files:
                        if fn.endswith(".py"):
                            fp = os.path.join(root, fn)
                            with open(fp, "r", encoding="utf-8") as f:
                                content = f.read()
                            audit = CodeClicheOracle.audit_content(content, filename=fn)
                            self.assertTrue(audit.clean, f"Code cliché in {fp}: {[f.to_dict() for f in audit.findings]}")


class TestProductionSealing(unittest.TestCase):
    """Verifies production sealing, checkpoint integrity, and wave verification."""

    def test_v2_9_prod_checkpoint_exists_and_verified(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--list-checkpoints", "--json"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        cps = json.loads(proc.stdout)
        v29 = next((c for c in cps if c["checkpoint_id"] == "v2.9-prod"), None)
        self.assertIsNotNone(v29, "v2.9-prod checkpoint not found")
        self.assertTrue(v29["checksum_valid"], "v2.9-prod checkpoint checksum invalid")

    def test_wave_verification_cli(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--verify-wave", "--json"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertTrue(data["clean"], "Wave verification failed")

    def test_audit_production_scorecard_clean(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--audit-production", "--json"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        scorecard = json.loads(proc.stdout)
        self.assertEqual(scorecard["production_readiness"], "PASS")
        self.assertEqual(scorecard["code_tell_violations"], 0)


if __name__ == "__main__":
    unittest.main()

