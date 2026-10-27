# Facet Contract: prototype (v3.3)
Context: Engineering | Mode: Disposable HTML/JS Spikes | Eviction: On Spike Settle

```facet-meta
schema: 1
id: prototype
summary: Disposable single-question spikes that settle into micro-ADRs
priority: 6
mode: WINDOW
applies_when: ["spike", "prototype", "sandbox", "does it fit", "sanity check", "hacky", "one html"]
oracle: ["--verify-spike", "--settle-spike"]
socratic:
  grounding: ["active gate contract"]
  stems: ["State the single falsifiable question this spike kills or keeps - one sentence."]
  cap: 1
usability:
  seed: "Create empty .focusgate/spikes/<name>.html with a status div."
  criterion: "--verify-spike exits 0 on the single-question harness."
```

## Invariant Directives
1. SINGLE_QUESTION: A prototype exists to resolve exactly one falsifiable hypothesis about a state machine or a layout.
2. HARNESS_VERIFICATION: Expose a runnable harness and check it with `focus-gate.py --verify-spike <path>` before trusting any answer.
3. VANILLA_SANDBOX: Ship one self-contained HTML file with zero external dependencies that opens directly in a browser.
4. SETTLE_AND_SLAY: Convert the validated spike into a micro-ADR with `--settle-spike` and delete the temporary files.
5. NO_PRODUCTION_IMPORTS: Production code never imports from a spike; port the validated logic, then remove the spike.

## Playbook
### Phases
1. State the question | DO: Write one sentence the spike can answer yes or no. | EXIT: one `?` sentence at the top of the spike file and in the ledger.
2. Scaffold | DO: Run `--scaffold-spike <logic or ui> <name> "<question>"`. | EXIT: file exists under `.focusgate/` and `--verify-spike` prints its checklist.
3. Answer | DO: Drive the pure logic module through the cases that could falsify the hypothesis. | EXIT: Current State panel shows the answer and `--verify-spike` exits 0.
4. Settle | DO: Record the answer as a micro-ADR via `--settle-spike`. | EXIT: ADR line appears under `## 3. Micro-ADR Ledger` and the spike file is gone.
### Lazy Tells
- SPIKE_BECOMES_APP | SAYS: "it works, let us ship the spike" | DETECT: spike path is imported or copied whole into `src/` | INSTEAD: port only the validated reducer and delete the spike.
- QUESTIONLESS_SPIKE | SAYS: "let me just try a few things" | DETECT: spike has no `?` sentence | INSTEAD: write the falsifiable question first.
### Gate Templates
```gate
- [ ] spike-verified: the prototype harness passes the spike verifier
  CHECK: python3 scripts/focus-gate.py --verify-spike {artifact}
  EXPECT: VALID_[A-Z]+_PROTOTYPE
```
### Handoff
- NEXT: codebase-design | WHEN: the spike answered yes and the logic needs a production seam.
- NEXT: grilling | WHEN: the spike answered no and the decision has alternatives.
