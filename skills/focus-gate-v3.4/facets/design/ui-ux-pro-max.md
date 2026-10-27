# Facet Contract: ui-ux-pro-max (v3.3)
Context: Design | Mode: UI State & Token Discipline | Eviction: On Gate Settle

```facet-meta
schema: 1
id: ui-ux-pro-max
summary: Interactive-state completeness and token-linked color discipline
priority: 5
mode: WINDOW
applies_when: ["ui states", "component states", "color scheme", "palette", "icon set", "interaction states", "typography scale"]
oracle: ["--audit-contrast", "--audit-tokens"]
socratic:
  grounding: ["file:line", "CONTEXT.md"]
  stems: ["Which of the 5 states is undeclared for {file}?"]
  cap: 1
usability:
  seed: "Tab through one component and name each visible focus change."
  criterion: "Every interactive component declares all 5 states in review."
```

## Invariant Directives
1. STATE_MATRIX: Every interactive component declares default, hover, focus-visible, active and disabled states explicitly.
2. TOKEN_LINK: Every color names a semantic token from the design-tokens facet; bare hex literals fail review.
3. WCAG_GATE: Text pairs reach 4.5:1 under `focus-gate.py --audit-contrast` before the gate settles.
4. ICON_CONSISTENCY: Use one icon set at one stroke weight across the component library.

## Playbook
### Phases
1. List components | DO: Enumerate interactive components in the touched files. | EXIT: component list with count N.
2. Fill the matrix | DO: For each component write the 5 states in CSS. | EXIT: `grep -c ":focus-visible"` is at least N.
3. Link colors | DO: Replace hex with semantic tokens. | EXIT: `--audit-tokens` prints `AUDIT_TOKENS_PASS`.
4. Prove contrast | DO: Run `--audit-contrast` for each text and surface pair. | EXIT: every pair prints `CONTRAST_PASS_AA`.
### Lazy Tells
- HOVER_ONLY | SAYS: "hover and default are enough" | DETECT: component CSS lacks `:focus-visible` or `:disabled` | INSTEAD: declare all 5 states.
- MOUSE_ONLY_TEST | SAYS: "clicked through it, works" | DETECT: no keyboard Tab pass recorded | INSTEAD: Tab through the component and name each focus change.
### Gate Templates
```gate
- [ ] focus-states-declared: components declare focus-visible styling
  CHECK: grep -c ":focus-visible" {css}
  EXPECT: ^[1-9]
```
### Handoff
- NEXT: focus-design | WHEN: states are declared and visual oracles must run.
- NEXT: code-review | WHEN: the matrix is complete and contrast passes.
