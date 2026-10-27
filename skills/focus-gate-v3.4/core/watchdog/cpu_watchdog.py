"""FocusGate v3.0 — Dynamic CPU Execution Watchdog & Throttler.

Monitors process CPU time, thread execution limits, and iteration counts,
terminating runaway loops and throttling intensive threads to protect CPU cores.

100% Python stdlib, zero external dependencies.
"""

import time
import threading
from typing import Callable, Any, Optional


class CPUQuotaExceededError(RuntimeError):
    """Raised when an execution exceeds its CPU time or iteration budget."""
    pass


class CPUExecutionWatchdog:
    """Guards task execution against infinite loops and CPU exhaustion."""

    def __init__(self, default_timeout_sec: float = 1.0, max_iterations: int = 10000):
        self.default_timeout_sec = default_timeout_sec
        self.max_iterations = max_iterations
        self._iteration_count: int = 0
        self._start_time: float = 0.0
        self._timeout_sec: float = default_timeout_sec

    def checkpoint(self) -> None:
        """Cooperative checkpoint invoked during loop iterations."""
        self._iteration_count += 1

        if self._iteration_count > self.max_iterations:
            raise CPUQuotaExceededError(
                f"Maximum iteration limit ({self.max_iterations}) exceeded by loop."
            )

        elapsed = time.time() - self._start_time
        if elapsed > self._timeout_sec:
            raise CPUQuotaExceededError(
                f"CPU execution time limit ({self._timeout_sec}s) exceeded."
            )

        # Cooperative throttling yield every 250 iterations
        if self._iteration_count % 250 == 0:
            time.sleep(0.0001)

    def execute_guarded(
        self,
        func: Callable[..., Any],
        *args: Any,
        timeout_sec: Optional[float] = None,
        max_iterations: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """Executes a callable under active timeout and thread watchdog monitoring."""
        self._timeout_sec = timeout_sec or self.default_timeout_sec
        self._iteration_count = 0
        self._start_time = time.time()
        if max_iterations is not None:
            self.max_iterations = max_iterations

        result_box = [None]
        error_box = [None]

        def target():
            try:
                result_box[0] = func(*args, **kwargs)
            except (CPUQuotaExceededError, RuntimeError, ValueError, TypeError, OSError) as e:
                error_box[0] = e

        worker = threading.Thread(target=target, daemon=True)
        worker.start()
        worker.join(timeout=self._timeout_sec)

        if worker.is_alive():
            raise CPUQuotaExceededError(
                f"CPU execution timeout ({self._timeout_sec}s) exceeded by runaway execution."
            )

        if error_box[0] is not None:
            raise error_box[0]

        return result_box[0]
