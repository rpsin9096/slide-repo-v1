"""FocusGate v3.0 — Parallel Swarm Wave Dispatcher & Execution Engine.

Executes unblocked DAG frontier gates concurrently using a thread pool or isolated
worktrees, collecting execution receipts and driving ledger state convergence.

Zero external dependencies (100% Python stdlib).
"""

import os
import re
import sys
import time
import json
import hashlib
import subprocess
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

from core.mesh import ActorMeshRouter
from core.swarm.scheduler import SwarmScheduler, ActorAssignment


@dataclass
class WaveExecutionReceipt:
    """Execution outcome for a single assigned gate within a wave."""
    gate_id: str
    actor_id: str
    passed: bool
    duration: float
    output: str
    exit_code: int = 0
    merkle_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes receipt to dictionary."""
        return {
            "gate_id": self.gate_id,
            "actor_id": self.actor_id,
            "passed": self.passed,
            "duration": round(self.duration, 4),
            "output": self.output,
            "exit_code": self.exit_code,
            "merkle_hash": self.merkle_hash
        }


@dataclass
class WaveResult:
    """Consolidated outcome of a parallel swarm execution wave."""
    wave_number: int
    total_gates: int
    passed_gates: int
    failed_gates: int
    all_passed: bool
    receipts: List[WaveExecutionReceipt] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes WaveResult to dictionary."""
        return {
            "wave_number": self.wave_number,
            "total_gates": self.total_gates,
            "passed_gates": self.passed_gates,
            "failed_gates": self.failed_gates,
            "all_passed": self.all_passed,
            "receipts": [r.to_dict() for r in self.receipts]
        }


class SwarmWaveDispatcher:
    """Dispatches parallel waves of gates across swarm actors."""

    def __init__(
        self,
        router: Optional[ActorMeshRouter] = None,
        scheduler: Optional[SwarmScheduler] = None,
        max_workers: int = 4,
        workspace_root: Optional[str] = None
    ):
        self.router = router or ActorMeshRouter()
        self.scheduler = scheduler or SwarmScheduler()
        self.max_workers = max_workers
        self.workspace_root = workspace_root or os.getcwd()

    def _execute_assignment(self, assignment: ActorAssignment) -> WaveExecutionReceipt:
        """Executes a single actor assignment and captures execution receipt."""
        start_time = time.time()
        check_cmd = assignment.check_cmd.strip()

        if not check_cmd:
            duration = time.time() - start_time
            mhash = hashlib.sha256(f"{assignment.gate_id}:PASS_MANUAL".encode("utf-8")).hexdigest()
            return WaveExecutionReceipt(
                gate_id=assignment.gate_id,
                actor_id=assignment.actor_id,
                passed=True,
                duration=duration,
                output="PASS_MANUAL (No check_cmd specified)",
                exit_code=0,
                merkle_hash=mhash
            )

        try:
            proc = subprocess.run(
                check_cmd,
                shell=True,
                cwd=self.workspace_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=60.0
            )
            duration = time.time() - start_time
            passed = (proc.returncode == 0)
            output = proc.stdout.strip()
            raw_hash = f"{assignment.gate_id}:{proc.returncode}:{output}"
            mhash = hashlib.sha256(raw_hash.encode("utf-8")).hexdigest()

            return WaveExecutionReceipt(
                gate_id=assignment.gate_id,
                actor_id=assignment.actor_id,
                passed=passed,
                duration=duration,
                output=output,
                exit_code=proc.returncode,
                merkle_hash=mhash
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            duration = time.time() - start_time
            return WaveExecutionReceipt(
                gate_id=assignment.gate_id,
                actor_id=assignment.actor_id,
                passed=False,
                duration=duration,
                output=f"Execution error: {exc}",
                exit_code=1,
                merkle_hash=hashlib.sha256(str(exc).encode("utf-8")).hexdigest()
            )

    def run_wave(self, frontier_gates: List[Any], wave_number: int = 1) -> WaveResult:
        """Runs a concurrent execution wave for the provided frontier gates."""
        if not frontier_gates:
            return WaveResult(
                wave_number=wave_number,
                total_gates=0,
                passed_gates=0,
                failed_gates=0,
                all_passed=True,
                receipts=[]
            )

        assignments = self.scheduler.plan_wave(frontier_gates, router=self.router)
        receipts: List[WaveExecutionReceipt] = []

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(assignments))) as executor:
            future_to_assign = {
                executor.submit(self._execute_assignment, a): a
                for a in assignments
            }
            for future in as_completed(future_to_assign):
                receipt = future.result()
                receipts.append(receipt)

        # Sort receipts by gate_id for determinism
        receipts.sort(key=lambda r: r.gate_id)

        passed_count = sum(1 for r in receipts if r.passed)
        failed_count = len(receipts) - passed_count
        all_passed = (failed_count == 0)

        return WaveResult(
            wave_number=wave_number,
            total_gates=len(receipts),
            passed_gates=passed_count,
            failed_gates=failed_count,
            all_passed=all_passed,
            receipts=receipts
        )

    def run_until_complete(
        self,
        ledger_path: str,
        max_waves: int = 10
    ) -> Dict[str, Any]:
        """Iteratively drives DAG frontier waves until complete convergence or error."""
        if not os.path.isfile(ledger_path):
            return {
                "converged": False,
                "error": f"Ledger file not found: {ledger_path}",
                "waves_executed": 0,
                "total_gates_met": 0
            }

        waves_run = 0
        total_met = 0

        # Read content
        with open(ledger_path, "r", encoding="utf-8") as f:
            content = f.read()

        while waves_run < max_waves:
            # Parse unchecked gates
            # Pattern: - [ ] <gate_id>: <title>\n  CHECK: <cmd>
            pattern = re.compile(
                r'-\s*\[\s*\]\s*([a-zA-Z0-9_\-\.]+):\s*([^\n]+)(?:\n\s*CHECK:\s*([^\n]+))?',
                re.MULTILINE
            )
            matches = list(pattern.finditer(content))
            if not matches:
                # All gates met!
                return {
                    "converged": True,
                    "waves_executed": waves_run,
                    "total_gates_met": total_met,
                    "status": "ALL_GATES_MET"
                }

            # Build frontier gates from current matches
            frontier = []
            for m in matches:
                gid = m.group(1).strip()
                title = m.group(2).strip()
                cmd = m.group(3).strip() if m.group(3) else ""
                frontier.append(ActorAssignment(
                    gate_id=gid,
                    actor_id="",
                    specialty=self.scheduler.classify_specialty(type("Obj", (), {"id": gid, "title": title, "check_cmd": cmd})()),
                    check_cmd=cmd,
                    title=title
                ))

            waves_run += 1
            wave_res = self.run_wave(frontier, wave_number=waves_run)

            # v3.3: settle through the Evidence Gate (re-runs the CHECK), never by editing the file.
            from core.gates.evidence import settle_gate
            refused = []
            for r in wave_res.receipts:
                if not r.passed:
                    continue
                if settle_gate(ledger_path, r.gate_id).ok:
                    total_met += 1
                else:
                    refused.append(r.gate_id)
            with open(ledger_path, "r", encoding="utf-8") as f:
                content = f.read()
            if refused:
                return {
                    "converged": False,
                    "waves_executed": waves_run,
                    "total_gates_met": total_met,
                    "status": "SETTLEMENT_REFUSED",
                    "refused": refused
                }

            if not wave_res.all_passed:
                return {
                    "converged": False,
                    "waves_executed": waves_run,
                    "total_gates_met": total_met,
                    "failed_gates": [r.gate_id for r in wave_res.receipts if not r.passed],
                    "status": "BLOCKED_ON_FAILURE"
                }

        return {
            "converged": False,
            "waves_executed": waves_run,
            "total_gates_met": total_met,
            "status": "MAX_WAVES_EXCEEDED"
        }
