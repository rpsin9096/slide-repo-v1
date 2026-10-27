"""Fragment, brief, shape and beat helpers for the writing facets (moved out of the CLI script in v3.4)."""
import os

from core.gates import TracerGate
from typing import Optional


class WritingSuite:
    """Provides native execution helpers for writing-fragments, writing-shape, writing-for-agents, and writing-beats."""

    @staticmethod
    def append_fragment(text: str, target_file: str = ".focusgate/FRAGMENTS.md", working_title: str = "Raw Fragments") -> str:
        os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)
        if not os.path.exists(target_file):
            content = f"# {working_title}\n\n{text.strip()}\n\n---\n"
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(target_file, "r", encoding="utf-8") as f:
                existing = f.read()
            clean_existing = existing.rstrip()
            addition = f"\n\n{text.strip()}\n\n---\n"
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(clean_existing + addition)
        return target_file

    @staticmethod
    def compile_agent_brief(gate: TracerGate, ledger: 'Ledger', out_path: Optional[str] = None) -> str:
        cmd_str = gate.check_cmd or "pytest"
        exp_str = gate.expect_pattern or "PASS"
        content = f"# Agent Brief: {gate.title}\n\n"
        content += f"**Target Gate:** `{gate.id}`\n"
        content += f"**Ledger:** `{ledger.filepath}`\n"
        content += f"**Est Time:** {ledger.state_meta.get('est_minutes', 15)} min\n\n"
        content += f"## 1. Objective & Scope\nImplement behavior for `{gate.id}`: {gate.title}.\n\n"
        content += f"## 2. Context Pointers (Authoritative Seams)\n- Active Ledger: `{ledger.filepath}`\n"
        if ledger.seams:
            for s in ledger.seams:
                content += f"- Public Seam: **{s['name']}** — {s['desc']}\n"
        if ledger.glossary:
            content += "\n## 3. Domain Micro-Glossary Anchors\n"
            for g in ledger.glossary:
                content += f"- **{g['term']}**: {g['def']}\n"
        content += f"\n## 4. Checkable Completion Criteria\n- [ ] `{gate.id}`:\n"
        content += f"  - Command: `{cmd_str}`\n"
        content += f"  - Expect: `{exp_str}`\n"
        content += f"  - Timeout: {gate.timeout}s\n"
        if out_path:
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
        return content
