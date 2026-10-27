# Facet Contract: diagnosing-bugs (v3.3)
Context: Engineering | Mode: Bespoke Differential Diagnosis Loop & Anti-Shotgun | Eviction: On Gate Settle

```facet-meta
schema: 1
id: diagnosing-bugs
summary: Reproduce-first differential diagnosis with falsifiable hypotheses
priority: 10
mode: WINDOW
applies_when: ["bug", "error", "fail", "crash", "broken", "flaky", "timeout", "regression", "exception", "null pointer", "typeerror", "bounds error", "deadlock", "p0", "fix", "defect", "failing", "patch", "emergency"]
socratic:
  grounding: ["file:line", "active gate contract"]
  stems: ["What is your falsifiable hypothesis, and what command refutes it?", "Between last-good and first-bad, what is the midpoint commit?"]
  cap: 2
usability:
  seed: "Run the failing command; capture exit code."
  criterion: "Repro command fails deterministically 3/3 before any fix."
```

## Invariant Directives
1. REPRODUCE: Write the CHECK for the FIXED behavior and see it RED under `focus-gate.py --baseline` before any source edit.
2. ANTI_SHOTGUN_PATCHING: Reject blind null-checks, blanket `except Exception: pass` and type casts that mask a failure without naming its cause.
3. HYPOTHESIZE: State one falsifiable root-cause hypothesis and the command that would refute it before changing code.
4. ISOLATE: Bisect the defect to one file:line and its boundary seam using instrumentation, not reading alone.
5. GATE_LOCK: Keep CHECK and EXPECT byte-identical through the fix; editing them voids the recorded red.
6. SETTLE_STRICT: Close with `focus-gate.py --check <id> --strict` so the fix is bound to the exact red you saw.

## Playbook
### Phases
1. Reproduce | DO: Write the gate for the fixed behavior, then run `--baseline`. | EXIT: status `RED` with exit code 1 on 3 of 3 runs, zero source files modified.
2. Hypothesize | DO: Write the cause as one sentence and the command that refutes it. | EXIT: ledger line `HYPOTHESIS:` plus a refuting command that was run.
3. Isolate | DO: Bisect between last-good and first-bad commit or add instrumentation at the seam. | EXIT: one `file:line` named as the first wrong value.
4. Fix at the cause | DO: Change the code at that line, leaving CHECK and EXPECT untouched. | EXIT: `--run` shows the gate `PASSED` with a recorded red.
5. Settle and guard | DO: Run `--check <id> --strict`, then add the neighbouring input class as a second gate. | EXIT: exit code 0 and 2 gates settled.
### Lazy Tells
- SYMPTOM_PATCH | SAYS: "wrap it in try/except and return a default" | DETECT: diff adds `except` or `if x is None` and no failing test names the input | INSTEAD: reproduce the input as a CHECK, then fix where the bad value is created.
- EDIT_THE_CHECK | SAYS: "the EXPECT was too strict" | DETECT: `--evidence` shows a second fingerprint for the same gate | INSTEAD: restore the CHECK, fix the code, re-baseline only if the behavior spec changed.
- ONE_GREEN_RUN | SAYS: "it passed once, flaky is gone" | DETECT: flaky gate ran fewer than 10 times | INSTEAD: loop the CHECK 10 times with `|| exit 1`.
### Gate Templates
```gate
- [ ] bug-repro: the failing input now returns the specified value
  CHECK: python3 -m unittest {module}.{test}
  EXPECT: \nOK
- [ ] flaky-stable: the test passes 10 consecutive runs
  CHECK: bash -c 'for i in 1 2 3 4 5 6 7 8 9 10; do python3 -m unittest {module}.{test} || exit 1; done'
  EXPECT: \nOK
```
### Handoff
- NEXT: unlazy | WHEN: root cause is isolated and the red is recorded.
- NEXT: code-review | WHEN: the fix touches more than one module.
