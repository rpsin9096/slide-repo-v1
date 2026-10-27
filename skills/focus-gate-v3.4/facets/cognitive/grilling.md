# Facet Contract: grilling (v3.3)
Context: Cognitive | Mode: Bespoke Socratic Stress-Testing & Anti-Consulting-Cliché | Eviction: On Gate Settle

```facet-meta
schema: 1
id: grilling
summary: Socratic stress-testing of gray-area decisions with grounded questions
priority: 7
mode: EPHEMERAL
applies_when: ["grill me", "stress test my plan", "poke holes", "gray area", "socratic", "compare options", "which should i choose", "challenge this decision"]
socratic:
  grounding: ["CONTEXT.md", "file:line", "active gate contract"]
  stems: ["Which falsifiable sentence commits the choice for {gate_id} - cite {file}."]
  cap: 5
usability:
  seed: "Write the decision as one falsifiable sentence in GATES.md."
  criterion: "Each settled gray area has a Micro-ADR entry in GATES.md."
```

## Invariant Directives
1. FRONTIER_ROUNDS: Ask every unblocked question in one numbered round, then wait; never trickle questions one at a time.
2. MICRO_STATE_CONCRETENESS: Every question cites an exact file:line, state-machine branch or numeric token or latency budget; generic consulting questions are banned.
3. ATTACHED_RECOMMENDATION: Give each question a recommended answer with a one-line trade-off, so the person can accept in one word.
4. DOMAIN_GROUNDING: Use only terms defined in `CONTEXT.md`; define a missing term before asking about it.
5. MICRO_ADR: Commit each settled decision as one falsifiable sentence in the Micro-ADR Ledger the moment it is made.

## Playbook
### Phases
1. Ground | DO: Read `CONTEXT.md` and the active gate, and list the terms the decision depends on. | EXIT: each term maps to a definition line or is flagged `UNDEFINED`.
2. Build the frontier | DO: List every decision that blocks the gate and drop those already answered by the code. | EXIT: numbered questions, each with a `file:line` or a number.
3. Recommend | DO: Attach a recommended answer and one-line cost to each question. | EXIT: count of questions without a recommendation is 0.
4. Commit | DO: Write each answer as a falsifiable sentence in the Micro-ADR Ledger. | EXIT: ADR count in GATES.md rose by the number of answers.
### Lazy Tells
- CONSULTING_QUESTION | SAYS: "have you considered scalability and edge cases" | DETECT: a question holds no `file:line`, branch or number | INSTEAD: name the exact line and the exact load.
- QUESTION_DRIP | SAYS: "one question first, then I will ask more" | DETECT: round holds fewer questions than the frontier | INSTEAD: ask the whole frontier in one round.
### Gate Templates
```gate
- [ ] decision-recorded: the settled gray area is a Micro-ADR in the ledger
  CHECK: grep -c "ADR-" {ledger}
  EXPECT: ^[1-9]
```
### Handoff
- NEXT: prototype | WHEN: an answer depends on behavior nobody can predict from the code.
- NEXT: wayfinder | WHEN: every question in the frontier has a committed answer.
