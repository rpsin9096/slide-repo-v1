# AUDIT: FocusGate v3.3-PROD -> v3.4-PROD

Method: dogfood. The v3.4 tests were written first and baselined RED with `--baseline` against an unmodified v3.3 tree; every gate was then settled with `--check --strict` on the v3.4 tree (`docs/evidence/v3.4-build.evidence.jsonl` continues the v3.3 hash chain). Each finding was reproduced on v3.3 first. v3.3 baseline: 719 tests, ~23 s. The migration of 62 `main()` branches was done by an AST tool that preserves the original bodies and comments, so the 719 existing tests were the safety net, not a rewrite.

## Findings fixed

| ID | Finding | v3.3 repro | v3.4 |
|---|---|---|---|
| G1 | **O8 closed.** `main()` was 1881 lines of 62 command branches; the script held 2903 lines and 13 domain classes. | `wc -l scripts/focus-gate.py` | script 25 lines, `main()` 90; ratchets in tests |
| G2 | **O9 closed.** Two dispatchers: `CLIDispatcher.dispatch` (162-line if-chain, 52 routes) and `main()`'s own chain, with different match rules. | read both | one `REGISTRY.resolve` over `(order, registration)`; early routes are a table |
| G3 | 4 branches of `main()` were unreachable: the early dispatcher pre-empts `--checkpoint`, `--restore-checkpoint`, `--list-checkpoints`, `--adversarial-audit`. | print a marker in each branch, run the 4 commands: 0 hits | removed (~53 lines) |
| G4 | `--help` documented flags nothing reads: `--install-guardrails`, `--retro`. | `grep -rn "install_guardrails\|retro" core scripts` finds only the parser | removed; `--dispatch` kept as the explicit opposite of `--preview` and now read |
| G5 | `ContractValidator` called `DomainEvent.validate_schema` without importing `DomainEvent`; the surrounding `try` caught only `JSONDecodeError`. | `--validate-contracts <log with one valid event>` -> `NameError` | imports it; test on a real log |
| G6 | Two facades kept only for tests (`JITHydrationEngine`, `_lint_facet_contracts`), plus `scripts/evaluate_distillation.py` importing the CLI script's internals. | grep | removed; callers use `FacetCatalog` / `core/` |
| O10 | **Closed.** `--unlazy-rigor` passed `except Exception: pass` (the guard allowed `pass` after `except` as an idiom). | `--unlazy-rigor` on a file with that handler: `RIGOR_PASS` | `SWALLOWED_EXCEPTION`; `ImportError`/`KeyError` handlers still allowed |
| O2 | **Partly closed.** CHECKs ran through the shell unconditionally; `command_guard` was never applied. | ledger with `CHECK: dd if=/dev/null of=/tmp/x count=0`; `--baseline` created `/tmp/x` | `DESTRUCTIVE_COMMAND` error; `observe()` never executes it (sentinel test) |

Two defects were mine, found by the suite: a test that ran `--orchestrate x` in the repo directory wrote orchestrator state into `.focusgate/` before the new argument check ran, which broke `--verify-wave` (fixed: validate before any side effect, test in a temp dir); and the rigor guard's new rule changed the rejection message `ToolSelectionMatrix` returns for shotgun suppression (fixed: that check leaves swallowed exceptions to the code-cliche oracle, which owns the dedicated message).

## Open items (not fixed, stated plainly)

- **O12 Handlers are moved, not redesigned.** The 62 migrated bodies are verbatim (explicit `ctx` prologue, `sys.exit` -> `return`). `audits.py` is 599 lines, `economy.py` 432, `verification.py` 425. Splitting them by seam and removing repeated argv parsing is the next structural step.
- **O13 `CLIDispatcher` is still a 1553-line class.** Routing is a table now; the 52 `dispatch_*` implementations still live in one class (`core/cli/dispatch.py`) and `distributed.py` wraps them. Moving each group next to its domain (`core/swarm`, `core/mesh`, ...) is the remaining half of O9.
- **O1 Suite time.** 747 tests take ~22 s here against the <= 15 s target (SPEC invariant 4). Subprocess-heavy; a parallel runner needs isolated `.focusgate` state.
- **O2 The guard is a pattern backstop, not a sandbox.** It does not see `curl ... | sh`, interpreter one-liners that delete files, or scripts invoked by name. Reading a foreign ledger before running it is still the control (SKILL.md Safety).
- **O3 Extended layers unreviewed.** Grid/consensus/mesh pass their own tests; no TLS or peer auth on the grid.
- **O4 Analyzer is heuristic.** It cannot see inside `./verify.sh` or judge whether a real test asserts anything.
- **O5 Evidence is tamper-evident, not tamper-proof.** Anchor the head hash externally for adversarial settings.
- **O7/O11 No model-in-the-loop eval of the facets.** Playbooks are linted for structure and honesty, not measured against real tasks. A v3.2-vs-v3.3 facet A/B on a fixed task set is still the missing evidence.
- **O14 Stale labels.** Some command output still says "v2.8" (e.g. orchestrator preview banner, contract validation report). Cosmetic; tests pin a few of them.

## Earlier audit: v3.2-PROD -> v3.3-PROD

Method: dogfood. v3.2 built v3.3: the build ledger (`.focusgate/GATES.md`, 12 gates) was baselined RED with `--baseline` before any change, and every gate was settled with `--check --strict`; the hash-chained log ships as `docs/evidence/v3.3-build.evidence.jsonl`. Each finding below was reproduced on the unmodified v3.2 first, then pinned by a test (`tests/test_v33_facets.py`, `tests/test_v33_architecture.py`). v3.2 baseline: 671 tests, 16.6 s.

## Findings fixed

| ID | Finding | v3.2 repro | v3.3 |
|---|---|---|---|
| F1 | Sub-agent briefs received facet rule **titles only** (`- DEEP_MODULE`), never the definition. The facet's content was dropped at the one seam where an agent reads it. | `AgentBrief.create(facet="codebase-design", ...).to_prompt()` | `- DEEP_MODULE: Put behavioral depth behind a small public surface...`; squeezed by clause length, then by trailing rules |
| F2 | SPEC invariant 3 (<= 400 / 150 tokens per facet) held for 2 of 19 facets; 13 exceeded it when hydrated whole (`unlazy` ~485). Only the title-only render was ever measured. | token count of `facets/**/*.md` | invariant redefined per tier and tested on all 19: injected render within ceiling, whole file <= 1500 |
| F3 | Router matched substrings: `fix` in `prefix`, `idea` in `ideal`, `short` in `shortcut`; rank was priority only. | `match_facets("update the prefix of the config key")` -> `diagnosing-bugs` | whole-word + inflection matching, evidence-weighted rank; 10 new eval cases incl. near-miss negatives |
| F4 | `AgentBrief.to_prompt` re-parsed every facet file per call (114 parses for 3 briefs), swallowed all exceptions, had a dead branch (`elif ctx == "engineering"` with `ctx` always None), stamped the engineering rigor block on writing facets, and never taught the v3.2 loop. | count `parse_facet_file` calls over 3 briefs | `FacetCatalog` cache (0 parses on unchanged tree); `brief_composer`; Evidence Protocol in every brief with a CHECK |
| F5 | **O6 closed.** Three writers of `[x]` bypassed `settle_gate`: `--swarm-wave`, the autonomous wave loop, `--settle-spike`. A gate `CHECK: echo ok` was ticked by `--swarm-wave`. | ledger with `CHECK: echo ok`; `--swarm-wave` -> `[x]` | all go through `evidence.py`; refused gates stay `[ ]`; `--settle-spike` logs to the chain and errors on an unknown spike |
| F6 | `main()` was ~2100 lines of ~70 sequential `if getattr(args, ...)` branches beside a second dispatcher; `scripts/focus-gate.py` held 3879 lines including five classes that are domain logic. | `wc -l scripts/focus-gate.py` | registry + 11 commands extracted; script 2903, `main()` 1881; ratchets in tests |
| F7 | `--status` raised `KeyError: 'stats'` on every ledger (same root as v3.2 A2: `kernel` is never None, so the kernel vector, which has no `stats`, was used). | `--status .focusgate/GATES.md` | merges ledger stats with the kernel vector |
| F8 | `core/orchestrator_kernel.py` imported `scripts.colab_train_focusgate` (core depending on scripts). | grep | loaded as a shipped asset by path; `test_core_never_imports_scripts` |

The facet linter also earned its keep during the build: it rejected the first draft of a facet gate template (`...; echo STABLE` masks the loop's exit code), which is the cheat the Evidence Gate exists to catch.

## Open items as of v3.3 (current status is in the v3.4 list above)

- **O1 Suite time.** 719 tests take ~23 s here against SPEC invariant 4 (<= 15 s reference-hardware target). Mostly subprocess spawns; a parallel runner is the real fix and is still not done (shared `.focusgate` state, TCP ports).
- **O2 Untrusted ledgers.** CHECK runs with `shell=True`; `core/sandbox/command_guard.py` exists but is not applied. Mitigation is the SKILL.md safety note.
- **O3 Extended layers unreviewed.** Grid/consensus/mesh pass their own tests; not reviewed here. No TLS or peer auth on the grid.
- **O4 Analyzer is heuristic.** It cannot see inside `./verify.sh` or judge whether a real test asserts anything.
- **O5 Evidence is tamper-evident, not tamper-proof.** Anchor the head hash externally for adversarial settings.
- **O7 Evals are v2.8-era.** v3.3 adds routing evals (`evals/facet_routing_v33.json`); there is still no model-in-the-loop eval that measures whether the deeper playbooks change agent behavior. The depth is linted for structure and honesty, not proven to improve outcomes.
- **O8 `main()` is still 1881 lines.** 11 of ~75 commands moved. The remaining branches (audits, orchestration, spikes, checkpoints, events) need the other script classes extracted first (`DomainAuditor`, `ContractValidator`, `WritingSuite`, ...). The ratchet (`MAX_MAIN_LINES`, `MAX_SCRIPT_LINES`) only goes down; the migration recipe is `core/cli/commands/` + `@command`.
- **O9 Two dispatchers.** `core/cli/dispatch.py` (1700 lines, early commands) and the registry coexist. Folding the first into the second is the next structural step after O8.
- **O10 `--unlazy-rigor` does not flag `except Exception: pass`** (it passed such a file in a probe); `--audit-code-cliche` does. The `unlazy` facet's gate template uses the rigor oracle for stubs only.
- **O11 Facet content is authored, not mined.** The 19 playbooks encode this audit's judgment about each kind of work; they have not been A/B tested against the v3.2 facets on real tasks.

## Earlier audit: v3.1-PROD -> v3.2-PROD

Method: read the four live docs, ran the real CLI in throwaway projects, and wrote a failing test for each defect *before* fixing it. Every finding has a repro that failed on v3.1 and passes on v3.2 (`tests/test_v32_evidence_gate.py`). v3.1 baseline: 630 tests passing in 16.3-17.0 s.

Note: older doc comments cite findings F5, F17, F18, F21, F24 from an earlier audit whose file was not shipped. Those numbers are historical. The IDs below (A1...) are this audit's own.

## Defects fixed

| ID | Finding | v3.1 repro | v3.2 |
|---|---|---|---|
| A1 | `--check` set `[x]` without executing the CHECK. The stated invariant "gate settles iff exit 0 and EXPECT matches" was honor-system. | gate `CHECK: false`; `--check id` -> `[x]` | `--check` runs CHECK, refuses on failure |
| A2 | `--run` crashed with `TypeError` on every call (`execute_active_gate()` missing `gate_id`); the working loop below it was unreachable because `kernel` is never None; it also ended in `sys.exit(0)` regardless of results. No CLI test existed. | `--run GATES.md` | `--run` reports all gates, exit 1 on any failure, `--json` supported |
| A3 | `FocusLinter.lint` documented "verification honesty" and implemented glossary count, gate count, `?` on spikes. `--lint` passed `CHECK: true / EXPECT: .*`. | lint a ledger of cheats -> 0 errors | structural analyzer (see references/gates.md) |
| A4 | Only an exact list of ~15 strings was rejected, and only in `--run`'s dead branch. `true && true`, `/bin/true`, `echo "passed"`, `pytest \|\| true` all passed. | see A3 | replaced by shell-structure analysis; false-positive corpus of 20 honest gates |
| A5 | No record that a gate was ever seen failing; the facet taught `EXPECT: FAIL`, which `execute_tracer` can never satisfy (it requires exit 0). Reproduction was inexpressible where settlement is decided. | `ShellOracleAdapter.execute_tracer` on a `FAIL` gate -> False | `--baseline` + hash-chained `*.evidence.jsonl`; red bound to CHECK+EXPECT fingerprint; `--strict` |
| A6 | Generated seeds passed in any repo: `--seed` and ten `-p` archetypes used `git status` / `On branch`; defect fallback was `pytest \|\| npm test \|\| echo 'reproduce'`. `--init` template's gate was `print('PASS_GATE_1')`. | `-p`, `--seed`, `--init` | seeds are red until a named artifact exists; template is a placeholder the linter blocks |
| A7 | `--init .` and `--seed .` wrote to the project root: `basename(".")` starts with `"."` so cwd was treated as the state dir. | `--init .` -> `./GATES.md` | uses `abspath` |
| A8 | SKILL.md: `disable-model-invocation: true` contradicted a description telling the model to invoke it WHENEVER (the model could not). Body was a 150-flag dump with no workflow. | read SKILL.md | flag removed (**revert it if you want user-invoked only**); body is the loop; flags in generated `references/cli.md` |
| A9 | Docs claimed `scripts/gen_cli_docs.py` and `tests/test_loop60_cli_truth.py` exist. Neither shipped. SPEC invariant 1 listed `ssl` as used; BRAINSTORM sold TLS that SPEC says was removed. | `ls` | generator and test now exist; SPEC/BRAINSTORM corrected |

## Open items as of v3.2 (current status is in the v3.3 list above)

- **O1 Suite time.** 671 tests take ~18 s here against SPEC invariant 4 (<= 15 s). No single slow test (slowest 0.66 s); it is ~26 ms x 665, mostly subprocess spawns. Invariant reworded as a reference-hardware target. A parallel runner is the real fix; not done (shared `.focusgate` state and TCP ports risk flakiness).
- **O2 Untrusted ledgers.** CHECK runs with `shell=True`. A cloned repo's `GATES.md` is arbitrary code under `--run/--check/--baseline`. `core/sandbox/command_guard.py` exists but is not applied. Mitigation today is the warning in SKILL.md.
- **O3 Extended layers unreviewed.** Grid/consensus/mesh/etc. pass their own tests; this audit did not review their correctness or load behavior. No TLS or peer auth on the grid.
- **O4 Analyzer is heuristic.** It cannot see inside `./verify.sh` or judge whether a real test asserts anything. Red-before-green narrows the gap, not closes it.
- **O5 Evidence is tamper-evident, not tamper-proof.** Anyone who can write the file can rewrite the whole chain consistently. It detects edits and truncation of history in place; for adversarial settings, anchor the head hash externally (commit it, or print it in CI).
- **O6 `--swarm-wave` still writes `[x]`** from actor receipts (core/cli/dispatch.py) without going through `settle_gate`.
- **O7 Evals are v2.8-era** and cover the original routing/oracles only. v3.2 behavior is covered by unit/CLI tests, not by model-in-the-loop evals.
