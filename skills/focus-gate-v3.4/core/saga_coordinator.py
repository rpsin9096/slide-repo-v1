"""Saga Compensation Coordinator for FocusGate v2.8.

Provides distributed transaction semantics for multi-agent workflows, ensuring
that mid-execution failures trigger deterministic compensating transactions
without corrupting session state or leaving orphaned artifacts.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import sys


@dataclass
class SagaStep:
    name: str
    action: Callable[[Dict[str, Any]], bool]
    compensate: Callable[[Dict[str, Any]], None]
    executed: bool = False


@dataclass
class SagaResult:
    success: bool
    completed_steps: List[str]
    compensated_steps: List[str]
    error_step: Optional[str] = None
    error_message: Optional[str] = None


class SagaCoordinator:
    """Manages transactional forward execution and compensating rollbacks."""

    def __init__(self, saga_name: str):
        self.saga_name = saga_name
        self.steps: List[SagaStep] = []
        self.context: Dict[str, Any] = {}

    def add_step(self, name: str, action: Callable[[Dict[str, Any]], bool], compensate: Callable[[Dict[str, Any]], None]) -> None:
        self.steps.append(SagaStep(name=name, action=action, compensate=compensate))

    def execute(self, initial_context: Optional[Dict[str, Any]] = None) -> SagaResult:
        if initial_context:
            self.context.update(initial_context)

        completed = []
        compensated = []

        for idx, step in enumerate(self.steps):
            try:
                ok = step.action(self.context)
                if ok:
                    step.executed = True
                    completed.append(step.name)
                else:
                    return self._rollback(idx, step.name, "Step action returned False", completed, compensated)
            except Exception as e:
                return self._rollback(idx, step.name, str(e), completed, compensated)

        return SagaResult(
            success=True,
            completed_steps=completed,
            compensated_steps=[]
        )

    def _rollback(self, failed_idx: int, failed_step_name: str, error_msg: str, completed: List[str], compensated: List[str]) -> SagaResult:
        print(f"[Saga Coordinator] Failure in step '{failed_step_name}': {error_msg}. Triggering compensation rollbacks...", file=sys.stderr)

        # Execute compensating transactions in reverse order for all completed steps
        for i in range(failed_idx - 1, -1, -1):
            s = self.steps[i]
            if s.executed:
                try:
                    s.compensate(self.context)
                    compensated.append(s.name)
                except Exception as comp_err:
                    print(f"[Saga Coordinator] Compensation error in '{s.name}': {comp_err}", file=sys.stderr)

        return SagaResult(
            success=False,
            completed_steps=completed,
            compensated_steps=compensated,
            error_step=failed_step_name,
            error_message=error_msg
        )
