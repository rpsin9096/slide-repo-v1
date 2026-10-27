# Facet Contract: writing-for-agents (v3.3)
Context: Writing | Mode: Machine Brief Synthesis & Anti-Sycophancy | Eviction: On Gate Settle

```facet-meta
schema: 1
id: writing-for-agents
summary: Machine briefs with checkable exits and zero prompt ballast
priority: 7
mode: EPHEMERAL
applies_when: ["agent brief", "subagent", "prompt for an agent", "handoff", "brief for gate", "machine-readable task"]
socratic:
  grounding: ["active gate contract"]
  stems: []
  cap: 0
usability:
  seed: "Convert one instruction into a CHECK/EXPECT pair."
  example: "CHECK: python3 -m pytest tests/x.py EXPECT: 1 failed (not `assert True`)."
  criterion: "Every brief line constrains input, transform, or exit."
```

## Invariant Directives
1. CHECKABLE_EXIT: Give each brief an observable exit: an exit code, a regex on output and a timeout.
2. CONTEXT_POINTERS: Pass content, not a bare `@pointer`; a pointer is allowed only beside the sentence that says when to open it.
3. NO_BALLAST_DIRECTIVE: Delete any line a capable model follows anyway; every line must constrain an input, a transform or an exit.
4. ANTI_SYCOPHANCY_GUARD: Omit flattery and cheerleading phrases; state inputs and outputs instead.
5. INFORMATION_TIERING: Put steps in the file first, rules second, and disk references third with a trigger for opening each.
6. POSITIVE_STEERING: State the target action in affirmative form; keep negative phrasing for hard prohibitions only.

## Playbook
### Phases
1. Extract the contract | DO: Copy the gate id, CHECK and EXPECT into the brief. | EXIT: brief holds one `CHECK:` and one `EXPECT:` line.
2. Inline the context | DO: Paste the facts the agent needs and attach each pointer to its trigger. | EXIT: `--audit-context-sufficiency` prints `CONTEXT_SUFFICIENCY_PASS`.
3. Cut ballast | DO: Delete lines that restate default behavior. | EXIT: every remaining line names an input, transform or exit.
4. Dry run | DO: Read the brief as the agent with no other context. | EXIT: the first command the agent issues is `--baseline`.
### Lazy Tells
- BARE_POINTER | SAYS: "see @design.md for details" | DETECT: `--audit-context-sufficiency` flags a bare pointer | INSTEAD: inline the needed facts and keep the pointer with its trigger.
- PEP_TALK | SAYS: "you are a world-class expert, be thorough" | DETECT: line constrains no input, transform or exit | INSTEAD: replace it with the exit criterion.
### Gate Templates
```gate
- [ ] brief-sufficient: the brief carries content instead of bare pointers
  CHECK: python3 scripts/focus-gate.py --audit-context-sufficiency {brief}
  EXPECT: CONTEXT_SUFFICIENCY_PASS
```
### Handoff
- NEXT: unlazy | WHEN: the brief is sufficient and the gate must be implemented.
- NEXT: code-review | WHEN: an agent returned work that must be judged against the brief.
