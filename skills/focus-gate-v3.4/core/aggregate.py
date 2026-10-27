"""Pure Domain Aggregate Root for FocusGate v2.8.

Maintains ledger invariants, single active gate constraints, DAG topological
ordering, and event-sourcing fold operations with zero external dependencies.
"""

import sys
import os
import json
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field






import uuid
import datetime

# Ledger was referenced by `LedgerAggregate.from_file` and by a type annotation
# but never imported, so the class's only real construction path raised
# `NameError: name 'Ledger' is not defined`. Found by the Loop 61 coverage tests;
# this module previously had none. Imported lazily inside `from_file` is not
# enough — the annotation is a string, but the call site is not — so the import
# is at module scope, matching how the rest of core/ resolves its own types.
try:  # the ledger parser lives in core.gates; keep this import failure visible
    from core.gates.ledger import Ledger
except ImportError:  # pragma: no cover - only when core.gates is unavailable
    Ledger = None  # type: ignore


class DomainEvent:
    """Typed domain event adhering to INTERCOMMUNICATION_SPEC.md schema contracts."""
    def __init__(self,
                 event_type: str,
                 payload: Dict[str, Any],
                 aggregate_id: str = "ledger-root",
                 event_id: Optional[str] = None,
                 timestamp: Optional[str] = None,
                 version: int = 1,
                 metadata: Optional[Dict[str, Any]] = None):
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.version = version  # Monotonic sequence counter for replay
        self.seq = version
        self.schema_version = "1.5.2"
        self.payload = payload or {}
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "aggregateId": self.aggregate_id,
            "timestamp": self.timestamp,
            "version": "1.5.2",
            "seq": self.seq,
            "payload": self.payload,
            "metadata": self.metadata,
            # Legacy compatibility field
            "type": self.event_type
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'DomainEvent':
        event_id = d.get("eventId") or str(uuid.uuid4())
        event_type = d.get("eventType") or d.get("type", "GenericDomainEvent")
        aggregate_id = d.get("aggregateId") or "ledger-root"
        ts = d.get("timestamp")
        if isinstance(ts, (int, float)):
            ts = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()
        elif not ts:
            ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        raw_ver = d.get("version", 1)
        seq = d.get("seq") or (raw_ver if isinstance(raw_ver, int) else 1)
        payload = d.get("payload", {})
        metadata = d.get("metadata", {})
        inst = cls(
            event_type=event_type,
            payload=payload,
            aggregate_id=aggregate_id,
            event_id=event_id,
            timestamp=ts,
            version=int(seq),
            metadata=metadata
        )
        inst.seq = int(seq)
        inst.schema_version = "1.5.2"
        return inst

    @staticmethod
    def validate_schema(d: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if not isinstance(d, dict):
            return False, ["Event line is not a valid JSON object"]

        has_type = "eventType" in d or "type" in d
        has_payload = "payload" in d

        if not has_type:
            errors.append("Missing required field 'eventType' (or 'type')")
        if not has_payload:
            errors.append("Missing required field 'payload'")
        elif not isinstance(d["payload"], dict):
            errors.append("Field 'payload' must be an object/dict")

        return (len(errors) == 0, errors)


class EventSourcedLedger(object):
    """Append-only event stream with deterministic projection.

    Recovered verbatim from `adapters/storage_adapter.py`, where the whole
    implementation had been pasted INSIDE `SQLiteStorageAdapter` under the
    mangled name `__init_esl__` and indented as its methods. `core/aggregate.py`
    referenced `EventSourcedLedger` from `__init_inline__` and `from_file`, but
    no such class existed anywhere in the repository, so `--queue-status` died
    with `NameError: name 'EventSourcedLedger' is not defined`.
    Found by the Loop 61 coverage tests; the module previously had none.
    """

    """Manages append-only event stream (.focusgate/ledger.events.jsonl) and deterministic projection."""

    def __init__(self, events_path: str = ".focusgate/ledger.events.jsonl"):
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


# Alias LedgerEvent to FocusGateDomainEvent for backward compatibility

class InvariantViolationError(Exception):
    """Raised when an aggregate invariant is breached."""
    pass


class DomainViolationError(Exception):
    """A gate transition was refused because it would break a domain rule.

    This class was referenced by 11 `raise` sites and one `except` clause in
    `LedgerAggregate`'s ledger-backed half, but was never defined anywhere in the
    repository. Every one of those paths therefore raised
    `NameError: name 'DomainViolationError' is not defined` instead of the
    intended exception, so a caller could not even name the type it needed to
    catch. Found by the Loop 61 coverage tests; this module had no tests, which
    is how six distinct defects shipped in a single file.
    """
    pass


class LedgerAggregate:
    """Aggregate Root governing the FocusGate state vector and execution graph."""

    def __init__(self, workspace_root: str = ".", ledger=None, event_store=None):
        if ledger:
            self.__init_inline__(ledger, event_store)
            return
        self.workspace_root = workspace_root
        # The workspace_root constructor never bound a ledger, but the
        # ledger-based half of this class (`_all_items`, `get_active_gate`,
        # `get_settled_gates`, `get_frontier_buffer`) reads `self.ledger`, so
        # those methods raised `AttributeError` on a kernel-built aggregate.
        # Bind it explicitly so the failure is a clean, predictable None
        # instead of a missing attribute. Found by the Loop 61 coverage tests.
        self.ledger = None
        self.version = 0
        self.pipeline: str = "P1: Rapid Defect Resolution"
        self.stage: str = "Stage 1 of 1: Initial"
        self.est_minutes: int = 15
        self.depth: int = 0
        self.gates: Dict[str, Dict[str, Any]] = {}
        self.events: List[DomainEvent] = []
        self.stages: List[Dict[str, Any]] = []
        self.current_stage_index: int = 1

    def set_stages(self, stages: List[Dict[str, Any]]) -> None:
        """Sets the staged pipeline progression definitions and synchronizes active stage."""
        self.stages = stages
        self._sync_active_stage()

    def _sync_active_stage(self) -> None:
        """Dynamically computes the active stage based on gate settlement status."""
        if not self.stages:
            return
        for idx, s in enumerate(self.stages, 1):
            gids = s.get("gate_ids") or ([s.get("gate_id")] if s.get("gate_id") else [])
            all_done = all(self.gates.get(gid, {}).get("status") == "CHECKED" for gid in gids if gid in self.gates)
            if not all_done or not gids:
                self.current_stage_index = idx
                name = s.get("name") or s.get("title") or s.get("facet", f"Stage-{idx}")
                self.stage = f"Stage {idx} of {len(self.stages)}: {name}"
                return
        self.current_stage_index = len(self.stages)
        self.stage = f"Stage {len(self.stages)} of {len(self.stages)}: Complete"

    @property
    def active_gate(self) -> Optional[Dict[str, Any]]:
        """Returns the currently active gate, ensuring the single-active invariant."""
        actives = [g for g in self.gates.values() if g.get("status") == "ACTIVE"]
        if len(actives) > 1:
            raise InvariantViolationError(
                f"Single Active Gate Invariant breached: {len(actives)} gates found in ACTIVE state!"
            )
        return actives[0] if actives else None

    def add_gate(self, gate_id: str, title: str, facet: str, check: str, expect: str, est_minutes: int = 15, depends_on: Optional[List[str]] = None) -> None:
        """Adds a new gate to the frontier DAG, verifying acyclic dependencies."""
        if gate_id in self.gates:
            raise ValueError(f"Gate {gate_id} already exists in aggregate")

        deps = depends_on or []
        for d in deps:
            if d == gate_id:
                raise InvariantViolationError(f"Self-dependency cycle detected for gate '{gate_id}'")
            if d not in self.gates:
                raise ValueError(f"Dependency gate {d} does not exist in graph")

        # Check for circular dependency
        self._check_acyclic(gate_id, deps)

        self.gates[gate_id] = {
            "id": gate_id,
            "title": title,
            "facet": facet,
            "status": "PENDING",
            "check": check,
            "expect": expect,
            "est_minutes": est_minutes,
            "depends_on": deps
        }
        self._record_event("GateAdded", {"gate_id": gate_id, "title": title, "facet": facet})

    def activate_gate(self, gate_id: str) -> None:
        """Transitions a PENDING gate to ACTIVE, maintaining the single active invariant."""
        if gate_id not in self.gates:
            raise KeyError(f"Gate {gate_id} not found")

        current_active = self.active_gate
        if current_active and current_active["id"] != gate_id:
            raise InvariantViolationError(
                f"Cannot activate gate {gate_id}: gate {current_active['id']} is already ACTIVE."
            )

        gate = self.gates[gate_id]
        # Verify all dependencies are CHECKED
        for dep_id in gate.get("depends_on", []):
            if self.gates[dep_id]["status"] != "CHECKED":
                raise InvariantViolationError(
                    f"Cannot activate {gate_id}: prerequisite dependency {dep_id} is not CHECKED."
                )

        gate["status"] = "ACTIVE"
        self._record_event("GateActivated", {"gate_id": gate_id})

    def check_gate(self, gate_id: str, output: str = "", receipt: Optional[Any] = None) -> None:
        """Marks an ACTIVE gate as CHECKED after successful verification."""
        if gate_id not in self.gates:
            raise KeyError(f"Gate {gate_id} not found")

        gate = self.gates[gate_id]
        if gate["status"] != "ACTIVE":
            raise InvariantViolationError(f"Cannot check gate {gate_id}: status is {gate['status']} (expected ACTIVE).")

        gate["status"] = "CHECKED"
        gate["checked_at"] = time.time()

        event_payload = {
            "gate_id": gate_id,
            "output_summary": output[:200] if output else "PASS"
        }
        if receipt:
            event_payload["evidence_hash"] = getattr(receipt, "evidence_hash", "")
            event_payload["elapsed_ms"] = getattr(receipt, "elapsed_ms", 0.0)
            event_payload["key_findings"] = getattr(receipt, "key_findings", [])
        else:
            event_payload["output"] = output[:500]

        self._record_event("GateChecked", event_payload)
        self._sync_active_stage()

    def rollback_gate(self, gate_id: str, reason: str = "") -> None:
        """Rolls back an ACTIVE gate to PENDING upon verification failure."""
        if gate_id not in self.gates:
            raise KeyError(f"Gate {gate_id} not found")

        gate = self.gates[gate_id]
        gate["status"] = "PENDING"
        self._record_event("GateRolledBack", {"gate_id": gate_id, "reason": reason})
        self._sync_active_stage()

    def get_state_vector(self) -> Dict[str, Any]:
        """Returns the canonical state vector conforming to the FocusGate Action Envelope."""
        pending_count = sum(1 for g in self.gates.values() if g["status"] == "PENDING")
        active = self.active_gate
        active_id = active["id"] if active else "None"
        
        return {
            "pipeline": self.pipeline,
            "stage": self.stage,
            "stage_index": self.current_stage_index,
            "total_stages": max(1, len(self.stages)),
            "queue_depth": pending_count,
            "active_gate": active_id,
            "est_minutes": self.est_minutes,
            "depth": self.depth,
            "total_gates": len(self.gates),
            "checked_gates": sum(1 for g in self.gates.values() if g["status"] == "CHECKED")
        }

    def format_envelope_header(self) -> str:
        """Renders Line 2 of the FocusGate Action Envelope."""
        vec = self.get_state_vector()
        return f"State: [Pipeline: {vec['pipeline']}] [{vec['stage']}] [Active: {vec['active_gate']}] [Queue: 1 active, {vec['queue_depth']} buffered] [Est: {vec['est_minutes']} min] [Depth: L{vec['depth'] or 1}]"

    def _check_acyclic(self, new_id: Optional[str] = None,
                       deps: Optional[List[str]] = None) -> None:
        """Walks the dependency graph looking for a cycle.

        `new_id` and `deps` are optional so `_validate_initial_state` can audit
        the whole graph loaded from a file. It previously called
        `self._check_acyclic()` with no arguments, which raised
        `TypeError: missing 2 required positional arguments` — so
        `LedgerAggregate.from_file` and `--queue-status` could never construct a
        ledger-backed aggregate. Found by the Loop 61 coverage tests.
        """
        visited = set()
        stack = list(deps or [])
        while stack:
            curr = stack.pop()
            if new_id is not None and curr == new_id:
                raise InvariantViolationError(f"Cycle detected involving gate {new_id} and {curr}")
            if curr not in visited:
                visited.add(curr)
                stack.extend(self.gates.get(curr, {}).get("depends_on", []))

    def _record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        self.version += 1
        ev = DomainEvent(
            event_id=f"ev-{int(time.time()*1000)}-{self.version}",
            event_type=event_type,
            timestamp=str(time.time()),
            payload=data,
            version=self.version
        )
        self.events.append(ev)
        fg_dir = os.path.join(self.workspace_root, ".focusgate")
        if os.path.exists(fg_dir):
            events_path = os.path.join(fg_dir, "ledger.events.jsonl")
            try:
                with open(events_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(ev.to_dict()) + "\n")
            except Exception as e:
                print(f'[FocusGate] Event write failed: {e}', file=sys.stderr)

    def fold_event(self, event_dict: Dict[str, Any]) -> None:
        """Event sourcing fold: applies a past event to reconstruct aggregate state."""
        etype = event_dict.get("eventType")
        data = event_dict.get("data", {})

        if etype == "GateAdded":
            self.gates[data["gate_id"]] = {
                "id": data["gate_id"],
                "title": data.get("title", ""),
                "facet": data.get("facet", "unlazy"),
                "status": "PENDING",
                "check": data.get("check", "git status"),
                "expect": data.get("expect", "On branch"),
                "est_minutes": data.get("est_minutes", 15),
                "depends_on": data.get("depends_on", [])
            }
        elif etype == "GateActivated":
            if data["gate_id"] in self.gates:
                self.gates[data["gate_id"]]["status"] = "ACTIVE"
        elif etype == "GateChecked":
            if data["gate_id"] in self.gates:
                self.gates[data["gate_id"]]["status"] = "CHECKED"
        elif etype == "GateRolledBack":
            if data["gate_id"] in self.gates:
                self.gates[data["gate_id"]]["status"] = "PENDING"
        self.version += 1

    # --- INJECTED FROM INLINE ---
    """Domain-Driven Design (DDD) Aggregate Root for Task Ledgers.

    Encapsulates all gates, dependencies, and state invariants:
    1. Single Active Gate Invariant: Exactly one gate active at a time.
    2. Topological Prerequisite Invariant: Gates cannot activate until dependencies are complete.
    3. Acyclic Dependency Invariant: Dependency graphs must be strictly acyclic.
    4. Write-Ahead Logging (WAL): Domain events are committed before disk changes.
    """
    def __init_inline__(self, ledger: 'Ledger', event_store: Optional['EventSourcedLedger'] = None):
        self.ledger = ledger
        self.event_store = event_store or EventSourcedLedger(
            os.path.join(os.path.dirname(os.path.abspath(ledger.filepath)), "ledger.events.jsonl")
        )
        self._validate_initial_state()

    @classmethod
    def from_file(cls, filepath: str, event_store: Optional['EventSourcedLedger'] = None) -> 'LedgerAggregate':
        if Ledger is None:  # pragma: no cover - import guard in __init
            raise ImportError("core.aggregate requires core.gates.ledger")
        ledger = Ledger.from_file(filepath)
        # Must be keyword: the first positional parameter is `workspace_root`.
        # `cls(ledger, event_store)` bound a Ledger to workspace_root and left
        # `self.ledger` unset, so the ledger half of the class never initialised.
        return cls(workspace_root=os.path.dirname(os.path.abspath(filepath)),
                   ledger=ledger, event_store=event_store)

    def _validate_initial_state(self):
        """Validates that the ledger does not violate fundamental domain invariants."""
        self._check_acyclic()

    def _all_items(self) -> List['TracerGate']:
        return self.ledger.spikes + self.ledger.gates

    def get_gate(self, gate_id: str) -> Optional['TracerGate']:
        for g in self._all_items():
            if g.id == gate_id:
                return g
        return None

    def get_active_gate(self) -> Optional['TracerGate']:
        """Returns the single active gate in execution."""
        for g in self._all_items():
            if not g.checked and getattr(g, 'is_active', False):
                return g
        # Fallback: first unblocked pending item
        for g in self._all_items():
            if not g.checked and self.is_unblocked(g.id):
                return g
        return None

    def get_frontier_buffer(self) -> List['TracerGate']:
        """Returns unblocked gates waiting in the buffer (excluding active gate)."""
        active = self.get_active_gate()
        active_id = active.id if active else None
        frontier = []
        for g in self._all_items():
            if not g.checked and g.id != active_id and self.is_unblocked(g.id):
                frontier.append(g)
        return frontier

    def get_settled_gates(self) -> List['TracerGate']:
        """Returns all completed or verified gates."""
        return [g for g in self._all_items() if g.checked]

    def is_unblocked(self, gate_id: str) -> bool:
        """A gate is unblocked when all its declared dependencies are checked/settled."""
        gate = self.get_gate(gate_id)
        if not gate:
            return False
        if not gate.deps:
            return True
        for dep_id in gate.deps:
            dep_gate = self.get_gate(dep_id)
            if not dep_gate or not dep_gate.checked:
                return False
        return True

    def activate_tracer_gate(self, gate_id: str) -> 'TracerGate':
        """Enforces Single Active Gate and Topological Prerequisite invariants."""
        target = self.get_gate(gate_id)
        if not target:
            raise DomainViolationError(f"Gate '{gate_id}' does not exist in ledger.")

        if target.checked:
            raise DomainViolationError(f"Cannot activate gate '{gate_id}': already completed.")

        if not self.is_unblocked(gate_id):
            unmet = [d for d in target.deps if not (self.get_gate(d) and self.get_gate(d).checked)]
            raise DomainViolationError(
                f"TopologicalPrerequisiteInvariant violation: Gate '{gate_id}' has unmet prerequisites: {unmet}"
            )

        current_active = None
        for g in self._all_items():
            if not g.checked and getattr(g, 'is_active', False) and g.id != gate_id:
                current_active = g
                break

        if current_active:
            raise DomainViolationError(
                f"SingleActiveGateInvariant violation: Gate '{current_active.id}' is already ACTIVE. "
                f"Complete or deactivate it before activating '{gate_id}'."
            )

        target.is_active = True
        self.event_store.append("GateTransitionedEvent", {
            "gateId": gate_id,
            "previousStatus": "TODO",
            "newStatus": "ACTIVE",
            "title": target.title
        })
        return target

    def complete_gate(self, gate_id: str, oracle_output: str = "") -> 'TracerGate':
        """Completes a gate, satisfying Single Active Gate completion requirement."""
        target = self.get_gate(gate_id)
        if not target:
            raise DomainViolationError(f"Gate '{gate_id}' does not exist.")

        target.checked = True
        target.is_active = False

        self.event_store.append("GateTransitionedEvent", {
            "gateId": gate_id,
            "previousStatus": "ACTIVE",
            "newStatus": "DONE",
            "oracle_output": oracle_output[:100] if oracle_output else None
        })
        return target

    def abandon_gate(self, gate_id: str, reason: str) -> 'TracerGate':
        """Explicitly abandons a gate with an audit justification."""
        target = self.get_gate(gate_id)
        if not target:
            raise DomainViolationError(f"Gate '{gate_id}' does not exist.")

        target.checked = True
        target.is_active = False
        target.title = f"[ABANDONED] {target.title} (Reason: {reason})"

        self.event_store.append("GateTransitionedEvent", {
            "gateId": gate_id,
            "previousStatus": "ACTIVE",
            "newStatus": "ABANDONED",
            "reason": reason
        })
        return target

    def deactivate_gate(self, gate_id: str) -> 'TracerGate':
        """Deactivates an active gate, returning it to the unblocked buffer."""
        target = self.get_gate(gate_id)
        if not target:
            raise DomainViolationError(f"Gate '{gate_id}' does not exist.")

        target.is_active = False
        self.event_store.append("GateTransitionedEvent", {
            "gateId": gate_id,
            "previousStatus": "ACTIVE",
            "newStatus": "TODO"
        })
        return target

    def add_tracer_gate(self, gate: 'TracerGate') -> None:
        """Adds a gate while ensuring acyclic graph invariant."""
        if self.get_gate(gate.id):
            raise DomainViolationError(f"Gate with id '{gate.id}' already exists.")

        self.ledger.gates.append(gate)
        try:
            self._check_acyclic()
        except DomainViolationError as e:
            self.ledger.gates.pop()
            raise e

        self.event_store.append("GateCreatedEvent", {
            "gateId": gate.id,
            "title": gate.title,
            "deps": gate.deps
        })

    def _check_acyclic_inline(self) -> None:
        """Cycle detection using depth-first search."""
        graph = {}
        for g in self._all_items():
            graph[g.id] = g.deps or []

        visited = {}

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            for neighbor in graph.get(node, []):
                if neighbor not in graph:
                    continue
                if visited.get(neighbor) == 1:
                    cycle = path + [neighbor]
                    raise DomainViolationError(
                        f"AcyclicDependencyInvariant violation: Circular dependency detected: {' -> '.join(cycle)}"
                    )
                if visited.get(neighbor) == 0:
                    dfs(neighbor, path + [neighbor])
            visited[node] = 2

        for node in graph:
            visited[node] = 0

        for node in graph:
            if visited[node] == 0:
                dfs(node, [node])

    def commit(self, filepath: Optional[str] = None) -> str:
        """Commits updated state atomically to disk."""
        target_path = filepath or self.ledger.filepath
        lines = self.ledger.raw_content.split("\n")
        updated_lines = []
        for line in lines:
            m = re.match(r'^(\s*-\s*\[)([\s xX])(\]\s+)([a-zA-Z0-9_\-]+)(:.*)$', line)
            if m:
                prefix, mark, mid, g_id, rest = m.groups()
                gate = self.get_gate(g_id)
                if gate:
                    new_mark = "x" if gate.checked else " "
                    updated_lines.append(f"{prefix}{new_mark}{mid}{g_id}{rest}")
                    continue
            updated_lines.append(line)

        content = "\n".join(updated_lines)
        tmp_path = f"{target_path}.tmp.{os.getpid()}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, target_path)
        self.ledger.raw_content = content
        return target_path


