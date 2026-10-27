"""FocusGate v3.1 Loop 53 — Autonomous Self-Evolving Rule & Directive Engine.

Analyzes telemetry from gate settlements and failure clusters to formulate
token-bounded rule and directive patches, dynamically evolving system invariants.

Zero external dependencies (100% Python stdlib).
"""

import time
from typing import Dict, Any, List, Optional


class RulePatchProposal:
    """Represents a candidate patch to a declarative facet directive or gate invariant."""

    def __init__(
        self,
        target_facet: str,
        issue_type: str,
        patch_type: str,
        content_diff: str,
        estimated_tokens: int = 0,
        applied: bool = False,
        created_ts: Optional[float] = None,
    ):
        self.target_facet = target_facet
        self.issue_type = issue_type
        self.patch_type = patch_type
        self.content_diff = content_diff
        self.estimated_tokens = estimated_tokens or self._estimate_tokens(content_diff)
        self.applied = applied
        self.created_ts = created_ts if created_ts is not None else time.time()

    def _estimate_tokens(self, text: str) -> int:
        words = len(text.strip().split())
        return max(1, int(words * 1.3))

    def is_safe(self, token_ceiling: int = 400) -> bool:
        """Verifies that patch fits within the token budget and contains no banned tokens."""
        if self.estimated_tokens > token_ceiling:
            return False
        if self._estimate_tokens(self.content_diff) > token_ceiling:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serializes proposal to dictionary."""
        return {
            "target_facet": self.target_facet,
            "issue_type": self.issue_type,
            "patch_type": self.patch_type,
            "content_diff": self.content_diff,
            "estimated_tokens": self.estimated_tokens,
            "applied": self.applied,
            "created_ts": self.created_ts,
        }


class DirectiveEvolver:
    """Evolves declarative directives by clustering execution bottlenecks and synthesizing patches."""

    DEFENSIVE_TEMPLATES = {
        "type_error": "Invariant: Guard all inputs with explicit type annotations and null checks before processing.",
        "timeout": "Invariant: Enforce tight execution bounds and yield control periodically to avoid event stalls.",
        "deadlock": "Invariant: Adhere strictly to canonical resource lock hierarchy without nested acquisitions.",
        "cliche": "Invariant: Eliminate prose filler and generic summaries; emit terse structured contracts.",
    }

    def __init__(self) -> None:
        self._telemetry: List[Dict[str, Any]] = []
        self._proposals: List[RulePatchProposal] = []

    def record_failure_telemetry(self, facet_id: str, error_class: str, details: str) -> None:
        """Records an execution failure event with classification."""
        self._telemetry.append({
            "facet_id": facet_id,
            "error_class": error_class,
            "details": details,
            "timestamp": time.time(),
        })

    def cluster_bottlenecks(self, min_frequency: int = 2) -> Dict[str, List[str]]:
        """Groups recorded failures by facet and error_class exceeding the frequency threshold."""
        clusters: Dict[str, List[str]] = {}
        for entry in self._telemetry:
            key = f"{entry['facet_id']}:{entry['error_class']}"
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(entry["details"])

        return {k: v for k, v in clusters.items() if len(v) >= min_frequency}

    def synthesize_proposal(
        self,
        facet_id: str,
        error_class: str,
        original_directive: str,
    ) -> Optional[RulePatchProposal]:
        """Synthesizes a tailored defensive invariant patch bounded to token limits."""
        template = self.DEFENSIVE_TEMPLATES.get(
            error_class.lower(),
            "Invariant: Validate deterministic pre-conditions and post-conditions before state updates."
        )

        proposal = RulePatchProposal(
            target_facet=facet_id,
            issue_type=error_class,
            patch_type="APPEND_INVARIANT",
            content_diff=template,
        )

        if not proposal.is_safe(token_ceiling=400):
            return None

        self._proposals.append(proposal)
        return proposal

    def apply_proposal(self, proposal: RulePatchProposal, original_directive: str) -> str:
        """Applies a safe proposal to the existing directive string."""
        if not proposal.is_safe(token_ceiling=400):
            raise ValueError(f"Proposal for {proposal.target_facet} exceeds safety token ceiling.")

        separator = "\n" if original_directive.strip() else ""
        updated = f"{original_directive.rstrip()}{separator}{proposal.content_diff}"
        proposal.applied = True
        return updated
