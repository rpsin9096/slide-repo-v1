"""FocusGate v3.0 — Push Event Stream IPC.

Provides in-memory pub/sub message queues and real-time streaming of reactive
workspace events, gate evaluations, and swarm state changes to Unix socket clients.

100% Python stdlib, zero external dependencies.
"""

import time
import json
import queue
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class StreamEvent:
    """A typed event broadcast over the push stream."""
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamEvent":
        return cls(
            event_id=data.get("event_id", ""),
            event_type=data.get("event_type", "UNKNOWN"),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", 0.0)
        )


class PushEventStream:
    """Manages active subscriber queues and broadcasts events with historical buffering."""

    def __init__(self, max_buffer: int = 100):
        self.max_buffer = max_buffer
        self.subscribers: Dict[str, queue.Queue] = {}
        self.history: List[StreamEvent] = []
        self._counter: int = 0

    def subscribe(self, subscriber_id: str) -> queue.Queue:
        """Registers a subscriber queue receiving subsequent broadcast events."""
        q: queue.Queue = queue.Queue()
        self.subscribers[subscriber_id] = q
        return q

    def unsubscribe(self, subscriber_id: str) -> None:
        """Removes a subscriber queue."""
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]

    def publish(self, event_type: str, payload: Dict[str, Any]) -> StreamEvent:
        """Publishes an event to all active subscriber queues and buffers in history."""
        self._counter += 1
        event_id = f"ev-{int(time.time()*1000)}-{self._counter}"
        event = StreamEvent(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            timestamp=time.time()
        )

        # Buffer in history
        self.history.append(event)
        if len(self.history) > self.max_buffer:
            self.history = self.history[-self.max_buffer:]

        # Broadcast to subscribers
        for sub_id, q in list(self.subscribers.items()):
            try:
                q.put_nowait(event)
            except queue.Full:
                pass

        return event

    def get_recent_events(self, limit: int = 50) -> List[StreamEvent]:
        """Returns the most recent buffered events."""
        return self.history[-limit:]
