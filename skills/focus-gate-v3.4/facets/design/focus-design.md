# Facet Contract: focus-design (v3.3)
Context: Design | Mode: Visual Delivery Orchestration | Eviction: On Gate Settle

```facet-meta
schema: 1
id: focus-design
summary: Audit and repair visual delivery via pure-python visual oracles
priority: 7
mode: WINDOW
applies_when: ["contrast", "wcag", "a11y", "accessibility", "color audit", "hardcoded", "design audit", "token audit", "safe zone", "visual polish", "touch target"]
never_when: ["bespoke", "landing page"]
oracle: ["--audit-contrast", "--audit-tokens", "--audit-safe-zone"]
socratic:
  grounding: ["file:line", "active gate contract"]
  stems: ["Which oracle CHECK proves the visual claim for {file}?"]
  cap: 2
usability:
  seed: "Run --audit-contrast on the target stylesheet."
  criterion: "All text pairs pass 4.5:1 and styles resolve to var(--*)."
```

## Invariant Directives
1. ORACLE_VERIFICATION: Prove each visual claim with a pure-Python oracle (`--audit-contrast`, `--audit-tokens`, `--audit-safe-zone`) and keep its verdict line.
2. ACTION_FIRST: Start the turn with the executable audit command or the asset path, not a description of intent.
3. TOKEN_DISCIPLINE: Styles resolve to `var(--*)` declared in `design-tokens.css`; raw values fail the audit.
4. DISPOSABLE_SPIKES: Validate layout and responsive guesses in a throwaway HTML spike before committing code.

## Playbook
### Phases
1. Audit | DO: Run `--audit-tokens` and `--audit-contrast` on the target. | EXIT: list of failing pairs with ratios and a violation count.
2. Repair | DO: Pick replacement tokens or colors that reach 4.5:1 for body text. | EXIT: each failing pair has a replacement with a computed ratio of 4.5 or more.
3. Re-audit | DO: Re-run every oracle on the changed files. | EXIT: `CONTRAST_PASS_AA` for each pair and `AUDIT_TOKENS_PASS`.
4. Touch targets | DO: Check interactive elements for a 44 px minimum hit area. | EXIT: smallest target in the file is 44 px or more.
### Lazy Tells
- LOOKS_ACCESSIBLE | SAYS: "the contrast looks fine" | DETECT: no `CONTRAST_PASS_AA` line recorded | INSTEAD: run `--audit-contrast <fg> <bg>`.
- FIX_ONE_PAIR | SAYS: "fixed the button text, done" | DETECT: audit not re-run on the whole file | INSTEAD: re-audit every text pair in the touched files.
### Gate Templates
```gate
- [ ] body-contrast: body text meets WCAG AA
  CHECK: python3 scripts/focus-gate.py --audit-contrast {fg} {bg}
  EXPECT: CONTRAST_PASS_AA
```
### Handoff
- NEXT: unlazy | WHEN: audits list concrete failures to implement.
- NEXT: code-review | WHEN: all oracles pass on the touched files.
