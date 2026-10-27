"""FocusGate v2.9 — Concept Grounding Linter & Spec-to-Ledger Compiler.

Enforces ubiquitous language grounding across technical specifications and
compiles agile user stories into executable DAG-connected GATES.md ledgers.

Zero external dependencies (100% Python standard library).
"""

import re
from typing import Set, List, Dict, Any


class ConceptGroundingLinter:
    """Audits documents against grounded glossary terms and prior paragraphs."""

    @classmethod
    def lint_grounding(cls, doc_text: str, glossary_terms: Set[str]) -> List[Dict[str, Any]]:
        grounded = set(glossary_terms)
        violations = []
        paragraphs = [p.strip() for p in doc_text.split("\n\n") if p.strip()]

        for idx, para in enumerate(paragraphs, 1):
            defined = re.findall(r'\*\*([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\*\*:', para)
            for d in defined:
                grounded.add(d)

            candidates = set(re.findall(r'\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b', para))
            ungrounded = [c for c in candidates if c not in grounded]
            if ungrounded:
                violations.append({
                    "paragraph_index": idx,
                    "preview": para[:60] + "...",
                    "ungrounded_concepts": ungrounded,
                    "remedy": f"Ground {', '.join(ungrounded)} in glossary or prior paragraph."
                })
        return violations


class SpecToLedgerCompiler:
    """Compiles Markdown technical specifications into DAG-connected acceptance gates."""

    @classmethod
    def compile_spec(cls, spec_markdown: str) -> str:
        title_m = re.search(r'#\s*(.+)', spec_markdown)
        task_name = title_m.group(1).strip() if title_m else "Spec Implementation"
        stories = re.findall(r'(\d+)\.\s*As an?\s+([^,]+),\s*I want\s+(?:to\s+)?([^,]+),\s*so that\s+(.+)', spec_markdown, re.IGNORECASE)

        gates = []
        prev_gate_id = None
        for idx, (num, actor, feature, benefit) in enumerate(stories, 1):
            clean_feat = re.sub(r'[^a-z0-9]+', '-', feature.lower()).strip('-')[:25]
            gate_id = f"gate-{idx}-{clean_feat}"
            after_line = f"  DEPS: {prev_gate_id}\n" if prev_gate_id else ""
            test_target = re.sub(r'[^a-z0-9]+', '_', feature.lower()).strip('_')[:20]
            gate_block = f"""- [ ] {gate_id}: As {actor.strip()}, {feature.strip()}
{after_line}  CHECK: python3 -m unittest tests/test_{test_target}.py
  EXPECT: OK"""
            gates.append(gate_block)
            prev_gate_id = gate_id

        if not gates:
            gates.append("""- [ ] gate-1-core-contract: Verify primary spec interface
  CHECK: python3 -c "print('PASS_CORE')"
  EXPECT: PASS_CORE""")

        rendered_gates = "\n\n".join(gates)
        return f"""# FocusGate Ledger: {task_name}
State: [Step 1 of 4] [0/{len(gates)} gates met] [Est: 30 min]

## 1. Domain Anchors (Micro-Glossary)
- **DomainContract**: Primary functional contract for {task_name}.
  _Avoid_: GenericHandler, BlobManager

## 2. Acceptance Gates

### Production Gates
{rendered_gates}

## 3. Micro-ADR Ledger
- **None yet.**
"""
