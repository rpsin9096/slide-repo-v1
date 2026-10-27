"""Unit Tests for Loop 10 Production Readiness & Checkpoint Verification (FocusGate v2.8).

Covers:
- Milestone 1: Production Checkpoint Engine & Rollback Lifecycle in OrchestratorKernel
- Milestone 2: CLI Integration for Production Checkpoints (--checkpoint, --restore-checkpoint, --list-checkpoints)
- Milestone 3: Complete Harmonization of Residual Legacy Version Strings
- Milestone 4: Wave Verification Checkpoint 7 (production_readiness)
"""

import unittest
import tempfile
import shutil
import os
import json
import time

from core.orchestrator_kernel import OrchestratorKernel



def read_cli_source():
    """Text of the CLI: the entry script plus every module under core/cli (v3.4 moved the code)."""
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    paths = [os.path.join(root, "scripts", "focus-gate.py")]
    for dp, _d, fns in os.walk(os.path.join(root, "core", "cli")):
        paths += [os.path.join(dp, f) for f in sorted(fns) if f.endswith(".py")]
    out = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as fh:
            out.append(fh.read())
    return "\n".join(out)


class TestLoop10ProductionReadiness(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ledger_root = os.path.join(self.test_dir, ".focusgate")
        os.makedirs(self.ledger_root, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_m1_create_and_restore_checkpoint(self):
        """M1: OrchestratorKernel creates and restores immutable production checkpoints."""
        orch = OrchestratorKernel(self.ledger_root)
        orch.plan_decomposition("Production authorization system")

        # Mark first gate as CHECKED
        first_gate_id = list(orch.aggregate.gates.keys())[0]
        orch.aggregate.gates[first_gate_id]["status"] = "ACTIVE"
        orch.aggregate.check_gate(first_gate_id, output="Verified auth gate")

        # Create checkpoint
        manifest = orch.create_checkpoint("v2.8-prod-checkpoint")
        self.assertEqual(manifest["checkpoint_id"], "v2.8-prod-checkpoint")
        self.assertEqual(manifest["version"], "2.8")
        self.assertTrue(manifest["checksum"])
        self.assertEqual(manifest["gates"][first_gate_id]["status"], "CHECKED")

        # Mutate memory state (simulate unwanted state drift)
        orch.aggregate.gates[first_gate_id]["status"] = "FAILED"
        self.assertEqual(orch.aggregate.gates[first_gate_id]["status"], "FAILED")

        # Restore checkpoint (Step 2: Return loops to previous checkpoint)
        restored = orch.restore_checkpoint("v2.8-prod-checkpoint")
        self.assertTrue(restored)
        self.assertEqual(orch.aggregate.gates[first_gate_id]["status"], "CHECKED")

    def test_m1_list_checkpoints(self):
        """M1: OrchestratorKernel lists checkpoints with cryptographic checksum status."""
        orch = OrchestratorKernel(self.ledger_root)
        orch.plan_decomposition("Production microservice architecture")
        orch.create_checkpoint("cp-alpha")
        orch.create_checkpoint("cp-beta")

        cps = orch.list_checkpoints()
        cp_ids = [c["checkpoint_id"] for c in cps]
        self.assertIn("cp-alpha", cp_ids)
        self.assertIn("cp-beta", cp_ids)
        for c in cps:
            self.assertTrue(c["checksum_valid"])
            self.assertEqual(c["version"], "2.8")

    def test_m1_checkpoint_tamper_detection(self):
        """M1: restore_checkpoint rejects tampered checkpoint with ValueError."""
        orch = OrchestratorKernel(self.ledger_root)
        orch.plan_decomposition("Financial settlement ledger")
        orch.create_checkpoint("tamper-test")

        cp_path = os.path.join(orch._checkpoints_dir, "tamper-test.json")
        with open(cp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Tamper with internal gate status without updating checksum
        first_gate = list(data["gates"].keys())[0]
        data["gates"][first_gate]["status"] = "TAMPERED"
        with open(cp_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        with self.assertRaises(ValueError):
            orch.restore_checkpoint("tamper-test")

    def test_m2_cli_checkpoint_flags_registered(self):
        """M2: CLI parser exposes --checkpoint, --restore-checkpoint, and --list-checkpoints."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        import importlib
        focus_gate_mod = importlib.import_module("focus-gate")
        parser = focus_gate_mod.build_parser()
        help_text = parser.format_help()

        self.assertIn("--checkpoint", help_text)
        self.assertIn("--restore-checkpoint", help_text)
        self.assertIn("--list-checkpoints", help_text)

    def test_m3_version_harmonization_scripts(self):
        """M3: No legacy version strings in argument groups or compiler signatures."""
        cli_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "focus-gate.py")
        cli_source = read_cli_source()

        # Argument groups must not mention v2.0, v2.1, v2.5, v2.6
        self.assertNotIn("Routing (v2.0)", cli_source)
        self.assertNotIn("Handoff (v2.5.1)", cli_source)
        self.assertNotIn("Matrix (v2.5.5)", cli_source)

        compiler_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "compiler", "dspy_signatures.py")
        with open(compiler_path, "r", encoding="utf-8") as f:
            comp_source = f.read()
        self.assertIn("FocusGate v2.8", comp_source)
        self.assertNotIn("FocusGate v2.6", comp_source)

    def test_m4_wave_verification_production_readiness_checkpoint(self):
        """M4: Wave verification includes production_readiness checkpoint."""
        cli_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "focus-gate.py")
        cli_source = read_cli_source()
        self.assertIn('"production_readiness"', cli_source)


if __name__ == "__main__":
    unittest.main()
