"""Tests for Loop 25: Bidirectional MCP Mesh Hub (Server + Client).

Tests StdlibMCPClient JSON-RPC 2.0 communication over stdio,
MCPMeshHub tool aggregation and namespaced routing,
and CLI commands --mcp-hub and --mcp-call.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import io
import unittest
from types import SimpleNamespace
from contextlib import redirect_stdout
from typing import Dict, Any

from core.mcp_server import FocusMCPServer
from core.mcp.client import StdlibMCPClient
from core.mcp.mesh_hub import MCPMeshHub


class TestStdlibMCPClient(unittest.TestCase):
    """Test JSON-RPC 2.0 MCP Client communication and lifecycle."""

    def test_client_in_memory_transport(self):
        """Verify client can communicate with a FocusMCPServer directly via in-memory transport."""
        server = FocusMCPServer()
        client = StdlibMCPClient.create_in_memory(server)

        # Initialize
        init_res = client.initialize()
        self.assertIn("serverInfo", init_res)
        self.assertEqual(init_res["serverInfo"]["name"], "focus-gate")

        # List tools
        tools = client.list_tools()
        self.assertIsInstance(tools, list)
        tool_names = [t["name"] for t in tools]
        self.assertIn("synthesize_pipeline", tool_names)
        self.assertIn("verify_wave", tool_names)

        # Call tool
        call_res = client.call_tool(
            "synthesize_pipeline",
            {"task_description": "Implement authentication gate"}
        )
        self.assertIn("content", call_res)
        self.assertFalse(call_res.get("isError", False))

    def test_client_subshell_transport(self):
        """Verify client can launch a python subprocess running focus-gate.py --mcp."""
        cli_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "focus-gate.py"))
        client = StdlibMCPClient.spawn(sys.executable, [cli_path, "--mcp"])
        try:
            init_res = client.initialize()
            self.assertEqual(init_res["serverInfo"]["name"], "focus-gate")

            tools = client.list_tools()
            self.assertTrue(len(tools) >= 5)

            call_res = client.call_tool("synthesize_pipeline", {"task_description": "test task"})
            self.assertIn("content", call_res)
        finally:
            client.close()


class TestMCPMeshHub(unittest.TestCase):
    """Test MCP Mesh Hub aggregation, namespacing, and routing."""

    def setUp(self):
        self.hub = MCPMeshHub()

    def tearDown(self):
        self.hub.shutdown_all()

    def test_register_local_server(self):
        server = FocusMCPServer()
        self.hub.register_local_server("local", server)

        catalog = self.hub.list_all_tools()
        self.assertTrue(len(catalog) >= 5)

        names = [t["namespaced_name"] for t in catalog]
        self.assertIn("local.synthesize_pipeline", names)
        self.assertIn("local.verify_wave", names)

        # Invoke through hub
        res = self.hub.invoke_tool("local.synthesize_pipeline", {"task_description": "fix bug"})
        self.assertIn("content", res)
        self.assertFalse(res.get("isError", False))

    def test_register_remote_client(self):
        server = FocusMCPServer()
        client = StdlibMCPClient.create_in_memory(server)
        self.hub.register_client("external_agent", client)

        catalog = self.hub.list_all_tools()
        names = [t["namespaced_name"] for t in catalog]
        self.assertIn("external_agent.adversarial_audit", names)

        # Invoke through hub
        res = self.hub.invoke_tool(
            "external_agent.adversarial_audit",
            {"proposal": "Use global shared state for everything"}
        )
        self.assertIn("content", res)

    def test_invoke_unknown_tool_returns_error(self):
        res = self.hub.invoke_tool("nonexistent.tool", {})
        self.assertTrue(res.get("isError", False))
        self.assertIn("Unknown tool", res["content"][0]["text"])

    def test_load_from_config_dict(self):
        config = {
            "servers": {
                "local_proc": {
                    "command": sys.executable,
                    "args": [
                        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "focus-gate.py")),
                        "--mcp"
                    ]
                }
            }
        }
        self.hub.load_config(config)
        catalog = self.hub.list_all_tools()
        names = [t["namespaced_name"] for t in catalog]
        self.assertIn("local_proc.synthesize_pipeline", names)


class TestMCPHubCLI(unittest.TestCase):
    """Test CLI dispatch for --mcp-hub and --mcp-call."""

    def test_cli_mcp_hub_list_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(mcp_hub=True, mcp_call=None)
        clean_args = ["--mcp-hub", "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("tools", output)
        self.assertTrue(len(output["tools"]) >= 5)

    def test_cli_mcp_call_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(mcp_call=True, mcp_hub=None)
        clean_args = [
            "--mcp-call", "local", "synthesize_pipeline",
            json.dumps({"task_description": "Build user auth"}),
            "--json"
        ]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("content", output)


if __name__ == '__main__':
    unittest.main()
