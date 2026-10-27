"""Proof-Carrying Acceptance Trees for FocusGate v2.8.

Eliminates superficial completion assertions by requiring multi-criteria observable
command artifacts, file diffs, and oracle verdicts before certifying gate completion.
Zero external dependencies (100% Python stdlib).
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
import os
import re


@dataclass
class ProofCriterion:
    id: str
    description: str
    verifier: Callable[[Dict[str, Any]], Tuple[bool, Dict[str, Any]]]
    status: str = "PENDING"
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProofVerdict:
    verified: bool
    compliance_score: float  # 0.0 to 100.0%
    passed_criteria: List[str]
    failed_criteria: List[str]
    evidence_bundle: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verified": self.verified,
            "compliance_score": self.compliance_score,
            "passed_criteria": self.passed_criteria,
            "failed_criteria": self.failed_criteria,
            "evidence_bundle": self.evidence_bundle
        }


class ProofTree:
    """Hierarchical verification tree requiring concrete artifacts for completion."""

    def __init__(self, gate_id: str):
        self.gate_id = gate_id
        self.criteria: List[ProofCriterion] = []

    def add_criterion(self, criterion_id: str, description: str, verifier: Callable[[Dict[str, Any]], Tuple[bool, Dict[str, Any]]]) -> None:
        self.criteria.append(ProofCriterion(id=criterion_id, description=description, verifier=verifier))

    def evaluate(self, context: Dict[str, Any]) -> ProofVerdict:
        passed = []
        failed = []
        bundle = {}

        for crit in self.criteria:
            try:
                ok, ev = crit.verifier(context)
                crit.evidence = ev
                bundle[crit.id] = ev
                if ok:
                    crit.status = "VERIFIED"
                    passed.append(crit.id)
                else:
                    crit.status = "FAILED"
                    failed.append(crit.id)
            except Exception as e:
                crit.status = "FAILED"
                crit.evidence = {"error": str(e)}
                bundle[crit.id] = {"error": str(e)}
                failed.append(crit.id)

        total = len(self.criteria)
        score = (len(passed) / total * 100.0) if total > 0 else 0.0
        all_passed = (len(passed) == total and total > 0)

        return ProofVerdict(
            verified=all_passed,
            compliance_score=round(score, 1),
            passed_criteria=passed,
            failed_criteria=failed,
            evidence_bundle=bundle
        )

    @classmethod
    def build_unlazy_criteria(cls, gate: Any, target_files: Optional[List[str]] = None) -> "ProofTree":
        """Factory creating the mandatory 3-criteria unlazy verification tree."""
        from .unlazy_guard import ExecutionRigorGuard

        gate_id = getattr(gate, "id", None) or (gate.get("id") if isinstance(gate, dict) else "gate-unknown")
        tree = cls(gate_id=gate_id)

        # 1. Execution Oracle Criterion
        def verify_oracle(ctx: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
            exit_code = ctx.get("exit_code")
            output = ctx.get("output", "")
            expect = getattr(gate, "expect", None) or getattr(gate, "expect_pattern", None)
            if isinstance(gate, dict):
                expect = gate.get("expect") or gate.get("expect_pattern")

            passed = (exit_code == 0)
            if passed and expect:
                passed = bool(re.search(expect, output))

            return passed, {
                "exit_code": exit_code,
                "matches_expect": passed,
                "output_snippet": output[:100]
            }

        tree.add_criterion("oracle_execution", "Verification command exits 0 and satisfies expect regex", verify_oracle)

        # 2. Grounded Side-Effect Criterion
        def verify_side_effects(ctx: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
            files_to_check = target_files or ctx.get("modified_files", [])
            if not files_to_check:
                # If no specific files designated, verify output is non-empty and non-trivial
                output = ctx.get("output", "").strip()
                return len(output) > 0, {"verified_output_presence": True, "length": len(output)}

            verified_files = []
            for path in files_to_check:
                if not os.path.exists(path):
                    return False, {"missing_file": path}
                size = os.path.getsize(path)
                if size == 0:
                    return False, {"empty_file": path}
                verified_files.append({"path": path, "size": size})

            return True, {"verified_files": verified_files}

        tree.add_criterion("grounded_side_effect", "Concrete real-world artifacts/state exist on disk", verify_side_effects)

        # 3. Rigor Invariant Criterion
        def verify_rigor(ctx: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
            diff = ctx.get("code_diff", "")
            test_out = ctx.get("output", "")
            is_valid, reasons = ExecutionRigorGuard.validate_completion(gate, code_diff=diff, test_output=test_out)
            return is_valid, {
                "rigor_passed": is_valid,
                "violations": reasons
            }

        tree.add_criterion("rigor_standards", "Zero placeholder stubs, TODOs, or superficial assertions", verify_rigor)

        return tree
