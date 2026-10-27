"""FocusGate v3.1 — Distributed Merkle CRDT & Grid Networking.

Implements zero-dependency TCP grid sockets and state-based delta CRDTs
to synchronize event vectors and state roots across distributed nodes.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import time
import json
import uuid
import socket
import select
import hashlib
import threading
from typing import Dict, Any, List, Optional, Set, Tuple

from core.consensus.vector_clock import VectorClock


class GridMessage:
    """Line-delimited JSON message envelope for grid node communication."""

    def __init__(
        self,
        msg_type: str,
        sender_node: str,
        payload: Optional[Dict[str, Any]] = None,
        msg_id: Optional[str] = None,
        timestamp: Optional[float] = None
    ):
        self.msg_id = msg_id or str(uuid.uuid4())[:8]
        self.msg_type = msg_type
        self.sender_node = sender_node
        self.payload = payload or {}
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "msg_type": self.msg_type,
            "sender_node": self.sender_node,
            "payload": self.payload,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict()) + "\n"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridMessage":
        return cls(
            msg_type=data.get("msg_type", "UNKNOWN"),
            sender_node=data.get("sender_node", ""),
            payload=data.get("payload", {}),
            msg_id=data.get("msg_id"),
            timestamp=data.get("timestamp")
        )

    @classmethod
    def from_json(cls, raw: str) -> "GridMessage":
        return cls.from_dict(json.loads(raw.strip()))


class CRDTEventRecord(dict):
    """Dictionary subclass supporting attribute access for convenience."""
    def __getattr__(self, name):
        if name in self:
            return self[name]
        if name == "origin_node":
            return self.get("source_node")
        if name == "lamport_ts":
            clock = self.get("clock", {})
            return max(clock.values()) if clock else 1
        raise AttributeError(f"'CRDTEventRecord' object has no attribute '{name}'")


class MerkleCRDTReplicator:
    """Conflict-free replicated data type (CRDT) for distributed event logs."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.vector_clock = VectorClock()
        self.events: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def apply_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        origin_node: Optional[str] = None,
        lamport_ts: Optional[int] = None
    ) -> CRDTEventRecord:
        """Applies a local or replicated event with attribute/dict access."""
        if origin_node and origin_node != self.node_id:
            ev_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
            event_id = f"ev-{origin_node}-{int(time.time()*1000)}-{len(self.events)+1}"
            clock = {origin_node: lamport_ts or 1}
            delta = CRDTEventRecord({
                "event_id": event_id,
                "event_type": event_type,
                "payload": dict(payload),
                "clock": clock,
                "source_node": origin_node,
                "timestamp": time.time(),
                "hash": ev_hash,
            })
            self.apply_remote_delta(delta)
            return delta
        else:
            return self.apply_local_event(event_type, payload)

    def apply_local_event(self, event_type: str, payload: Dict[str, Any]) -> CRDTEventRecord:
        """Applies a new locally originated event and increments the node clock."""
        with self._lock:
            self.vector_clock.tick(self.node_id)
            ev_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
            event_id = f"ev-{self.node_id}-{int(time.time()*1000)}-{len(self.events)+1}"

            event_data = CRDTEventRecord({
                "event_id": event_id,
                "event_type": event_type,
                "payload": dict(payload),
                "clock": self.vector_clock.to_dict(),
                "source_node": self.node_id,
                "timestamp": time.time(),
                "hash": ev_hash,
            })
            self.events[event_id] = event_data
            return event_data

    def apply_remote_delta(self, delta: Dict[str, Any]) -> bool:
        """Merges a remote event delta and causally advances the vector clock."""
        with self._lock:
            remote_clock_data = delta.get("clock", {})
            remote_clock = VectorClock(remote_clock_data)
            self.vector_clock = self.vector_clock.merge(remote_clock)

            event_id = delta.get("event_id")
            if event_id and event_id not in self.events:
                self.events[event_id] = dict(delta)
                return True
            return False

    def get_state_root(self) -> str:
        """Deterministic fingerprint of all contained event IDs and hashes."""
        with self._lock:
            if not self.events:
                return "0" * 64
            sorted_keys = sorted(self.events.keys())
            raw = ":".join(f"{k}-{self.events[k].get('hash', '')}" for k in sorted_keys)
            return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_deltas_since(self, peer_clock: VectorClock) -> List[Dict[str, Any]]:
        """Finds all events that strictly happened after or are unknown to peer_clock."""
        with self._lock:
            deltas = []
            for ev_id, ev in self.events.items():
                ev_clock = VectorClock(ev.get("clock", {}))
                source = ev.get("source_node", "")
                if ev_clock.get(source) > peer_clock.get(source) or ev_id not in peer_clock.clock:
                    deltas.append(dict(ev))
            return deltas

    def reconcile_with_peer(self, peer: "MerkleCRDTReplicator") -> int:
        """Exchanges deltas in both directions until both peers converge."""
        deltas_to_peer = self.get_deltas_since(peer.vector_clock)
        deltas_to_self = peer.get_deltas_since(self.vector_clock)

        transferred = 0
        for d in deltas_to_peer:
            if peer.apply_remote_delta(d):
                transferred += 1
        for d in deltas_to_self:
            if self.apply_remote_delta(d):
                transferred += 1

        # Final clock alignment
        with self._lock:
            self.vector_clock = self.vector_clock.merge(peer.vector_clock)
        with peer._lock:
            peer.vector_clock = peer.vector_clock.merge(self.vector_clock)

        return transferred


class GridNode:
    """Zero-dependency TCP socket server coordinating distributed swarm grid peers."""

    def __init__(self, node_id: str, host: str = "127.0.0.1", port: int = 0):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.server_port: int = port
        self.replicator = MerkleCRDTReplicator(node_id=node_id)

        self.server_socket: Optional[socket.socket] = None
        self.peers: Dict[str, socket.socket] = {}
        self._peer_threads: List[threading.Thread] = []
        self._pong_events: Dict[str, threading.Event] = {}
        self.running: bool = False
        self._accept_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Starts TCP listening socket and background connection handler."""
        if self.running:
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_port = self.server_socket.getsockname()[1]
        self.server_socket.listen(10)
        self.server_socket.settimeout(0.2)

        self.running = True
        self._accept_thread = threading.Thread(target=self._run_acceptor, daemon=True)
        self._accept_thread.start()

    def _run_acceptor(self) -> None:
        while self.running and self.server_socket:
            try:
                client_sock, addr = self.server_socket.accept()
                peer_key = f"{addr[0]}:{addr[1]}"
                self.peers[peer_key] = client_sock
                t = threading.Thread(target=self._handle_client, args=(client_sock, peer_key), daemon=True)
                self._peer_threads.append(t)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break

    def connect_peer(self, host: str, port: int) -> bool:
        """Establishes an outgoing connection to a peer grid node."""
        peer_key = f"{host}:{port}"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((host, port))
            self.peers[peer_key] = s
            t = threading.Thread(target=self._handle_client, args=(s, peer_key), daemon=True)
            self._peer_threads.append(t)
            t.start()
            return True
        except (socket.error, OSError):
            return False

    def ping_peer(self, peer_key: str, timeout: float = 1.0) -> bool:
        """Sends PING message to a peer and blocks until PONG received or timeout."""
        sock = self.peers.get(peer_key)
        if not sock:
            return False

        ev = threading.Event()
        self._pong_events[peer_key] = ev

        msg = GridMessage(msg_type="PING", sender_node=self.node_id)
        try:
            sock.sendall(msg.to_json().encode("utf-8"))
            return ev.wait(timeout=timeout)
        except (socket.error, OSError):
            return False
        finally:
            if peer_key in self._pong_events:
                del self._pong_events[peer_key]

    def apply_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Applies a local event and broadcasts delta to all connected peers."""
        ev = self.replicator.apply_local_event(event_type, payload)
        msg = GridMessage(msg_type="DELTA_BROADCAST", sender_node=self.node_id, payload={"delta": ev})
        self.broadcast(msg)
        return ev

    def broadcast(self, msg: GridMessage) -> int:
        """Broadcasts a GridMessage to all active connected peer sockets."""
        sent = 0
        raw = msg.to_json().encode("utf-8")
        for pk, sock in list(self.peers.items()):
            try:
                sock.sendall(raw)
                sent += 1
            except (socket.error, OSError):
                if pk in self.peers:
                    del self.peers[pk]
        return sent

    def _handle_client(self, sock: socket.socket, peer_key: str) -> None:
        """Reads incoming line-delimited messages from a connected peer."""
        sock.settimeout(0.2)
        buffer = b""

        while self.running:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk

                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line.strip():
                        try:
                            msg = GridMessage.from_json(line.decode("utf-8"))
                            self._dispatch_message(msg, sock, peer_key)
                        except (json.JSONDecodeError, ValueError):
                            pass
            except socket.timeout:
                continue
            except (socket.error, OSError):
                break

        if peer_key in self.peers:
            del self.peers[peer_key]
        try:
            sock.close()
        except OSError:
            pass

    def _dispatch_message(self, msg: GridMessage, sock: socket.socket, peer_key: str) -> None:
        """Routes and handles incoming grid network messages."""
        if msg.msg_type == "PING":
            resp = GridMessage(msg_type="PONG", sender_node=self.node_id)
            try:
                sock.sendall(resp.to_json().encode("utf-8"))
            except (socket.error, OSError):
                pass

        elif msg.msg_type == "PONG":
            if peer_key in self._pong_events:
                self._pong_events[peer_key].set()

        elif msg.msg_type == "DELTA_BROADCAST":
            delta = msg.payload.get("delta")
            if delta:
                self.replicator.apply_remote_delta(delta)

    def stop(self) -> None:
        """Gracefully shuts down sockets and peer threads."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
            self.server_socket = None

        for sock in list(self.peers.values()):
            try:
                sock.close()
            except OSError:
                pass
        self.peers.clear()
