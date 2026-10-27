"""FocusGate v3.0 — CPU Resource Circuit Breaker.

Trips and isolates actors or processes that repeatedly exceed CPU execution quotas,
preventing cascading thread exhaustion and system lockup.

100% Python stdlib, zero external dependencies.
"""

import time
from typing import Dict, Any


class CPUResourceCircuitBreaker:
    """Circuit breaker isolating components causing CPU runaways."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 1.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state: str = "CLOSED"  # "CLOSED" | "OPEN" | "HALF_OPEN"
        self.failure_counts: Dict[str, int] = {}
        self.last_tripped_time: float = 0.0

    def allow_execution(self, actor_id: str) -> bool:
        """Determines whether execution is permitted for actor."""
        if self.state == "OPEN":
            if time.time() - self.last_tripped_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def record_violation(self, actor_id: str) -> None:
        """Records a CPU quota violation and trips circuit if threshold reached."""
        self.failure_counts[actor_id] = self.failure_counts.get(actor_id, 0) + 1
        if self.failure_counts[actor_id] >= self.failure_threshold:
            self.state = "OPEN"
            self.last_tripped_time = time.time()

    def record_success(self, actor_id: str) -> None:
        """Resets violation history upon verified healthy execution."""
        self.failure_counts[actor_id] = 0
        self.state = "CLOSED"
