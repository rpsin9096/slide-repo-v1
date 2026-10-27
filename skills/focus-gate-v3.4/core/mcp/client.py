"""FocusGate v3.0 — Native Stdlib Model Context Protocol (MCP) Client.

Implements a lightweight, zero-dependency JSON-RPC 2.0 MCP Client over stdio
or in-memory direct transport:
- Subprocess stdio pipe transport (spawn any external MCP tool server)
- Direct in-memory transport (zero-overhead in-process communication)
- JSON-RPC 2.0 request/response correlation with monotonic request IDs
- MCP lifecycle: initialize, notifications/initialized, tools/list, tools/call

Zero external dependencies (100% Python stdlib).
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any, List, Optional, Tuple


class StdlibMCPClient:
    """Lightweight stdio & in-memory MCP client adhering to MCP 2024-11-05."""

    PROTOCOL_VERSION = "2024-11-05"

    def __init__(
        self,
        process: Optional[subprocess.Popen] = None,
        in_memory_server: Optional[Any] = None
    ):
        self.process = process
        self.in_memory_server = in_memory_server
        self._request_id = 0
        self.server_info: Dict[str, Any] = {}
        self.initialized: bool = False

    @classmethod
    def spawn(
        cls,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None
    ) -> "StdlibMCPClient":
        """Spawns an external MCP tool server as a subprocess communicating over stdio."""
        cmd_list = [command] + (list(args) if args else [])
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        proc = subprocess.Popen(
            cmd_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=merged_env
        )
        return cls(process=proc)

    @classmethod
    def create_in_memory(cls, server: Any) -> "StdlibMCPClient":
        """Creates an MCP client wired directly to an in-memory FocusMCPServer instance."""
        return cls(in_memory_server=server)

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Sends a JSON-RPC 2.0 request and waits for response."""
        req_id = self._next_id()
        msg = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {}
        }

        if self.in_memory_server is not None:
            resp = self.in_memory_server.handle_message(msg)
            if not resp:
                return {}
            if "error" in resp:
                err_msg = resp["error"].get("message", "Unknown MCP error")
                raise RuntimeError(f"MCP RPC Error ({resp['error'].get('code')}): {err_msg}")
            return resp.get("result", {})

        if self.process is None or self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("MCP Client is not connected to a server process.")

        try:
            raw_line = json.dumps(msg) + "\n"
            self.process.stdin.write(raw_line)
            self.process.stdin.flush()

            line = self.process.stdout.readline()
            if not line:
                stderr_out = self.process.stderr.read() if self.process.stderr else ""
                raise RuntimeError(f"MCP server closed stdout stream. Stderr: {stderr_out}")

            resp = json.loads(line.strip())
            if "error" in resp:
                err_msg = resp["error"].get("message", "Unknown MCP error")
                raise RuntimeError(f"MCP RPC Error ({resp['error'].get('code')}): {err_msg}")
            return resp.get("result", {})
        except (BrokenPipeError, OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"MCP communication failure: {exc}")

    def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Sends a JSON-RPC 2.0 notification (no response expected)."""
        msg = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }

        if self.in_memory_server is not None:
            self.in_memory_server.handle_message(msg)
            return

        if self.process and self.process.stdin:
            try:
                raw_line = json.dumps(msg) + "\n"
                self.process.stdin.write(raw_line)
                self.process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

    def initialize(
        self,
        client_name: str = "focus-gate-mesh",
        client_version: str = "3.0.0"
    ) -> Dict[str, Any]:
        """Performs initial MCP protocol handshake."""
        result = self.send_request("initialize", {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": client_name,
                "version": client_version
            }
        })
        self.server_info = result.get("serverInfo", {})
        self.initialized = True
        self.send_notification("notifications/initialized", {})
        return result

    def list_tools(self) -> List[Dict[str, Any]]:
        """Queries the server's registered tool catalog."""
        result = self.send_request("tools/list", {})
        return result.get("tools", [])

    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invokes a specific tool on the remote MCP server."""
        return self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })

    def close(self) -> None:
        """Terminates server subprocess and cleans up open pipes."""
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                if self.process.stdout:
                    self.process.stdout.close()
                if self.process.stderr:
                    self.process.stderr.close()
                self.process.terminate()
                self.process.wait(timeout=1.0)
            except (subprocess.TimeoutExpired, OSError):
                self.process.kill()
            finally:
                self.process = None

    def __enter__(self) -> "StdlibMCPClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
