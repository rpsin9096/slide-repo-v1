# Facet Contract: codebase-design (v3.3)
Context: Engineering | Mode: Bespoke Deep Module Architecture & Anti-Shallow-Abstraction | Eviction: On Gate Settle

```facet-meta
schema: 1
id: codebase-design
summary: Deep modules behind minimal public seams proven by two adapters
priority: 8
mode: WINDOW
applies_when: ["refactor", "seam", "architecture", "decouple", "deep module", "interface", "adapter", "redesign", "clean up"]
oracle: ["--audit-code-cliche"]
socratic:
  grounding: ["file:line", "CONTEXT.md"]
  stems: ["Name the seam both the caller and the test cross - file:line.", "Which 2 adapters prove {file}?"]
  cap: 2
usability:
  seed: "List the module's public methods; delete or fold one passthrough."
  example: "`LedgerParser.parse(text)->LedgerAST` crossed by CLI + tests; 1 public method, 6 internal rules."
  criterion: "`--audit-code-cliche` clean + >=2 adapters listed."
```

## Invariant Directives
1. DEEP_MODULE: Put behavioral depth behind a small public surface: few public methods, many internal rules, one reason to change.
2. ANTI_SHALLOW_ABSTRACTION: Fold any single-method passthrough or bare `*args, **kwargs` delegation into its caller; indirection without behavior is debt.
3. NO_JUNK_DRAWER_UTILS: Group helpers by domain context; `utils.py`, `helpers.py` and `common.py` are rejected by `--audit-code-cliche`.
4. PUBLIC_SEAM: Name the seam by file:line; callers and tests must cross the same interface, never a private one.
5. TWO_ADAPTERS: A seam is real only with two implementations in the tree, production plus a test fake.
6. FITNESS_RATCHET: Encode each structural rule as a test that fails today and can only get stricter (size caps, import direction, single writer).
7. INTERFACE_CONTRACT: The public interface states its invariants, domain exceptions and return guarantees in one docstring.

## Playbook
### Phases
1. Measure | DO: Rank files and functions by line count and count branches in the largest, and list import edges that point the wrong way. | EXIT: ledger lists the top 5 by `wc -l` with function spans, and each wrong-way edge as `file:line`.
2. Name the seam | DO: Pick one cohesive responsibility inside the largest unit and write its interface in three lines. | EXIT: `file:line` of the proposed interface and the list of callers that will cross it.
3. Deepen | DO: Move behavior behind the interface and delete passthroughs it replaces. | EXIT: public method count is lower than before, `--audit-code-cliche` prints `CODE_CLICHE_AUDIT_PASS`.
4. Prove with two adapters | DO: Add a test fake beside the production implementation and run the same test against both. | EXIT: one test file exercises 2 adapters and `--check <id> --strict` exits 0.
5. Ratchet | DO: Add a fitness test pinning the new boundary (size cap, forbidden import, single writer). | EXIT: the fitness test fails on a deliberate violation and passes on the tree.
### Lazy Tells
- MOVE_NOT_DEEPEN | SAYS: "I split the file into three files" | DETECT: new modules each export one thin function that forwards to another | INSTEAD: move behavior, delete the forwarder, count public methods before and after.
- FAKE_SEAM | SAYS: "it is an interface, one implementation is enough" | DETECT: grep finds exactly 1 implementation of the named seam | INSTEAD: write the test fake or remove the seam.
- UTILS_DUMP | SAYS: "shared helpers go in utils" | DETECT: `--audit-code-cliche` reports a junk drawer | INSTEAD: place each helper in the context that owns its data.
### Gate Templates
```gate
- [ ] seam-ratchet: the extracted module stays within its size cap and imports only inward
  CHECK: python3 -m unittest {fitness_module}
  EXPECT: \nOK
- [ ] no-junk-drawer: touched files carry no shallow-architecture tells
  CHECK: python3 scripts/focus-gate.py --audit-code-cliche {path}
  EXPECT: CODE_CLICHE_AUDIT_PASS
```
### Handoff
- NEXT: unlazy | WHEN: the seam is named and two adapters are specified.
- NEXT: code-review | WHEN: the ratchet test is green and the diff crosses more than one module.
