# Writing a facet (v3.3)

A facet is the process for one kind of work. It has two tiers so depth does not
cost context: the **rules** are injected into sub-agent briefs under a token
ceiling; the **playbook** is loaded on demand (`--hydrate-facet <id> --depth playbook`).

```
facets/<context>/<id>.md
  # Facet Contract: <id> (v3.3)
  Context: ... | Mode: WINDOW|EPHEMERAL | Eviction: ...
  ```facet-meta ... ```            (id, priority, applies_when, never_when, oracle, seed, ...)
  ## Invariant Directives          tier 1
  ## Playbook                      tier 2
```

## Tier 1: rules

`N. NAME: definition.` One sentence; the operative clause comes first, because the
injected render clips each rule at the first sentence break (110, then 70, then 44
characters) and drops trailing rules before it drops the front ones. **Order rules
most-critical-first.** A definition under 8 words is `THIN_DIRECTIVE`: a label is not a rule.

Injected ceiling: 400 tokens (WINDOW), 150 (EPHEMERAL), at least 3 rules visible.
Whole file: at most 1500 tokens (`OVER_BUDGET` for either).

## Tier 2: playbook

One record per line, fields separated by ` | `.

```
### Phases
1. Reproduce | DO: Run the failing command. | EXIT: exit code 1 on 3 of 3 runs, zero files modified.
### Lazy Tells
- SYMPTOM_PATCH | SAYS: "wrap it in try/except" | DETECT: diff adds `except` and no test names the input | INSTEAD: reproduce the input as a CHECK first.
### Gate Templates
```gate
- [ ] bug-repro: the failing input now returns the specified value
  CHECK: python3 -m unittest {module}.{test}
  EXPECT: \nOK
```
### Handoff
- NEXT: code-review | WHEN: the fix touches more than one module.
```

- **Phase EXIT must be observable**: a backticked command, an exit code, a count, a file path. `UNOBSERVABLE_EXIT` if it names nothing a command could show.
- **Lazy tell** = the shortcut in the lazy agent's own words (`SAYS`), how to catch it (`DETECT`, observable), and the counter-move (`INSTEAD`).
- **Gate templates** use `{placeholders}` and are run through the same `GateIntegrity` analyzer as real gates, so a facet cannot teach `echo ok` or `; echo DONE` as a CHECK.
- **Handoff** names an existing facet and the condition that triggers it.

## Lint codes (`--lint-facets`)

| Code | Meaning |
|---|---|
| `CONTRACT_INVALID`, `DUPLICATE_ID` | facet-meta does not parse, or two files claim one id |
| `NO_PLAYBOOK` | no `## Playbook` section |
| `FEW_PHASES` | fewer than 3 phases |
| `PHASE_NO_DO`, `PHASE_NO_EXIT` | phase missing a field (reported with its line number) |
| `UNOBSERVABLE_EXIT` | EXIT names nothing a command or file can show |
| `FEW_TELLS` | fewer than 2 lazy tells |
| `TELL_BAD_ID`, `TELL_NO_SAYS`, `TELL_NO_DETECT`, `TELL_NO_INSTEAD` | malformed lazy tell |
| `NO_GATE_TEMPLATE`, `TEMPLATE_BAD` | no gate template, or one without CHECK/EXPECT |
| `TEMPLATE_DISHONEST` | a template fails `GateIntegrity` (self-satisfying, masked exit, vacuous EXPECT) |
| `NO_HANDOFF`, `HANDOFF_BAD`, `DANGLING_HANDOFF` | missing handoff, bad syntax, or NEXT is not a facet |
| `THIN_DIRECTIVE` | a rule definition under 8 words |
| `OVER_BUDGET` | file over 1500 tokens, or fewer than 3 rules fit the injected ceiling |
| `VAGUE_PHRASE` | text that constrains nothing ("best practice", "leverage", "where possible") |

After editing, run `python3 scripts/compile_facets.py` (regenerates `facet_index.json`),
then `--lint-facets`. Routing changes need a case in `evals/facet_routing_v33.json`, with a
`must_exclude` entry for the near-miss word.
