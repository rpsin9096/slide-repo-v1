"""BriefComposer: the facet-, rigor- and evidence-aware sections of a sub-agent brief.

`AgentBrief.to_prompt` owns gate, task, upstream and stage sections. Everything
that depends on *which facet* the gate runs under lives here, so the prompt is
composed from facet data instead of text pasted into one long method:

  facet_section   rules with definitions, squeezed to the facet's token ceiling
  rigor_block     the 4-pass loop, worded for the facet's context
  fallback_block  keyword fallback for facets that are not registered
  evidence_block  the v3.2 loop: --baseline, unchanged CHECK, --check --strict
"""
from typing import List, Optional

from core.facets.catalog import FacetCatalog, UnknownFacet

_RIGOR_HEAD = "\n## Mandatory Implementation Rigor Directive (Dual-Phase /unlazy)"

# Pass names are a fixed contract (evals/evals.json eval-03); the wording of each
# pass is tailored so a writing brief is not told to avoid `NotImplementedError`.
_RIGOR = {
    "engineering": [
        "Execute work strictly across the 4-Pass Implementation Loop:",
        "  1. Pass 1 (Complete Deliverable): Full real implementation. Zero placeholders, zero TODO/FIXME, zero empty pass, zero NotImplementedError, zero dummy returns.",
        "  2. Pass 2 (Domain Elevation): Replace naive patterns with robust domain models, strict types, and explicit error handling.",
        "  3. Pass 3 (Boundary Defense): Hunt edge cases, timeouts, malformed inputs, and concurrency collisions.",
        "  4. Pass 4 (Low-Cost Polish): Clean diffs, zero leftover debug statements, verified formatted code.",
    ],
    "design": [
        "Execute work strictly across the 4-Pass Implementation Loop:",
        "  1. Pass 1 (Complete Deliverable): Real markup, styles and copy. Zero lorem ipsum, zero placeholder images, zero TODO.",
        "  2. Pass 2 (Domain Elevation): Resolve every color and size through tokens; declare default, hover, focus-visible, active and disabled states.",
        "  3. Pass 3 (Boundary Defense): Check narrow and wide viewports, empty and error states, long strings, and keyboard-only use.",
        "  4. Pass 4 (Low-Cost Polish): Remove unused rules and debug outlines; run the audit oracles last.",
    ],
    "writing": [
        "Execute work strictly across the 4-Pass Implementation Loop:",
        "  1. Pass 1 (Complete Deliverable): Finish the whole section or brief. Zero TODO, zero bracketed placeholders, zero 'to be written'.",
        "  2. Pass 2 (Domain Elevation): Tie every paragraph to a named entity, metric, symbol or command.",
        "  3. Pass 3 (Boundary Defense): Check each claim against its source and delete numbers you cannot trace.",
        "  4. Pass 4 (Low-Cost Polish): Cut filler, throat-clearing and closing summaries; run the prose oracle last.",
    ],
    "reasoning": [
        "Execute work strictly across the 4-Pass Implementation Loop:",
        "  1. Pass 1 (Complete Deliverable): Produce the concrete artifact (ledger entry, ticket, decision or reply), not a description of it.",
        "  2. Pass 2 (Domain Elevation): Ground every statement in a file:line, a defined term or a number.",
        "  3. Pass 3 (Boundary Defense): Test the conclusion against the strongest counter-case before committing it.",
        "  4. Pass 4 (Low-Cost Polish): Cut to the action; fold detail the reader does not need now.",
    ],
}
_CONTEXT_PROFILE = {"engineering": "engineering", "design": "design", "writing": "writing",
                    "cognitive": "reasoning", "navigation": "reasoning"}

_WRITING_FALLBACK = [
    "\n## Bespoke Writing Directive (Anti-AI Cliché & Restraint)",
    "- SUBJECT_GROUNDING: Ground every paragraph in concrete domain entities or symbols.",
    "- ANTI_PROSE_CLICHE: Eliminate conversational throat-clearing, 'delve', 'testament', 'tapestry', and sycophantic praise.",
    "- RESTRAINT_DOCTRINE: Zero conversational padding; adhere strictly to specified density.",
]


def facet_context(facet: str) -> Optional[str]:
    """Context of a registered facet, else None."""
    try:
        return FacetCatalog.default().get(facet).contract.context
    except UnknownFacet:
        return None


def facet_section(facet: str, budget_tokens: int) -> str:
    try:
        return FacetCatalog.default().render(facet, budget_tokens)
    except UnknownFacet:
        return ""


def rigor_block(facet: str) -> List[str]:
    ctx = facet_context(facet)
    profile = _CONTEXT_PROFILE.get(ctx or "", "engineering")
    return [_RIGOR_HEAD] + _RIGOR[profile]


def fallback_block(facet: str, has_section: bool) -> List[str]:
    """Keyword fallback, used only for facets the catalog does not know."""
    if has_section or facet_context(facet) is not None:
        return []
    name = (facet or "").lower()
    if any(w in name for w in ("writing", "agent", "shape", "beats", "fragment")):
        return list(_WRITING_FALLBACK)
    return []


def evidence_block(gate_id: str, acceptance_criteria: List[str]) -> List[str]:
    """The v3.2 loop, only when the gate has an executable CHECK to prove."""
    if not any(str(c).lstrip().startswith("CHECK:") for c in acceptance_criteria):
        return []
    return [
        "\n## Evidence Protocol",
        "1. Before editing, run `python3 scripts/focus-gate.py --baseline`; this gate must print RED.",
        "2. Leave CHECK and EXPECT unchanged. Fix the code; an edited CHECK voids the red.",
        f"3. Finish with `python3 scripts/focus-gate.py --check {gate_id} --strict` and paste its output into the receipt.",
    ]
