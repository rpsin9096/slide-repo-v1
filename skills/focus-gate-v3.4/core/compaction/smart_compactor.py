"""FocusGate v2.9 — Smart-Zone Context Compactor.

Defends LLM context reasoning quality by preserving <150k token limits
and 5-item active working memory ceilings.

Zero external dependencies (100% Python standard library).
"""

import os
import time
from typing import Dict, Any, List, Optional
from core.tokens import estimate_tokens
from core.gates.ledger import Ledger


class SmartZoneCompactor:
    """Preserves LLM context reasoning quality by defending <150k token limit and 5-item working memory cap."""

    DEFAULT_TOKEN_BUDGET = 150000
    MAX_ACTIVE_GATES = 5

    @classmethod
    def estimate_tokens(cls, text_or_path: str) -> int:
        """Fast heuristic: ~4 characters per token."""
        if os.path.isfile(text_or_path):
            try:
                with open(text_or_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return estimate_tokens(content)
            except (OSError, IOError, UnicodeDecodeError):
                return 0
        return estimate_tokens(text_or_path)

    @classmethod
    def needs_compaction(cls, ledger: Any, token_budget: int = DEFAULT_TOKEN_BUDGET, max_active: int = MAX_ACTIVE_GATES) -> bool:
        settled_gates = [g for g in getattr(ledger, "gates", []) if getattr(g, "checked", False)]
        if not settled_gates:
            return False

        current_tokens = cls.estimate_tokens(getattr(ledger, "raw_content", ""))
        if current_tokens >= token_budget:
            return True

        active_count = len(getattr(ledger, "gates", [])) + len(getattr(ledger, "spikes", []))
        if active_count > max_active:
            return True

        return False

    @classmethod
    def compact(cls, ledger_path: str, archive_path: str = ".focusgate/ARCHIVE.md",
                token_budget: int = DEFAULT_TOKEN_BUDGET, max_active: int = MAX_ACTIVE_GATES, **kwargs) -> Dict[str, Any]:
        if "archive_file" in kwargs:
            archive_path = kwargs["archive_file"]
        ledger = Ledger.from_file(ledger_path)
        settled_gates = [g for g in ledger.gates if g.checked]
        settled_spikes = [s for s in ledger.spikes if s.checked]

        if not settled_gates and not settled_spikes:
            return {
                "compacted": False,
                "archived_gates": 0,
                "freed_tokens": 0,
                "reason": "No settled gates or spikes to compact."
            }

        os.makedirs(os.path.dirname(os.path.abspath(archive_path)), exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        archive_lines = [f"\n### Settled Compaction [{timestamp}]\n"]
        archived_ids = []

        for s in settled_spikes:
            archive_lines.append(f"- [x] {s.id}: {s.title} ({s.branch})\n  ARTIFACT: {s.artifact}\n")
            archived_ids.append(s.id)

        for g in settled_gates:
            archive_lines.append(f"- [x] {g.id}: {g.title}\n  CHECK: {g.check_cmd}\n")
            archived_ids.append(g.id)

        with open(archive_path, "a", encoding="utf-8") as af:
            af.writelines(archive_lines)

        # Regenerate ledger without settled items
        original_lines = ledger.raw_content.splitlines()
        new_lines = []
        skipping = False

        for line in original_lines:
            s_line = line.strip()
            if s_line.startswith("- [x]") or s_line.startswith("- [X]"):
                skipping = True
                continue
            elif skipping:
                if s_line.startswith("- [ ]") or s_line.startswith("## ") or s_line.startswith("### "):
                    skipping = False
                    new_lines.append(line)
                elif any(s_line.startswith(p) for p in ["CHECK:", "EXPECT:", "TIMEOUT:", "CWD:", "DEPS:", "AFTER:", "BRANCH:", "QUESTION:", "ARTIFACT:"]):
                    continue
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        new_content = "\n".join(new_lines)
        with open(ledger_path, "w", encoding="utf-8") as lf:
            lf.write(new_content)

        freed_tokens = max(0, estimate_tokens(ledger.raw_content) - estimate_tokens(new_content))

        return {
            "compacted": True,
            "archived_ids": archived_ids,
            "archived_count": len(archived_ids),
            "freed_tokens": freed_tokens,
            "archive_path": archive_path,
            "ledger_path": ledger_path
        }
