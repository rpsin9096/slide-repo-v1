# Architecture and maturity

## Core (used by the loop in SKILL.md)
`scripts/focus-gate.py` (CLI), `core/gates/` (ledger parser, TracerGate, **evidence.py**), `adapters/oracle_adapter.py` (runs CHECK), `core/unlazy_guard.py` (stub/empty-suite rigor), `core/facet_router.py` + `facets/` (routing and directives), `core/oracles/` (anti-cliche audits). This is what the 41 v3.2 regression tests and the CLI tests exercise end to end.

## Extended layers (loops 23-56)
Actor mesh, worktree sagas, Merkle ledger and CRDT sync, Byzantine quorum, TCP grid, binary wire protocol, speculative scheduler, persona synthesis, episodic memory, AST self-repair, heartbeat watchdog, chaos simulators.

Status as established by the v3.2 audit, stated narrowly:
- Each has unit tests that pass (the suite is 671 tests).
- None is on the path of the loop in SKILL.md. Starting the CLI loads ~9 mesh modules (about 165 ms), so cost is not the issue; surface area is. An agent should not need them to do evidence-gated work.
- `core/grid/` uses plain TCP. There is **no TLS** and no peer authentication. Do not expose a grid node beyond localhost.
- The audit did **not** review these layers for correctness beyond their own tests, nor measure them under real multi-host load. Treat them as experimental until someone does.

## Decision recorded
v3.2 deliberately does not delete the extended layers (they are tested and may be wanted). It removes them from the agent-facing surface: SKILL.md teaches the core loop, and the layers are documented here. Revisit if they remain unused.

## v3.3 structure (what changed, where to look)

| Concern | Module | Notes |
|---|---|---|
| Settlement | `core/gates/evidence.py` | only writer of `[x]`; `settle_gate`, `settle_spike` |
| Facet load / route / render / lint | `core/facets/catalog.py` | cached, self-invalidating; the one seam |
| Facet body grammar | `core/facets/playbook.py` | directives + playbook parser, `PlaybookError(code, line)` |
| Facet contract + injected render | `core/facet_contract.py` | `render_compact` emits rules with definitions |
| Routing | `core/facet_router.py` | whole-word + inflection match, evidence-weighted rank |
| Brief sections that depend on the facet | `core/brief_composer.py` | rules, tailored rigor, fallback, Evidence Protocol |
| CLI commands | `core/cli/registry.py`, `core/cli/commands/*.py` | `@command`; handlers return exit codes; modules never import siblings |
| Ledger views | `core/gates/views.py` | header and lint report |

Layering rule, tested: `core/` never imports `scripts/`.

## v3.4 structure: one dispatcher

```
scripts/focus-gate.py          25 lines: make core importable, run main
  core/cli/app.py              main(): parse, build ctx, REGISTRY.resolve(ctx), run one handler
    core/cli/registry.py       Command, CommandContext, REGISTRY; resolve in (order, registration) sequence
    core/cli/commands/*.py     124 handlers: handler(ctx) -> exit code; modules never import siblings
      distributed.py           52 early routes (early=True: run before event store / kernel exist)
      orchestration, history, verification, writing, audits, economy, focus, spikes, swarm_ops
      facets, routing, evidence, ledger_views, scaffold   (v3.3)
    core/cli/dispatch.py       CLIDispatcher.dispatch_* implementations (1553 lines; dispatch() is a registry lookup)
    core/cli/{parser,pipeline,intent,paths,documents}.py
```

Adding a command: write `def handler(ctx) -> int` in the module of its domain and decorate it with
`@command(name, flags=(...), dest=None, summary=..., matches=<predicate or None>, order=...)`.
Order: early routes 0-99, flag commands 100, the former `main()` chain 200+. Handlers return exit codes
and never call `sys.exit` (tested). Ratchets in `tests/test_v34_architecture.py` only go down.

