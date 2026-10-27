"""Tests for FocusGate v2.8.5 — Milestone 12 (Loop 15: Transactional Worktree Swarm Merges & Saga Compensation).

Covers:
1. 3-Way semantic conflict detection across parallel worktrees.
2. AST-level symbol collision analysis.
3. Transactional worktree merging with staging isolation.
4. Automated Saga compensation rollback on post-merge test failure.
5. DLQ tombstone persistence on rollback aborts.
"""

import unittest
import os
import tempfile
import shutil
import subprocess

from core.worktree_runner import WorktreeRunner, TransactionalMergeResult


class TestWorktreeConflictDetection(unittest.TestCase):
    """Verifies semantic conflict detection between concurrent worktree branches."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self._init_git_repo(self.tmp_dir)
        self.runner = WorktreeRunner(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _init_git_repo(self, path: str):
        subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "TestRunner"], cwd=path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@focusgate.io"], cwd=path, capture_output=True, check=True)
        init_file = os.path.join(path, "README.md")
        with open(init_file, "w") as f:
            f.write("# Repo\n")
        subprocess.run(["git", "add", "README.md"], cwd=path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=path, capture_output=True, check=True)

    def test_disjoint_worktree_changes_have_no_conflict(self):
        wt_a = self.runner.provision_worktree("agent-a")
        wt_b = self.runner.provision_worktree("agent-b")

        with open(os.path.join(wt_a, "module_a.py"), "w") as f:
            f.write("def func_a(): return 'a'\n")
        self.runner.commit_worktree("agent-a", "add module a")

        with open(os.path.join(wt_b, "module_b.py"), "w") as f:
            f.write("def func_b(): return 'b'\n")
        self.runner.commit_worktree("agent-b", "add module b")

        has_conflict, conflicts, details = self.runner.detect_conflicts(["agent-a", "agent-b"])
        self.assertFalse(has_conflict, "Disjoint file additions should have no conflict.")
        self.assertEqual(len(conflicts), 0)

    def test_overlapping_file_collision_detected(self):
        wt_a = self.runner.provision_worktree("agent-a")
        wt_b = self.runner.provision_worktree("agent-b")

        with open(os.path.join(wt_a, "shared.py"), "w") as f:
            f.write("def shared(): return 'version_a'\n")
        self.runner.commit_worktree("agent-a", "edit shared a")

        with open(os.path.join(wt_b, "shared.py"), "w") as f:
            f.write("def shared(): return 'version_b'\n")
        self.runner.commit_worktree("agent-b", "edit shared b")

        has_conflict, conflicts, details = self.runner.detect_conflicts(["agent-a", "agent-b"])
        self.assertTrue(has_conflict, "Overlapping edits to shared.py must be detected as conflict.")
        self.assertIn("shared.py", conflicts)

    def test_ast_symbol_collision_detected(self):
        wt_a = self.runner.provision_worktree("agent-a")
        wt_b = self.runner.provision_worktree("agent-b")

        with open(os.path.join(wt_a, "models.py"), "w") as f:
            f.write("class User:\n    name: str = 'A'\n")
        self.runner.commit_worktree("agent-a", "add User class A")

        with open(os.path.join(wt_b, "models.py"), "w") as f:
            f.write("class User:\n    email: str = 'B'\n")
        self.runner.commit_worktree("agent-b", "add User class B")

        has_conflict, conflicts, details = self.runner.detect_conflicts(["agent-a", "agent-b"])
        self.assertTrue(has_conflict)
        symbols = details.get("symbol_collisions", [])
        self.assertTrue(any("User" in s for s in symbols), f"Symbol collision for User should be detected: {symbols}")


class TestTransactionalWorktreeMerge(unittest.TestCase):
    """Verifies transactional merging, test verification, and Saga rollback."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.dlq_dir = os.path.join(self.tmp_dir, ".focusgate", "dlq")
        self._init_git_repo(self.tmp_dir)
        self.runner = WorktreeRunner(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _init_git_repo(self, path: str):
        subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "TestRunner"], cwd=path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@focusgate.io"], cwd=path, capture_output=True, check=True)
        init_file = os.path.join(path, "README.md")
        with open(init_file, "w") as f:
            f.write("# Repo\n")
        subprocess.run(["git", "add", "README.md"], cwd=path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=path, capture_output=True, check=True)

    def test_merge_success_when_verifier_passes(self):
        wt_a = self.runner.provision_worktree("agent-1")
        new_file = os.path.join(wt_a, "feature.py")
        with open(new_file, "w") as f:
            f.write("def feature(): return True\n")
        self.runner.commit_worktree("agent-1", "implement feature")

        result = self.runner.merge_worktree_transactional(
            agent_id="agent-1",
            test_verifier=lambda: True,
            dlq_dir=self.dlq_dir
        )
        self.assertTrue(result.success, f"Merge should succeed: {result.message}")
        self.assertEqual(result.status, "COMMITTED")
        self.assertFalse(result.rollback_performed)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, "feature.py")), "Merged file must exist in repo root.")

    def test_merge_rolls_back_when_verifier_fails(self):
        wt_a = self.runner.provision_worktree("agent-2")
        broken_file = os.path.join(wt_a, "broken.py")
        with open(broken_file, "w") as f:
            f.write("def broken(): raise RuntimeError()\n")
        self.runner.commit_worktree("agent-2", "add broken feature")

        # Test verifier simulates failing test suite
        result = self.runner.merge_worktree_transactional(
            agent_id="agent-2",
            test_verifier=lambda: False,
            dlq_dir=self.dlq_dir
        )
        self.assertFalse(result.success, "Merge should fail when test verifier fails.")
        self.assertEqual(result.status, "ROLLED_BACK")
        self.assertTrue(result.rollback_performed, "Saga rollback must be performed on verifier failure.")
        self.assertFalse(os.path.exists(os.path.join(self.tmp_dir, "broken.py")), "Broken file must NOT remain in repo root after rollback.")
        
        # Verify DLQ tombstone was written
        self.assertTrue(os.path.isdir(self.dlq_dir))
        tombstones = [f for f in os.listdir(self.dlq_dir) if f.endswith(".json")]
        self.assertGreaterEqual(len(tombstones), 1, "DLQ tombstone should be recorded for aborted merge.")


if __name__ == "__main__":
    unittest.main()
