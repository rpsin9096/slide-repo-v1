"""FocusGate v2.8 Part 3 — Richness Sufficiency Oracle.

Guards the "Reference-Is-Never-Enough" invariant (v2.8 spec section 4.2):
a WINDOW-facet sub-agent brief MUST NOT present an upstream dependency as an
unresolvable bare @pointer or as a lost-summary placeholder. Concrete
defects flagged:

  * BARE_POINTER  - upstream line resolves to a bare @hex (Part 2 elision bug).
  * LOST_SUMMARY  - WINDOW-facet dep carries the graceful "(no summary
                    available)" placeholder, i.e. the resolver missed AND the
                    receipt carried no key_findings -> content starved.

EPHEMERAL facets are sterile by design and only the BARE_POINTER check applies
(a bare @hash is universally unresolvable regardless of facet mode).
"""
import re
from typing import Any, Dict, List, Tuple

from ..context_policy import mode_for_facet, FacetContextMode


_LINE_RE = re.compile(r"^-\s*(\S+)\s*\[([^\]]*)\]:\s*(.*)$")
_BARE_POINTER_RE = re.compile(r"@?[0-9a-fA-F]{4,}")
_LOST_SUMMARY_RE = re.compile(r"^\(upstream .*no summary available\)$")
_FACET_RE = re.compile(r"^facet:\s*(.+)$", re.MULTILINE)
_HEADER = "## Upstream Context"
_FACET_HEADER = "## Facet Directive:"


class RichnessSufficiencyOracle:
    """Static auditor for generated AGENT_PROMPT.md sufficiency (v2.8 Part 3)."""

    @staticmethod
    def _upstream_section(text: str) -> str:
        idx = text.find(_HEADER)
        if idx == -1:
            return ""
        rest = text[idx + len(_HEADER):]
        nxt = rest.find("\n## ")
        return rest if nxt == -1 else rest[:nxt]

    @classmethod
    def _iter_dependency_lines(cls, upstream: str):
        for raw in upstream.splitlines():
            m = _LINE_RE.match(raw.strip())
            if m:
                yield m.group(1), m.group(2), m.group(3).strip()

    @staticmethod
    def _facet_section(text: str) -> str:
        idx = text.find(_FACET_HEADER)
        if idx == -1:
            return ""
        rest = text[idx:]
        nxt = rest.find("\n## ", len(_FACET_HEADER))
        return rest if nxt == -1 else rest[:nxt]

    @classmethod
    def audit_prompt(cls, text: str) -> Dict[str, Any]:
        m = _FACET_RE.search(text or "")
        facet = (m.group(1).strip() if m else "engineering")
        is_window = mode_for_facet(facet) == FacetContextMode.WINDOW

        findings: List[Dict[str, str]] = []
        for gate, _status, value in cls._iter_dependency_lines(cls._upstream_section(text or "")):
            if _BARE_POINTER_RE.fullmatch(value):
                findings.append({"gate": gate, "kind": "BARE_POINTER", "detail": value})
                continue
            body = value.split(" (ref ", 1)[0]
            if is_window and _LOST_SUMMARY_RE.match(body):
                findings.append({"gate": gate, "kind": "LOST_SUMMARY", "detail": body})

        facet_sec = cls._facet_section(text or "")
        if facet_sec:
            from ..context_policy import brief_budget
            from ..tokens import estimate_tokens
            total = estimate_tokens(cls._upstream_section(text or "")) + estimate_tokens(facet_sec)
            if total > brief_budget(facet):
                findings.append({"gate": "facet", "kind": "FACET_SECTION_OVERFLOW",
                                 "detail": f"dynamic context {total} > budget {brief_budget(facet)}"})

        clean = not findings
        return {
            "clean": clean,
            "category": "context",
            "findings": findings,
            "summary": f"{len(findings)} context sufficiency finding(s) [facet={facet}]",
        }
