# FocusGate v3.4 Deep Facet Catalogue: 19 Operational Directives & Playbooks

Exhaustive two-tier reference for all 19 FocusGate facets across 5 Bounded Contexts.
Tier 1 defines the **Invariant Directives** injected into subagent briefs.
Tier 2 defines the **Playbook** (Phases, Lazy Tells, Gate Templates, and Handoff).

---

## Context 1: Cognitive Facets

### 1. `unlazy`
- **Context**: Cognitive | **Priority**: 9 | **Mode**: WINDOW
- **Summary**: Completion discipline: gates settle only on real verified evidence without stubs.
- **Triggers**: implement, finish, complete, build, no stubs, to completion, ship it, production ready.
- **Invariant Directives**:
  1. `EVIDENCE_OR_NOT_DONE`: A gate is done only when `--check <id> --strict` exits 0; prose or diff reviews settle nothing.
  2. `RED_BEFORE_GREEN`: Run baseline before editing; keep CHECK and EXPECT unchanged.
  3. `NO_PLACEHOLDERS`: Reject stub comments, empty `pass`, `raise NotImplementedError`, and dummy returns before filesystem write.
  4. `SINGLE_ACTIVE`: Hold one active gate; successors wait in topological order in the frontier buffer.
  5. `FOUR_PASS_LOOP`: Work in 4 passes: complete deliverable, domain elevation, boundary defense, low-cost polish.
- **Playbook**:
  - **Phases**:
    1. Lint the contract | DO: Run `--lint` and fix every error | EXIT: `Lint result: 0 error(s)`.
    2. Baseline | DO: Run baseline before touching code | EXIT: Gate prints `RED`.
    3. Complete deliverable | DO: Implement full behavior with real logic | EXIT: Rigor pass with zero stubs.
    4. Elevate & defend | DO: Add boundary assertions | EXIT: $\ge 3$ boundary assertions verified.
    5. Settle | DO: Run `--check <id> --strict` | EXIT: Gate checked and passed.
  - **Lazy Tells**:
    - `DECLARED_DONE`: Saying "it should work now" without running the check. DETECT: No check output in turn. INSTEAD: Run check and paste output.
    - `STUB_AND_MOVE_ON`: Leaving dummy functions to fill in later. DETECT: Empty returns or pass. INSTEAD: Write complete logic now.
    - `GREEN_BY_WEAKENING`: Weakening check/expect to make it pass. DETECT: Changed fingerprint in evidence log. INSTEAD: Restore check, fix code.
    - `STOP_EARLY`: Stopping when main path works. DETECT: Open gates remaining. INSTEAD: Continue until all gates pass.
  - **Gate Templates**:
    - `CHECK: python3 -m unittest {test_path} && EXPECT: \nOK`
  - **Handoff**: NEXT: `code-review` when diff spans multiple modules; NEXT: `wayfinder` when next ticket is needed.

### 2. `grilling`
- **Context**: Cognitive | **Priority**: 7 | **Mode**: EPHEMERAL
- **Summary**: Socratic stress-testing of gray-area decisions with grounded questions.
- **Triggers**: decide, tradeoff, architecture choice, which option, gray area.
- **Invariant Directives**:
  1. Challenge implicit assumptions, identify failure modes, and quantify hidden trade-offs.
  2. Emit a Micro-ADR in `GATES.md` recording Context, Decision, and Consequences.
- **Playbook**:
  - **Phases**: 1. Frame decision $\to$ 2. Stress-test failure modes $\to$ 3. Record ADR.
  - **Lazy Tells**: `PREMATURE_CONSENSUS`, `UNGROUNDED_PROS_CONS`.
  - **Handoff**: NEXT: `codebase-design` or `prototype`.

### 3. `i-have-adhd`
- **Context**: Cognitive | **Priority**: 8 | **Mode**: WINDOW
- **Summary**: Working memory protection via high-density scannable envelope.
- **Triggers**: adhd, focus, overwhelmed, dense, short, concise.
- **Invariant Directives**: Action Envelope compliance, $\le 3$ body items, collapsible `<details>`, $<2\text{ min}$ next action.
- **Playbook**:
  - **Phases**: 1. Envelope synthesis $\to$ 2. High-density execution $\to$ 3. Micro-next action.
  - **Lazy Tells**: `WALL_OF_TEXT`, `UNFOCUSED_RABBIT_HOLE`.
  - **Handoff**: NEXT: active gate facet.

### 4. `loop-me`
- **Context**: Cognitive | **Priority**: 8 | **Mode**: WINDOW
- **Summary**: Recurring toil automation with Push-Right human checkpoints.
- **Triggers**: automate, recurring, toil, workflow loop.
- **Invariant Directives**: Automate deterministic 90%; push human approval to the boundary.
- **Playbook**:
  - **Phases**: 1. Identify toil pattern $\to$ 2. Script runner $\to$ 3. Insert human checkpoint.
  - **Lazy Tells**: `UNPROTECTED_AUTONOMY`, `MANUAL_REPETITION`.
  - **Handoff**: NEXT: `unlazy`.

---

## Context 2: Engineering Facets

### 5. `diagnosing-bugs`
- **Context**: Engineering | **Priority**: 10 | **Mode**: WINDOW
- **Summary**: Reproduce-first differential diagnosis with falsifiable hypotheses.
- **Triggers**: bug, error, fail, broken, crash, segfault, regression.
- **Invariant Directives**: Reproduce failure (`RED`) before editing; minimal reproducer; root cause proof; atomic patch; regression guard.
- **Playbook**:
  - **Phases**: 1. Isolate symptom $\to$ 2. Formulate hypothesis $\to$ 3. Prove root cause $\to$ 4. Patch $\to$ 5. Guard.
  - **Lazy Tells**: `PATCH_WITHOUT_REPRO`, `SHOTGUN_FIX`.
  - **Gate Templates**: `CHECK: python3 -m pytest tests/test_regression.py && EXPECT: 1 passed`
  - **Handoff**: NEXT: `code-review`.

### 6. `codebase-design`
- **Context**: Engineering | **Priority**: 8 | **Mode**: WINDOW
- **Summary**: Deep modules behind minimal public seams proven by two adapters.
- **Triggers**: refactor, module architecture, decouple, clean code.
- **Invariant Directives**: Deep modules; $\ge 2$ adapters; zero junk drawers.
- **Playbook**:
  - **Phases**: 1. Identify public seam $\to$ 2. Build 2 adapters $\to$ 3. Eliminate junk drawers.
  - **Lazy Tells**: `PASSTHROUGH_FACADE`, `JUNK_DRAWER_CONSOLIDATION`.
  - **Handoff**: NEXT: `unlazy`.

### 7. `code-review`
- **Context**: Engineering | **Priority**: 7 | **Mode**: WINDOW
- **Summary**: Dual-axis review with schema-bound findings and severity gate.
- **Triggers**: review, pr, diff, code smell, audit.
- **Invariant Directives**: Standards axis + Spec axis; prescriptive severity ratings (`CRITICAL`, `WARNING`, `NIT`).
- **Playbook**:
  - **Phases**: 1. Standards axis scan $\to$ 2. Spec axis invariant audit $\to$ 3. Report findings with diff remedies.
  - **Lazy Tells**: `SUPERFICIAL_RUBBER_STAMP`, `NITPICK_AVOIDANCE`.
  - **Handoff**: NEXT: `unlazy` (for remediation).

### 8. `prototype`
- **Context**: Engineering | **Priority**: 7 | **Mode**: WINDOW
- **Summary**: Disposable vertical slice spikes in vanilla HTML/JS/Python.
- **Triggers**: spike, prototype, poc, experiment.
- **Invariant Directives**: Single-file model; domain logic isolated from UI; answers one explicit question.
- **Playbook**:
  - **Phases**: 1. Scaffold spike $\to$ 2. Run logic test $\to$ 3. Settle question.
  - **Lazy Tells**: `PRODUCTION_PREMATURE_COMPLEXITY`.
  - **Handoff**: NEXT: `codebase-design`.

---

## Context 3: Design Facets

### 9. `focus-design`
- **Context**: Design | **Priority**: 7 | **Mode**: WINDOW
- **Summary**: Audit and repair visual delivery via pure oracles.
- **Triggers**: styling, theme, design audit, visual review.
- **Invariant Directives**: Eliminate hardcoded hex/RGB; verify token allowlists; WCAG AA contrast.
- **Playbook**:
  - **Phases**: 1. Token scan $\to$ 2. Contrast evaluation $\to$ 3. Patch stylesheets.
  - **Lazy Tells**: `HARDCODED_HEX_SPRAY`.
  - **Handoff**: NEXT: `ui-ux-pro-max`.

### 10. `frontend-design`
- **Context**: Design | **Priority**: 8 | **Mode**: WINDOW
- **Summary**: Bespoke visual identity with anti-cliché two-pass workflow.
- **Triggers**: bespoke, custom ui, visual identity, landing page.
- **Invariant Directives**: Pass 1 palette grounded in domain; Pass 2 responsive CSS and micro-interactions.
- **Playbook**:
  - **Phases**: 1. Aesthetic thesis $\to$ 2. Token derivation $\to$ 3. Production styles.
  - **Lazy Tells**: `GENERIC_INDIGO_GRADIENT`, `TEMPLATE_BORROWING`.
  - **Handoff**: NEXT: `design-tokens`.

### 11. `design-tokens`
- **Context**: Design | **Priority**: 6 | **Mode**: WINDOW
- **Summary**: 3-layer token governance (Primitive $\to$ Semantic $\to$ Component).
- **Triggers**: design tokens, css variables, design system.
- **Invariant Directives**: 3-layer governance; component styles bind only to semantic tokens.
- **Playbook**:
  - **Phases**: 1. Primitive tokens $\to$ 2. Semantic aliases $\to$ 3. Component binding.
  - **Lazy Tells**: `TOKEN_LEAKAGE`, `PRIMITIVE_BYPASS`.
  - **Handoff**: NEXT: `ui-ux-pro-max`.

### 12. `banner-safe-zone`
- **Context**: Design | **Priority**: 6 | **Mode**: WINDOW
- **Summary**: Central 70% safe-zone validation across standard aspect ratios.
- **Triggers**: banner, hero, social card, open graph.
- **Invariant Directives**: 15% margin envelope $[0.15, 0.85]$ across platforms (16:9, 9:16, 1:1, 4:5, 3:2).
- **Playbook**:
  - **Phases**: 1. Aspect check $\to$ 2. Bounding box audit $\to$ 3. Adjustment.
  - **Lazy Tells**: `EDGE_BLEED_CONTENT`.
  - **Handoff**: NEXT: `focus-design`.

### 13. `ui-ux-pro-max`
- **Context**: Design | **Priority**: 8 | **Mode**: WINDOW
- **Summary**: Interactive-state completeness and WCAG AA accessibility.
- **Triggers**: ui component, accessible, interactive states.
- **Invariant Directives**: Complete states (default, hover, focus-visible, active, disabled, loading); $\ge 4.5:1$ contrast.
- **Playbook**:
  - **Phases**: 1. State matrix mapping $\to$ 2. Accessibility audit $\to$ 3. Polish.
  - **Lazy Tells**: `MISSING_FOCUS_OUTLINE`, `DISABLED_CONTRAST_FAIL`.
  - **Handoff**: NEXT: `code-review`.

---

## Context 4: Writing Facets

### 14. `writing-beats`
- **Context**: Writing | **Priority**: 7 | **Mode**: WINDOW
- **Summary**: Structured narrative pacing with sharp thematic checkpoints.
- **Triggers**: tutorial, guide, story, explanation, article.
- **Invariant Directives**: Modular pacing, progressive disclosure, zero throat-clearing.
- **Playbook**:
  - **Phases**: 1. Beat outline $\to$ 2. Prose draft $\to$ 3. Anti-cliché sieve.
  - **Lazy Tells**: `REPETITIVE_PREAMBLE`, `PASSIVE_VOICE_SWARM`.
  - **Handoff**: NEXT: `code-review`.

### 15. `writing-for-agents`
- **Context**: Writing | **Priority**: 8 | **Mode**: WINDOW
- **Summary**: Machine-readable protocols and bounded briefs for subagents.
- **Triggers**: subagent, brief, machine-readable, schema.
- **Invariant Directives**: Briefs $\le 400$ tokens; unambiguous input/output schemas; testable criteria.
- **Playbook**:
  - **Phases**: 1. Scope definition $\to$ 2. Interface contract $\to$ 3. Acceptance gate.
  - **Lazy Tells**: `NAKED_POINTER_REFERENCE`, `UNBOUNDED_BRIEF`.
  - **Handoff**: NEXT: subagent execution.

### 16. `writing-shape`
- **Context**: Writing | **Priority**: 8 | **Mode**: WINDOW
- **Summary**: Concept-grounded technical spec shaping from raw fragments.
- **Triggers**: rfc, spec, architecture proposal.
- **Invariant Directives**: Grounded thesis, prerequisite definitions, explicit boundary contracts.
- **Playbook**:
  - **Phases**: 1. Mine fragments $\to$ 2. Structure RFC $\to$ 3. Define invariants.
  - **Lazy Tells**: `JARGON_INFLATION`, `SPEC_DRIFT`.
  - **Handoff**: NEXT: `prototype`.

### 17. `writing-fragments`
- **Context**: Writing | **Priority**: 6 | **Mode**: WINDOW
- **Summary**: Mining unstructured thoughts into load-bearing leading concepts.
- **Triggers**: brainstorm, raw thoughts, ideas, fragments.
- **Invariant Directives**: Ingest stream-of-consciousness into `FRAGMENTS.md` with persistent synchronization.
- **Playbook**:
  - **Phases**: 1. Ingest raw notes $\to$ 2. Identify load-bearing terms $\to$ 3. Sync to disk.
  - **Lazy Tells**: `PREMATURE_STRUCTURING`.
  - **Handoff**: NEXT: `writing-shape`.

---

## Context 5: Navigation Facets

### 18. `triage`
- **Context**: Navigation | **Priority**: 7 | **Mode**: WINDOW
- **Summary**: Rapid classification of defects, stack traces, and failure modes.
- **Triggers**: triage, incoming issue, error log, crash report.
- **Invariant Directives**: Fast classification of blast radius, environment repro, routing to specialized pipeline.
- **Playbook**:
  - **Phases**: 1. Categorize error $\to$ 2. Determine blast radius $\to$ 3. Route to pipeline.
  - **Lazy Tells**: `CONFIDENT_MISDIAGNOSIS`.
  - **Handoff**: NEXT: `diagnosing-bugs`.

### 19. `wayfinder`
- **Context**: Navigation | **Priority**: 6 | **Mode**: WINDOW
- **Summary**: Strategic navigation through ambiguous or large codebases.
- **Triggers**: explore, codebase map, lost in code, where do I start.
- **Invariant Directives**: High-level module mapping; charting unblocked DAG frontier paths.
- **Playbook**:
  - **Phases**: 1. Directory census $\to$ 2. Dependency tracing $\to$ 3. Frontier queue synthesis.
  - **Lazy Tells**: `RABBIT_HOLE_DRIFT`.
  - **Handoff**: NEXT: active gate facet.
