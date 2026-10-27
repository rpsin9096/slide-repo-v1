"""TDD Contract for Loop 12: FocusGate v2.8.1 Features.

Covers:
- Track 1: Workspace-Aware Deterministic Synthesis (Smart Fast-Path without models).
  * Auto-detects tech stack (Python, Node/TypeScript, Rust, Go) in <3ms.
  * Injects bespoke contextual seed check commands and target source files into Action Envelope.
- Track 3: Autonomous Trajectory Telemetry & One-Click Colab Pack.
  * Auto-harvests verified stage completion into .focusgate/trajectories/auto_harvested.jsonl.
  * Generates turnkey Google Colab training pack with zero local compute.
"""

import unittest
import os
import sys
import tempfile
import shutil
import json

# Ensure repository root is in sys.path
V28_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if V28_ROOT not in sys.path:
    sys.path.insert(0, V28_ROOT)

from core.workspace_detector import WorkspaceDetector
from core.orchestrator_kernel import OrchestratorKernel
from scripts.evaluate_distillation import PipelineSynthesizer


class TestLoop12V281Features(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ledger_root = os.path.join(self.test_dir, ".focusgate")
        os.makedirs(self.ledger_root, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_m1_workspace_detection_python(self):
        """M1: WorkspaceDetector accurately detects Python projects and preferred test runner."""
        with open(os.path.join(self.test_dir, "pyproject.toml"), "w") as f:
            f.write("[project]\nname = 'test-proj'\n")
        with open(os.path.join(self.test_dir, "pytest.ini"), "w") as f:
            f.write("[pytest]\n")

        info = WorkspaceDetector.detect(self.test_dir)
        self.assertEqual(info["stack"], "python")
        self.assertEqual(info["test_runner"], "pytest")
        self.assertIn("pyproject.toml", info["manifests"])

    def test_m1_workspace_detection_node(self):
        """M1: WorkspaceDetector accurately detects Node/TypeScript projects."""
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            json.dump({"name": "web-app", "scripts": {"test": "jest"}}, f)

        info = WorkspaceDetector.detect(self.test_dir)
        self.assertEqual(info["stack"], "typescript_node")
        self.assertEqual(info["test_runner"], "npm test")
        self.assertIn("package.json", info["manifests"])

    def test_m1_workspace_detection_rust_and_go(self):
        """M1: WorkspaceDetector accurately detects Rust and Go projects."""
        rust_dir = tempfile.mkdtemp()
        try:
            with open(os.path.join(rust_dir, "Cargo.toml"), "w") as f:
                f.write("[package]\nname = 'rust-crate'\n")
            info_rust = WorkspaceDetector.detect(rust_dir)
            self.assertEqual(info_rust["stack"], "rust")
            self.assertEqual(info_rust["test_runner"], "cargo test")
        finally:
            shutil.rmtree(rust_dir, ignore_errors=True)

        go_dir = tempfile.mkdtemp()
        try:
            with open(os.path.join(go_dir, "go.mod"), "w") as f:
                f.write("module example.com/app\n")
            info_go = WorkspaceDetector.detect(go_dir)
            self.assertEqual(info_go["stack"], "go")
            self.assertEqual(info_go["test_runner"], "go test ./...")
        finally:
            shutil.rmtree(go_dir, ignore_errors=True)

    def test_m1_pipeline_synthesizer_bespoke_seed_action(self):
        """M1: PipelineSynthesizer tailors seed step to workspace stack and mentioned files."""
        # Create a Python repo with a specific file
        with open(os.path.join(self.test_dir, "pyproject.toml"), "w") as f:
            f.write("[project]\nname = 'my-lib'\n")
        with open(os.path.join(self.test_dir, "worker.py"), "w") as f:
            f.write("# async worker\n")

        query = "Fix intermittent race condition in worker.py under high load"
        plan = PipelineSynthesizer.synthesize(query, workspace_root=self.test_dir)

        self.assertEqual(plan["archetype"], "DEFECT")
        seed_step = plan["seed_step"]
        # Must specifically name worker.py and use pytest
        self.assertIn("worker.py", seed_step["action"])
        self.assertTrue("pytest" in seed_step["check"] or "python3" in seed_step["check"])

    def test_m2_auto_harvesting_on_stage_verified(self):
        """M2: OrchestratorKernel automatically logs verified trajectories on stage completion."""
        orch = OrchestratorKernel(self.ledger_root)
        orch.plan_decomposition("Build authenticated user profile endpoint")

        # Manually verify first stage
        first_stage = orch.stage_definitions[0]
        # Satisfy gates for first stage
        for gid in first_stage.gate_ids:
            orch.aggregate.gates[gid]["status"] = "ACTIVE"
            orch.aggregate.check_gate(gid, output="Gate verified successfully")

        # Verify stage
        ok, reasons = orch.verify_stage(first_stage.stage_id)
        self.assertTrue(ok, f"Stage verification should succeed: {reasons}")

        # Check trajectory file created
        trajectories_dir = os.path.join(self.ledger_root, "trajectories")
        harvest_file = os.path.join(trajectories_dir, "auto_harvested.jsonl")
        self.assertTrue(os.path.exists(harvest_file), f"Auto-harvested file should exist at: {harvest_file}")

        with open(harvest_file, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]

        self.assertGreaterEqual(len(lines), 1)
        record = lines[0]
        self.assertIn("instruction", record)
        self.assertIn("output", record)
        self.assertTrue(record["output"].startswith("▶ NEXT ACTION:"))
        self.assertIn("State: [Pipeline:", record["output"])

    def test_m3_export_colab_pack(self):
        """M3: OrchestratorKernel exports standalone Google Colab training pack."""
        orch = OrchestratorKernel(self.ledger_root)
        pack_dir = os.path.join(self.test_dir, "colab_pack")
        pack_info = orch.export_colab_pack(pack_dir)

        self.assertTrue(os.path.isdir(pack_dir))
        self.assertTrue(os.path.exists(os.path.join(pack_dir, "train_focusgate_colab.py")))
        self.assertTrue(pack_info["success"])
        self.assertEqual(pack_info["base_model"], "Qwen/Qwen2.5-1.5B-Instruct")
        self.assertEqual(pack_info["peft_type"], "LORA")
        self.assertGreaterEqual(pack_info["record_count"], 0)

    def test_m3_cli_export_colab_pack(self):
        """M3: CLI --export-colab-pack runs cleanly and produces JSON output."""
        import subprocess
        script_path = os.path.join(V28_ROOT, "scripts", "focus-gate.py")
        pack_dir = os.path.join(self.test_dir, "cli_pack")
        cmd = [sys.executable, script_path, "--export-colab-pack", pack_dir, "--ledger-root", self.ledger_root, "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI exited with error: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("export_dir"), pack_dir)
        self.assertTrue(os.path.exists(os.path.join(pack_dir, "train_focusgate_colab.py")))


if __name__ == "__main__":
    unittest.main()
