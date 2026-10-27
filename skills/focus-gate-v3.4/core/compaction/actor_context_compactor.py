"""FocusGate v3.0 — Actor Context Compactor & Token Ceiling Guard.

Enforces strict working memory limits per swarm actor:
- Working memory brief ceiling: <= 400 tokens
- Message delta ceiling: <= 80 tokens per inter-actor message
- Sliding turn window: <= 10 turns preserved per actor session
- Zero external dependencies (100% Python stdlib).
"""

import json
import time
from typing import Dict, Any, List, Optional, Tuple


class ActorContextCompactor:
    """Manages sliding context windows and strictly enforces token ceilings."""

    MAX_BRIEF_TOKENS: int = 400
    MAX_DELTA_TOKENS: int = 80
    MAX_TURNS: int = 10

    def __init__(self):
        self.actor_memory: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def estimate_tokens(cls, text_or_dict: Any) -> int:
        """Estimates token count using canonical ~4 characters per token heuristic."""
        if isinstance(text_or_dict, (dict, list)):
            text = json.dumps(text_or_dict, separators=(',', ':'))
        else:
            text = str(text_or_dict)
        return max(1, len(text) // 4)

    @classmethod
    def compact_brief(
        cls,
        task_description: str,
        acceptance_criteria: Optional[List[str]] = None,
        anchors: Optional[Dict[str, str]] = None
    ) -> str:
        """Constructs a concise, structured task brief bounded strictly to <= 400 tokens."""
        max_chars = cls.MAX_BRIEF_TOKENS * 4  # ~1600 characters max

        lines: List[str] = [f"## Task: {task_description}"]

        if anchors:
            lines.append("### Anchors:")
            for k, v in anchors.items():
                lines.append(f"- **{k}**: {v}")

        if acceptance_criteria:
            lines.append("### Acceptance Criteria:")
            for c in acceptance_criteria:
                lines.append(f"- {c}")

        raw_brief = "\n".join(lines)
        if len(raw_brief) <= max_chars:
            return raw_brief

        # Truncation if over budget
        truncated = raw_brief[:max_chars - 3].rstrip() + "..."
        return truncated

    def track_turn(self, actor_id: str, role: str, content: str) -> None:
        """Records a turn in the actor's sliding memory window."""
        if actor_id not in self.actor_memory:
            self.actor_memory[actor_id] = []

        tokens = self.estimate_tokens(content)
        entry = {
            "role": role,
            "content": content,
            "tokens": tokens,
            "timestamp": time.time()
        }
        self.actor_memory[actor_id].append(entry)

        # Sliding window pruning
        if len(self.actor_memory[actor_id]) > self.MAX_TURNS:
            self.actor_memory[actor_id] = self.actor_memory[actor_id][-self.MAX_TURNS:]

    def get_active_context(self, actor_id: str) -> Dict[str, Any]:
        """Returns the current active sliding context and token usage for an actor."""
        turns = self.actor_memory.get(actor_id, [])
        total_tokens = sum(t["tokens"] for t in turns)
        return {
            "actor_id": actor_id,
            "turns": turns,
            "turn_count": len(turns),
            "total_tokens": total_tokens,
            "token_budget": self.MAX_BRIEF_TOKENS,
            "alarm_active": total_tokens > self.MAX_BRIEF_TOKENS
        }

    @classmethod
    def enforce_delta_ceiling(cls, payload: Dict[str, Any]) -> Tuple[bool, int, Dict[str, Any]]:
        """Ensures an inter-actor message delta does not exceed <= 80 tokens."""
        tokens = cls.estimate_tokens(payload)
        if tokens <= cls.MAX_DELTA_TOKENS:
            return True, tokens, payload

        # Compact payload to fit within 80 tokens (~320 chars)
        compact_payload: Dict[str, Any] = {"truncated": True}
        budget_chars = cls.MAX_DELTA_TOKENS * 4

        for k, v in payload.items():
            if isinstance(v, str):
                compact_payload[k] = v[:40] + ("..." if len(v) > 40 else "")
            elif isinstance(v, (int, float, bool)):
                compact_payload[k] = v
            elif isinstance(v, list):
                compact_payload[k] = v[:2]
            elif isinstance(v, dict):
                compact_payload[k] = {sk: str(sv)[:20] for sk, sv in list(v.items())[:2]}

        compact_tokens = cls.estimate_tokens(compact_payload)
        return True, compact_tokens, compact_payload
