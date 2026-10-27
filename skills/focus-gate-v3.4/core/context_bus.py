"""FocusGate v2.8 — SharedContextBus: broadcast-efficient shared state for multi-agent sessions.

Agents SUBSCRIBE to delta types they care about.
Agents PUBLISH ContextDeltaEvents (<=80 tokens each) when they settle gates.
Orchestrator READS the bus to compose each AgentBrief's upstream context (<=400 tokens total).
All state is persisted to .focusgate/context_bus.jsonl (mirrors ledger.events.jsonl pattern).
"""
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .tokens import estimate_tokens


CONTEXT_DELTA_MAX_TOKENS = 80
AGENT_WINDOW_MAX_TOKENS = 400
VALID_DELTA_TYPES = frozenset([
    "RECEIPT",        # Sub-agent settled a gate — payload is key_findings snippet
    "DOMAIN_ANCHOR",  # SessionBranchDAG merged a branch — payload is state summary
    "FILE_PATCH",     # A specific file was written — payload is file path + first 50 chars of diff
    "REORIENT",       # Orchestrator issued a reorient signal — payload is micro-task summary
])


class ContextDeltaOverflowError(ValueError):
    """Raised when a published delta exceeds the 80-token ceiling."""
    pass


@dataclass(frozen=True)
class ContextDeltaEvent:
    """A single broadcast event on the SharedContextBus.
    
    Immutable. Identified by SHA-256(content) so identical payloads
    deduplicate automatically.
    """
    delta_id: str         # SHA-256 of content — content-addressed
    source_agent: str     # gate_id or "orchestrator" that produced this delta
    delta_type: str       # One of VALID_DELTA_TYPES
    payload_tokens: int   # Estimated token count of content — must be <=80
    content: str          # The actual snippet (diff, receipt summary, etc.)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(cls, source_agent: str, delta_type: str, content: str) -> 'ContextDeltaEvent':
        if delta_type not in VALID_DELTA_TYPES:
            raise ValueError(f"Unknown delta_type '{delta_type}'. Valid: {VALID_DELTA_TYPES}")
        tokens = max(1, estimate_tokens(content))
        if tokens > CONTEXT_DELTA_MAX_TOKENS:
            raise ContextDeltaOverflowError(
                f"Delta content is ~{tokens} tokens, exceeds ceiling of {CONTEXT_DELTA_MAX_TOKENS}. "
                f"Truncate to {CONTEXT_DELTA_MAX_TOKENS * 4} chars before publishing."
            )
        delta_id = hashlib.sha256(content.encode()).hexdigest()
        return cls(
            delta_id=delta_id,
            source_agent=source_agent,
            delta_type=delta_type,
            payload_tokens=tokens,
            content=content,
        )

    def to_dict(self) -> dict:
        return {
            "deltaId": self.delta_id,
            "sourceAgent": self.source_agent,
            "deltaType": self.delta_type,
            "payloadTokens": self.payload_tokens,
            "content": self.content,
            "timestamp": self.timestamp,
        }


class SharedContextBus:
    """Broadcast-efficient shared state store for multi-agent orchestration.
    
    Design invariants:
    - Each delta <= 80 tokens (enforced at publish time)
    - Each agent window <= 400 tokens (enforced at hydrate time)
    - No full context duplicated across agents — only delta_id references flow
    - Bus persisted to .focusgate/context_bus.jsonl on every publish
    """

    def __init__(self, workspace_root: str = ".") -> None:
        self._workspace_root = workspace_root
        self._bus_path = os.path.join(workspace_root, ".focusgate", "context_bus.jsonl")
        self._deltas: List[ContextDeltaEvent] = []     # In-memory ordered log
        self._seen_ids: set = set()                    # Deduplication set
        self._subscriptions: Dict[str, List[str]] = {} # agent_id -> [delta_types]
        self._load_from_disk()

    def publish(self, delta: ContextDeltaEvent) -> None:
        """Publish a delta to the bus. Deduplicates by delta_id."""
        if delta.delta_id in self._seen_ids:
            return  # Identical content already on bus
        self._deltas.append(delta)
        self._seen_ids.add(delta.delta_id)
        self._append_to_disk(delta)

    def subscribe(self, agent_id: str, delta_types: List[str]) -> None:
        """Register an agent's interest in specific delta types."""
        self._subscriptions[agent_id] = list(delta_types)

    def hydrate_window(
        self,
        agent_id: str,
        max_tokens: int = AGENT_WINDOW_MAX_TOKENS,
    ) -> List[ContextDeltaEvent]:
        """Return a token-bounded slice of the bus for an agent.

        Filters by the agent's subscribed delta_types, ordered by recency.
        Skips oversized deltas best-effort to pack compact history (v2.8).
        """
        subscribed = self._subscriptions.get(agent_id, list(VALID_DELTA_TYPES))
        window: List[ContextDeltaEvent] = []
        tokens_used = 0
        for delta in reversed(self._deltas):  # Most recent first
            if delta.delta_type not in subscribed:
                continue
            if tokens_used + delta.payload_tokens > max_tokens:
                continue
            window.append(delta)
            tokens_used += delta.payload_tokens
        return list(reversed(window))  # Chronological order for prompt rendering

    def evict_stale(self, max_stage_age: int = 1, current_stage: int = 0) -> int:
        """Prune deltas older than stage TTL (v2.8). DOMAIN_ANCHOR survives."""
        import time as _time
        now = _time.time()
        kept: List[ContextDeltaEvent] = []
        pruned = 0
        for delta in self._deltas:
            if delta.delta_type == "DOMAIN_ANCHOR":
                kept.append(delta)
                continue
            try:
                from datetime import datetime as _dt
                ts = _dt.fromisoformat(delta.timestamp.replace("Z", "+00:00"))
                age_days = (now - ts.timestamp()) / 86400.0
                if age_days > 1:
                    pruned += 1
                    self._seen_ids.discard(delta.delta_id)
                    continue
            except (ValueError, TypeError, AttributeError):
                pass
            kept.append(delta)
        self._deltas = kept
        if pruned > 0:
            self._compact_disk()
        return pruned

    def publish_file_patch(self, gate_id: str, file_path: str, diff_head: str) -> None:
        content = f"{file_path}: {diff_head[:50]}"[:320]
        self.publish(ContextDeltaEvent.create(
            source_agent=gate_id,
            delta_type="FILE_PATCH",
            content=content,
        ))

    def evict_settled(self, gate_id: str) -> int:
        kept: List[ContextDeltaEvent] = []
        pruned = 0
        for delta in self._deltas:
            if delta.delta_type == "DOMAIN_ANCHOR":
                kept.append(delta)
                continue
            if delta.delta_type == "REORIENT" and gate_id in delta.content:
                pruned += 1
                self._seen_ids.discard(delta.delta_id)
                continue
            kept.append(delta)
        self._deltas = kept
        if pruned > 0:
            self._compact_disk()
        return pruned

    def _compact_disk(self) -> None:
        """Atomically synchronizes active in-memory deltas back to on-disk context_bus.jsonl."""
        try:
            os.makedirs(os.path.dirname(self._bus_path), exist_ok=True)
            temp_path = self._bus_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                for d in self._deltas:
                    f.write(json.dumps(d.to_dict()) + "\n")
            os.replace(temp_path, self._bus_path)
        except Exception as e:
            print(f"[FocusGate] Context bus compaction failed: {e}", file=sys.stderr)

    def snapshot_hash(self) -> str:
        """SHA-256 of all delta_ids in order — stable bus identity token."""
        content = "|".join(d.delta_id for d in self._deltas)
        return hashlib.sha256(content.encode()).hexdigest()

    def get_all_deltas(self) -> List[ContextDeltaEvent]:
        """Return full bus log (for orchestrator audit)."""
        return list(self._deltas)

    def resolve_delta(self, delta_id: str) -> Optional[str]:
        """Dereference a content-addressed delta_id to its <=80-token snippet.

        TTL-aware by construction: evicted deltas are absent from the live
        _deltas log and resolve to None, so callers fall back to a summary
        instead of leaking an unresolvable bare pointer (v2.8 Part 3).
        """
        for delta in self._deltas:
            if delta.delta_id == delta_id:
                return delta.content
        return None

    def _append_to_disk(self, delta: ContextDeltaEvent) -> None:
        try:
            os.makedirs(os.path.dirname(self._bus_path), exist_ok=True)
            with open(self._bus_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(delta.to_dict()) + "\n")
        except Exception as e:
            print(f"[FocusGate] Context bus write failed: {e}", file=sys.stderr)

    def _load_from_disk(self) -> None:
        if not os.path.exists(self._bus_path):
            return
        try:
            with open(self._bus_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line)
                    delta = ContextDeltaEvent(
                        delta_id=d["deltaId"],
                        source_agent=d["sourceAgent"],
                        delta_type=d["deltaType"],
                        payload_tokens=d["payloadTokens"],
                        content=d["content"],
                        timestamp=d.get("timestamp", ""),
                    )
                    if delta.delta_id not in self._seen_ids:
                        self._deltas.append(delta)
                        self._seen_ids.add(delta.delta_id)
        except Exception as e:
            print(f"[FocusGate] Context bus load failed: {e}", file=sys.stderr)
