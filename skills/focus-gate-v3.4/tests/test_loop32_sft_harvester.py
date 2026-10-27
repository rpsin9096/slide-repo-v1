"""Tests for Loop 32: Autonomous Trajectory SFT Harvester & Preview 2 Seal.

Tests TrajectoryHarvester recording of swarm traces, SFTDatasetExporter formatting
for OpenAI/Claude/Gemini formats, sensitive token sanitization, and CLI flags.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import io
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from contextlib import redirect_stdout
from typing import Dict, Any, List

from core.harvest.trajectory_harvester import TrajectoryHarvester, SwarmTrajectory
from core.harvest.dataset_export import SFTDatasetExporter


class TestTrajectoryHarvester(unittest.TestCase):
    """Test recording and filtering of multi-agent swarm trajectories."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_harvest_test_")
        self.harvester = TrajectoryHarvester(storage_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_and_save_trajectory(self):
        traj = self.harvester.record(
            task_brief="Implement high-concurrency rate limiter",
            actor_traces=[
                {"actor": "coder-01", "action": "code_edit", "observation": "Added token bucket algorithm"},
                {"actor": "verifier-01", "action": "test_run", "observation": "All 12 test assertions passed"}
            ],
            dialectics=[{"round": 1, "verdict": "CONVERGED"}],
            receipt={"gate_id": "gate-1", "signature": "abc123sha", "status": "APPROVED"},
            verdict="SUCCESS"
        )
        self.assertIsInstance(traj, SwarmTrajectory)
        self.assertEqual(traj.verdict, "SUCCESS")
        self.assertGreater(traj.token_count, 20)

        # Check saved on disk
        saved = self.harvester.load_trajectories()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].trajectory_id, traj.trajectory_id)

    def test_filter_successful_trajectories(self):
        self.harvester.record(
            task_brief="Broken gate run",
            actor_traces=[{"actor": "coder-01", "action": "error", "observation": "SyntaxError"}],
            dialectics=[],
            receipt=None,
            verdict="FAILED"
        )
        self.harvester.record(
            task_brief="Working gate run",
            actor_traces=[{"actor": "coder-01", "action": "success", "observation": "Passed"}],
            dialectics=[],
            receipt={"status": "APPROVED"},
            verdict="SUCCESS"
        )
        successful = self.harvester.get_successful_trajectories()
        self.assertEqual(len(successful), 1)
        self.assertEqual(successful[0].verdict, "SUCCESS")


class TestSFTDatasetExporter(unittest.TestCase):
    """Test multi-model dataset exports and sanitization."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_export_test_")
        self.traj = SwarmTrajectory(
            trajectory_id="traj-test-01",
            task_brief="Implement secure session handler with secret_key=sk-secret1234567890abcdef",
            actor_traces=[
                {"actor": "coder-01", "action": "generate_token", "observation": "Generated bearer token using secret"},
                {"actor": "verifier-01", "action": "verify_entropy", "observation": "Entropy > 3.9 bits/byte. Invariant held."}
            ],
            dialectics=[{"round": 1, "synthesis": "Consensus on cryptographic safety"}],
            receipt={"gate_id": "gate-auth", "signature": "sig123", "status": "APPROVED"},
            verdict="SUCCESS",
            token_count=120
        )
        self.exporter = SFTDatasetExporter()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_openai_format(self):
        sample = self.exporter.format_openai(self.traj)
        self.assertIn("messages", sample)
        roles = [m["role"] for m in sample["messages"]]
        self.assertIn("system", roles)
        self.assertIn("user", roles)
        self.assertIn("assistant", roles)

    def test_export_claude_format(self):
        sample = self.exporter.format_claude(self.traj)
        self.assertIn("system", sample)
        self.assertIn("messages", sample)
        self.assertEqual(sample["messages"][0]["role"], "user")
        self.assertEqual(sample["messages"][1]["role"], "assistant")

    def test_export_gemini_format(self):
        sample = self.exporter.format_gemini(self.traj)
        self.assertIn("contents", sample)
        roles = [c["role"] for c in sample["contents"]]
        self.assertIn("user", roles)
        self.assertIn("model", roles)

    def test_sanitize_sensitive_data(self):
        sanitized = self.exporter.sanitize_text(
            "Connection established with token=sk-abcdef1234567890 and path=/Users/private/keys"
        )
        self.assertNotIn("sk-abcdef1234567890", sanitized)
        self.assertIn("[REDACTED_SECRET]", sanitized)

    def test_export_dataset_file(self):
        out_path = os.path.join(self.temp_dir, "sft_openai.jsonl")
        count = self.exporter.export_file([self.traj], out_path=out_path, model_format="openai")
        self.assertEqual(count, 1)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            line = f.readline()
            data = json.loads(line)
        self.assertIn("messages", data)


class TestHarvestCLI(unittest.TestCase):
    """Test CLI dispatch for --harvest-swarm and --export-swarm-pack."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_hcli_")
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        os.makedirs(".focusgate/trajectories", exist_ok=True)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_harvest_swarm_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(harvest_swarm=True, export_swarm_pack=None)
        clean_args = ["--harvest-swarm", "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("trajectories_count", output)

    def test_cli_export_swarm_pack_json(self):
        from core.cli.dispatch import CLIDispatcher
        from core.harvest.trajectory_harvester import TrajectoryHarvester

        # Pre-seed a trajectory
        h = TrajectoryHarvester(storage_dir=".focusgate/trajectories")
        h.record("Test Task", [{"action": "a", "observation": "o"}], [], None, "SUCCESS")

        args = SimpleNamespace(harvest_swarm=None, export_swarm_pack=["openai"])
        clean_args = ["--export-swarm-pack", "openai", "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("exported_count", output)
        self.assertEqual(output["exported_count"], 1)


if __name__ == '__main__':
    unittest.main()
