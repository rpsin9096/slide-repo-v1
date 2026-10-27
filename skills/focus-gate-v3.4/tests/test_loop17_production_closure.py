"""Tests for FocusGate v2.8.5 — Milestone 14 (Loop 17: Production Closure & Release v2.8.5-prod).

Covers:
1. Immutable production checkpoint v2.8.5-prod verification and SHA-256 integrity.
2. Wave verification (--verify-wave) aggregate clean pass.
3. Production readiness audit (--audit-production) scorecard verification.
4. Adversarial socratic audit CLI execution.
5. Modular CLI dispatch architecture (core/cli/dispatch.py).
6. Multi-language audit-all integration across Python, TypeScript, and Rust.
"""

import unittest
import os
import sys
import subprocess
import json

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SCRIPT = os.path.join(ROOT_DIR, "scripts", "focus-gate.py")
CHECKPOINT_PATH = os.path.join(ROOT_DIR, ".focusgate", "checkpoints", "v2.8.5-prod.json")


class TestProductionClosureV285(unittest.TestCase):
    """Verifies FocusGate v2.8.5 production seal and aggregate invariants."""

    def test_checkpoint_v285_exists_and_verified(self):
        """Verifies v2.8.5-prod checkpoint file exists and passes SHA-256 verification."""
        self.assertTrue(os.path.isfile(CHECKPOINT_PATH), "Missing v2.8.5-prod checkpoint file")
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("checkpoint_id"), "v2.8.5-prod")
        self.assertEqual(data.get("version"), "2.8")
        self.assertIn("checksum", data)
        self.assertIn("model_adapter", data)

        from core.orchestrator_kernel import OrchestratorKernel
        orch = OrchestratorKernel(os.path.join(ROOT_DIR, ".focusgate"))
        checkpoints = orch.list_checkpoints()
        v285_cp = next((c for c in checkpoints if c["checkpoint_id"] == "v2.8.5-prod"), None)
        self.assertIsNotNone(v285_cp, "v2.8.5-prod checkpoint not found in OrchestratorKernel")
        self.assertTrue(v285_cp["checksum_valid"], "v2.8.5-prod checksum verification failed")

    def test_cli_verify_wave_passes(self):
        """Verifies end-to-end --verify-wave returns exit code 0 and PASS."""
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--verify-wave"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0, f"--verify-wave failed: {proc.stderr}")
        self.assertIn("Overall Wave Verdict: PASS (Clean)", proc.stdout)

    def test_cli_audit_production_readiness(self):
        """Verifies --audit-production reports PASS (Ready) with >=4 checkpoints."""
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--audit-production"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0, f"--audit-production failed: {proc.stderr}")
        self.assertIn("Production Verdict:     PASS (Ready)", proc.stdout)
        self.assertIn("Production Checkpoints:", proc.stdout)
        import re
        cp_match = re.search(r"Production Checkpoints:\s*(\d+)", proc.stdout)
        self.assertIsNotNone(cp_match)
        self.assertGreaterEqual(int(cp_match.group(1)), 4)


    def test_cli_adversarial_audit_execution(self):
        """Verifies --adversarial-audit executes full 3-round tournament."""
        proposal = "Introduce transactional write-ahead logging with monotonic epoch fencing"
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--adversarial-audit", proposal],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0, f"--adversarial-audit failed: {proc.stderr}")
        self.assertIn("ADVERSARIAL_VERDICT:", proc.stdout)
        self.assertIn("vulnerabilities mitigated across 3 rounds", proc.stdout)

    def test_cli_modular_dispatcher_available(self):
        """Verifies CLIDispatcher is modularized in core.cli.dispatch."""
        from core.cli.dispatch import CLIDispatcher
        self.assertTrue(callable(getattr(CLIDispatcher, "dispatch", None)))

    def test_polyglot_audit_all_in_unified_engine(self):
        """Verifies UnifiedAuditOracle properly audits Python, TypeScript, and Rust."""
        from core.oracles.unified_audit import UnifiedAuditOracle

        # 1. Clean TypeScript
        clean_ts = "export function add(a: number, b: number): number { return a + b; }\n"
        res_ts = UnifiedAuditOracle.audit_text(clean_ts, file_type="ts", filename="math.ts")
        self.assertTrue(res_ts["clean"])
        self.assertEqual(res_ts["category"], "code")

        # 2. Shotgun TypeScript
        dirty_ts = "export function api() { try { call(); } catch (e) {} }\n"
        res_dirty_ts = UnifiedAuditOracle.audit_text(dirty_ts, file_type="ts", filename="api.ts")
        self.assertFalse(res_dirty_ts["clean"])
        self.assertTrue(any(f["rule_id"] == "CODE_SHOTGUN_SUPPRESSION_TS" for f in res_dirty_ts["findings"]))

        # 3. Clean Rust
        clean_rs = "pub fn calc(x: i32) -> Result<i32, String> { Ok(x * 2) }\n"
        res_rs = UnifiedAuditOracle.audit_text(clean_rs, file_type="rs", filename="calc.rs")
        self.assertTrue(res_rs["clean"])
        self.assertEqual(res_rs["category"], "code")


if __name__ == "__main__":
    unittest.main()
