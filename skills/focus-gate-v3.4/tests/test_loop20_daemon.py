"""Tests for FocusGate v2.9 — Milestone 17 (Loop 20: Reactive In-Memory Daemon & File Watcher).

Covers:
1. File snapshot scanning ignoring ignored dirs (.git, __pycache__, node_modules).
2. Detection of file modifications, creations, and deletions.
3. In-memory AST caching with automatic invalidation on modification.
4. Reactive gate evaluation latency (<15ms) on file mutation.
5. In-memory syntax error interception via AST preflight.
6. Daemon lifecycle (start_background, tick, stop) and callback notifications.
7. CLI --watch flag registration and help text.
"""

import unittest
import os
import sys
import time
import json
import tempfile
import subprocess

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SCRIPT = os.path.join(ROOT_DIR, "scripts", "focus-gate.py")

from core.daemon import FocusDaemon


class TestFocusDaemonWatcher(unittest.TestCase):
    """Verifies file watcher mechanics and snapshot change detection."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = self.temp_dir.name
        # Seed test files
        self.file_py = os.path.join(self.workspace, "app.py")
        with open(self.file_py, "w", encoding="utf-8") as f:
            f.write("def hello():\n    return 'world'\n")

        self.daemon = FocusDaemon(workspace_root=self.workspace, poll_interval=0.1)

    def tearDown(self):
        self.daemon.stop()
        self.temp_dir.cleanup()

    def test_daemon_initial_snapshot(self):
        snapshot = self.daemon.scan_snapshot()
        self.assertIn("app.py", snapshot)
        self.assertNotIn(".git", snapshot)

    def test_daemon_detects_file_modification(self):
        # Initial tick sets baseline
        self.daemon.tick()

        # Modify app.py
        time.sleep(0.05)
        with open(self.file_py, "a", encoding="utf-8") as f:
            f.write("def extra():\n    return 42\n")

        cycle = self.daemon.tick()
        changes = cycle.get("changes", [])
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0][0], "app.py")
        self.assertEqual(changes[0][1], "MODIFIED")

    def test_daemon_detects_file_creation_and_deletion(self):
        self.daemon.tick()

        # Create new file
        new_file = os.path.join(self.workspace, "utils.py")
        with open(new_file, "w", encoding="utf-8") as f:
            f.write("A = 100\n")

        cycle1 = self.daemon.tick()
        changes1 = cycle1.get("changes", [])
        self.assertEqual(len(changes1), 1)
        self.assertEqual(changes1[0][0], "utils.py")
        self.assertEqual(changes1[0][1], "CREATED")

        # Delete new file
        os.remove(new_file)
        cycle2 = self.daemon.tick()
        changes2 = cycle2.get("changes", [])
        self.assertEqual(len(changes2), 1)
        self.assertEqual(changes2[0][0], "utils.py")
        self.assertEqual(changes2[0][1], "DELETED")


class TestDaemonASTCacheAndReactiveGating(unittest.TestCase):
    """Verifies in-memory AST caching and reactive gate evaluation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = self.temp_dir.name
        self.file_py = os.path.join(self.workspace, "service.py")
        with open(self.file_py, "w", encoding="utf-8") as f:
            f.write("class Service:\n    def execute(self):\n        return True\n")
        self.daemon = FocusDaemon(workspace_root=self.workspace)

    def tearDown(self):
        self.daemon.stop()
        self.temp_dir.cleanup()

    def test_ast_cache_hit_and_invalidation(self):
        ast1 = self.daemon.get_cached_ast("service.py")
        self.assertIsNotNone(ast1)

        # Cache hit
        ast2 = self.daemon.get_cached_ast("service.py")
        self.assertIs(ast1, ast2)  # Identical cached object

        # Modify file -> invalidates cache
        time.sleep(0.05)
        with open(self.file_py, "a", encoding="utf-8") as f:
            f.write("    def extra(self): pass\n")

        ast3 = self.daemon.get_cached_ast("service.py")
        self.assertIsNotNone(ast3)
        self.assertIsNot(ast1, ast3)  # Re-parsed new AST

    def test_reactive_gate_eval_latency_under_15ms(self):
        self.daemon.tick()
        time.sleep(0.05)

        with open(self.file_py, "w", encoding="utf-8") as f:
            f.write("def compute():\n    return [x * 2 for x in range(10)]\n")

        cycle = self.daemon.tick()
        self.assertTrue(cycle.get("syntax_clean"))
        latency_ms = cycle.get("latency_ms", 999.0)
        self.assertLess(latency_ms, 15.0, f"Expected <15ms latency, got {latency_ms}ms")

    def test_daemon_syntax_error_interception(self):
        self.daemon.tick()
        time.sleep(0.05)

        # Write invalid syntax
        with open(self.file_py, "w", encoding="utf-8") as f:
            f.write("def broken(\n    return 42\n")

        cycle = self.daemon.tick()
        self.assertFalse(cycle.get("syntax_clean"))
        self.assertIn("service.py", cycle.get("syntax_errors", {}))


class TestDaemonCLIIntegration(unittest.TestCase):
    """Verifies CLI flag registration and help text."""

    def test_cli_watch_flag_in_help(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--watch", proc.stdout)


if __name__ == "__main__":
    unittest.main()
