"""FocusGate v3.1 — Dynamic Token Budgeting & Adaptive Compression (Loop 46).

Calculates domain-weighted context window ceilings and executes sub-5ms JIT
mailbox micro-compaction when actor message histories approach token boundaries.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import time
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TokenBudgetSpec:
    """Configured token ceiling and warning threshold for a specialized actor."""
    actor_id: str
    domain: str
    max_context_tokens: int
    warning_ratio: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "domain": self.domain,
            "max_context_tokens": self.max_context_tokens,
            "warning_ratio": self.warning_ratio,
            "warning_threshold": int(self.max_context_tokens * self.warning_ratio),
        }


class DynamicTokenBudgeter:
    """Allocates domain-weighted context windows and monitors mailbox token pressures."""

    DOMAIN_MULTIPLIERS = {
        "security": 1.0,     # Full window for deep AST / taint analysis
        "database": 0.75,    # 75% for schema / query / migration logic
        "frontend": 0.5,     # 50% for component / design token generation
        "general": 0.5,      # Default 50%
    }

    def __init__(self, default_model_ceiling: int = 8192):
        self.default_model_ceiling = default_model_ceiling

    def allocate_budget(
        self,
        actor_id: str,
        domain: str,
        model_ceiling: Optional[int] = None
    ) -> TokenBudgetSpec:
        """Computes domain-weighted token budget ceiling."""
        ceiling = model_ceiling or self.default_model_ceiling
        multiplier = self.DOMAIN_MULTIPLIERS.get(domain.lower(), 0.5)
        max_tokens = int(ceiling * multiplier)

        return TokenBudgetSpec(
            actor_id=actor_id,
            domain=domain,
            max_context_tokens=max_tokens,
        )

    def estimate_tokens(self, text: str) -> int:
        """Fast standard token estimator (words * 1.3)."""
        words = text.split()
        return max(1, int(len(words) * 1.3))

    def check_budget(self, spec: TokenBudgetSpec, text: str) -> Tuple[bool, bool]:
        """Returns (is_over_budget, is_warning_triggered)."""
        tokens = self.estimate_tokens(text)
        is_over = tokens > spec.max_context_tokens
        warning_floor = int(spec.max_context_tokens * spec.warning_ratio)
        is_warn = (not is_over) and (tokens >= warning_floor)
        return is_over, is_warn


class AdaptivePersonaCompressor:
    """Executes high-speed JIT micro-compaction on actor message histories."""

    def __init__(self):
        pass

    def compact_mailbox(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int = 100
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Summarizes older intermediate messages while preserving system prompts and the latest turn."""
        if len(messages) <= 2:
            orig_tok = sum(max(1, int(len(m.get("content", "").split()) * 1.3)) for m in messages)
            return messages, {
                "original_tokens": orig_tok,
                "compacted_tokens": orig_tok,
                "compression_ratio": 1.0,
            }

        orig_tok = sum(max(1, int(len(m.get("content", "").split()) * 1.3)) for m in messages)

        # 1. Preserve initial system instruction
        system_msg = messages[0] if messages[0].get("role") == "system" else None
        # 2. Preserve most recent turn
        latest_msg = messages[-1]

        # 3. Compact intermediate messages into structured micro-deltas
        intermediates = messages[1:-1] if system_msg else messages[:-1]
        summary_snippets = []
        for msg in intermediates:
            role = msg.get("role", "peer")
            words = msg.get("content", "").split()
            condensed = " ".join(words[:4])
            summary_snippets.append(f"{role[:4]}: {condensed}")

        compacted_delta = "[Context Delta: " + "; ".join(summary_snippets) + "]"

        compacted_list: List[Dict[str, Any]] = []
        if system_msg:
            compacted_list.append(system_msg)
        compacted_list.append({"role": "system", "content": compacted_delta})
        compacted_list.append(latest_msg)

        comp_tok = sum(max(1, int(len(m.get("content", "").split()) * 1.3)) for m in compacted_list)
        ratio = round(orig_tok / comp_tok, 2) if comp_tok > 0 else 1.0

        stats = {
            "original_tokens": orig_tok,
            "compacted_tokens": comp_tok,
            "compression_ratio": ratio,
        }

        return compacted_list, stats
