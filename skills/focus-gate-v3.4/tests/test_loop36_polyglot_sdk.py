"""FocusGate v3.0 — Polyglot Actor SDK Specification & Client Tests (Loop 36).

Verifies cross-language protocol specifications (JSON Schema, TypeScript, Rust),
zero-dependency Python client connector, and shell IPC bridge.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import unittest

from core.sdk.protocol_spec import (
    get_protocol_schema,
    validate_rpc_message,
    export_typescript_definitions,
    export_rust_definitions
)
from core.sdk.shell_actor_bridge import FocusGateClient, ClientConnectionError, ShellActorBridge
from core.daemon.unified_supervisor import UnifiedSwarmSupervisor


class TestProtocolSpec(unittest.TestCase):
    """Verifies polyglot schema generation and message validation."""

    def test_get_protocol_schema(self):
        schema = get_protocol_schema()
        self.assertIsInstance(schema, dict)
        self.assertEqual(schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("properties", schema)
        self.assertIn("method", schema["properties"])
        self.assertIn("definitions", schema)

    def test_validate_rpc_message_success(self):
        valid_req = {
            "method": "ping",
            "params": {}
        }
        ok, err = validate_rpc_message(valid_req)
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_validate_rpc_message_invalid(self):
        invalid_req = {
            "not_a_method": 123
        }
        ok, err = validate_rpc_message(invalid_req)
        self.assertFalse(ok)
        self.assertIsNotNone(err)

    def test_export_typescript_definitions(self):
        ts_code = export_typescript_definitions()
        self.assertIn("export interface FocusGateMessage", ts_code)
        self.assertIn("export type FocusGateMethod", ts_code)
        self.assertIn("export interface SupervisorStatus", ts_code)

    def test_export_rust_definitions(self):
        rust_code = export_rust_definitions()
        self.assertIn("pub enum FocusGateMethod", rust_code)
        self.assertIn("pub struct FocusGateMessage", rust_code)
        self.assertIn("Serialize, Deserialize", rust_code)


class TestFocusGateClient(unittest.TestCase):
    """Verifies stdlib Python client connector against active supervisor."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.socket_path = os.path.join(self.test_dir, "test_client.sock")
        self.supervisor = UnifiedSwarmSupervisor(
            socket_path=self.socket_path,
            workspace_root=self.test_dir,
            poll_interval=0.1
        )
        self.supervisor.start()
        time.sleep(0.15)

    def tearDown(self):
        if self.supervisor:
            self.supervisor.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_client_ping(self):
        with FocusGateClient(socket_path=self.socket_path) as client:
            res = client.ping()
            self.assertTrue(res)

    def test_client_get_status(self):
        client = FocusGateClient(socket_path=self.socket_path)
        status = client.get_status()
        self.assertTrue(status.get("running"))
        self.assertIn("tracked_files", status)
        self.assertIn("actors", status)
        client.disconnect()

    def test_client_eval_gate(self):
        with FocusGateClient(socket_path=self.socket_path) as client:
            res = client.eval_gate("gate-sdk-01")
            self.assertEqual(res.get("verdict"), "PASS")
            self.assertEqual(res.get("gate_id"), "gate-sdk-01")

    def test_client_get_events(self):
        with FocusGateClient(socket_path=self.socket_path) as client:
            events = client.get_events(limit=10)
            self.assertIsInstance(events, list)
            self.assertTrue(len(events) > 0)
            event_types = [e.get("event_type") for e in events]
            self.assertIn("SUPERVISOR_STARTED", event_types)

    def test_client_connection_error_on_missing_socket(self):
        missing_sock = os.path.join(self.test_dir, "nonexistent.sock")
        client = FocusGateClient(socket_path=missing_sock)
        with self.assertRaises(ClientConnectionError):
            client.ping()


class TestShellActorBridge(unittest.TestCase):
    """Verifies shell one-liner generation and bridge execution."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.socket_path = os.path.join(self.test_dir, "test_shell.sock")
        self.supervisor = UnifiedSwarmSupervisor(
            socket_path=self.socket_path,
            workspace_root=self.test_dir,
            poll_interval=0.1
        )
        self.supervisor.start()
        time.sleep(0.15)

    def tearDown(self):
        if self.supervisor:
            self.supervisor.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_shell_command_generation(self):
        cmd = ShellActorBridge.generate_shell_command(self.socket_path, "ping")
        self.assertIn("python3", cmd)
        self.assertIn(self.socket_path, cmd)

    def test_exec_shell_request(self):
        resp = ShellActorBridge.exec_request(self.socket_path, "ping")
        self.assertIn("result", resp)
        self.assertTrue(resp["result"].get("pong"))


class TestSDKCLI(unittest.TestCase):
    """Verifies CLI flags for SDK schema and ping."""

    def test_cli_sdk_schema_json(self):
        from core.cli.dispatch import CLIDispatcher
        clean_args = ["--sdk-schema"]

        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = CLIDispatcher.dispatch_sdk_schema(clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(stdout.getvalue())
        self.assertIn("properties", output)
