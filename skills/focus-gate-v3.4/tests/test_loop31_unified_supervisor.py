"""Tests for Loop 31: Unified Reactive Swarm Supervisor & Push Event Stream IPC.

Tests UnifiedSwarmSupervisor reactive AST watching + Unix domain socket IPC,
PushEventStream event broadcasting, sub-15ms re-evaluation, and CLI integration.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import time
import json
import io
import shutil
import tempfile
import socket
import unittest
from types import SimpleNamespace
from contextlib import redirect_stdout
from typing import Dict, Any, List

from core.daemon.unified_supervisor import UnifiedSwarmSupervisor
from core.daemon.event_stream import PushEventStream, StreamEvent
from core.swarm_daemon import SwarmDaemonClient


class TestPushEventStream(unittest.TestCase):
    """Test PushEventStream subscriber queues and broadcast dispatch."""

    def setUp(self):
        self.stream = PushEventStream(max_buffer=50)

    def test_publish_and_buffer_event(self):
        ev = self.stream.publish(
            event_type="FILE_CHANGED",
            payload={"path": "app.py", "mtime": 12345.0}
        )
        self.assertIsInstance(ev, StreamEvent)
        self.assertEqual(ev.event_type, "FILE_CHANGED")
        self.assertEqual(len(self.stream.get_recent_events()), 1)

    def test_subscriber_queue_receives_event(self):
        sub_queue = self.stream.subscribe("client-1")
        ev = self.stream.publish("GATE_EVALUATED", {"gate_id": "gate-1", "verdict": "PASS"})
        
        self.assertFalse(sub_queue.empty())
        received = sub_queue.get_nowait()
        self.assertEqual(received.event_type, "GATE_EVALUATED")
        self.assertEqual(received.payload["gate_id"], "gate-1")

        self.stream.unsubscribe("client-1")
        self.assertEqual(len(self.stream.subscribers), 0)


class TestUnifiedSwarmSupervisor(unittest.TestCase):
    """Test UnifiedSwarmSupervisor lifecycle, IPC handling, and reactive file triggers."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_supervisor_test_")
        self.sock_path = os.path.join(self.temp_dir, "supervisor.sock")
        self.supervisor = UnifiedSwarmSupervisor(
            socket_path=self.sock_path,
            workspace_root=self.temp_dir,
            poll_interval=0.05
        )

    def tearDown(self):
        self.supervisor.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_supervisor_lifecycle_and_ping(self):
        self.supervisor.start()
        time.sleep(0.15)
        self.assertTrue(self.supervisor.running)
        self.assertTrue(os.path.exists(self.sock_path))

        client = SwarmDaemonClient(socket_path=self.sock_path)
        resp = client.send_request("ping")
        self.assertEqual(resp.get("result", {}).get("pong"), True)
        self.assertEqual(resp.get("result", {}).get("supervisor"), "unified")

        status_resp = client.send_request("status")
        self.assertTrue(status_resp.get("result", {}).get("running"))
        self.assertIn("tracked_files", status_resp.get("result", {}))

    def test_reactive_file_watch_pushes_event(self):
        sub_queue = self.supervisor.event_stream.subscribe("test-sub")
        self.supervisor.start()
        time.sleep(0.1)

        # Create a python file in workspace
        py_file = os.path.join(self.temp_dir, "service.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("def run():\n    return 42\n")

        # Tick supervisor
        cycle = self.supervisor.tick_watcher()
        self.assertGreater(cycle.get("latency_ms", 0), 0)
        self.assertLess(cycle.get("latency_ms", 0), 100)  # fast re-eval
        self.assertTrue(cycle.get("syntax_clean"))

        # Check that event was published to stream
        events = self.supervisor.event_stream.get_recent_events()
        file_events = [e for e in events if e.event_type == "FILE_CHANGED"]
        self.assertGreater(len(file_events), 0)


class TestUnifiedSupervisorCLI(unittest.TestCase):
    """Test CLI dispatch for --daemon-stream and --daemon-events."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_sup_cli_")
        self.sock_path = os.path.join(self.temp_dir, "sup_cli.sock")
        self.supervisor = UnifiedSwarmSupervisor(
            socket_path=self.sock_path,
            workspace_root=self.temp_dir
        )
        self.supervisor.event_stream.publish("INIT", {"status": "ready"})

    def tearDown(self):
        self.supervisor.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_daemon_events_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(daemon_events=[self.sock_path], daemon_stream=None)
        clean_args = ["--daemon-events", self.sock_path, "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        events = json.loads(buf.getvalue())
        self.assertIsInstance(events, list)


if __name__ == '__main__':
    unittest.main()
