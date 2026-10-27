# Facet Contract: writing-shape (v3.3)
Context: Writing | Mode: Bespoke Technical Specification & Anti-Prose-Cliché | Eviction: On Gate Settle

```facet-meta
schema: 1
id: writing-shape
summary: Shape grounded fragments into specs via opening-thesis selection
priority: 6
mode: EPHEMERAL
applies_when: ["rfc", "spec doc", "specification", "design doc", "shape this", "write a decision doc", "post-mortem", "tutorial", "migration guide", "release notes", "system spec", "architecture spec", "data contract", "changelog", "postmortem"]
oracle: ["--audit-prose-cliche"]
socratic:
  grounding: ["CONTEXT.md", "file:line"]
  stems: ["Which of the 3 openings matches the reader's job?", "Which paragraph lacks a grounded entity - name it."]
  cap: 2
usability:
  seed: "Draft the 3 candidate opening theses before paragraph one."
  criterion: "--audit-prose-cliche clean on the finished section."
```

## Invariant Directives
1. DOMAIN_GROUNDING: Anchor every paragraph in at least one checkable entity: a metric, a file:line, a command or a symbol.
2. ANTI_PROSE_CLICHE: Strip throat-clearing, buzzwords and closing summaries, and prove it with `--audit-prose-cliche`.
3. THREE_OPENINGS: Offer 2 to 3 distinct opening theses and let the human pick before drafting section one.
4. SURVEY_FRAGMENTS: Read `.focusgate/FRAGMENTS.md` before proposing structure so raw material shapes the outline.
5. ITERATIVE_SECTIONS: Commit one agreed section at a time and render uniform schemas as tables.
6. DISK_SYNC: Re-read the file from disk immediately before every section edit.
7. RESTRAINT_DOCTRINE: Prefer prioritized weights to symmetrical three-bullet lists and add zero conversational padding.

## Playbook
### Phases
1. Survey | DO: Read the fragments and list the entities they mention. | EXIT: entity list with count N and the source line of each.
2. Choose the opening | DO: Draft 3 opening theses for the reader's job. | EXIT: 3 candidates shown and 1 chosen by the human.
3. Write a section | DO: Draft one section where each paragraph names an entity. | EXIT: paragraphs without an entity count 0.
4. Audit | DO: Run `--audit-prose-cliche` on the file. | EXIT: `PROSE_CLICHE_AUDIT_PASS`.
### Lazy Tells
- SUMMARY_CLOSER | SAYS: "in conclusion, to summarize the above" | DETECT: `--audit-prose-cliche` reports a closing trope | INSTEAD: end on the last concrete fact.
- ABSTRACT_PARAGRAPH | SAYS: "this enables better outcomes for teams" | DETECT: paragraph names no metric, symbol or file | INSTEAD: replace it with the measured claim and its source.
### Gate Templates
```gate
- [ ] prose-clean: the finished section carries no AI writing tells
  CHECK: python3 scripts/focus-gate.py --audit-prose-cliche {path}
  EXPECT: PROSE_CLICHE_AUDIT_PASS
```
### Handoff
- NEXT: writing-beats | WHEN: the section is a story whose order matters.
- NEXT: code-review | WHEN: the document specifies code and must match the diff.
