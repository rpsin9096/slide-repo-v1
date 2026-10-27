"""FocusGate v3.0 — Persistent Autonomous Swarm Supervisor Daemon.

Implements Unix domain socket IPC daemon providing background swarm orchestration,
reactive gate evaluation, and persistent actor mesh state:
- Unix domain socket IPC server (/tmp/focusgate-v3.sock)
- Standardized JSON-RPC request/response protocol
- Client helper for seamless CLI connection, status querying, and teardown
- Zero external pip dependencies (100% Python standard library)
"""

import os
import sys
import time
import json
import socket
import select
import threading
from typing import Dict, Any, Optional, List, Tuple

from core.mesh import (
    ActorMeshRouter,
    ArchitectActor,
    CoderActor,
    VerifierActor,
    RemediatorActor
)


DEFAULT_SOCKET_PATH = "/tmp/focusgate-v3.sock"
DAEMON_VERSION = "3.0.0-preview.1"


class SwarmDaemon:
    """Unix domain socket IPC server managing persistent swarm state."""

    def __init__(
        self,
        socket_path: Optional[str] = None,
        workspace_root: Optional[str] = None
    ):
        self.socket_path = socket_path or DEFAULT_SOCKET_PATH
        self.workspace_root = os.path.abspath(workspace_root or os.getcwd())
        self.server_socket: Optional[socket.socket] = None
        self.running: bool = False
        self.start_time: float = 0.0
        self._thread: Optional[threading.Thread] = None

        # Swarm substrate
        self.router = ActorMeshRouter()
        self.router.register(ArchitectActor("actor-architect-01"))
        self.router.register(CoderActor("actor-coder-01"))
        self.router.register(VerifierActor("actor-verifier-01"))
        self.router.register(RemediatorActor("actor-remediator-01"))

    def handle_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an incoming IPC request to the appropriate daemon method."""
        method = msg.get("method")
        params = msg.get("params", {})

        if method == "ping":
            return {"pong": True, "version": DAEMON_VERSION}

        elif method == "status":
            uptime = round(time.time() - self.start_time, 2) if self.start_time else 0.0
            return {
                "running": True,
                "version": DAEMON_VERSION,
                "uptime_seconds": uptime,
                "workspace_root": self.workspace_root,
                "registered_actors": len(self.router.actors),
                "actors": [a.to_dict() for a in self.router.list_actors()]
            }

        elif method == "shutdown":
            self.running = False
            return {"stopped": True, "message": "Daemon shutting down"}

        elif method == "actor_status":
            return {
                "total_registered": len(self.router.actors),
                "actors": [a.to_dict() for a in self.router.list_actors()],
                "dead_letters": len(self.router.dead_letters)
            }

        return {"error": f"Unknown method '{method}'"}

    def run(self) -> None:
        """Starts the Unix socket IPC server loop."""
        # Clean up stale socket file
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except OSError:
                pass

        sock_dir = os.path.dirname(os.path.abspath(self.socket_path))
        os.makedirs(sock_dir, exist_ok=True)

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen(5)
        self.server_socket.settimeout(0.2)

        self.running = True
        self.start_time = time.time()

        try:
            while self.running:
                try:
                    conn, _ = self.server_socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break

                try:
                    conn.settimeout(2.0)
                    raw_data = b""
                    while not raw_data.endswith(b"\n"):
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        raw_data += chunk

                    if raw_data:
                        try:
                            msg = json.loads(raw_data.decode("utf-8").strip())
                            resp = self.handle_message(msg)
                        except (json.JSONDecodeError, ValueError) as exc:
                            resp = {"error": f"Invalid JSON payload: {exc}"}

                        resp_bytes = (json.dumps(resp) + "\n").encode("utf-8")
                        conn.sendall(resp_bytes)
                except (OSError, socket.timeout):
                    pass
                finally:
                    conn.close()
        finally:
            self._cleanup_socket()

    def _cleanup_socket(self) -> None:
        """Closes server socket and removes file."""
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
            self.server_socket = None

        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except OSError:
                pass

    def start_background(self) -> None:
        """Launches the daemon in a background thread."""
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the daemon and joins background thread."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._cleanup_socket()

    def is_alive(self) -> bool:
        """Checks if the background server loop is currently running."""
        return self.running and (self._thread.is_alive() if self._thread else False)


class SwarmDaemonClient:
    """Client utility for communicating with SwarmDaemon over Unix domain socket."""

    def __init__(self, socket_path: Optional[str] = None):
        self.socket_path = socket_path or DEFAULT_SOCKET_PATH

    def send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 2.0
    ) -> Dict[str, Any]:
        """Sends request to SwarmDaemon over Unix socket and returns response."""
        if not os.path.exists(self.socket_path):
            return {"running": False, "status": "Offline (socket not found)"}

        for attempt in range(4):
            sock = None
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect(self.socket_path)

                req = {"method": method, "params": params or {}}
                raw = (json.dumps(req) + "\n").encode("utf-8")
                sock.sendall(raw)

                resp_data = b""
                while not resp_data.endswith(b"\n"):
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    resp_data += chunk

                if not resp_data:
                    return {"running": False, "status": "Empty response"}

                return json.loads(resp_data.decode("utf-8").strip())
            except (ConnectionRefusedError, FileNotFoundError) as exc:
                if attempt < 3:
                    time.sleep(0.05)
                    continue
                return {"running": False, "status": f"Offline ({exc})"}
            except (socket.timeout, OSError) as exc:
                return {"running": False, "status": f"Offline ({exc})"}
            finally:
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass

    def ping(self) -> Dict[str, Any]:
        """Pings daemon."""
        return self.send_request("ping")

    def status(self) -> Dict[str, Any]:
        """Queries daemon status."""
        return self.send_request("status")

    def stop(self) -> Dict[str, Any]:
        """Sends shutdown command to daemon."""
        return self.send_request("shutdown")
