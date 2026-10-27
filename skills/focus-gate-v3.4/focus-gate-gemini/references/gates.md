# Writing Gates That Count: Evidence Catalogue (v3.4 Edition)

A gate is evidence only if its `CHECK:` could fail for the right reason. Use this catalogue when standard test commands need adaptation.

---

## 1. Bug Fix
Write the `CHECK:` for the **fixed** behavior, run baseline, observe `RED`, then implement the fix.
```markdown
- [ ] bug-142: empty cart total is 0, not NaN
  CHECK: python3 -c "from cart import total; assert total([]) == 0"
  EXPECT: ^$
```
Do not write `EXPECT: FAIL` or look for reproduction error codes; the evidence log records the red failure automatically.

---

## 2. Flaky Test
One green run proves little. Force repeatability:
```markdown
- [ ] flaky-worker: passes 10 consecutive runs without timeout
  CHECK: bash -o pipefail -c "for i in {1..10}; do pytest -q tests/test_worker.py || exit 1; done"
  EXPECT: passed
```
The `|| exit 1` propagates failure honestly; `|| true` is prohibited.

---

## 3. No Test Runner / Blackbox Testing
Check observable artifacts, CLI exit codes, or structured outputs:
```markdown
- [ ] export-cli: produces non-empty report
  CHECK: test -s dist/report.csv && echo ARTIFACT_OK
  EXPECT: ARTIFACT_OK

- [ ] health-endpoint: returns healthy status code
  CHECK: curl -sf http://localhost:8000/health
  EXPECT: "status":\s*"ok"
```
Existence checks are weaker than behavior checks; prefer behavior wherever possible.

---

## 4. UI / Visual Behavior
Assert on DOM structure, ARIA accessibility, or calculated contrast ratios:
```markdown
- [ ] login-modal: accessible dialog with keyboard focus
  CHECK: node scripts/check-dom.js
  EXPECT: ACCESSIBLE_DIALOG_VALIDATED
```
Visual aesthetic judgment remains a manual gate (no `CHECK:` line), which the evidence log records as `manual`.

---

## 5. Refactor
Behavior must not change, so the existing test suite will be `ALREADY_GREEN` at baseline.
1. Use `WAIVED_RED: "behavior-preserving refactor"`.
2. Add a new gate that is red today proving the *structural* goal:
```markdown
- [ ] eliminate-legacy-utils: zero imports of legacy module
  CHECK: grep -rn "from legacy_utils" src/ || echo UNLINKED
  EXPECT: UNLINKED
```

---

## 6. Pure Addition / Greenfield Feature
When creating a new file or feature, the initial red is "does not exist yet":
```markdown
- [ ] parser-json: parses v2 payload correctly
  CHECK: python3 -c "import parser_v2; assert parser_v2.parse('{}') == {}"
  EXPECT: ^$
```
An `ImportError` or `AssertionError` is a genuine RED observation. Missing external CLI tools (exit 127) are ERRORs, not RED.

---

## 7. Anti-Patterns Caught by Cognitive Linter

| Pattern | Code | Rationale |
|---|---|---|
| `true`, `echo ok`, `exit 0` | `SELF_SATISFYING` | Cannot fail; proves nothing |
| `cmd \|\| true`, `cmd; true`, `set +e`, `cmd &` | `MASKED_EXIT` | Turns failures into false successes |
| `EXPECT: .*`, `^`, `x*` | `VACUOUS_EXPECT` | Matches any output string |
| `EXPECT: (` | `INVALID_EXPECT` | Broken regex pattern |
| `<command>`, template placeholders | `UNFILLED_TEMPLATE` | Unfinished template leftover |
| `rm -rf /`, `rm -rf ~`, `git push --force`, `mkfs` | `DESTRUCTIVE_COMMAND` | Catastrophic command; refused permanently even with override |
| `curl ... \| sh` | `REMOTE_CODE_EXEC` | Unsafe remote script execution |
| `except Exception: pass` / `except: pass` | `SWALLOWED_EXCEPTION` | Swallows errors and conceals bugs |
| `git status`, bare `ls`, `date` | `TAUTOLOGY_CHECK` | Succeeds in any git repository |
| `pytest \| tail` | `PIPE_MASKS_EXIT` | Discards test runner exit status |
| `python -c "print('ok')"` | `LITERAL_OUTPUT` | Output is a static string, not state |
