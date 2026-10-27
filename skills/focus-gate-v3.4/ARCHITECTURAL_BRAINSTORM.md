# FocusGate v3.1 (historical RFC; see AUDIT.md for v3.2): Architectural Brainstorm & Engineering RFC
## The Transition from Cognitive Swarm OS to Self-Refining Swarm Grid

### 1. The Architectural Inflection Point
In FocusGate v3.0, we achieved a complete, production-grade **Autonomous Distributed Cognitive Swarm OS**:
- In-process actor message routing and priority mailboxes.
- Merkle state vector synchronization and vector clocks.
- Bidirectional Model Context Protocol (MCP) tooling.
- Worktree-isolated Saga execution and atomic rollbacks.
- Token compaction, socratic peer review, and continuous reactive supervision.
- CPU watchdog throttles, destructive action sandboxes, and polyglot SDK connectors.

However, production multi-agent systems face four critical scaling boundaries:
1. **Persona Rigidity**: Static roles (`ArchitectActor`, `CoderActor`, `VerifierActor`, `RemediatorActor`) lack domain-specific grounding when assigned heterogeneous tasks (e.g. database schema migrations vs CSS design tokens vs cryptographic protocols).
2. **Single-Node Isolation**: Operating exclusively on localhost (`/tmp/focusgate-v3.sock`) prevents orchestrating swarms across multiple containers, pods, or developer workstations.
3. **Amnesia Across Waves**: While verified trajectories are harvested to disk (`.focusgate/trajectories/`), actors in subsequent waves cannot rapidly query past failure-and-repair episodes to avoid repeating known gotchas.
4. **Serial Critical Path Bottlenecks**: Waiting for a parent gate's dialectic review before scheduling child actors adds latency to high-confidence task chains.

FocusGate v3.1 solves these four boundaries through the **Adaptive Swarm Grid & Self-Refining Mesh**.

---

### 2. Core Pillars of FocusGate v3.1

#### Pillar I: Dynamic Adaptive Persona Synthesis (`core/grid/persona_synthesizer.py`)
- Automatically synthesizes specialized micro-personas matching the semantic ontology of the task.
- Generates scoped tool affinities: an SQL actor receives database inspection tools; a security auditor receives AST taint-analysis tools.
- Zero manual configuration; personas hydrate and register dynamically into `ActorMeshRouter`.

#### Pillar II: Distributed Merkle CRDT & Grid Networking (`core/grid/crdt_mesh.py`)
- Zero external dependency networking: pure Python `socket` (plain TCP). *Correction (v3.2): the TLS originally proposed here was never implemented; there is no `ssl` use and no peer authentication.*
- State-based Merkle delta CRDTs synchronize vector clocks and event trees across multiple machines with deterministic conflict-free causal convergence.

#### Pillar III: Episodic Immune Memory & Token-Bounded Retrieval (`core/memory/episodic_cache.py`)
- Fast-path TF-IDF cosine similarity index running in pure Python stdlib.
- Indexes past remediation receipts, dialectic disputes, and test failures.
- Injects top-2 anti-pattern "vaccines" ($\le 120$ tokens) into the actor's initial brief, inoculating against known failure modes in $<5$ms.

#### Pillar IV: Speculative Parallel Wave Scheduling (`core/grid/speculative_scheduler.py`)
- Anticipates frontier DAG resolutions and pre-dispatches downstream actors in speculative ephemeral worktrees.
- If parent passes: zero-latency promotion to `main`.
- If parent fails: instantaneous zero-cost teardown.

#### Pillar V: Deterministic AST Self-Repair Engine (`core/repair/ast_refactor.py`)
- Solves syntactic, termination, and hygiene defects directly via `ast.NodeTransformer` passes in $<2$ms without consuming LLM API tokens.

---

### 3. Sacred Invariants
- **100% Python Standard Library**: No external dependencies.
- **Strict Backward Compatibility**: All 404 tests from `v3.0-prod` must continue to pass without regression.
- **Action Envelope Protocol**: Mandatory 3-part header on every agent turn.
