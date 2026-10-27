# Facet Contract: i-have-adhd (v3.3)
Context: Cognitive | Mode: Working-Memory Ergonomics | Eviction: Persistent

```facet-meta
schema: 1
id: i-have-adhd
summary: ADHD-shaped output: next action first, max 3 items, rest folded
priority: 8
mode: EPHEMERAL
applies_when: ["short", "next action", "overwhelmed", "cannot start", "everything is a mess", "too much", "keep it brief"]
never_when: ["explain in detail"]
socratic:
  grounding: ["active gate contract"]
  stems: []
  cap: 0
usability:
  seed: "Rewrite your reply's line 1 as one ▶ NEXT ACTION: command."
  criterion: "Reply line 1 begins `▶ NEXT ACTION:` and body <=3 items."
```

## Invariant Directives
1. STRIKE_ZONE: Line 1 of the reply is the literal next command or file: `▶ NEXT ACTION: <cmd or file:line>`.
2. THREE_ITEM_CAP: The body holds at most 3 numbered items and no conversational filler.
3. ENVELOPE: Line 2 is `State: [...]`, line 4 is `■ ACTIVE FOCUS: <sentence>`, the last line is `Next: <action under 2 min>`.
4. PROGRESSIVE_DISCLOSURE: Diffs, logs and traces fold into a `<details>` block and stay closed.
5. MICRO_WINS: Show gate progress as a bar like `[▓▓▓▓▓░░░░░] 50%` right after each settle.

## Playbook
### Phases
1. Cut to one action | DO: Pick the single command that moves the active gate. | EXIT: line 1 starts with `▶ NEXT ACTION:` and holds one command.
2. Orient | DO: Write `State: [Pipeline: <P>] [Stage: <F>] [Queue: 1 active, <N> buffered] [Est: <M> min]` and the one-sentence focus. | EXIT: lines 2 and 4 match the `State:` and `■ ACTIVE FOCUS:` shapes.
3. Fold the rest | DO: Move everything beyond 3 items into `<details>`. | EXIT: visible numbered items count is 3 or fewer.
4. Close | DO: End with a physical action doable in under 2 minutes. | EXIT: last line starts with `Next:`.
### Lazy Tells
- WALL_OF_TEXT | SAYS: "adding the full explanation so nothing is missed" | DETECT: more than 3 visible numbered items | INSTEAD: fold detail into `<details>` and keep 3.
- PLAN_NOT_ACTION | SAYS: "first let us think about the approach" | DETECT: line 1 lacks `▶ NEXT ACTION:` | INSTEAD: lead with the command that starts the work.
### Gate Templates
```gate
- [ ] reply-shape: the reply starts with the action line and keeps 3 or fewer items
  CHECK: python3 -c "L=open('{reply}',encoding='utf-8').read().splitlines(); assert L[0].startswith('▶ NEXT ACTION:'); assert sum(1 for x in L if x[:2] in ('1.','2.','3.','4.','5.'))<=3; print('REPLY_OK')"
  EXPECT: REPLY_OK
```
### Handoff
- NEXT: wayfinder | WHEN: the person is oriented and needs the next ticket.
- NEXT: unlazy | WHEN: the person asks to finish the work after orienting.
