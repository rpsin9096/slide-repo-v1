"""FocusGate v3.0 — High-Throughput Atomic Event Ring Buffer.

Provides a bounded circular ring buffer with monotonic sequence tracking,
pre-allocated fixed slots, and thread-safe low-latency pub/sub reads.

100% Python stdlib, zero external dependencies.
"""

import threading
from typing import Any, List, Tuple, Optional


class AtomicEventRingBuffer:
    """Thread-safe circular ring buffer with pre-allocated slots."""

    def __init__(self, capacity: int = 1024):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
        self._buffer: List[Any] = [None] * capacity
        self._seqs: List[int] = [0] * capacity
        self._head: int = 0
        self._lock = threading.Lock()

    def push(self, item: Any) -> int:
        """Pushes an item into the circular buffer, returning its sequence number."""
        with self._lock:
            seq = self._head
            idx = seq % self.capacity
            self._buffer[idx] = item
            self._seqs[idx] = seq
            self._head += 1
            return seq

    def size(self) -> int:
        """Returns the current number of items buffered (capped at capacity)."""
        with self._lock:
            return min(self._head, self.capacity)

    def total_pushed(self) -> int:
        """Returns the monotonic count of all items ever pushed."""
        with self._lock:
            return self._head

    def latest(self, count: int = 10) -> List[Tuple[int, Any]]:
        """Returns up to `count` most recent items in ascending sequence order."""
        with self._lock:
            available = min(self._head, self.capacity)
            n = min(count, available)
            if n <= 0:
                return []
            res: List[Tuple[int, Any]] = []
            for i in range(self._head - n, self._head):
                idx = i % self.capacity
                res.append((self._seqs[idx], self._buffer[idx]))
            return res

    def read_since(self, seq_num: int, limit: int = 100) -> List[Tuple[int, Any]]:
        """Reads items strictly greater than `seq_num` up to `limit`."""
        with self._lock:
            oldest_available = max(0, self._head - self.capacity)
            start = max(seq_num + 1, oldest_available)
            if start >= self._head:
                return []
            end = min(self._head, start + limit)
            res: List[Tuple[int, Any]] = []
            for i in range(start, end):
                idx = i % self.capacity
                res.append((self._seqs[idx], self._buffer[idx]))
            return res

    def clear(self) -> None:
        """Resets the ring buffer."""
        with self._lock:
            self._head = 0
            self._buffer = [None] * self.capacity
            self._seqs = [0] * self.capacity
