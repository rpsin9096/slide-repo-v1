"""FocusGate v3.0 — Smart-Zone & Actor Context Compaction Package."""

from core.compaction.smart_compactor import SmartZoneCompactor
from core.compaction.actor_context_compactor import ActorContextCompactor
from core.compaction.proof_tree_compactor import ProofTreeCompactor, MicroDeltaBus
from core.compaction.adaptive_budget import (
    TokenBudgetSpec,
    DynamicTokenBudgeter,
    AdaptivePersonaCompressor,
)

__all__ = [
    "SmartZoneCompactor",
    "ActorContextCompactor",
    "ProofTreeCompactor",
    "MicroDeltaBus",
    "TokenBudgetSpec",
    "DynamicTokenBudgeter",
    "AdaptivePersonaCompressor",
]
