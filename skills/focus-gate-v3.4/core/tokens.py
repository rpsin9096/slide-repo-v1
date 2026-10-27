"""FocusGate v2.8 — Canonical token estimation utility.

Single source of truth for token counting heuristics.
All modules must import from here instead of re-implementing.
"""

def estimate_tokens(text: str) -> int:
    """Estimate token count using character-length heuristic.
    
    Uses len(text) // 4 as a fast approximation.
    Centralized here to eliminate drift across modules.
    """
    return max(1, len(text) // 4) if text else 0
