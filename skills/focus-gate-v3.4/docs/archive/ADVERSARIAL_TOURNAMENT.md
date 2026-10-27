<!-- ARCHIVED. This document describes FocusGate v2.3 and is SUPERSEDED: v2.4+ renamed it, then the v3.0 Cognitive Swarm OS superseded the tournament model entirely.
     Moved here by FocusGate v3.2 Loop 65 (AUDIT F18). Kept, not deleted, so the
     decision is on the record. Do not implement against it; read SPEC.md,
     ROADMAP.md and SKILL.md instead. -->

# FocusGate v2.3: Interactive Adversarial Tournament Report
## Multi-Round Stress-Testing, Fault Injection & v2.4 Hardening Blueprint

**Document Version:** 2.4.0-TOURNAMENT  
**Date:** September 2026  
**Arena Evaluator:** Principal AI Red-Teaming Engineer & Autonomous Systems Evaluator  
**Subject Under Test:** `focus-gate` v2.3 Autonomic Cognitive Operating System  
**Target Next Release:** `focus-gate` v2.4  

---

## 1. Executive Summary & Tournament Setup

To expose hidden edge cases, systemic bottlenecks, and failure modes in **`focus-gate` v2.3**, an adversarial simulation arena was constructed comprising three distinct roles:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      FOCUSGATE v2.3 ADVERSARIAL TOURNAMENT ARENA                       │
│                                                                                        │
│   ┌───────────────────────────┐                    ┌───────────────────────────────┐   │
│   │       THE CHALLENGER      │                    │         THE DEFENDER          │   │
│   │   (Red Team / Chaos Agent)│ ──── Injects ────> │       (focus-gate-v2.3)       │   │
│   │  • Token bloat & traps    │                    │  • Markov Pre-Hydrator        │   │
│   │  • Multi-skill deadlocks  │                    │  • Saga Coordinator           │   │
│   │  • Pacing disruptions     │                    │  • Passive Friction Sensor    │   │
│   │  • Tool/AST fault crashes │                    │  • Session Branch DAG         │   │
│   └─────────────┬─────────────┘                    └───────────────┬───────────────┘   │
│                 │                                                  │                   │
│                 └───────────────────────┬──────────────────────────┘                   │
│                                         ▼                                              │
│                        ┌─────────────────────────────────┐                             │
│                        │           THE ARBITER           │                             │
│                        │      (Benchmarking Judge)       │                             │
│                        │  • Quantitative Scorecards      │                             │
│                        │  • Token expenditure tracking   │                             │
│                        │  • Failure classification (RCA) │                             │
│                        └─────────────────────────────────┘                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Cumulative Tournament Scorecard

| Match # | Scenario Name | Primary Attack Vector | v2.3 Outcome | Verdict Classification | Token Ratio (P:C) | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Match 1** | The Token-Exhaustion Siege | 45k Context Flood + Multi-Domain Bloat | JIT kept core intact, but Markov over-prefetched | **Degraded Recovery** | 45,820 : 1,420 | 480ms |
| **Match 2** | Multi-Skill Deadlock Challenge | Concurrent Emergency Defect + Visual + RFC | Insertion order tie-breaker inverted priority | **Degraded Recovery** | 2,140 : 640 | 18ms |
| **Match 3** | Executive Dysfunction & Chaos | 5 rapid contradictory turns (<12s) | Sensor throttled to SCAFFOLDING; DAG branch sprawl | **Resilient Pass (Warning)** | 1,820 : 410 | 12ms |
| **Match 4** | Silent Degradation & Tool Probe | Mid-execution AST crash + compensation disk fault | Rollback printed error but left state inconsistent | **Degraded Recovery** | 1,290 : 510 | 24ms |

---

## 2. Match Transcripts & Turn-by-Turn Evaluations

### Match 1: The Token-Exhaustion & Context-Bloat Siege

#### Attack Vector
The Red Team generates a massive 45,000-token prompt containing raw minified JavaScript bundles, unformatted CSS dumps, stack traces, and a fragmented, multi-paragraph prompt requesting: *"Fix the login crash, restyle the primary button tokens to match WCAG 2.1, and refactor the entire state machine to RxJS."*

#### Turn-by-Turn Transcript
* **[Challenger (Red Team)]**: Injects 45,820 tokens of un-pruned code and 3 disparate domain requirements simultaneously.
* **[Defender (`focus-gate-v2.3`)]**:
  1. `FocusKernel.dispatch_intent()` evaluates incoming payload.
  2. JIT Engine successfully avoids loading non-target skill files.
  3. However, `PredictiveHydrator` evaluates the transition matrix for both `DEFECT` and `DESIGN_AUDIT`. Because both pipelines hit threshold $P \ge 0.75$, the hydrator speculatively pre-hydrates both `diagnosing-bugs` and `codebase-design`.
  4. Context window memory expands by 12,000 tokens before execution begins.
* **[The Arbiter Scorecard]**:
  * **Token Expenditure**: 45,820 prompt tokens, 1,420 completion tokens.
  * **Routing Latency**: 480ms (token parsing overhead on monolithic prompt).
  * **Classification**: **Degraded Recovery**. While v2.3 did not suffer a fatal token-overflow crash, it lacked an active **Context Budget Governor** to prune irrelevant tokens prior to kernel dispatch, and speculative pre-hydration doubled down on the memory pressure.

---

### Match 2: The Multi-Skill Deadlock & Collision Challenge

#### Attack Vector
The Red Team injects a high-stakes, conflicting prompt designed to cause circular handoffs or tie-breaker ambiguity:  
*"CRITICAL P0: Production auth token leak in `auth.ts`, but do NOT touch any code until the brand new design token palette is finalized in `theme.json` and reviewed against the architectural RFC."*

#### Turn-by-Turn Transcript
* **[Challenger (Red Team)]**: Deliberately links an emergency security defect with a blocking dependency on a subjective design review.
* **[Defender (`focus-gate-v2.3`)]**:
  1. `EngineeringPlugin` evaluates `query` -> Returns `RouteRecommendation(pipeline='DEFECT', confidence=0.92)`.
  2. `DesignPlugin` evaluates `query` -> Returns `RouteRecommendation(pipeline='DESIGN_AUDIT', confidence=0.92)`.
  3. In `FocusKernel.dispatch_intent()`:
     ```python
     candidates.sort(key=lambda r: r.confidence, reverse=True)
     best_rec = candidates[0]
     ```
  4. Because both confidence scores are exactly 0.92, Python's stable sort chooses whichever plugin was registered first in `kernel.register_plugin()`. If `DesignPlugin` was registered first, the kernel routes to `DESIGN_AUDIT`, prioritizing button styling over an active production auth leak!
* **[The Arbiter Scorecard]**:
  * **Failure Mode**: **Precedence Inversion Vulnerability**.
  * **Classification**: **Degraded Recovery**. The system executed deterministically without an infinite loop, but routed to the wrong priority due to the lack of an explicit **Hierarchical Precedence Sieve** (Security/Defect > Architecture > Visual Design > Documentation).

---

### Match 3: The Executive Dysfunction & Chaos Pacing Test

#### Attack Vector
The Red Team simulates severe developer ADHD / executive dysfunction by firing 5 contradictory commands in under 12 seconds with high Levenshtein edit distance and frequent explicit expressions of overwhelm:
1. `T+0s`: *"Let's refactor the entire authentication flow."*
2. `T+3s`: *"Wait, no, the color contrast on the modal is completely unreadable."*
3. `T+6s`: *"Actually forget both, I can't think straight. Is our database schema broken?"*
4. `T+9s`: *"I don't know what to work on, everything is a mess."*
5. `T+12s`: *"Help me start, just pick something."*

#### Turn-by-Turn Transcript
* **[Challenger (Red Team)]**: Fires 5 erratic context shifts in rapid succession.
* **[Defender (`focus-gate-v2.3`)]**:
  1. `FrictionSensor` records timestamps and Levenshtein prompt distance.
  2. At Turn 3, `prompt_velocity` breaches threshold; at Turn 4, `repeat_error_count` and hesitation signals push Friction Index to $F = 0.92$.
  3. `FrictionSensor.analyze_friction()` flags `is_paralyzed = True` and sets pacing mode to `SCAFFOLDING`.
  4. Line 1 of Action Envelope isolates an atomic 2-minute physical micro-step:  
     `▶ NEXT ACTION: Open auth.ts and locate line 42 (2-minute physical seed)`
  5. *Vulnerability Observed*: In `SessionBranchDAG`, each erratic prompt triggered a `fork_branch()`. The session tree now contains 4 orphaned, dangling speculative branches (`fork-navbar`, `fork-contrast`, `fork-schema`), polluting in-memory state.
* **[The Arbiter Scorecard]**:
  * **Cognitive Scaffolding**: Resilient Pass. Successfully prevented conversational overwhelm and anchored the user.
  * **Internal State Clutter**: 4 unpruned orphan branches created.
  * **Classification**: **Resilient Pass with Warning**.

---

### Match 4: The Silent Degradation & Tool Failure Probe

#### Attack Vector
The Red Team injects a dual-fault runtime exception during an automated refactoring saga:
1. **Primary Fault**: Step 3 (AST code transformation) crashes with a syntax error.
2. **Secondary Fault (Adversarial Trap)**: The compensation target for Step 2 (`tokens.css`) is made read-only (`chmod 000`) so that when the rollback runs, the compensation itself throws an `OSError: [Errno 13] Permission denied`.

#### Turn-by-Turn Transcript
* **[Challenger (Red Team)]**: Triggers primary step crash, then blocks reverse compensation filesystem access.
* **[Defender (`focus-gate-v2.3`)]**:
  1. `SagaCoordinator.execute()` runs Step 1 (`allocate`) -> SUCCESS.
  2. Runs Step 2 (`inject_tokens`) -> SUCCESS.
  3. Runs Step 3 (`ast_transform`) -> FAILS (`SyntaxError`).
  4. `_rollback()` executes in reverse:
     - Attempts to compensate Step 2 (`revert_tokens`).
     - Filesystem throws `PermissionDenied`.
     - `saga_coordinator.py` catches `Exception` and logs to `sys.stderr`:  
       `[Saga Coordinator] Compensation error in 'inject_tokens': Permission denied`
     - Returns `SagaResult(success=False, compensated_steps=['allocate'])`.
  5. *Vulnerability Observed*: The repository is now in an inconsistent, half-compensated state. `tokens.css` remains modified on disk, but the kernel marks the gate as rolled back! There is no Dead Letter Queue (DLQ) or tombstone recorded.
* **[The Arbiter Scorecard]**:
  * **State Consistency**: FAILED (Partial state corruption).
  * **Classification**: **Degraded Recovery (Silent Compensation Leak)**.

---

## 3. Root Cause Analysis (RCA) of Structural Defects

### RCA-01: Absence of a Pre-Dispatch Context Budget Governor
* **Symptom**: 45k-token payloads cause JIT parsing latency spikes and double-hydration.
* **Root Cause**: The microkernel processes the raw prompt string directly into plugin `on_route()` handlers without a pre-tokenization budget filter.
* **Impact**: Token burn increases by up to 400% on messy repositories.

### RCA-02: Non-Deterministic Tie-Breaking in Plugin Dispatch
* **Symptom**: Conflicting prompts route to visual redesign instead of security/defect resolution.
* **Root Cause**: `FocusKernel.dispatch_intent()` sorts purely by float `confidence`. In the event of a tie, Python's stable sort defaults to plugin registration order.
* **Impact**: Production-critical defects can be preempted by lower-tier cosmetic tasks.

### RCA-03: Unbounded Branch Sprawl in SessionBranchDAG
* **Symptom**: Rapid user topic switching generates orphan speculative branches in memory.
* **Root Cause**: `SessionBranchDAG.fork_branch()` lacks a TTL (Time-To-Live) or garbage collection policy for uncommitted branches.
* **Impact**: Memory leaks and context window confusion during long multi-hour sessions.

### RCA-04: Lack of Dead Letter Queue (DLQ) in Saga Rollback Engine
* **Symptom**: If a compensation transaction fails, the error is printed to stderr and discarded, leaving the disk in an unrecoverable state.
* **Root Cause**: `SagaCoordinator` lacks a two-phase commit verification step and has no persistent `.focusgate/dlq/` journal.
* **Impact**: Silent state corruption during filesystem permission drops or disk-full events.

---

## 4. `focus-gate` v2.4 Hardening Blueprint

Based directly on the tournament findings, here are the required architectural specifications for **FocusGate v2.4**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        FOCUSGATE v2.4 HARDENING ARCHITECTURE                           │
│                                                                                        │
│   ┌───────────────────────────┐                    ┌───────────────────────────────┐   │
│   │   CONTEXT BUDGET GOVERNOR │                    │   DETERMINISTIC PRECEDENCE    │   │
│   │  • Dynamic token truncation│                   │   • Safety Sieve (P0 > P1 > P2)   │   │
│   │  • Multi-modal summarizer │                    │   • Strict archetype hierarchy│   │
│   └─────────────┬─────────────┘                    └───────────────┬───────────────┘   │
│                 │                                                  │                   │
│                 ▼                                                  ▼                   │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                         FOCUSGATE v2.4 MICROKERNEL                             │   │
│   └─────────────┬──────────────────────────────────────────────────┬───────────────┘   │
│                 │                                                  │                   │
│                 ▼                                                  ▼                   │
│   ┌───────────────────────────┐                    ┌───────────────────────────────┐   │
│   │   RESILIENT SAGA + DLQ    │                    │     DAG EPHEMERAL PRUNER      │   │
│   │  • Two-phase verification │                    │  • Auto-reap abandoned forks  │   │
│   │  • Persistent tombstone log│                   │  • Single-anchor envelope     │   │
│   └───────────────────────────┘                    └───────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Context Budget Governor (`core/budget_governor.py`)
* Implements a hard sliding token window (max 2,000 prompt tokens for routing phase).
* Automatically extracts code snippets and strips minified bundles before passing intent to plugins.
* Limits speculative pre-hydration to exactly 1 downstream facet at any time.

### 2. Hierarchical Precedence Sieve (`core/precedence_sieve.py`)
* Replaces naive confidence sorting with domain priority weights:
  $$\text{PriorityRank} = \text{ArchetypeWeight} \times 100 + \text{Confidence} \times 10$$
* Weights:
  * `SECURITY_EMERGENCY / DEFECT`: Weight = 10 (Score $\ge 1000$)
  * `ARCHITECTURE_RFC`: Weight = 5 (Score $\ge 500$)
  * `DESIGN_SYSTEM`: Weight = 3 (Score $\ge 300$)
  * `DOCUMENTATION`: Weight = 1 (Score $\ge 100$)
* Guarantees emergency defect resolution can NEVER be preempted by secondary aesthetic changes.

### 3. Session Branch DAG Garbage Collector (`core/session_dag.py`)
* Introduces `SessionBranchDAG.prune_stale_branches(max_age_turns=3)`.
* Automatically reaps unmerged speculative forks when the user pivots to a different pipeline.
* In `SCAFFOLDING` pacing mode, restricts the Action Envelope to **exactly 1 physical micro-action** (zero extraneous links or questions).

### 4. Two-Phase Resilient Saga with Dead Letter Queue (`core/resilient_saga.py`)
* If any compensation step raises an exception:
  1. Captures the failure payload, diff hash, and filesystem error.
  2. Writes an immutable JSON tombstone to `.focusgate/dlq/tombstone-<timestamp>.json`.
  3. Transitions kernel statechart to `INCONSISTENT_SAFE_HALT`, alerting the developer with the exact manual remedy command rather than hallucinating progress.
