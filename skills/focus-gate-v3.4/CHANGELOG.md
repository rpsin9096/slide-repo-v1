# Changelog

## v3.4-PROD: One Dispatcher
Behavior changes: (1) `--install-guardrails` and `--retro` are gone from `--help`: they were documented and implemented nowhere. (2) `--orchestrate ... --preview --dispatch` exits 2 (they are opposites; `--dispatch` is the default) before touching any state. (3) `--unlazy-rigor` now reports `SWALLOWED_EXCEPTION` for `except:` / `except Exception:` whose body is `pass` or `...`. (4) A CHECK matching a catastrophic pattern (root or home wipe, force push, raw disk write, mkfs, shutdown) is a `DESTRUCTIVE_COMMAND` integrity error and is never executed by `--baseline`, `--run` or `--check`, even with `--force`; scoped deletes such as `rm -rf /tmp/build` are still allowed. (5) `--validate-contracts` works (it raised `NameError` on any non-empty event log).

- **Architecture**: `scripts/focus-gate.py` 2903 -> 25 lines (an entry point); `main()` 1881 -> 90 lines in `core/cli/app.py`. All 124 commands are registry entries (`core/cli/commands/`, 15 modules); the 52 early routes are a table, replacing the 162-line if-chain of `CLIDispatcher.dispatch`. Moved to `core/`: pipeline middleware, intent routing, ledger-root resolution, `ActivationSeed`/`DistractionRecovery`/`SingleItemQueue`, `WritingSuite`, `DomainAuditor`/`ContractValidator`, parser and help text.
- **Dead code removed**: 4 branches of `main()` (`checkpoint`, `restore-checkpoint`, `list-checkpoints`, `adversarial-audit`) that the early dispatcher always pre-empted.
- **Facades removed**: `JITHydrationEngine` and `_lint_facet_contracts` (announced in v3.3); tests use `FacetCatalog`.
- **Fitness tests** (`tests/test_v34_architecture.py`): thin entry, one dispatcher, handlers return codes and never call `sys.exit`, no dead flags, ratchets (script <= 28 lines, `main()` <= 95).
- Fixed on the way: `scripts/evaluate_distillation.py` reached into the CLI script's internals; the swallowed-exception rule is no longer double-reported by `ToolSelectionMatrix`.

## v3.3-PROD: Deep Facets, Thin Seams
Behavior changes: (1) `--swarm-wave` and the autonomous wave loop no longer tick `[x]` from receipts; they call `settle_gate`, so a self-satisfying CHECK is refused and a settled gate has an evidence record. (2) `--settle-spike` exits 1 when no open spike matches (it used to print success). (3) `--lint-facets` now fails facets that lack a playbook. (4) `--status` works (it raised `KeyError` on every ledger in v3.2).

- **Facets**: all 19 rewritten. Rules carry definitions; each facet has a playbook (phases with observable exits, lazy tells with detectors, gate templates validated by the evidence linter, handoff). New `--hydrate-facet <id> --depth directive|playbook|full`.
- **Injected facet text carries rule definitions.** Sub-agent briefs used to receive bare rule titles (`- DEEP_MODULE`).
- **Token ceilings enforced on all 19 facets** (v3.2: 2 of 19; 13 exceeded the declared ceiling when hydrated whole).
- **`FacetCatalog`** (`core/facets/`): one cached, self-invalidating seam for load, route, render, lint, hydrate. `AgentBrief.to_prompt` no longer re-parses every facet per call.
- **Router v2**: whole-word matching with inflections, evidence-weighted ranking; `evals/facet_routing_v33.json` adds positives and near-miss negatives.
- **Briefs** (`core/brief_composer.py`): teach the v3.2 loop (`--baseline`, unchanged CHECK, `--check --strict`); rigor wording tailored per facet context; the engineering block is no longer stamped on writing facets.
- **Command registry** (`core/cli/registry.py`, `core/cli/commands/`): 11 commands out of `main()`; `EmbeddedTemplates`, `PipelineSynthesizer`, `StateSynthesizer`, `FocusLinter` moved to `core/`. `scripts/focus-gate.py` 3879 -> 2903 lines, `main()` 2128 -> 1881; both ratcheted by test.
- **Fitness tests**: only `evidence.py` writes `[x]`; `core/` never imports `scripts/` (one violation fixed); size ratchets.
- Small: `... | head` no longer prints a `BrokenPipeError` traceback; `--list-facets` header no longer says "v2".
- Compatibility: `JITHydrationEngine` and `_lint_facet_contracts` stay importable from the script as thin facades (removed in v3.4).

## v3.2-PROD: Evidence Gate
Behavior change: `--check` now executes the gate. Scripts that relied on `--check` as a bare "mark done" must supply a real CHECK, add `--force`, or use a manual (CHECK-less) gate.
- New `core/gates/evidence.py`: `GateIntegrity`, hash-chained `EvidenceLog`, `settle_gate`, `baseline`, `run_gates`.
- New flags: `--baseline`, `--evidence`, `--strict`, `--force`, `--waive-red`.
- Fixed: `--run` crash and exit code; `--check` never executing; lint teeth; falsifiable seeds and init template; `--init .`/`--seed .` path bug.
- New: `scripts/gen_cli_docs.py`, `references/{cli,gates,architecture}.md`, `AUDIT.md`; SKILL.md rewritten around the loop.
- Tests: 630 -> 671 (41 new). See AUDIT.md for open items.

## v3.1-PROD
Adaptive Swarm Grid & Self-Refining Mesh (loops 39-56). See ROADMAP.md.
