"""Hierarchical Precedence Sieve for FocusGate v2.8.

Provides deterministic routing resolution across competing multi-skill plugin
recommendations, preventing precedence inversion (e.g. aesthetic redesign
preempting active P0 security or production defects) and eliminating registration-order ties.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from .plugin_interface import RouteRecommendation


class PrecedenceTier(Enum):
    """Explicit priority tiers for operational task archetypes."""
    EMERGENCY_DEFECT = 10
    ARCHITECTURE_RFC = 5
    DESIGN_SYSTEM = 3
    DOCUMENTATION = 1


@dataclass
class SieveResult:
    """Outcome of hierarchical precedence sieve evaluation."""
    winning_route: RouteRecommendation
    calculated_rank: float
    competing_routes: List[Dict[str, Any]]
    precedence_tier: str


class HierarchicalPrecedenceSieve:
    """Ranks competing route recommendations via explicit domain tier weights."""

    def __init__(self, custom_tier_map: Optional[Dict[str, PrecedenceTier]] = None):
        self.custom_tier_map = custom_tier_map or {}

    def resolve_tier(self, rec: RouteRecommendation) -> PrecedenceTier:
        """Determines the precedence tier based on archetype and pipeline descriptors."""
        arch = getattr(rec, "archetype", "").upper()
        pipe = getattr(rec, "pipeline", "").upper()

        combined = f"{arch} {pipe}"

        for key, tier in self.custom_tier_map.items():
            if key.upper() in combined:
                return tier

        # Tier 0: Emergency defects, bugs, security leaks
        if any(k in combined for k in ("DEFECT", "EMERGENCY", "SECURITY", "CRASH", "RAPID DEFECT", "BUG")):
            return PrecedenceTier.EMERGENCY_DEFECT

        # Tier 1: Architecture, RFC, deep module design
        if any(k in combined for k in ("ARCHITECTURE", "RFC", "SEAM", "STRATEGIC")):
            return PrecedenceTier.ARCHITECTURE_RFC

        # Tier 2: Design system, accessibility, visual polish, UI components
        if any(k in combined for k in ("DESIGN", "UI", "A11Y", "ACCESSIBILITY", "CONTRAST", "COMPONENT")):
            return PrecedenceTier.DESIGN_SYSTEM

        # Tier 3: Writing, documentation, fragments, minor refactors
        return PrecedenceTier.DOCUMENTATION

    def calculate_rank(self, rec: RouteRecommendation) -> float:
        """Calculates deterministic composite rank: (Weight * 100) + (Confidence * 10)."""
        tier = self.resolve_tier(rec)
        weight = tier.value
        confidence = max(0.0, min(1.0, rec.confidence))
        return round((weight * 100.0) + (confidence * 10.0), 3)

    def resolve_best_route(self, candidates: List[RouteRecommendation]) -> Optional[SieveResult]:
        """Resolves the highest-priority route from competing plugin recommendations."""
        if not candidates:
            return None

        scored: List[Dict[str, Any]] = []
        for c in candidates:
            tier = self.resolve_tier(c)
            rank = self.calculate_rank(c)
            scored.append({
                "route": c,
                "rank": rank,
                "tier": tier.name,
                "pipeline": c.pipeline,
                "archetype": getattr(c, "archetype", ""),
                "confidence": c.confidence
            })

        # Deterministic sort: descending by rank, then descending by confidence
        scored.sort(key=lambda s: (s["rank"], s["confidence"]), reverse=True)
        winner_info = scored[0]

        return SieveResult(
            winning_route=winner_info["route"],
            calculated_rank=winner_info["rank"],
            competing_routes=scored,
            precedence_tier=winner_info["tier"]
        )
