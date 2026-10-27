# Facet Contract: code-review (v3.3)
Context: Engineering | Mode: Dual-Axis Review | Eviction: On Gate Settle

```facet-meta
schema: 1
id: code-review
summary: Dual-axis review with schema-bound findings and severity gate
priority: 7
mode: WINDOW
applies_when: ["review", "diff", "pull request", "merge", "pre-merge", "check my changes", "standards"]
socratic:
  grounding: ["active gate contract", "file:line"]
  stems: ["Which axis finding lacks a replacement snippet - write it."]
  cap: 1
usability:
  seed: "Run both axes on the smallest file in the diff."
  criterion: "Both axes emit PASS or findings with snippets; no narrative-only findings."
```

## Invariant Directives
1. DUAL_AXIS: Review every diff on the Standards axis (hygiene, seams, types) and the Spec axis (issue and gate criteria) separately.
2. ACTIONABLE_FINDINGS: Each finding carries axis, file:line, severity and a concrete replacement snippet; narrative-only findings are rejected.
3. SEVERITY_GATE: Blockers are must-fix and stop settlement; minors are advisory and never block.
4. EVIDENCE_LINK: Spec-axis findings cite the originating gate id and the `--evidence` record proving its CHECK ran.
5. PARALLEL_EVAL: Audit the two axes in independent passes so the second verdict cannot copy the first.
6. UNANIMOUS_PASS: Settle only when both axes report PASS and the gate passes `--check <id> --strict`.

## Playbook
### Phases
1. Scope the diff | DO: List changed files with `git diff --stat` and map each to a gate id. | EXIT: every changed file maps to one gate or is flagged `UNOWNED`.
2. Spec axis | DO: Re-run each gate CHECK unmodified and compare observed behavior with the criteria. | EXIT: per gate, `PASS` or a finding citing the gate id.
3. Standards axis | DO: Read seams, types and error paths, then run `--audit-code-cliche` on touched files. | EXIT: `CODE_CLICHE_AUDIT_PASS` or findings carrying `file:line`.
4. Write findings | DO: Emit findings as JSON with axis, file_line, severity, snippet. | EXIT: count of findings missing a `snippet` is 0.
### Lazy Tells
- LGTM_NO_RUN | SAYS: "the diff looks fine to me" | DETECT: review output holds no re-run CHECK result | INSTEAD: run every gate CHECK before judging.
- NARRATIVE_FINDING | SAYS: "consider improving error handling" | DETECT: finding lacks `file:line` or a snippet | INSTEAD: name the line and write the replacement.
### Gate Templates
```gate
- [ ] findings-complete: every finding names axis, file_line, severity and snippet
  CHECK: python3 -c "import json; f=json.load(open('{findings}')); assert f and all(k in x for x in f for k in ('axis','file_line','severity','snippet')); print('FINDINGS_OK')"
  EXPECT: FINDINGS_OK
```
### Handoff
- NEXT: unlazy | WHEN: one or more blockers are open.
- NEXT: wayfinder | WHEN: both axes pass and the next ticket must be claimed.
