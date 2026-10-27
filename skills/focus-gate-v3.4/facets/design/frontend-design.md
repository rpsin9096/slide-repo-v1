# Facet Contract: frontend-design (v3.3)
Context: Design | Mode: Bespoke Visual Identity & Anti-Cliché Orchestration | Eviction: On Gate Settle

```facet-meta
schema: 1
id: frontend-design
summary: Bespoke visual identity with anti-cliche two-pass workflow
priority: 8
mode: WINDOW
applies_when: ["bespoke", "landing page", "frontend design", "aesthetic", "visual identity", "cliche", "anti-cliche", "typography", "distinctive"]
never_when: ["audit"]
oracle: ["--audit-design-cliche"]
socratic:
  grounding: ["CONTEXT.md", "active gate contract"]
  stems: ["Who is the audience and the primary job - one line, before any color is chosen.", "Which of the 5 AI tells is most likely here, and what token blocks it?"]
  cap: 2
usability:
  seed: "Draft the 4-6 named-hex token plan on one page before any CSS."
  criterion: "--audit-design-cliche clean on the diff."
```

## Invariant Directives
1. SUBJECT_GROUNDING: State the audience and the primary job in one line before choosing any color or type.
2. ANTI_CLICHE_GUARD: Reject AI template tells: cream with terracotta, black with acid green, SaaS card kits, tracked all-caps eyebrows, middle-dot strings, single-word headline accents.
3. TWO_PASS_WORKFLOW: First write a plan of 4 to 6 named hex values, type roles and an ASCII wireframe; audit it against generic defaults; only then write code.
4. TYPOGRAPHIC_DISCIPLINE: Use at most 2 font families, keep lines under 80 characters and follow one stated type scale.
5. RESTRAINT_DOCTRINE: Spend visual boldness in exactly one place; give every control a visible keyboard focus and WCAG 2.1 AA contrast.
6. ACTIVE_VOICE_COPY: Write interface copy with active verbs ("Save changes", not "Submit") and direction in empty and error states.

## Playbook
### Phases
1. Ground the subject | DO: Write audience, job and one concrete object from the subject's world. | EXIT: 3 lines in `.focusgate/DESIGN-SPEC.md`.
2. Plan tokens | DO: Name 4 to 6 hex values, 2 type roles and a wireframe, then list which AI tell each choice avoids. | EXIT: plan lists every hex with a name and a rejected default.
3. Prototype | DO: Build one throwaway HTML page of the hero and one component. | EXIT: page opens with no external dependency and `--audit-design-cliche` prints `CLICHE_AUDIT_PASS`.
4. Implement | DO: Port the plan into tokens and components. | EXIT: `--audit-tokens` prints `AUDIT_TOKENS_PASS`.
### Lazy Tells
- DEFAULT_PALETTE | SAYS: "warm neutral with a terracotta accent is tasteful" | DETECT: `--audit-design-cliche` flags the palette | INSTEAD: derive color from the subject's own materials.
- STYLE_BEFORE_SUBJECT | SAYS: "starting with the CSS" | DETECT: no `DESIGN-SPEC.md` subject lines before code | INSTEAD: write audience and job first.
- EVERY_THING_BOLD | SAYS: "make every section pop" | DETECT: more than one accent treatment in the plan | INSTEAD: choose one place for boldness.
### Gate Templates
```gate
- [ ] no-design-tells: the page carries no template-look markers
  CHECK: python3 scripts/focus-gate.py --audit-design-cliche {path}
  EXPECT: CLICHE_AUDIT_PASS
```
### Handoff
- NEXT: design-tokens | WHEN: the token plan passes the cliche audit.
- NEXT: prototype | WHEN: layout or typography is still a guess.
