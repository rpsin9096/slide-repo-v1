"""FocusGate v3.0 — Actor Message Envelope & Priority Mailbox.

Implements priority-ordered messaging and bounded capacity queues for
autonomous cognitive swarm actors.

Zero external dependencies (100% Python standard library).
"""

import time
import uuid
import queue
from enum import IntEnum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class MessagePriority(IntEnum):
    """Priority tiers for actor message scheduling (lower value = higher priority)."""
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass(order=True)
class ActorMessage:
    """Prioritized immutable message envelope exchanged across the actor mesh."""
    priority: int = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8], compare=False)
    source: str = field(default="", compare=False)
    target: str = field(default="", compare=False)
    topic: str = field(default="", compare=False)
    payload: Dict[str, Any] = field(default_factory=dict, compare=False)
    correlation_id: Optional[str] = field(default=None, compare=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "priority": int(self.priority),
            "timestamp": self.timestamp,
            "source": self.source,
            "target": self.target,
            "topic": self.topic,
            "payload": self.payload,
            "correlation_id": self.correlation_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActorMessage":
        return cls(
            priority=data.get("priority", MessagePriority.NORMAL),
            timestamp=data.get("timestamp", time.time()),
            message_id=data.get("message_id", str(uuid.uuid4())[:8]),
            source=data.get("source", ""),
            target=data.get("target", ""),
            topic=data.get("topic", ""),
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id")
        )


class ActorMailbox:
    """Thread-safe priority mailbox with bounded capacity and backpressure."""

    def __init__(self, maxsize: int = 100):
        self.maxsize = maxsize
        self._queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=maxsize)

    def put(self, message: ActorMessage, timeout: Optional[float] = None) -> bool:
        """Pushes a message into the priority queue."""
        try:
            self._queue.put(message, block=True, timeout=timeout)
            return True
        except queue.Full:
            return False

    def get(self, timeout: Optional[float] = None) -> Optional[ActorMessage]:
        """Pops the highest priority message from the mailbox."""
        try:
            return self._queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def get_nowait(self) -> Optional[ActorMessage]:
        """Non-blocking pop of the highest priority message."""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def empty(self) -> bool:
        return self._queue.empty()

    def qsize(self) -> int:
        return self._queue.qsize()
