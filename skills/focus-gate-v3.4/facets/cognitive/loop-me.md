# Facet Contract: loop-me (v3.3)
Context: Cognitive | Mode: Recurring Workflow Synthesis | Eviction: On Gate Settle

```facet-meta
schema: 1
id: loop-me
summary: Convert recurring toil into scripted gates with push-right checkpoints
priority: 6
mode: EPHEMERAL
applies_when: ["every time", "each time", "recurring", "workflow", "cron", "nightly", "polling", "watch the", "script this", "automate", "routine", "push right", "checklist"]
socratic:
  grounding: ["active gate contract", "file:line"]
  stems: ["Which single run of this loop is automatable today - cite the command.", "What decision must stay human - cite the checkpoint."]
  cap: 2
usability:
  seed: "List the exact command you re-run by hand in a scratch file."
  criterion: "One loop run executes end-to-end from the scratch file unattended."
```

## Invariant Directives
1. LOOP_LENS: Treat anything the person re-runs by hand, polls or re-checks as a loop candidate and write the exact command down.
2. COMPILE_GATES: Turn each recurring workflow into a tracer gate whose CHECK is the command the person used to run manually.
3. PUSH_RIGHT: Defer human decisions to the latest checkpoint and precompute the diff and verdict before asking.
4. DECISION_BRIEF: A checkpoint shows the finished output, the rationale and exact file:line links so the person decides in one read.

## Playbook
### Phases
1. Capture the manual run | DO: Write the exact commands the person repeats into a scratch file. | EXIT: scratch file exists and `bash` runs it start to end.
2. Find the human decision | DO: Mark the single step that needs judgment. | EXIT: one `CHECKPOINT:` line naming a `file:line` to inspect.
3. Compile | DO: Convert the unattended steps into gates with CHECK and EXPECT. | EXIT: `--lint` prints `0 error(s)` and `--baseline` prints `RED` for each.
4. Run unattended | DO: Execute the loop end to end without prompts. | EXIT: exit code 0 and the final line `LOOP_DONE`.
### Lazy Tells
- AUTOMATE_THE_DECISION | SAYS: "I will let the script decide that too" | DETECT: no `CHECKPOINT:` line in the script | INSTEAD: keep the judgment step and precompute its brief.
- UNTESTED_LOOP | SAYS: "the script is written, it should run" | DETECT: no unattended run recorded in `--evidence` | INSTEAD: run it once start to end and settle the gate.
### Gate Templates
```gate
- [ ] loop-runs-unattended: one full loop run finishes without prompts
  CHECK: bash {script}
  EXPECT: LOOP_DONE
```
### Handoff
- NEXT: unlazy | WHEN: the loop script exists and its gates need implementing.
- NEXT: wayfinder | WHEN: several loops compete and one must be claimed first.
