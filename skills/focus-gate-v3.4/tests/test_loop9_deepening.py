"""Unit Tests for Loop 9 Deepening Milestones (FocusGate v2.8).

Covers:
- Milestone 1: Session DAG Branch Self-Healing & Pruning in OrchestratorKernel
- Milestone 2: Whitespace & Line-Ending Tolerant Patch Precondition Checking in ToolSelectionMatrix
- Milestone 3: Standalone Stage Matrix Discovery (stages.json) in Wave Verification
- Milestone 4: Ephemeral Session Expiration & Stale Session Cleanup in EphemeralSessionManager
"""

import unittest
import tempfile
import shutil
import os
import json
import time

from core.orchestrator_kernel import OrchestratorKernel, AgentReceiptBundle
from core.session_dag import SessionBranchDAG
from core.tool_matrix import ToolSelectionMatrix, PatchPreconditionCheck
from core.ephemeral_session import EphemeralSessionManager, EphemeralSessionContext, EphemeralSession



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


class TestLoop9Deepening(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ledger_root = os.path.join(self.test_dir, ".focusgate")
        os.makedirs(self.ledger_root, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_m1_session_dag_self_healing_on_unbranched_merge(self):
        """M1: OrchestratorKernel.merge_results handles missing branch without KeyError or crash."""
        orch = OrchestratorKernel(self.ledger_root)
        orch.plan_decomposition("Deploy auth subsystem")

        # Emulate receiving a verified bundle for gate-1-seam without forking an agent branch in DAG
        bundle = AgentReceiptBundle(
            bundle_id="bundle-test-m1",
            gate_id="gate-1-seam",
            brief_id="brief-test-m1",
            gate_receipts=[{"gate_id": "gate-1-seam", "status": "PASS"}],
            delta_ids=[],
            artifacts_produced=["auth.py"],
            patch_hashes=["hash123"],
            status="PASS"
        )
        orch.active_bundles["gate-1-seam"] = bundle
        orch.aggregate.gates["gate-1-seam"]["status"] = "ACTIVE"

        # merge_results should not throw KeyError or print unhandled errors
        merged = orch.merge_results("gate-1-seam")
        self.assertTrue(merged)
        self.assertEqual(orch.aggregate.gates["gate-1-seam"]["status"], "CHECKED")

    def test_m1_session_dag_pruning_after_merge(self):
        """M1: Session DAG auto-prunes stale branches on merge_results."""
        orch = OrchestratorKernel(self.ledger_root)
        orch.plan_decomposition("Deploy auth subsystem")

        # Fork an agent branch
        dag = orch.session_manager._dag
        dag.fork_branch("agent-gate-1-seam")
        # Fork an older stale branch and advance turns
        dag.fork_branch("stale-speculative-branch")
        dag.switch_branch("agent-gate-1-seam")
        for _ in range(5):
            dag.checkpoint({"step": "work"})

        bundle = AgentReceiptBundle(
            bundle_id="bundle-test-m1-prune",
            gate_id="gate-1-seam",
            brief_id="brief-test-m1-prune",
            gate_receipts=[{"gate_id": "gate-1-seam", "status": "PASS"}],
            delta_ids=[],
            artifacts_produced=[],
            patch_hashes=[],
            status="PASS"
        )
        orch.active_bundles["gate-1-seam"] = bundle
        orch.aggregate.gates["gate-1-seam"]["status"] = "ACTIVE"
        merged = orch.merge_results("gate-1-seam")
        self.assertTrue(merged)
        # Stale branch should have been pruned
        self.assertNotIn("stale-speculative-branch", dag.branches)

    def test_m2_patch_preconditions_whitespace_tolerance_diagnostics(self):
        """M2: ToolSelectionMatrix detects trailing whitespace drift and provides diagnostic."""
        target_file = os.path.join(self.test_dir, "sample.py")
        # File has trailing whitespace on line 2
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("def calculate_total(items):   \n    return sum(items)\n")

        matrix = ToolSelectionMatrix(self.test_dir)
        # Search block without trailing spaces
        search_block = "def calculate_total(items):\n    return sum(items)"

        # Default fuzzy_whitespace=False should reject exact match but flag whitespace_match_found
        check = matrix.verify_patch_preconditions(target_file, search_block, fuzzy_whitespace=False)
        self.assertFalse(check.valid)
        self.assertFalse(check.exact_match_found)
        self.assertTrue(check.whitespace_match_found)
        self.assertIn("trailing whitespace", check.reason.lower())
        self.assertEqual(check.matched_start_line, 1)
        self.assertEqual(check.matched_end_line, 2)

    def test_m2_patch_preconditions_fuzzy_whitespace_flag(self):
        """M2: ToolSelectionMatrix accepts patch when fuzzy_whitespace=True is enabled."""
        target_file = os.path.join(self.test_dir, "sample2.py")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("class Engine:  \n    def start(self):  \n        pass\n")

        matrix = ToolSelectionMatrix(self.test_dir)
        search_block = "class Engine:\n    def start(self):\n        pass"

        check = matrix.verify_patch_preconditions(target_file, search_block, fuzzy_whitespace=True)
        self.assertTrue(check.valid)
        self.assertFalse(check.exact_match_found)
        self.assertTrue(check.whitespace_match_found)
        self.assertEqual(check.matched_start_line, 1)
        self.assertEqual(check.matched_end_line, 3)

    def test_m3_wave_verification_discovers_stages_json(self):
        """M3: Wave verification Checkpoint 5 executes when stages.json exists without GATES.md."""
        stages_path = os.path.join(self.ledger_root, "stages.json")
        gates_path = os.path.join(self.ledger_root, "gates.json")

        stages_data = [
            {
                "stage_id": "stage-core",
                "index": 1,
                "name": "Core Domain",
                "facet": "engineering",
                "gate_ids": ["gate-1"],
                "exit_criteria": [],
                "status": "PENDING"
            }
        ]
        gates_data = {
            "gate-1": {
                "id": "gate-1",
                "title": "Core tests",
                "status": "CHECKED",
                "depends_on": []
            }
        }
        with open(stages_path, "w", encoding="utf-8") as f:
            json.dump(stages_data, f)
        with open(gates_path, "w", encoding="utf-8") as f:
            json.dump(gates_data, f)

        # Ensure no GATES.md exists
        gates_md = os.path.join(self.ledger_root, "GATES.md")
        if os.path.exists(gates_md):
            os.remove(gates_md)

        # Import and run wave verification Checkpoint 5 logic
        from core.orchestrator_kernel import OrchestratorKernel
        orch = OrchestratorKernel(self.ledger_root)
        active_stage = orch.stage_matrix.get_active_stage(orch.stage_definitions, orch.aggregate.gates)
        self.assertIsNotNone(active_stage)
        self.assertEqual(active_stage.stage_id, "stage-core")

        # Verify scripts/focus-gate.py contains stages.json discovery in stage_matrix check
        cli_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "focus-gate.py")
        cli_source = read_cli_source()
        self.assertIn('stages_json_cand = os.path.join(ledger_root, "stages.json")', cli_source)

    def test_m4_ephemeral_session_expiration_cleanup(self):
        """M4: EphemeralSessionManager reaps and evicts expired sessions."""
        manager = EphemeralSessionManager(self.test_dir)

        # Spawn active session
        session = manager.spawn_session(
            facet="engineering",
            active_gate={"id": "gate-expired", "title": "Stale task"}
        )
        self.assertIn(session.session_id, manager.active_sessions)

        # Simulate expiration by rolling back created_at
        session.ctx.created_at = time.time() - 3600 * 25  # 25 hours old

        # Spawn another fresh session
        fresh_session = manager.spawn_session(
            facet="testing",
            active_gate={"id": "gate-fresh", "title": "Active task"}
        )

        expired_ids = manager.cleanup_expired_sessions(max_age_hours=24.0)

        self.assertIn(session.session_id, expired_ids)
        self.assertNotIn(session.session_id, manager.active_sessions)
        self.assertTrue(session._is_reaped)

        # Fresh session remains active
        self.assertIn(fresh_session.session_id, manager.active_sessions)
        self.assertNotIn(fresh_session.session_id, expired_ids)


if __name__ == "__main__":
    unittest.main()
