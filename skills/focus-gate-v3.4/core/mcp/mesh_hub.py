"""FocusGate v3.0 — Bidirectional MCP Mesh Hub Orchestrator.

Aggregates local FocusGate tools and external connected MCP servers into a unified,
namespaced tool discovery registry:
- Dynamic tool discovery across local servers and remote subprocesses
- Namespaced routing (<server>.<tool>) preventing collisions
- Configuration-driven multi-server orchestration
- Zero-leak clean lifecycle management and process shutdown

Zero external dependencies (100% Python stdlib).
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional, Union

from core.mcp_server import FocusMCPServer
from core.mcp.client import StdlibMCPClient


class MCPMeshHub:
    """Central orchestrator aggregating local and remote MCP tool providers."""

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.getcwd()
        self.local_servers: Dict[str, FocusMCPServer] = {}
        self.clients: Dict[str, StdlibMCPClient] = {}

    def register_local_server(self, name: str, server: FocusMCPServer) -> None:
        """Registers an in-process FocusMCPServer instance."""
        self.local_servers[name] = server

    def register_client(self, name: str, client: StdlibMCPClient) -> None:
        """Registers and initializes an external StdlibMCPClient."""
        if not client.initialized:
            client.initialize()
        self.clients[name] = client

    def load_config(self, config_or_path: Union[str, Dict[str, Any]]) -> None:
        """Loads and connects to remote MCP servers specified in configuration."""
        if isinstance(config_or_path, str):
            if not os.path.isfile(config_or_path):
                return
            with open(config_or_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = config_or_path

        servers_cfg = config.get("servers", {})
        for srv_name, srv_def in servers_cfg.items():
            cmd = srv_def.get("command")
            args = srv_def.get("args", [])
            env = srv_def.get("env")
            if cmd:
                try:
                    client = StdlibMCPClient.spawn(command=cmd, args=args, env=env)
                    self.register_client(srv_name, client)
                except (OSError, RuntimeError):
                    pass

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """Aggregates and namespacing all available tools across local servers and remote clients."""
        catalog: List[Dict[str, Any]] = []

        # Local servers
        for srv_name, srv in self.local_servers.items():
            for tool in srv.get_tool_catalog():
                entry = dict(tool)
                entry["server"] = srv_name
                entry["namespaced_name"] = f"{srv_name}.{tool['name']}"
                catalog.append(entry)

        # Remote clients
        for client_name, client in self.clients.items():
            try:
                tools = client.list_tools()
                for tool in tools:
                    entry = dict(tool)
                    entry["server"] = client_name
                    entry["namespaced_name"] = f"{client_name}.{tool['name']}"
                    catalog.append(entry)
            except (RuntimeError, OSError):
                pass

        return catalog

    def invoke_tool(self, namespaced_tool: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Routes execution of a namespaced tool (<server>.<tool>) to the appropriate provider."""
        args = arguments or {}

        if "." in namespaced_tool:
            srv_name, tool_name = namespaced_tool.split(".", 1)
        else:
            # Fallback to local server if unqualified
            srv_name = "local" if "local" in self.local_servers else None
            tool_name = namespaced_tool

        # Check local servers
        if srv_name and srv_name in self.local_servers:
            srv = self.local_servers[srv_name]
            msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }
            resp = srv.handle_message(msg)
            if not resp or "error" in resp:
                err_text = resp.get("error", {}).get("message", "Invocation failed") if resp else "Empty response"
                return {
                    "content": [{"type": "text", "text": f"Execution error in '{namespaced_tool}': {err_text}"}],
                    "isError": True
                }
            return resp.get("result", {})

        # Check remote clients
        if srv_name and srv_name in self.clients:
            client = self.clients[srv_name]
            try:
                return client.call_tool(tool_name, args)
            except (RuntimeError, OSError) as exc:
                return {
                    "content": [{"type": "text", "text": f"Execution error on server '{srv_name}': {exc}"}],
                    "isError": True
                }

        return {
            "content": [{"type": "text", "text": f"Unknown tool or server '{namespaced_tool}'"}],
            "isError": True
        }

    def shutdown_all(self) -> None:
        """Terminates all active client processes cleanly."""
        for client in self.clients.values():
            client.close()
        self.clients.clear()

    def __enter__(self) -> "MCPMeshHub":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown_all()
