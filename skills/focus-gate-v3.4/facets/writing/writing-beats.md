# Facet Contract: writing-beats (v3.3)
Context: Writing | Mode: Narrative Exposition Progression | Eviction: On Gate Settle

```facet-meta
schema: 1
id: writing-beats
summary: Atomic narrative beats that ground each term before leaning on it
priority: 5
mode: EPHEMERAL
applies_when: ["beats", "beat", "narrative", "step by step", "exposition", "story of the", "walkthrough order"]
socratic:
  grounding: ["CONTEXT.md", "active gate contract"]
  stems: ["Which beat introduces the prerequisite for {beat}?", "Does this term appear in an earlier beat first?"]
  cap: 3
usability:
  seed: "Write the next single beat in 3 sentences or fewer."
  criterion: "Each committed beat grounds every term it reuses."
```

## Invariant Directives
1. PREREQUISITE_CHECK: Build each beat only on concepts an earlier beat already grounded.
2. ATOMIC_COMMIT: Commit the one agreed beat before proposing the next.
3. BEAT_UNIT: Advance exposition by one narrative move at a time, such as symptom, root cause, prevention.
4. BRANCHING_OPTIONS: Offer 2 to 3 candidate next beats and preview where each leads.

## Playbook
### Phases
1. Ground the vocabulary | DO: List terms the next beat will use and the beat that introduced each. | EXIT: count of terms with no earlier beat number is 0.
2. Propose branches | DO: Write 2 to 3 candidate next beats in one line each. | EXIT: candidates count is 2 or 3, each with a stated next consequence.
3. Write the beat | DO: Draft the chosen beat in 3 sentences or fewer. | EXIT: sentence count is 3 or fewer and each reused term has an earlier beat.
4. Commit | DO: Append the beat to the beats file. | EXIT: the file's `## Beat` count rose by 1.
### Lazy Tells
- LEAP_AHEAD | SAYS: "I will cover the next three beats together" | DETECT: one commit holds more than 1 beat | INSTEAD: commit one beat and ask.
- UNGROUNDED_TERM | SAYS: "the reader will know what a saga is" | DETECT: a term has no earlier beat | INSTEAD: introduce it in its own beat first.
### Gate Templates
```gate
- [ ] beats-committed: the beats file holds at least one committed beat
  CHECK: grep -c "^## Beat" {beats_file}
  EXPECT: ^[1-9]
```
### Handoff
- NEXT: writing-shape | WHEN: the beats are complete and must become a structured document.
- NEXT: writing-fragments | WHEN: new raw observations arrive that do not fit a beat yet.
