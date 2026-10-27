"""Hexagonal Storage Adapters for FocusGate v2.8.

Provides ACID-compliant embedded SQLite WAL storage alongside backward-compatible
JSONL event logging and snapshot persistence.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import sqlite3
import json
import os
import time
from core.aggregate import DomainEvent


class StoragePort(ABC):
    """Abstract port for event ledger and session state persistence."""

    @abstractmethod
    def append_event(self, event_type: str, data: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def get_events(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_snapshot(self, snapshot_id: str, state_vector: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        pass


class SQLiteStorageAdapter(StoragePort):
    """ACID-compliant SQLite adapter with WAL mode and dual-write JSONL synchronization."""

    def __init__(self, db_path: str, sync_jsonl_path: Optional[str] = None):
        if db_path.endswith(".jsonl"):
            self.sync_jsonl_path = db_path
            self.db_path = db_path[:-6] + ".db"
        else:
            self.db_path = db_path
            self.sync_jsonl_path = sync_jsonl_path or (os.path.splitext(db_path)[0] + ".jsonl")
        
        self.events_path = self.sync_jsonl_path
        self.events: List[Any] = []
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()
        self._load()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ledger_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    data_json TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id TEXT UNIQUE NOT NULL,
                    timestamp REAL NOT NULL,
                    state_json TEXT NOT NULL
                );
            """)

    def append_event(self, event_type: str, data: Dict[str, Any]) -> str:
        ts = time.time()
        event_id = f"ev-{int(ts * 1000)}-{os.urandom(3).hex()}"
        data_str = json.dumps(data)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO ledger_events (event_id, event_type, timestamp, data_json) VALUES (?, ?, ?, ?)",
                (event_id, event_type, ts, data_str)
            )

        # Dual-write sync to JSONL for legacy tooling compatibility
        if self.sync_jsonl_path:
            os.makedirs(os.path.dirname(os.path.abspath(self.sync_jsonl_path)), exist_ok=True)
            with open(self.sync_jsonl_path, "a", encoding="utf-8") as f:
                record = {
                    "event_id": event_id,
                    "event_type": event_type,
                    "timestamp": ts,
                    "data": data
                }
                f.write(json.dumps(record) + "\n")

        return event_id

    def get_events(self) -> List[Any]:
        if self.events:
            return self.events
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT event_id, event_type, timestamp, data_json FROM ledger_events ORDER BY id ASC"
            ).fetchall()

            return [
                DomainEvent(
                    event_id=r["event_id"],
                    event_type=r["event_type"],
                    timestamp=str(r["timestamp"]),
                    payload=json.loads(r["data_json"])
                )
                for r in rows
            ]

    def save_snapshot(self, snapshot_id: str, state_vector: Dict[str, Any]) -> None:
        ts = time.time()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO state_snapshots (snapshot_id, timestamp, state_json) VALUES (?, ?, ?)",
                (snapshot_id, ts, json.dumps(state_vector))
            )

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT snapshot_id, timestamp, state_json FROM state_snapshots ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row:
                return {
                    "snapshot_id": row["snapshot_id"],
                    "timestamp": row["timestamp"],
                    "state": json.loads(row["state_json"])
                }
            return None


    # --- INJECTED FROM EventSourcedLedger ---
    """Manages append-only event stream (.focusgate/ledger.events.jsonl) and deterministic projection."""

    def __init_esl__(self, events_path: str = ".focusgate/ledger.events.jsonl"):
        self.events_path = events_path
        self.events: List[DomainEvent] = []
        self._load()

    def _load(self):
        self.events = []
        if os.path.exists(self.events_path):
            with open(self.events_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            self.events.append(DomainEvent.from_dict(json.loads(line)))
                        except Exception:
                            continue

    def append(self, event_type: str, payload: Dict[str, Any], aggregate_id: str = "ledger-root", metadata: Optional[Dict[str, Any]] = None) -> DomainEvent:
        next_ver = len(self.events) + 1
        event = DomainEvent(
            version=next_ver,
            event_type=event_type,
            aggregate_id=aggregate_id,
            payload=payload,
            metadata=metadata
        )
        self.events.append(event)
        os.makedirs(os.path.dirname(os.path.abspath(self.events_path)), exist_ok=True)
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict()) + "\n")
        return event

    def replay_to_version(self, target_version: int) -> Dict[str, Any]:
        events_to_replay = [e for e in self.events if e.version <= target_version]
        return self._project(events_to_replay)

    def current_state(self) -> Dict[str, Any]:
        return self._project(self.events)

    def rollback_to_version(self, target_version: int) -> Dict[str, Any]:
        if target_version > len(self.events):
            raise ValueError(f"Target version {target_version} exceeds current event count {len(self.events)}")

        kept_events = [e for e in self.events if e.version <= target_version]
        self.events = kept_events
        os.makedirs(os.path.dirname(os.path.abspath(self.events_path)), exist_ok=True)
        with open(self.events_path, "w", encoding="utf-8") as f:
            for e in self.events:
                f.write(json.dumps(e.to_dict()) + "\n")

        self.append("TIME_TRAVEL_ROLLED_BACK", {
            "target_version": target_version,
            "rollback_timestamp": time.time()
        })
        return self.current_state()

    def _project(self, events: List[DomainEvent]) -> Dict[str, Any]:
        state = {
            "step": 1,
            "total_steps": 4,
            "est_minutes": 20,
            "gates": {},
            "archive": [],
            "version": len(events)
        }
        for e in events:
            p = e.payload
            if e.event_type == "STEP_TRANSITIONED":
                state["step"] = p.get("step", state["step"])
                state["total_steps"] = p.get("total_steps", state["total_steps"])
                state["est_minutes"] = p.get("est_minutes", state["est_minutes"])
            elif e.event_type == "GATE_REGISTERED":
                g_id = p["id"]
                state["gates"][g_id] = {
                    "id": g_id,
                    "title": p.get("title", ""),
                    "deps": p.get("deps", []),
                    "checked": p.get("checked", False),
                    "check_cmd": p.get("check_cmd", "")
                }
            elif e.event_type == "GATE_CHECKED":
                g_id = p["id"]
                if g_id in state["gates"]:
                    state["gates"][g_id]["checked"] = True
            elif e.event_type == "GATES_ARCHIVED":
                for g_id in p.get("archived_ids", []):
                    if g_id in state["gates"]:
                        state["archive"].append(state["gates"].pop(g_id))
        return state


# =============================================================================
# Candidate 2: Git Worktree Swarm Orchestrator
# =============================================================================
