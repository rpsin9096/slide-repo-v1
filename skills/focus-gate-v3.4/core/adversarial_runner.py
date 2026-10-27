"""Red/Blue Adversarial Review Loop Runner for FocusGate v2.8.

Coordinates dialectic architectural stress-tests pitting Blue Team (codebase-design)
against Red Team (grilling) across multi-round adversarial tournaments before
certifying major architectural proposals or RFCs.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Callable


@dataclass
class AdversarialRound:
    """A single debate round between Blue and Red teams."""
    round_number: int
    blue_statement: str
    red_critique: str
    vulnerabilities_found: List[str]
    mitigations_verified: List[str]
    passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "blue_statement": self.blue_statement,
            "red_critique": self.red_critique,
            "vulnerabilities_found": self.vulnerabilities_found,
            "mitigations_verified": self.mitigations_verified,
            "passed": self.passed
        }


@dataclass
class AdversarialVerdict:
    """Final outcome of an adversarial review tournament."""
    proposal_id: str
    status: str  # "APPROVED" | "REJECTED_NEEDS_HARDENING"
    rounds: List[AdversarialRound]
    total_rounds: int
    vulnerabilities_mitigated: int
    residual_risk_score: float  # 0.0 (safest) to 1.0 (hazardous)
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "status": self.status,
            "rounds": [r.to_dict() for r in self.rounds],
            "total_rounds": self.total_rounds,
            "vulnerabilities_mitigated": self.vulnerabilities_mitigated,
            "residual_risk_score": self.residual_risk_score,
            "summary": self.summary
        }


class AdversarialRunner:
    """Runs a 3-round dialectic tournament between Blue (proposer) and Red (stress-tester)."""

    def __init__(self, max_rounds: int = 3, risk_threshold: float = 0.25):
        self.max_rounds = max_rounds
        self.risk_threshold = risk_threshold

    def run_tournament(
        self,
        proposal_id: str,
        initial_proposal: str,
        blue_agent: Optional[Callable[[int, List[str], str], str]] = None,
        red_agent: Optional[Callable[[int, str], Dict[str, Any]]] = None
    ) -> AdversarialVerdict:
        """Executes the multi-round dialectic review tournament.
        
        Args:
            proposal_id: Unique identifier for the RFC or architecture.
            initial_proposal: Text description of the interface or seam design.
            blue_agent: Callable(round_idx, pending_risks, prior_context) -> blue_response
            red_agent: Callable(round_idx, blue_statement) -> {"critique": str, "vulnerabilities": List[str], "mitigated": List[str]}
        """
        rounds: List[AdversarialRound] = []
        current_proposal = initial_proposal
        unmitigated_vulns: List[str] = []
        total_mitigated = 0

        # Default Blue Agent heuristic (codebase-design persona)
        def default_blue(r_idx: int, pending: List[str], ctx: str) -> str:
            if r_idx == 1:
                return f"[Blue Round 1 Proposal]: Interface contract defined with invariant assertions: {ctx[:120]}..."
            elif r_idx == 2:
                return f"[Blue Round 2 Hardening]: Added isolated error boundaries and circuit breaker for: {', '.join(pending)}"
            else:
                return f"[Blue Round 3 Final Spec]: Hardened seam verified with automated fuzz assertions and idempotency."

        # Default Red Agent heuristic (grilling persona)
        def default_red(r_idx: int, statement: str) -> Dict[str, Any]:
            if r_idx == 1:
                return {
                    "critique": "Unchecked concurrency race in cache layer and unhandled timeout on external I/O.",
                    "vulnerabilities": ["concurrency_race_condition", "unhandled_io_timeout"],
                    "mitigated": []
                }
            elif r_idx == 2:
                return {
                    "critique": "Concurrency race resolved via mutex; unhandled I/O timeout remains partially unmitigated under network partition.",
                    "vulnerabilities": ["network_partition_stall"],
                    "mitigated": ["concurrency_race_condition", "unhandled_io_timeout"]
                }
            else:
                return {
                    "critique": "All critical failure modes and boundary leaks mitigated with zero residual high-severity risks.",
                    "vulnerabilities": [],
                    "mitigated": ["network_partition_stall"]
                }

        blue_fn = blue_agent or default_blue
        red_fn = red_agent or default_red

        for r in range(1, self.max_rounds + 1):
            blue_statement = blue_fn(r, unmitigated_vulns, current_proposal)
            red_eval = red_fn(r, blue_statement)

            critique = red_eval.get("critique", "")
            found = red_eval.get("vulnerabilities", [])
            mitigated = red_eval.get("mitigated", [])

            # Update tracked vulnerabilities
            total_mitigated += len(mitigated)
            unmitigated_vulns = [v for v in unmitigated_vulns if v not in mitigated]
            for v in found:
                if v not in unmitigated_vulns:
                    unmitigated_vulns.append(v)

            round_passed = len(found) == 0 or len(mitigated) >= len(found)
            rounds.append(
                AdversarialRound(
                    round_number=r,
                    blue_statement=blue_statement,
                    red_critique=critique,
                    vulnerabilities_found=found,
                    mitigations_verified=mitigated,
                    passed=round_passed
                )
            )

        # Residual risk calculation
        risk_score = round(len(unmitigated_vulns) / max(1, (len(unmitigated_vulns) + total_mitigated)), 2)
        is_approved = (risk_score <= self.risk_threshold) and (len(unmitigated_vulns) == 0)

        summary = (
            f"Adversarial tournament completed in {len(rounds)} rounds. "
            f"Mitigated: {total_mitigated} vulnerabilities. Residual unmitigated: {len(unmitigated_vulns)}. "
            f"Verdict: {'APPROVED' if is_approved else 'REJECTED_NEEDS_HARDENING'}."
        )

        return AdversarialVerdict(
            proposal_id=proposal_id,
            status="APPROVED" if is_approved else "REJECTED_NEEDS_HARDENING",
            rounds=rounds,
            total_rounds=len(rounds),
            vulnerabilities_mitigated=total_mitigated,
            residual_risk_score=risk_score,
            summary=summary
        )
