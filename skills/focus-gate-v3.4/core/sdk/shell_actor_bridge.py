"""FocusGate v3.0 — Native Zero-Dependency Client SDK & Shell Bridge.

Provides a clean Python stdlib client connector and shell bridge to communicate
with the Unified Swarm Supervisor over Unix domain sockets.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import time
import socket
import subprocess
from typing import Dict, Any, List, Optional


class ClientConnectionError(Exception):
    """Raised when connection to FocusGate supervisor socket fails."""
    pass


class ClientTimeoutError(ClientConnectionError):
    """Raised when an RPC request times out."""
    pass


class FocusGateClient:
    """Zero-dependency client connector for FocusGate Supervisor IPC."""

    DEFAULT_SOCKET_PATH = "/tmp/focusgate-v3.sock"

    def __init__(self, socket_path: Optional[str] = None, timeout: float = 3.0):
        self.socket_path = socket_path or self.DEFAULT_SOCKET_PATH
        self.timeout = timeout
        self._connected = False

    def connect(self) -> None:
        """Verifies socket accessibility and marks client connected."""
        if not os.path.exists(self.socket_path):
            raise ClientConnectionError(f"Supervisor socket does not exist: {self.socket_path}")
        self._connected = True

    def disconnect(self) -> None:
        """Disconnects client."""
        self._connected = False

    def __enter__(self) -> "FocusGateClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    def call(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Sends an RPC request to the supervisor Unix socket and returns parsed response."""
        if not os.path.exists(self.socket_path):
            raise ClientConnectionError(f"Socket '{self.socket_path}' not found. Is the supervisor running?")

        t_out = timeout or self.timeout
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(t_out)

        try:
            sock.connect(self.socket_path)
            req = {
                "method": method,
                "params": params or {}
            }
            msg = json.dumps(req) + "\n"
            sock.sendall(msg.encode("utf-8"))

            raw = b""
            while not raw.endswith(b"\n"):
                chunk = sock.recv(4096)
                if not chunk:
                    break
                raw += chunk

            if not raw:
                raise ClientConnectionError("Received empty response from supervisor socket")

            data = json.loads(raw.decode("utf-8").strip())
            return data
        except socket.timeout:
            raise ClientTimeoutError(f"Timeout ({t_out}s) awaiting response for method '{method}'")
        except socket.error as exc:
            raise ClientConnectionError(f"Socket communication error: {exc}")
        finally:
            sock.close()

    def ping(self) -> bool:
        """Pings the supervisor daemon; returns True if active."""
        resp = self.call("ping")
        result = resp.get("result", {})
        return bool(result.get("pong", False))

    def get_status(self) -> Dict[str, Any]:
        """Queries supervisor state and actor health."""
        resp = self.call("status")
        return resp.get("result", {})

    def eval_gate(self, gate_id: str) -> Dict[str, Any]:
        """Triggers gate evaluation."""
        resp = self.call("eval_gate", {"gate_id": gate_id})
        return resp.get("result", {})

    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent stream events from the supervisor."""
        resp = self.call("get_events", {"limit": limit})
        return resp.get("result", {}).get("events", [])


class ShellActorBridge:
    """Utilities for invoking FocusGate supervisor methods from shell scripts or non-Python runtimes."""

    @staticmethod
    def generate_shell_command(socket_path: str, method: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generates a standalone Python 3 one-liner shell command to send an RPC request."""
        p_json = json.dumps(params or {})
        escaped_socket = socket_path.replace("'", "'\\''")
        escaped_method = method.replace("'", "'\\''")
        escaped_params = p_json.replace("'", "'\\''")

        cmd = (
            f"python3 -c \""
            f"import socket, json; "
            f"s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); "
            f"s.connect('{escaped_socket}'); "
            f"s.sendall((json.dumps({{'method': '{escaped_method}', 'params': {escaped_params}}}) + '\\n').encode('utf-8')); "
            f"print(s.recv(4096).decode('utf-8').strip()); "
            f"s.close()\""
        )
        return cmd

    @classmethod
    def exec_request(cls, socket_path: str, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes an RPC request via a generated shell command process and parses output."""
        cmd = cls.generate_shell_command(socket_path, method, params)
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if proc.returncode != 0:
            raise ClientConnectionError(f"Shell bridge execution failed: {proc.stderr}")
        try:
            return json.loads(proc.stdout.strip())
        except json.JSONDecodeError as exc:
            raise ClientConnectionError(f"Failed to parse shell bridge JSON output: {exc}")
