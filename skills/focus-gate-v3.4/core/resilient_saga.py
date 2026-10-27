"""Resilient Saga Coordinator with Dead Letter Queue (DLQ) for FocusGate v2.8.

Guarantees transactional consistency across multi-agent handoffs and emits
ephemeral GateReceipt proofs. When a mid-execution step fails and a subsequent
compensating rollback also fails (e.g. disk permission, file lock, or network drop),
it creates an immutable failure tombstone in .focusgate/dlq/ and signals an
invariant safe-halt with a structured GateReceipt.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
import os
import json
import time
import sys
import uuid
import traceback

from .saga_coordinator import SagaCoordinator, SagaStep, SagaResult
from .ephemeral_session import GateReceipt


@dataclass
class DLQTombstone:
    """Immutable record of an uncompensated transaction failure."""
    tombstone_id: str
    saga_name: str
    failed_step: str
    failed_compensation_step: str
    error_message: str
    compensation_error: str
    timestamp: float
    remediation_cmd: str
    context_snapshot: Dict[str, Any]


@dataclass
class ResilientSagaResult:
    """Execution outcome of a resilient saga execution."""
    success: bool
    completed_steps: List[str]
    compensated_steps: List[str]
    uncompensated_steps: List[str]
    tombstone_path: Optional[str] = None
    inconsistent_halt: bool = False
    error_step: Optional[str] = None
    error_message: Optional[str] = None
    receipt: Optional[GateReceipt] = None


class ResilientSagaCoordinator(SagaCoordinator):
    """Saga coordinator with Dead Letter Queue (DLQ) persistence and invariant protection."""

    def __init__(self, saga_name: str, dlq_dir: Optional[str] = None):
        super().__init__(saga_name=saga_name)
        self.dlq_dir = dlq_dir or os.path.join(".focusgate", "dlq")

    def execute(self, initial_context: Optional[Dict[str, Any]] = None) -> ResilientSagaResult:
        """Executes saga forward steps; rolls back with DLQ on compensation failure."""
        if initial_context:
            self.context.update(initial_context)

        completed: List[str] = []
        compensated: List[str] = []
        uncompensated: List[str] = []
        tombstone_path: Optional[str] = None
        has_compensation_fault = False
        failed_step_name: Optional[str] = None
        error_msg: Optional[str] = None

        t0 = time.perf_counter()

        for step in self.steps:
            try:
                success = step.action(self.context)
                if success:
                    completed.append(step.name)
                else:
                    failed_step_name = step.name
                    error_msg = f"Step '{step.name}' returned False"
                    break
            except Exception as e:
                failed_step_name = step.name
                error_msg = f"Step '{step.name}' threw exception: {str(e)}"
                break

        # If forward execution failed, trigger rollback in reverse order
        if failed_step_name is not None:
            for step_to_undo in reversed([s for s in self.steps if s.name in completed]):
                try:
                    step_to_undo.compensate(self.context)
                    compensated.append(step_to_undo.name)
                except Exception as comp_err:
                    has_compensation_fault = True
                    uncompensated.append(step_to_undo.name)
                    comp_err_msg = str(comp_err)

                    # Persist Dead Letter Queue (DLQ) failure tombstone
                    tombstone_path = self._write_tombstone(
                        failed_step=failed_step_name,
                        comp_step=step_to_undo.name,
                        primary_error=error_msg or "Unknown primary failure",
                        comp_error=comp_err_msg
                    )
                    break

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        saga_success = (failed_step_name is None)

        # Emit GateReceipt proof
        key_findings = []
        if saga_success:
            key_findings.append(f"Saga {self.saga_name} completed {len(completed)} steps cleanly")
        else:
            key_findings.append(f"Saga {self.saga_name} failed at {failed_step_name}")
            if has_compensation_fault:
                key_findings.append(f"DLQ Tombstone created at {os.path.basename(tombstone_path or '')}")

        receipt = GateReceipt(
            session_id=f"saga-{uuid.uuid4().hex[:8]}",
            gate_id=self.saga_name,
            facet="saga",
            status="PASS" if saga_success else "FAIL",
            key_findings=key_findings,
            artifacts_produced=[tombstone_path] if tombstone_path else [],
            elapsed_ms=elapsed_ms
        )

        return ResilientSagaResult(
            success=saga_success,
            completed_steps=completed,
            compensated_steps=compensated,
            uncompensated_steps=uncompensated,
            tombstone_path=tombstone_path,
            inconsistent_halt=has_compensation_fault,
            error_step=failed_step_name,
            error_message=error_msg,
            receipt=receipt
        )

    def _write_tombstone(
        self,
        failed_step: str,
        comp_step: str,
        primary_error: str,
        comp_error: str
    ) -> str:
        """Persists an immutable DLQ tombstone JSON file for human or CLI remediation."""
        os.makedirs(self.dlq_dir, exist_ok=True)
        tombstone_id = f"dlq-{uuid.uuid4().hex[:8]}"
        filename = f"tombstone-{int(time.time())}-{tombstone_id}.json"
        filepath = os.path.join(self.dlq_dir, filename)

        remediation_cmd = (
            f"focus-gate --remedy-dlq {filepath} || "
            f"git checkout -- . && echo 'Restored clean working tree'"
        )

        tombstone = DLQTombstone(
            tombstone_id=tombstone_id,
            saga_name=self.saga_name,
            failed_step=failed_step,
            failed_compensation_step=comp_step,
            error_message=primary_error,
            compensation_error=comp_error,
            timestamp=time.time(),
            remediation_cmd=remediation_cmd,
            context_snapshot={k: str(v) for k, v in self.context.items()}
        )

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(tombstone.__dict__, f, indent=2)

        return filepath
