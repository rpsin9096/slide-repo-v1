---
name: focus-gate-v3-4
description: Evidence-gated workflow for non-trivial engineering work. Splits a task into acceptance gates, each with an executable CHECK command and EXPECT pattern, and lets a gate close only when the command actually ran and passed (red before green, tamper-evident log). Use this whenever the user asks to plan, build, implement, fix a bug, refactor, review, debug, or "finish / complete / ship" multi-step work, or says gates, GATES.md, FocusGate, red-green, "no stubs", "prove it works", or "don't stop until it's done" - even if they never name FocusGate. Also use it to audit whether an existing checklist or test gate actually proves anything.
license: MIT
metadata:
  version: "v3.4-PROD"
  runtime: "Python 3.9+ standard library only"
---

# FocusGate v3.4-PROD: Evidence Gate + Deep Facets

Agents declare work "done" far too easily. FocusGate makes "done" something a command
proves, not something you assert. A **gate** is a checkbox plus `CHECK:` (a shell
command) and `EXPECT:` (a regex that must appear in its output). `--check` runs the
command and only then writes `[x]`. You cannot close a gate by editing the file.

All commands: `python3 scripts/focus-gate.py <flag>` (path relative to this skill).

## The loop

1. **Route** the task: `-p "<task>"` prints the pipeline and which facets apply (deterministic, ~0.2s, no model tokens). `--hydrate-facet <id> --depth playbook` loads that facet's rules and its process: phases with observable exits, the shortcuts to avoid and how to detect them, gate templates, and the next facet.
2. **Write gates** in `.focusgate/GATES.md` (`--init` scaffolds it). One gate per observable behavior. Write the CHECK for the *finished* behavior, so it fails today.
3. **Lint** them: `--lint`. Fix every `[ERROR]`; read every `[WARN]`. This is where cheats such as `|| true` or `echo passed` get caught.
4. **Baseline before touching code**: `--baseline`. Every gate should print `RED`. `ALREADY_GREEN` means the gate cannot prove your change: tighten it or drop it. `ERROR` (exit 126/127) means the tool is missing, not that the feature is.
5. **Implement**, one gate at a time. `--run` reports every gate's status and never settles anything, so use it freely.
6. **Settle**: `--check <gate_id> --strict`. It re-executes the CHECK and writes `[x]` only if it passes and this exact CHECK/EXPECT was seen red earlier. Done when every gate is `[x]` and `--run` exits 0.

`--evidence` shows the log of observations and verifies its hash chain. Show it to the user when they ask "how do I know it works?".

## Why the rules are what they are

- **Red before green.** A check that never failed proves nothing about *your change*: it may already pass, or be unable to fail. The log binds each red to a fingerprint of the exact CHECK+EXPECT, so if you edit the CHECK after seeing it fail (the classic way to "fix" a failing gate), the red no longer counts and you must re-baseline. Do not edit a CHECK to make it pass; fix the code.
- **Honest CHECKs.** The linter reads the shell structure. It rejects commands that cannot fail (`true`, `echo ok`, `exit 0`), that mask failure (`|| true`, trailing `; true`, `set +e`, `&` backgrounding), and EXPECT patterns that match any output (`.*`, `^`). It warns on probes that pass in any repo (`git status`, bare `ls`) and on `pytest | tail` (the pipe discards pytest's exit code; use `bash -o pipefail -c '...'`).
- **Overrides exist but leave a trail.** `--force` bypasses an integrity error; `--waive-red "<reason>"` bypasses the red requirement (legitimate when a bug was already fixed upstream). Both are written to the log and shown by `--evidence`. Use them rarely, and tell the user when you did.

## A good gate, a bad gate

```markdown
- [ ] login-timeout: expired session returns 401, not 500
  CHECK: python3 -m pytest -q tests/test_auth.py::test_expired_session
  EXPECT: 1 passed
```
Good: fails until the behavior exists; names the behavior; EXPECT cannot match a failure.

```markdown
- [ ] done: everything works
  CHECK: pytest -q | tail -1
  EXPECT: passed
```
Bad: `1 failed, 4 passed` also matches "passed", and the pipe hides pytest's exit code. Details and a larger catalogue: `references/gates.md`.

## Audits worth running before you call work done

- `--verify-wave` runs every invariant gate end to end; use it as the final check on a whole task.
- `--audit-all <path>` scores prose, code and design for machine-written tells (junk-drawer modules, `except: pass`, filler phrases). `--audit-prose-cliche`, `--audit-code-cliche` and `--audit-design-cliche` run one oracle each.
- `--lint-facets` verifies the facet contracts themselves; `--audit-context-sufficiency <brief>` catches sub-agent briefs that hand over a bare `@pointer` instead of the content.
- `--synthesize-pipeline "<task>"` is the long form of `-p`.

## Output format (Action Envelope)

Keep each turn scannable: first line `▶ NEXT ACTION: <command or file:line>`, second line `State: [Pipeline: <name>] [Active Gate: <id>] [Queue: 1 active, <N> buffered] FocusGate v3.4-PROD`, then `■ ACTIVE FOCUS: <one sentence>`, at most 3 numbered items, collapsible `<details>` for traces, and a closing `Next:` that takes under 2 minutes. One active gate at a time keeps working memory small, which is the point.

## Safety

`CHECK` lines run through the shell with your permissions. Treat a `GATES.md` you did not write like a script from the internet: read its CHECK lines before running `--run`, `--check` or `--baseline` on it, especially in a freshly cloned repo. Since v3.4 a CHECK that matches a catastrophic pattern (root or home wipe, force push, raw disk write, mkfs, shutdown) is refused and never executed, even with `--force`; this is a backstop, not a sandbox, so the reading advice still applies.

## Where to go next (read only when needed)

| Need | Read |
|---|---|
| Writing hard gates (flaky tests, UI, bug repro, no test runner) | `references/gates.md` |
| Any flag not listed above (audits, facets, orchestration) | `references/cli.md` (generated from the live parser) |
| Swarm / grid / consensus layers, and what is experimental | `references/architecture.md` |
| Writing or changing a facet (format, lint codes, token tiers) | `references/facets.md` |
| What was found and fixed in v3.4 (and v3.3, v3.2), with repro commands | `AUDIT.md` |
| Component invariants | `SPEC.md` |

Facets (`facets/*/*.md`) hold the process for a kind of work (diagnosing bugs, code review, design). Each has two tiers: the **rules** (what sub-agent briefs receive, within a token ceiling) and the **playbook** (phases, lazy tells, gate templates, handoff; load it with `--depth playbook`). `-p` tells you which facets apply; load only those, and follow the playbook's phase exits as your gates. `--lint-facets` rejects a facet that is only slogans.
