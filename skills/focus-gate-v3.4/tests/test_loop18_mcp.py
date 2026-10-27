"""Tests for FocusGate v2.9 — Milestone 15 (Loop 18: Pure Stdlib Model Context Protocol Server).

Covers:
1. JSON-RPC 2.0 protocol compliance (initialize, ping, notifications/initialized).
2. MCP tools/list catalog exposing 6 FocusGate core tools.
3. MCP tools/call dispatch for synthesize_pipeline, audit_code_cliche, patch_preflight, adversarial_audit.
4. Error handling for unknown methods and missing arguments.
5. CLI --mcp flag registration and stdio streaming pipeline.
"""

import unittest
import os
import sys
import subprocess
import json

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SCRIPT = os.path.join(ROOT_DIR, "scripts", "focus-gate.py")

from core.mcp_server import FocusMCPServer


class TestMCPServerProtocol(unittest.TestCase):
    """Verifies FocusMCPServer JSON-RPC 2.0 protocol mechanics."""

    def setUp(self):
        self.server = FocusMCPServer(workspace_root=ROOT_DIR)

    def test_mcp_initialize_handshake(self):
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        res = self.server.handle_message(msg)
        self.assertEqual(res.get("jsonrpc"), "2.0")
        self.assertEqual(res.get("id"), 1)
        self.assertIn("result", res)
        result = res["result"]
        self.assertEqual(result.get("protocolVersion"), "2024-11-05")
        self.assertEqual(result.get("serverInfo", {}).get("name"), "focus-gate")
        self.assertIn("capabilities", result)

    def test_mcp_ping(self):
        msg = {"jsonrpc": "2.0", "id": 42, "method": "ping", "params": {}}
        res = self.server.handle_message(msg)
        self.assertEqual(res.get("jsonrpc"), "2.0")
        self.assertEqual(res.get("id"), 42)
        self.assertEqual(res.get("result"), {})

    def test_mcp_initialized_notification_no_response(self):
        msg = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        res = self.server.handle_message(msg)
        self.assertIsNone(res)

    def test_mcp_tools_list(self):
        msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        res = self.server.handle_message(msg)
        self.assertIn("result", res)
        tools = res["result"].get("tools", [])
        tool_names = {t["name"] for t in tools}
        expected_tools = {
            "verify_wave",
            "audit_code_cliche",
            "patch_preflight",
            "synthesize_pipeline",
            "stage_frontier",
            "adversarial_audit"
        }
        self.assertTrue(expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}")


class TestMCPToolExecution(unittest.TestCase):
    """Verifies execution of individual tools via tools/call."""

    def setUp(self):
        self.server = FocusMCPServer(workspace_root=ROOT_DIR)

    def test_tool_call_synthesize_pipeline(self):
        msg = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "synthesize_pipeline",
                "arguments": {"task_description": "Fix navigation bar active link color and contrast ratio"}
            }
        }
        res = self.server.handle_message(msg)
        self.assertEqual(res.get("id"), 10)
        self.assertIn("result", res)
        content = res["result"]["content"]
        self.assertTrue(len(content) > 0)
        payload = json.loads(content[0]["text"])
        self.assertIn("pipeline", payload)

    def test_tool_call_audit_code_cliche(self):
        shotgun_code = "def worker():\n    try:\n        run()\n    except Exception:\n        pass\n"
        msg = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "audit_code_cliche",
                "arguments": {"content": shotgun_code, "filename": "worker.py"}
            }
        }
        res = self.server.handle_message(msg)
        self.assertEqual(res.get("id"), 11)
        content = res["result"]["content"]
        payload = json.loads(content[0]["text"])
        self.assertFalse(payload["clean"])
        self.assertTrue(any(f["rule_id"] == "CODE_SHOTGUN_SUPPRESSION" for f in payload["findings"]))
        self.assertTrue(len(payload["findings"][0]["prescribed_remedy"]) > 10)

    def test_tool_call_patch_preflight(self):
        bad_syntax_code = "def parse(x:\n    return x + 1"
        msg = {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {
                "name": "patch_preflight",
                "arguments": {"content": bad_syntax_code, "filename": "parser.py"}
            }
        }
        res = self.server.handle_message(msg)
        self.assertEqual(res.get("id"), 12)
        content = res["result"]["content"]
        payload = json.loads(content[0]["text"])
        self.assertFalse(payload["valid"])
        self.assertIn("SyntaxError", payload["reason"])

    def test_tool_call_adversarial_audit(self):
        msg = {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {
                "name": "adversarial_audit",
                "arguments": {"proposal": "Implement decentralized consensus using raft and epoch fencing."}
            }
        }
        res = self.server.handle_message(msg)
        self.assertEqual(res.get("id"), 13)
        content = res["result"]["content"]
        payload = json.loads(content[0]["text"])
        self.assertIn("status", payload)
        self.assertEqual(payload.get("total_rounds"), 3)

    def test_tool_call_unknown_tool_returns_error(self):
        msg = {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "tools/call",
            "params": {
                "name": "non_existent_tool_xyz",
                "arguments": {}
            }
        }
        res = self.server.handle_message(msg)
        self.assertEqual(res.get("id"), 14)
        self.assertIn("error", res)
        self.assertEqual(res["error"]["code"], -32601)


class TestMCPCLIIntegration(unittest.TestCase):
    """Verifies CLI flag registration and pipe communication."""

    def test_cli_mcp_flag_in_help(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--mcp", proc.stdout)

    def test_cli_mcp_stdio_pipe_execution(self):
        req = json.dumps({"jsonrpc": "2.0", "id": 99, "method": "tools/list", "params": {}})
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--mcp"],
            input=req + "\n",
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            check=False
        )
        self.assertEqual(proc.returncode, 0)
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        self.assertTrue(len(lines) > 0, f"Expected output, got: {proc.stdout}")
        resp = json.loads(lines[0])
        self.assertEqual(resp.get("id"), 99)
        self.assertIn("result", resp)
        self.assertIn("tools", resp["result"])


if __name__ == "__main__":
    unittest.main()
