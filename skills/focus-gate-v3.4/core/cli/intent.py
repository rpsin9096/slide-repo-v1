"""Intent reframing and autonomous routing (moved out of the CLI script in v3.4)."""
import re

from typing import Any
from typing import Dict


class TechnicalEnglishReframer:
    STE_REPLACEMENTS = [
        (r'\butilize\b', 'use'),
        (r'\bleverage\b', 'use'),
        (r'\bfacilitate\b', 'help'),
        (r'\bcommence\b', 'start'),
        (r'\bterminate\b', 'stop'),
        (r'\boptimal\b', 'best'),
        (r'\bparamount\b', 'key'),
        (r'\bin order to\b', 'to'),
    ]

    @classmethod
    def re_pitch(cls, text: str) -> str:
        reframed = text
        for pattern, repl in cls.STE_REPLACEMENTS:
            reframed = re.sub(pattern, repl, reframed, flags=re.IGNORECASE)
        return reframed


class AutonomousRouter:
    @classmethod
    def route_query(cls, query: str) -> Dict[str, Any]:
        q = query.lower()
        if any(k in q for k in ["bug", "error", "fail", "slow", "broken", "diagnos"]):
            return {"pipeline": "diagnosing-bugs", "confidence": 0.95, "next_command": "focus-gate.py --status"}
        elif any(k in q for k in ["review", "pr", "diff", "standards", "smell"]):
            return {"pipeline": "code-review", "confidence": 0.92, "next_command": "focus-gate.py --run"}
        elif any(k in q for k in ["spec", "ticket", "user story", "decompose"]):
            return {"pipeline": "spec-compiler", "confidence": 0.94, "next_command": "focus-gate.py --compile-spec"}
        elif any(k in q for k in ["grounding", "jargon", "writing", "terms"]):
            return {"pipeline": "concept-grounding", "confidence": 0.90, "next_command": "focus-gate.py --lint-grounding"}
        elif any(k in q for k in ["swarm", "worktree", "parallel", "frontier"]):
            return {"pipeline": "swarm-orchestrator", "confidence": 0.96, "next_command": "focus-gate.py --frontier"}
        elif any(k in q for k in ["replay", "rollback", "events", "audit"]):
            return {"pipeline": "event-sourcing", "confidence": 0.96, "next_command": "focus-gate.py --replay 1"}
        elif any(k in q for k in ["compact", "memory", "tokens", "archive"]):
            return {"pipeline": "smart-zone-compactor", "confidence": 0.94, "next_command": "focus-gate.py --compact"}
        return {"pipeline": "wayfinder", "confidence": 0.70, "next_command": "focus-gate.py --status"}
