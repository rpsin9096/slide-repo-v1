# Facet Contract: triage (v3.3)
Context: Navigation | Mode: Defect & Feature Triage | Eviction: On Gate Settle

```facet-meta
schema: 1
id: triage
summary: Classify incoming items and compile ready-for-agent gate ledgers
priority: 6
mode: WINDOW
applies_when: ["incident", "ticket", "report from", "bug report", "regression from", "enhancement request", "ready-for-agent", "triage"]
socratic:
  grounding: ["active gate contract", "file:line"]
  stems: ["Is this DEFECT or ENHANCEMENT - cite the first divergent behavior."]
  cap: 2
usability:
  seed: "Run the reporter's command once, verbatim."
  criterion: "Item is DEFECT or ENHANCEMENT with a CHECK/EXPECT pair compiled."
```

## Invariant Directives
1. REPRODUCE_FIRST: Run the reporter's command verbatim on this checkout before classifying or writing any fix gate.
2. CATEGORIZATION: Label each item DEFECT (a regression or error) or ENHANCEMENT (new capability) and cite the first divergent behavior.
3. EARLY_EXIT: If the reproduction passes on the first run, record that passing CHECK as evidence and stop; do not route to review.
4. COMPILE_LEDGER: Write each ready item into `.focusgate/GATES.md` with an explicit CHECK and EXPECT.

## Playbook
### Phases
1. Reproduce | DO: Run the reporter's exact command once. | EXIT: exit code and first output line recorded in the ticket.
2. Classify | DO: Compare observed and expected behavior. | EXIT: label `DEFECT` or `ENHANCEMENT` plus the first divergent `file:line` or output line.
3. Compile | DO: Turn the expected behavior into CHECK and EXPECT. | EXIT: `--lint` prints `0 error(s)` for the new gate.
4. Baseline and route | DO: Run `--baseline`, then route defects to diagnosing-bugs and enhancements to wayfinder. | EXIT: gate status `RED` and one named next facet.
### Lazy Tells
- TRIAGE_BY_TITLE | SAYS: "the title says crash, so it is a bug" | DETECT: no reproduction output attached | INSTEAD: run the command and attach exit code and output.
- UNFALSIFIABLE_TICKET | SAYS: "the fix is done when it feels better" | DETECT: compiled gate has no CHECK | INSTEAD: write the observable behavior as CHECK and EXPECT.
### Gate Templates
```gate
- [ ] reported-behavior: the behavior the reporter expects holds
  CHECK: python3 -m unittest {module}.{test}
  EXPECT: \nOK
```
### Handoff
- NEXT: diagnosing-bugs | WHEN: the item is a DEFECT and its reproduction fails.
- NEXT: wayfinder | WHEN: the item is an ENHANCEMENT that needs sequencing.
