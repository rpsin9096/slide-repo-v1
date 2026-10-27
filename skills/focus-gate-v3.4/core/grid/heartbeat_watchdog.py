"""FocusGate v3.1 Loop 51 — Dynamic Swarm Actor Heartbeat & Adaptive Liveness Watchdog.

Monitors actor heartbeat telemetry, evaluates degradation/hung states,
detects wait-graph deadlocks via cycle detection, and automatically recycles
hung or dead actors.

Zero external dependencies (100% Python stdlib).
"""

import time
import threading
from typing import Dict, Any, List, Optional, Set, Callable


class ActorHeartbeatRecord:
    """Telemetry record tracking actor heartbeat timestamps, CPU usage, and state."""

    def __init__(
        self,
        actor_id: str,
        last_beat_ts: Optional[float] = None,
        status: str = "ALIVE",
        cpu_time_ms: float = 0.0,
        pending_tasks: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.actor_id = actor_id
        self.last_beat_ts = last_beat_ts if last_beat_ts is not None else time.time()
        self.status = status
        self.cpu_time_ms = cpu_time_ms
        self.pending_tasks = pending_tasks
        self.metadata = metadata or {}

    def touch(self, cpu_delta_ms: float = 0.0, pending: int = 0, ts: Optional[float] = None) -> None:
        """Updates heartbeat timestamp and accumulated telemetry."""
        self.last_beat_ts = ts if ts is not None else time.time()
        self.cpu_time_ms += cpu_delta_ms
        self.pending_tasks = pending

    def is_expired(self, now: float, timeout: float) -> bool:
        """Returns True if the duration since last heartbeat exceeds timeout."""
        return (now - self.last_beat_ts) > timeout

    def to_dict(self) -> Dict[str, Any]:
        """Serializes record to dictionary."""
        return {
            "actor_id": self.actor_id,
            "last_beat_ts": self.last_beat_ts,
            "status": self.status,
            "cpu_time_ms": self.cpu_time_ms,
            "pending_tasks": self.pending_tasks,
            "metadata": self.metadata,
        }


class ActorLivenessPolicy:
    """Configurable policy thresholds for actor liveness state evaluation."""

    def __init__(
        self,
        warning_timeout: float = 2.0,
        hung_timeout: float = 5.0,
        dead_timeout: float = 10.0,
        auto_recycle: bool = True,
    ):
        self.warning_timeout = warning_timeout
        self.hung_timeout = hung_timeout
        self.dead_timeout = dead_timeout
        self.auto_recycle = auto_recycle

    def evaluate_status(self, record: ActorHeartbeatRecord, now: float) -> str:
        """Evaluates actor state based on elapsed time since last heartbeat."""
        elapsed = now - record.last_beat_ts
        if elapsed > self.dead_timeout:
            return "DEAD"
        if elapsed > self.hung_timeout:
            return "HUNG"
        if elapsed > self.warning_timeout:
            return "DEGRADED"
        return "ALIVE"


class DeadlockDetector:
    """Directed graph cycle detector for actor wait dependencies."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # Adjacency list: waiting_actor -> set of actors/resources it is waiting on
        self._wait_graph: Dict[str, Set[str]] = {}

    def add_wait_dependency(self, waiting_actor: str, blocking_actor: str) -> None:
        """Registers a directed wait dependency (waiting_actor -> blocking_actor)."""
        with self._lock:
            if waiting_actor not in self._wait_graph:
                self._wait_graph[waiting_actor] = set()
            self._wait_graph[waiting_actor].add(blocking_actor)

    def remove_dependency(self, waiting_actor: str, blocking_actor: str) -> None:
        """Removes a specific wait dependency."""
        with self._lock:
            if waiting_actor in self._wait_graph:
                self._wait_graph[waiting_actor].discard(blocking_actor)
                if not self._wait_graph[waiting_actor]:
                    del self._wait_graph[waiting_actor]

    def clear_actor(self, actor_id: str) -> None:
        """Cleans all incoming and outgoing dependencies for an actor."""
        with self._lock:
            self._wait_graph.pop(actor_id, None)
            for targets in self._wait_graph.values():
                targets.discard(actor_id)

    def detect_cycles(self) -> List[List[str]]:
        """Finds all elementary cycles in the wait dependency graph using DFS."""
        with self._lock:
            graph = {k: set(v) for k, v in self._wait_graph.items()}

        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: List[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.append(node)

            for neighbor in graph.get(node, ()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found cycle: extract from index of neighbor to current
                    idx = rec_stack.index(neighbor)
                    cycle = list(rec_stack[idx:])
                    cycle.append(neighbor)
                    cycles.append(cycle)

            rec_stack.pop()

        all_nodes = list(graph.keys())
        for node in all_nodes:
            if node not in visited:
                dfs(node)

        return cycles


class SwarmHeartbeatMonitor:
    """Supervises active actors, heartbeat health, and automated recovery."""

    def __init__(
        self,
        policy: Optional[ActorLivenessPolicy] = None,
        on_actor_recycled: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.policy = policy or ActorLivenessPolicy()
        self.on_actor_recycled = on_actor_recycled
        self.deadlock_detector = DeadlockDetector()
        self._lock = threading.Lock()
        self._actors: Dict[str, ActorHeartbeatRecord] = {}

    def register_actor(self, actor_id: str, metadata: Optional[Dict[str, Any]] = None) -> ActorHeartbeatRecord:
        """Registers a new actor for heartbeat monitoring."""
        with self._lock:
            record = ActorHeartbeatRecord(actor_id=actor_id, metadata=metadata)
            self._actors[actor_id] = record
            return record

    def deregister_actor(self, actor_id: str) -> None:
        """Removes an actor from heartbeat monitoring and clears wait dependencies."""
        with self._lock:
            self._actors.pop(actor_id, None)
        self.deadlock_detector.clear_actor(actor_id)

    def record_heartbeat(
        self,
        actor_id: str,
        cpu_time_ms: float = 0.0,
        pending_tasks: int = 0,
        ts: Optional[float] = None,
    ) -> None:
        """Records a heartbeat tick for the given actor."""
        with self._lock:
            record = self._actors.get(actor_id)
            if record:
                record.touch(cpu_delta_ms=cpu_time_ms, pending=pending_tasks, ts=ts)
                record.status = "ALIVE"

    def check_liveness(self, now: Optional[float] = None) -> Dict[str, Any]:
        """Evaluates the status of all registered actors and detects deadlocks."""
        eval_now = now if now is not None else time.time()
        with self._lock:
            records = list(self._actors.values())

        alive_count = 0
        degraded_count = 0
        hung_count = 0
        dead_count = 0
        recycled_actors: List[str] = []
        actor_details: Dict[str, Any] = {}

        for rec in records:
            new_status = self.policy.evaluate_status(rec, eval_now)
            rec.status = new_status

            if new_status == "ALIVE":
                alive_count += 1
            elif new_status == "DEGRADED":
                degraded_count += 1
            elif new_status == "HUNG":
                hung_count += 1
            elif new_status == "DEAD":
                dead_count += 1

            if self.policy.auto_recycle and new_status in ("HUNG", "DEAD"):
                recycled_actors.append(rec.actor_id)
                rec.status = "RECYCLED"
                if self.on_actor_recycled:
                    try:
                        self.on_actor_recycled(rec.actor_id)
                    except (RuntimeError, ValueError, KeyError, TypeError, OSError):
                        pass

            actor_details[rec.actor_id] = rec.to_dict()

        deadlocks = self.deadlock_detector.detect_cycles()

        return {
            "total_actors": len(records),
            "alive_count": alive_count,
            "degraded_count": degraded_count,
            "hung_count": hung_count,
            "dead_count": dead_count,
            "recycled_actors": recycled_actors,
            "deadlocks": deadlocks,
            "actor_details": actor_details,
        }
