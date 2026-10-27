"""Tests for Loop 27: Background Swarm Daemon (focus-gated) & Preview 1 Seal.

Tests SwarmDaemon Unix socket IPC server, SwarmDaemonClient protocol,
graceful shutdown, CLI flags (--daemon-status, --daemon-stop),
and Preview 1 release verification.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import io
import time
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from contextlib import redirect_stdout
from typing import Dict, Any

from core.swarm_daemon import SwarmDaemon, SwarmDaemonClient


class TestSwarmDaemonIPC(unittest.TestCase):
    """Test SwarmDaemon Unix domain socket server and client IPC."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_daemon_test_")
        self.sock_path = os.path.join(self.temp_dir, "test-daemon.sock")
        self.daemon = SwarmDaemon(socket_path=self.sock_path, workspace_root=self.temp_dir)
        self.daemon.start_background()
        # Wait up to 1 second for socket to appear
        for _ in range(50):
            if os.path.exists(self.sock_path):
                break
            time.sleep(0.02)

    def tearDown(self):
        if self.daemon.is_alive():
            self.daemon.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_daemon_ping(self):
        client = SwarmDaemonClient(socket_path=self.sock_path)
        res = client.ping()
        self.assertTrue(res.get("pong", False))
        self.assertEqual(res.get("version"), "3.0.0-preview.1")

    def test_daemon_status(self):
        client = SwarmDaemonClient(socket_path=self.sock_path)
        status = client.status()
        self.assertTrue(status.get("running", False))
        self.assertEqual(status.get("version"), "3.0.0-preview.1")
        self.assertIn("uptime_seconds", status)
        self.assertIn("registered_actors", status)

    def test_daemon_stop_and_cleanup(self):
        client = SwarmDaemonClient(socket_path=self.sock_path)
        res = client.stop()
        self.assertTrue(res.get("stopped", False))
        time.sleep(0.1)
        self.assertFalse(self.daemon.is_alive())


class TestSwarmDaemonCLI(unittest.TestCase):
    """Test CLI dispatch for --daemon-status and --daemon-stop."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_daemon_cli_")
        self.sock_path = os.path.join(self.temp_dir, "cli-daemon.sock")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_status_offline(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(daemon_status=True, daemon_stop=None, daemon_start=None)
        clean_args = ["--daemon-status", self.sock_path, "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 1)
        output = json.loads(buf.getvalue())
        self.assertFalse(output["running"])
        self.assertIn("offline", output["status"].lower())

    def test_cli_status_online_and_stop(self):
        from core.cli.dispatch import CLIDispatcher

        daemon = SwarmDaemon(socket_path=self.sock_path, workspace_root=self.temp_dir)
        daemon.start_background()
        for _ in range(50):
            if os.path.exists(self.sock_path):
                break
            time.sleep(0.02)

        try:
            # Test status online
            args = SimpleNamespace(daemon_status=True, daemon_stop=None, daemon_start=None)
            clean_args = ["--daemon-status", self.sock_path, "--json"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

            self.assertEqual(code, 0)
            output = json.loads(buf.getvalue())
            self.assertTrue(output["running"])

            # Test stop
            args_stop = SimpleNamespace(daemon_stop=True, daemon_status=None, daemon_start=None)
            clean_args_stop = ["--daemon-stop", self.sock_path, "--json"]
            buf_stop = io.StringIO()
            with redirect_stdout(buf_stop):
                code_stop = CLIDispatcher.dispatch(args_stop, clean_args_stop, is_json=True)

            self.assertEqual(code_stop, 0)
            output_stop = json.loads(buf_stop.getvalue())
            self.assertTrue(output_stop["stopped"])
        finally:
            if daemon.is_alive():
                daemon.stop()


if __name__ == '__main__':
    unittest.main()
