<!-- ARCHIVED. This document describes FocusGate v2.3 and is SUPERSEDED: superseded by ROADMAP.md, which is the live plan.
     Moved here by FocusGate v3.2 Loop 65 (AUDIT F18). Kept, not deleted, so the
     decision is on the record. Do not implement against it; read SPEC.md,
     ROADMAP.md and SKILL.md instead. -->

# FocusGate v2.3: Strategic Innovation Blueprint
## Technical Architecture for Autonomic, Self-Calibrating & Distributed Agent Operations

**Document Version:** 2.3.0-SPEC  
**Author:** Principal AI Systems Architect & Lead Engine Engineer  
**Status:** Approved Architectural Design  

---

## 1. System Vision & Architecture Paradigm

FocusGate v2.3 transforms the system from a **reactive procedural orchestrator** into an **autonomic cognitive operating system**:
- **From Reactive to Speculative**: Anticipates required facet directives and pre-hydrates working memory prior to handoff.
- **From Linear to Non-Linear**: Coordinates parallel sub-agent swarms across isolated git worktrees via a hierarchical branch DAG.
- **From Passive to Active Ergonomics**: Senses developer cognitive load, hesitation loops, and paralysis without requiring explicit meta-prompts.
- **From Superficial to Proof-Carrying**: Requires multi-criteria proof trees (file diffs, runtime assertions, oracle verdicts) before permitting phase transitions.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        FOCUSGATE v2.3 AUTONOMIC AGENT OS                               │
│                                                                                        │
│   ┌───────────────────────────┐                    ┌───────────────────────────────┐   │
│   │    AUTONOMIC ROUTING      │                    │    SESSION BRANCH DAG         │   │
│   │  • Markov Pre-Hydrator    │                    │  • Non-linear time-travel     │   │
│   │  • Bayesian Self-Tuning   │                    │  • Saga Compensation Engine   │   │
│   └─────────────┬─────────────┘                    └───────────────┬───────────────┘   │
│                 │                                                  │                   │
│                 ▼                                                  ▼                   │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        MICROKERNEL COORDINATION BUS                            │   │
│   │              (Versioned Wire Protocol: FocusGate Transport FGTP/1.0)           │   │
│   └─────────────┬──────────────────────────────────────────────────┬───────────────┘   │
│                 │                                                  │                   │
│                 ▼                                                  ▼                   │
│   ┌───────────────────────────┐                    ┌───────────────────────────────┐   │
│   │  PASSIVE FRICTION SENSOR  │                    │     PROOF-CARRYING TREES      │   │
│   │  • Hesitation & paralysis │                    │  • Observable verification    │   │
│   │  • Cognitive pacing engine│                    │  • Anti-context-drift tracker │   │
│   └───────────────────────────┘                    └───────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Pillar 1: Autonomic Orchestration & Adaptive Routing

### 2.1 Predictive & Speculative Pre-Hydration
To eliminate the synchronous JIT loading latency identified in `DEEPEN_AUDIT.md`, v2.3 introduces the **Markov Predictive Pre-Hydrator**:
- Maintains a lightweight first-order Markov Transition Matrix $P(F_{t+1} \mid F_t, A)$ estimating the probability of transitioning to facet $F_{t+1}$ given current facet $F_t$ and archetype $A$:
  $$P(\text{unlazy} \mid \text{codebase-design}, \text{ARCHITECTURE}) = 0.88$$
  $$P(\text{code-review} \mid \text{unlazy}, \text{DEFECT}) = 0.94$$
- When an active gate is executing in stage $F_t$, the kernel asynchronously pre-loads the top predicted facet directive ($P \ge 0.75$) into an in-memory cache.
- When the active gate resolves, handoff to the next facet completes in **0 milliseconds** cold-start latency.

### 2.2 Self-Calibrating Decision Thresholds
- Instead of fixed confidence numbers, routing confidence is computed via **Bayesian Prior Updating**:
  $$\text{Score}(A \mid Q, H) \propto P(Q \mid A) \cdot P(A \mid H)$$
  where $H$ is the trailing 20-turn session history.
- If the current workspace has been resolving multiple accessibility regressions, $P(\text{DESIGN_AUDIT} \mid H)$ increases, ensuring ambiguous queries like *"Clean up contrast in button"* route accurately without developer intervention.

---

## 3. Pillar 2: Advanced State Engineering & Fault Recovery

### 3.1 Non-Linear Session Traversal (Session Branch DAG)
Replaces the scalar `current_state` with a directed acyclic graph of session checkpoints:

```
                  ┌── [Branch: bugfix/auth-leak] ── Checkpoint ── Verify ──┐
                  │                                                        ▼
[Root: Feature A] ┴──────────────────────────────────────────────────> Rebase & Merge
```

- **Forking**: When an active implementation triggers an unexpected defect, `kernel.fork_session("defect-reproduction")` creates an isolated sub-state without polluting the parent feature context.
- **Rewind**: Instantaneous traversal to any historical node via monotonic snapshot IDs (`snap-001`, `snap-002`).
- **Rebase**: Upon defect resolution, the fix is committed to the main branch and rebased into the parent feature state.

### 3.2 Saga Compensation Coordinator
To prevent partial execution corruption across multi-agent handoffs, all cross-plugin operations implement the **Saga Pattern**:
- Every forward action (`Action_i`) is paired with an explicit compensating transaction (`Compensate_i`).
- Example: If a design token injection succeeds in CSS but component compilation subsequently crashes in TypeScript:
  1. `Action 1`: Inject CSS variables into `tokens.css` (SUCCESS)
  2. `Action 2`: Refactor React component props (FAILURE - syntax error)
  3. `Compensate 1`: Revert `tokens.css` git diff automatically.
- Guarantees transactional consistency across multi-stage handoffs.

---

## 4. Pillar 3: Deep Cognitive Ergonomics & Passive Friction Sensing

### 4.1 Passive Friction & Paralysis Sensing
v2.3 introduces passive behavioral telemetry tracking three core friction vectors:
1. **Prompt Revision Velocity**: User revising and resubmitting prompts within $<10$ seconds with high Levenshtein similarity indicates conceptual hesitation.
2. **Command Abort Frequency**: Terminating agent tool calls repeatedly indicates output mismatch or panic.
3. **Repetitive Error Stalls**: Experiencing $\ge 3$ consecutive test failures on the same gate without progress indicates analysis paralysis.

#### Autonomic Intervention Policy:
When Friction Index $F \ge 0.8$, the engine does NOT interrupt with an alarming dialog. Instead, it adjusts the Action Envelope:
- Injects a single recommended 2-minute physical micro-action into Line 1.
- Automatically isolates the smallest possible sub-seam.
- Invokes `i-have-adhd` scaffolding invisibly in the background.

### 4.2 Contextual Cognitive Pacing
The verbosity and density of FocusGate responses are dynamically modulated based on active momentum:
- **Flow State (High Momentum)**: Minimalist envelope, zero verbose explanations, single-line check verdicts.
- **Ambiguity / High Friction**: Exploded technical context, decision tradeoffs highlighted in bold, single-choice socratic questions.

---

## 5. Pillar 4: Multi-Agent Synthesis, Concurrency & Adversarial Loops

### 5.1 Isolated Git Worktree Swarm Runner
To enable safe concurrent multi-agent execution:
- Every sub-agent invoked via `invoke_subagent` is provisioned an isolated ephemeral git worktree at `.focusgate/worktrees/agent-<id>`.
- Agents execute their acceptance gates in total filesystem isolation.
- Upon successful oracle verification, the worktree is cleanly committed and merged back to the target branch via atomic rebase, or pruned if abandoned.
- Eliminates SQLite writer lock contention by utilizing branch-local append-only event ledgers.

### 5.2 Red Team / Blue Team Adversarial Review Loops
Before implementing high-impact architectural proposals (e.g. `P3: Architecture` or `P7: RFC`):
- **Blue Agent (`codebase-design`)**: Drafts candidate seam interface and invariants.
- **Red Agent (`grilling`)**: Autonomously attacks the proposal, interrogating edge cases, concurrency hazards, and Rule of Two Adapters violations.
- Implementation only proceeds once the proposal survives 3 adversarial interrogation rounds.

---

## 6. Pillar 5: Execution Guarantees & Phased Plan Completion

### 6.1 Durable Phased Plan Tracking
To eradicate long-horizon context drift:
- Plans are represented as first-class, immutable graph entities (`PhasedPlanTracker`).
- Each phase explicitly defines:
  * Input preconditions (prerequisite artifacts).
  * Invariant boundary conditions (what must remain unchanged).
  * Proof-carrying exit criteria (observable evidence).
- Survives context window compaction by injecting an ultra-dense **Plan State Vector** on every turn.

### 6.2 Proof-Carrying Acceptance Trees (`ProofTree`)
Replaces binary exit code checks with multi-criteria proof trees:

```
Gate: Rapid Defect Resolution
├── [x] Criterion 1: Failing Reproduction Command (EXIT != 0 recorded in trace)
├── [x] Criterion 2: Minimal Code Diff Isolated (Diff restricted to target module)
├── [x] Criterion 3: Regression Suite Passes (All 37 unit tests green)
└── [x] Criterion 4: Zero Negative Steering (Domain audit 100/100)
```
A gate CANNOT transition to `CHECKED` without producing physical proof artifacts for all leaf criteria.

---

## 7. Pillar 6: Codebase Hardening & Protocol Standardization

### 7.1 FocusGate Transport Protocol (`FGTP/1.0`)
Standardizes all inter-plugin and inter-agent communication into a versioned JSON-RPC wire format:
```json
{
  "jsonrpc": "2.0",
  "fgtp_version": "1.0",
  "id": "req-9842",
  "method": "plugin.execute_gate",
  "params": {
    "gate_id": "gate-1",
    "facet": "codebase-design",
    "context": { "workspace_root": "/app", "depth": "L2" }
  }
}
```
Enables running plugins out-of-process, in Docker containers, or across remote worker nodes with zero change to the core microkernel logic.

### 7.2 Continuous Synthetic Evals Pipeline
- Automated evaluation runner executing 20 synthetic edge-case variations on every commit.
- Monitors drift in:
  * Reasoning retention rate ($\text{RRR} \ge 98\%$).
  * Behavioral adherence score ($\text{BAS} = 100\%$).
  * Token compression ratio ($\text{TCR} \ge 85\%$).
  * Execution latency ($<10$ms).
