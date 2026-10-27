"""Tests for Loop 28: Ephemeral Worktree Swarm Isolation & Saga Rollback Engine.

Tests ActorWorktreeManager filesystem isolation per actor,
SagaMergeCoordinator atomic merges, verification barrier checks,
and tombstone rollbacks on conflict/failure.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
import unittest
from types import SimpleNamespace
from contextlib import redirect_stdout
from typing import Dict, Any

from core.mesh import CoderActor
from core.swarm.actor_worktree import ActorWorktreeManager
from core.swarm.saga_merge import SagaMergeCoordinator, SagaMergeResult


class TestActorWorktreeManager(unittest.TestCase):
    """Test filesystem isolation and worktree lifecycle per swarm actor."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_wt_test_")
        # Initialize a real git repo in temp_dir
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@focusgate.io"], cwd=self.temp_dir, check=True)

        # Initial commit on main
        init_file = os.path.join(self.temp_dir, "README.md")
        with open(init_file, "w") as f:
            f.write("# Main Repo\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.temp_dir, check=True)

        self.mgr = ActorWorktreeManager(repo_root=self.temp_dir)

    def tearDown(self):
        self.mgr.cleanup_all(force=True)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_provision_and_cleanup(self):
        actor_id = "actor-coder-01"
        wt_path = self.mgr.provision_worktree(actor_id)
        self.assertTrue(os.path.isdir(wt_path))
        self.assertTrue(os.path.exists(os.path.join(wt_path, "README.md")))

        # Verify active mapping
        self.assertEqual(self.mgr.get_worktree_path(actor_id), wt_path)

        # Cleanup
        self.mgr.cleanup_worktree(actor_id)
        self.assertFalse(os.path.exists(wt_path))
        self.assertIsNone(self.mgr.get_worktree_path(actor_id))

    def test_isolation_between_actors(self):
        wt1 = self.mgr.provision_worktree("coder-1")
        wt2 = self.mgr.provision_worktree("coder-2")

        # Coder 1 creates a file in wt1
        f1 = os.path.join(wt1, "feature_1.py")
        with open(f1, "w") as f:
            f.write("# feature 1\n")

        # Coder 2 creates a file in wt2
        f2 = os.path.join(wt2, "feature_2.py")
        with open(f2, "w") as f:
            f.write("# feature 2\n")

        # Neither can see the other's file
        self.assertTrue(os.path.exists(f1))
        self.assertFalse(os.path.exists(os.path.join(wt2, "feature_1.py")))
        self.assertTrue(os.path.exists(f2))
        self.assertFalse(os.path.exists(os.path.join(wt1, "feature_2.py")))

    def test_run_in_worktree(self):
        actor_id = "actor-tester"
        self.mgr.provision_worktree(actor_id)

        res = self.mgr.run_in_worktree(actor_id, [sys.executable, "-c", "print('ISOLATED_OK')"])
        self.assertTrue(res.success)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("ISOLATED_OK", res.stdout)


class TestSagaMergeCoordinator(unittest.TestCase):
    """Test atomic Saga merges, verification barriers, and rollback tombstones."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_saga_test_")
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@focusgate.io"], cwd=self.temp_dir, check=True)

        init_file = os.path.join(self.temp_dir, "app.py")
        with open(init_file, "w") as f:
            f.write("def run(): return 1\n")
        subprocess.run(["git", "add", "app.py"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.temp_dir, check=True)

        self.mgr = ActorWorktreeManager(repo_root=self.temp_dir)
        self.saga = SagaMergeCoordinator(worktree_manager=self.mgr)

    def tearDown(self):
        self.mgr.cleanup_all(force=True)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_successful_saga_merge(self):
        actor_id = "actor-success"
        wt_path = self.mgr.provision_worktree(actor_id)

        # Modify app.py in worktree and commit
        with open(os.path.join(wt_path, "app.py"), "w") as f:
            f.write("def run(): return 42\n")
        subprocess.run(["git", "add", "app.py"], cwd=wt_path, check=True)
        subprocess.run(["git", "commit", "-m", "Implement run()=42"], cwd=wt_path, check=True)

        # Merge with passing verification command
        res = self.saga.merge_actor_branch(
            actor_id=actor_id,
            gate_id="gate-run-42",
            verify_cmd=f"{sys.executable} -c 'import app; assert app.run() == 42'"
        )

        self.assertTrue(res.success)
        self.assertEqual(res.status, "COMMITTED")
        self.assertEqual(res.actor_id, actor_id)

        # Main repo now reflects the change
        with open(os.path.join(self.temp_dir, "app.py"), "r") as f:
            content = f.read()
        self.assertIn("return 42", content)

    def test_failed_verification_aborts_saga(self):
        actor_id = "actor-fail"
        wt_path = self.mgr.provision_worktree(actor_id)

        with open(os.path.join(wt_path, "app.py"), "w") as f:
            f.write("def run(): return 0\n")
        subprocess.run(["git", "add", "app.py"], cwd=wt_path, check=True)
        subprocess.run(["git", "commit", "-m", "Implement faulty return 0"], cwd=wt_path, check=True)

        # Merge with failing verification command
        res = self.saga.merge_actor_branch(
            actor_id=actor_id,
            gate_id="gate-fail-check",
            verify_cmd=f"{sys.executable} -c 'import app; assert app.run() == 42'"
        )

        self.assertFalse(res.success)
        self.assertEqual(res.status, "ROLLED_BACK")
        self.assertIsNotNone(res.tombstone_id)

        # Main repo is untouched (still return 1)
        with open(os.path.join(self.temp_dir, "app.py"), "r") as f:
            content = f.read()
        self.assertIn("return 1", content)


class TestSwarmWorktreeCLI(unittest.TestCase):
    """Test CLI dispatch for --swarm-worktree and --swarm-merge."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_wt_cli_")
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@focusgate.io"], cwd=self.temp_dir, check=True)

        with open(os.path.join(self.temp_dir, "README.md"), "w") as f:
            f.write("# Root\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Init"], cwd=self.temp_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_swarm_worktree_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(swarm_worktree=True, swarm_merge=None)
        clean_args = ["--swarm-worktree", "coder-cli", "--repo", self.temp_dir, "--json"]

        import io
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["actor_id"], "coder-cli")
        self.assertTrue(os.path.isdir(output["worktree_path"]))

        # Cleanup
        mgr = ActorWorktreeManager(repo_root=self.temp_dir)
        mgr.cleanup_all(force=True)


if __name__ == '__main__':
    unittest.main()
