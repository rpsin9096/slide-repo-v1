"""Deterministic Hierarchical Statechart Engine for FocusGate v2.8.

Provides formal state-machine coordination for agent workflows, guard evaluations,
transition actions, deterministic recovery paths, and invariant safe-halt transitions.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import copy


class StatechartState(str, Enum):
    IDLE = "IDLE"
    TRIAGING = "TRIAGING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    RECOVERY = "RECOVERY"
    INCONSISTENT_SAFE_HALT = "INCONSISTENT_SAFE_HALT"


@dataclass
class Transition:
    event: str
    target: StatechartState
    guard: Optional[Callable[[Dict[str, Any]], bool]] = None
    action: Optional[Callable[[Dict[str, Any]], None]] = None


class WorkflowStatechart:
    """Finite Statechart machine orchestrating FocusGate pipeline lifecycle."""

    def __init__(self, initial_state: StatechartState = StatechartState.IDLE):
        self.current_state: StatechartState = initial_state
        self.context: Dict[str, Any] = {
            "retries": 0,
            "max_retries": 3,
            "history": [initial_state.value],
            "checkpoint": None
        }
        self.transitions: Dict[StatechartState, List[Transition]] = {
            StatechartState.IDLE: [
                Transition(event="SUBMIT_TASK", target=StatechartState.TRIAGING)
            ],
            StatechartState.TRIAGING: [
                Transition(
                    event="ROUTE_SETTLED",
                    target=StatechartState.PLANNING,
                    guard=lambda ctx: bool(ctx.get("pipeline"))
                )
            ],
            StatechartState.PLANNING: [
                Transition(
                    event="GATE_ACTIVATED",
                    target=StatechartState.EXECUTING,
                    guard=lambda ctx: bool(ctx.get("active_gate_id"))
                )
            ],
            StatechartState.EXECUTING: [
                Transition(event="RUN_VERIFY", target=StatechartState.VERIFYING),
                Transition(event="ABORT", target=StatechartState.RECOVERY),
                Transition(event="DLQ_HALT", target=StatechartState.INCONSISTENT_SAFE_HALT)
            ],
            StatechartState.VERIFYING: [
                Transition(
                    event="ORACLE_PASS",
                    target=StatechartState.EXECUTING,
                    guard=lambda ctx: ctx.get("has_pending_gates", False)
                ),
                Transition(
                    event="ALL_GATES_PASS",
                    target=StatechartState.REVIEWING,
                    guard=lambda ctx: not ctx.get("has_pending_gates", False)
                ),
                Transition(
                    event="ORACLE_FAIL",
                    target=StatechartState.RECOVERY,
                    action=self._increment_retry
                ),
                Transition(event="DLQ_HALT", target=StatechartState.INCONSISTENT_SAFE_HALT)
            ],
            StatechartState.REVIEWING: [
                Transition(
                    event="REVIEW_CLEAN",
                    target=StatechartState.COMPLETED
                ),
                Transition(
                    event="REVIEW_REJECT",
                    target=StatechartState.EXECUTING,
                    action=lambda ctx: ctx.update({"review_feedback": "Defect spotted"})
                )
            ],
            StatechartState.RECOVERY: [
                Transition(
                    event="ROLLBACK_SUCCESS",
                    target=StatechartState.EXECUTING,
                    guard=lambda ctx: ctx.get("retries", 0) <= ctx.get("max_retries", 3)
                ),
                Transition(
                    event="RECOVERY_EXHAUSTED",
                    target=StatechartState.IDLE,
                    action=lambda ctx: ctx.update({"aborted": True})
                ),
                Transition(event="DLQ_HALT", target=StatechartState.INCONSISTENT_SAFE_HALT)
            ],
            StatechartState.INCONSISTENT_SAFE_HALT: [
                Transition(event="RESET", target=StatechartState.IDLE),
                Transition(event="MANUAL_REMEDIED", target=StatechartState.IDLE)
            ],
            StatechartState.COMPLETED: [
                Transition(event="RESET", target=StatechartState.IDLE)
            ]
        }

    def trigger(self, event: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        """Evaluates available transitions for the event and performs state transition."""
        if payload:
            self.context.update(payload)

        available = self.transitions.get(self.current_state, [])
        for trans in available:
            if trans.event == event:
                if trans.guard is None or trans.guard(self.context):
                    old_state = self.current_state
                    if trans.action:
                        trans.action(self.context)
                    self.current_state = trans.target
                    self.context["history"].append(self.current_state.value)
                    return True
        return False

    def can_trigger(self, event: str) -> bool:
        """Returns True if the event is permitted in the current state with satisfied guards."""
        available = self.transitions.get(self.current_state, [])
        for trans in available:
            if trans.event == event:
                return trans.guard is None or trans.guard(self.context)
        return False

    def checkpoint(self) -> None:
        """Saves current state and context for transactional rollback."""
        self.context["checkpoint"] = {
            "state": self.current_state,
            "context_snapshot": copy.deepcopy(self.context)
        }

    def rollback_to_checkpoint(self) -> bool:
        """Restores state from last checkpoint if available."""
        cp = self.context.get("checkpoint")
        if not cp:
            return False
        self.current_state = cp["state"]
        self.context = dict(cp["context_snapshot"])
        self.context["history"].append(f"ROLLBACK:{self.current_state.value}")
        return True

    def _increment_retry(self, ctx: Dict[str, Any]) -> None:
        ctx["retries"] = ctx.get("retries", 0) + 1
