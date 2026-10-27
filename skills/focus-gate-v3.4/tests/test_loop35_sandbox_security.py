"""Tests for Loop 35: Destructive Action Sandbox & Security Guardrails.

Tests PathJailSandbox path confinement, CommandGuard destructive command blocking,
safe command execution, and CLI integration.

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

from core.sandbox.path_jail import PathJailSandbox, PathJailViolationError
from core.sandbox.command_guard import CommandGuard, BlockedCommandError


class TestPathJailSandbox(unittest.TestCase):
    """Test filesystem confinement and path traversal interception."""

    def setUp(self):
        self.jail_root = tempfile.mkdtemp(prefix="focusgate_jail_root_")
        self.sandbox = PathJailSandbox(root_path=self.jail_root)

    def tearDown(self):
        shutil.rmtree(self.jail_root, ignore_errors=True)

    def test_safe_path_resolution_within_jail(self):
        resolved = self.sandbox.resolve_safe_path("src/app.py")
        self.assertTrue(resolved.startswith(self.sandbox.root_path))

    def test_path_traversal_attack_blocked(self):
        with self.assertRaises(PathJailViolationError):
            self.sandbox.resolve_safe_path("../../etc/passwd")

    def test_absolute_path_escape_blocked(self):
        with self.assertRaises(PathJailViolationError):
            self.sandbox.resolve_safe_path("/var/log/system.log")


class TestCommandGuard(unittest.TestCase):
    """Test destructive shell command pattern interception."""

    def setUp(self):
        self.guard = CommandGuard()

    def test_block_destructive_rm(self):
        blocked, reason = self.guard.is_destructive("rm -rf /")
        self.assertTrue(blocked)
        self.assertIn("root deletion", reason.lower())

    def test_block_force_push(self):
        blocked, reason = self.guard.is_destructive("git push --force origin main")
        self.assertTrue(blocked)
        self.assertIn("force push", reason.lower())

    def test_block_fork_bomb(self):
        blocked, reason = self.guard.is_destructive(":(){ :|:& };:")
        self.assertTrue(blocked)

    def test_allow_safe_commands(self):
        safe_cmds = [
            "python3 -m unittest",
            "git status",
            "ls -la",
            "cat GATES.md",
            "pytest tests/"
        ]
        for cmd in safe_cmds:
            blocked, reason = self.guard.is_destructive(cmd)
            self.assertFalse(blocked, f"Safe command '{cmd}' was incorrectly blocked: {reason}")


class TestSandboxCLI(unittest.TestCase):
    """Test CLI dispatch for --sandbox-exec and --verify-sandbox."""

    def test_cli_verify_sandbox_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(verify_sandbox=True, sandbox_exec=None)
        clean_args = ["--verify-sandbox", "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("sandbox_status", output)
        self.assertEqual(output["sandbox_status"], "ACTIVE")


if __name__ == '__main__':
    unittest.main()
