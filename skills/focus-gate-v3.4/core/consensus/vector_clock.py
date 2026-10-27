"""FocusGate v3.0 — Monotonic Vector Clock for Distributed Swarm Consensus.

Provides logical timestamps, causal partial ordering, and concurrency detection
across autonomous swarm actors and worktrees:
- Lamport-style monotonically increasing ticks per actor ID
- Element-wise merge calculating least upper bound
- Strict happened-before partial ordering (Leslie Lamport 1978)
- Deterministic concurrency detection for branch point isolation

Zero external dependencies (100% Python stdlib).
"""

import json
import hashlib
from typing import Dict, Any, Optional, Set


class VectorClock:
    """Monotonic logical vector clock tracking causal history across swarm nodes."""

    def __init__(self, clock: Optional[Dict[str, int]] = None):
        self.clock: Dict[str, int] = dict(clock) if clock else {}

    def tick(self, actor_id: str) -> int:
        """Monotonically increments clock for actor_id and returns the new value."""
        current = self.clock.get(actor_id, 0)
        new_val = current + 1
        self.clock[actor_id] = new_val
        return new_val

    def get(self, actor_id: str) -> int:
        """Returns the logical clock value for actor_id (defaults to 0)."""
        return self.clock.get(actor_id, 0)

    def set_val(self, actor_id: str, value: int) -> None:
        """Sets the logical clock for actor_id directly."""
        self.clock[actor_id] = max(0, int(value))

    def merge(self, other: "VectorClock") -> "VectorClock":
        """Calculates element-wise supremum (maximum) across all known actors.

        Returns a new VectorClock instance.
        """
        all_actors: Set[str] = set(self.clock.keys()) | set(other.clock.keys())
        merged_clock: Dict[str, int] = {}
        for a in all_actors:
            merged_clock[a] = max(self.get(a), other.get(a))
        return VectorClock(merged_clock)

    def happened_before(self, other: "VectorClock") -> bool:
        """Determines if self strictly causally precedes other (self < other).

        True if self <= other for all actors AND self < other for at least one actor.
        """
        all_actors: Set[str] = set(self.clock.keys()) | set(other.clock.keys())
        if not all_actors:
            return False

        has_strictly_less = False
        for a in all_actors:
            val_self = self.get(a)
            val_other = other.get(a)
            if val_self > val_other:
                return False
            if val_self < val_other:
                has_strictly_less = True

        return has_strictly_less

    def is_concurrent(self, other: "VectorClock") -> bool:
        """Determines if self and other represent concurrent, non-causal branches (self || other).

        True if neither happened before the other and they are not identical.
        """
        if self.clock == other.clock:
            return False
        return not self.happened_before(other) and not other.happened_before(self)

    def clone(self) -> "VectorClock":
        """Creates an independent deep copy of the vector clock."""
        return VectorClock(self.clock.copy())

    def to_dict(self) -> Dict[str, int]:
        """Serializes clock to a standard dictionary."""
        return dict(self.clock)

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "VectorClock":
        """Deserializes vector clock from dictionary."""
        return cls({str(k): int(v) for k, v in data.items()})

    def hash(self) -> str:
        """Computes deterministic SHA-256 fingerprint of the vector clock state."""
        canonical = json.dumps(self.clock, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def __repr__(self) -> str:
        return f"VectorClock({self.clock})"
