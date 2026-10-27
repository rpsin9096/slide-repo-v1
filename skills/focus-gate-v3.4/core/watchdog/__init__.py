"""FocusGate v3.0 — Infinite Loop Detection & CPU Watchdog Package."""

from core.watchdog.ast_loop_analyzer import ASTLoopAnalyzer, LoopSafetyReport, LoopIssue
from core.watchdog.cpu_watchdog import CPUExecutionWatchdog, CPUQuotaExceededError
from core.watchdog.circuit_breaker import CPUResourceCircuitBreaker

__all__ = [
    "ASTLoopAnalyzer",
    "LoopSafetyReport",
    "LoopIssue",
    "CPUExecutionWatchdog",
    "CPUQuotaExceededError",
    "CPUResourceCircuitBreaker"
]
