# Facet Contract: wayfinder (v3.3)
Context: Navigation | Mode: Roadmap & Frontier Mapping | Eviction: On Gate Settle

```facet-meta
schema: 1
id: wayfinder
summary: Chart milestone frontiers and claim exactly one unblocked ticket
priority: 5
mode: WINDOW
applies_when: ["roadmap", "milestone", "epic", "blocker", "unblocked", "next ticket", "frontier", "what is left", "plan the work", "strategy", "direction", "explore", "idea"]
socratic:
  grounding: ["active gate contract", "file:line"]
  stems: ["Which single gate unblocks the most frontier edges for {file}?"]
  cap: 2
usability:
  seed: "List unblocked gates, pick exactly one, claim it."
  criterion: "Exactly one claimed ticket with a settled frontier hash."
```

## Invariant Directives
1. SINGLE_CLAIM: Claim and resolve exactly one ticket at a time through the single active gate slot.
2. FOG_OF_WAR: Keep unblocked frontier gates visibly apart from unresolved exploratory items, and never plan the fog in detail.
3. CHARTING_PURITY: Chart milestone dependencies only; hand code execution to unlazy.
4. MILESTONE_HASH: Record a state hash at every frontier transition so the run can be replayed and verified.

## Playbook
### Phases
1. Chart | DO: List gates and their dependencies as a DAG. | EXIT: every gate has a `depends_on` list, possibly empty.
2. Find the frontier | DO: Run `--frontier` to list gates with no open dependency. | EXIT: output lists N ready gates with N at least 1.
3. Claim one | DO: Pick the gate that unblocks the most edges and run `--queue-next`. | EXIT: `ACTIVE GATE` names exactly 1 gate.
4. Record the transition | DO: After settling, run `--evidence` and note the chain state. | EXIT: line `chain: OK` and the next frontier size.
### Lazy Tells
- PARALLEL_CLAIM | SAYS: "I will start three tickets at once" | DETECT: `--queue-next` shows more than 1 active gate | INSTEAD: claim one and buffer the rest.
- PLAN_THE_FOG | SAYS: "let me detail every later milestone now" | DETECT: gates with unresolved dependencies carry CHECK lines | INSTEAD: detail only the frontier.
### Gate Templates
```gate
- [ ] frontier-claimed: exactly one gate is active
  CHECK: python3 scripts/focus-gate.py --queue-next {ledger}
  EXPECT: ACTIVE GATE
```
### Handoff
- NEXT: unlazy | WHEN: one ticket is claimed and ready to implement.
- NEXT: grilling | WHEN: the frontier holds a decision with competing options.
