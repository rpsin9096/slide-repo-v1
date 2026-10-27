# Facet Contract: unlazy (v3.3)
Context: Cognitive | Mode: Dual-Phase Execution Rigor | Eviction: On Gate Settle

```facet-meta
schema: 1
id: unlazy
summary: Completion discipline: gates settle only on real verified evidence
priority: 9
mode: WINDOW
applies_when: ["implement", "finish", "complete", "build the", "no stubs", "to completion", "do not stop until", "ship it", "production ready", "remaining gates"]
oracle: ["--run"]
socratic:
  grounding: ["active gate contract", "file:line"]
  stems: ["Which of the 4 passes is unproven for {gate_id}: cite the CHECK line."]
  cap: 1
usability:
  seed: "Open the active gate's CHECK command and run it unmodified."
  criterion: "Every settled gate has exit-code 0 + EXPECT match + no TODO/FIXME in diff."
```

## Invariant Directives
1. EVIDENCE_OR_NOT_DONE: A gate is done only when `--check <id> --strict` exits 0; prose, a green-looking diff or "should work" settle nothing.
2. RED_BEFORE_GREEN: Run `--baseline` before editing and keep CHECK and EXPECT unchanged afterwards; a gate never seen RED proves nothing.
3. NO_PLACEHOLDERS: Reject `TODO`, `FIXME`, empty `pass`, `raise NotImplementedError` and dummy returns before they reach the filesystem.
4. SINGLE_ACTIVE: Hold one active gate; successors wait in topological order in the frontier buffer.
5. PRE_LINT: Run `focus-gate.py --lint` on the ledger before any verification run so cheating CHECKs are caught first.
6. FOUR_PASS_LOOP: Work in 4 passes: complete deliverable, domain elevation, boundary defense, low-cost polish; do not skip to polish.
7. PROACTIVE_RESOLUTION: When a command fails, diagnose and repair in the same turn before reporting the failure.
8. ABANDON_PROTOCOL: Discard a gate only by writing `ABANDON: <id> <reason>` to the ledger.
9. DEEP_VERIFICATION: Certify a gate only after the execution oracle, side-effect check and rigor invariants all agree.

## Playbook
### Phases
1. Lint the contract | DO: Run `--lint` and fix every `[ERROR]` in the active gate. | EXIT: `Lint result: 0 error(s)`.
2. Baseline | DO: Run `--baseline` before touching code. | EXIT: each gate prints `RED`; any `ALREADY_GREEN` is tightened or dropped.
3. Complete the deliverable | DO: Implement the whole behavior with real logic, no stubs, in the smallest diff. | EXIT: `--unlazy-rigor <path>` prints `RIGOR_PASS`.
4. Elevate and defend | DO: Replace naive patterns with domain types and probe malformed input, timeouts and empty collections. | EXIT: at least 3 boundary cases added as assertions in the gate test.
5. Settle | DO: Run `--check <id> --strict`, then `--run`. | EXIT: `--check` exits 0 and `--run` exits 0 with every gate `PASSED`.
### Lazy Tells
- DECLARED_DONE | SAYS: "implemented, it should work now" | DETECT: no `--check` or `--run` output in the turn | INSTEAD: run the gate and paste its result.
- STUB_AND_MOVE_ON | SAYS: "stubbed for now, will fill in later" | DETECT: `--unlazy-rigor` flags `TODO`, `pass` or `NotImplementedError` | INSTEAD: write the real logic now or abandon the gate with a reason.
- GREEN_BY_WEAKENING | SAYS: "relaxed the EXPECT so it passes" | DETECT: `--evidence` shows a new fingerprint for the gate | INSTEAD: restore the CHECK and fix the code.
- STOP_EARLY | SAYS: "the main path works, rest is similar" | DETECT: open gates remain in `--run` output | INSTEAD: continue; the task ends when `--run` exits 0.
### Gate Templates
```gate
- [ ] no-stubs: touched files contain no placeholder or empty-body tells
  CHECK: python3 scripts/focus-gate.py --unlazy-rigor {path}
  EXPECT: RIGOR_PASS
- [ ] suite-green: the whole suite passes after the change
  CHECK: python3 -m unittest discover -s tests
  EXPECT: \nOK
```
### Handoff
- NEXT: code-review | WHEN: every gate is settled and the diff spans more than one module.
- NEXT: wayfinder | WHEN: the active gate is settled and the next ticket must be claimed.
