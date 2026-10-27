# FocusGate v3.4: Technical Specification (Evidence Gate on the v3.1 grid) (Adaptive Swarm Grid & Self-Refining Mesh)
## Formal Engineering Specification & Cognitive Grid Foundation

**Version:** 3.4 — released as `v3.4-PROD` (see `core/version.py`, the single source)  
**Parent Baseline:** FocusGate v3.0-PROD (404 passing tests; the SHA originally
quoted here was fabricated — see AUDIT F17).
**Current release:** FocusGate v3.1-PROD, 630 passing tests at baseline commit `b6a8ac5`. (The previously cited checkpoint was a pre-re-init commit removed by the Loop 68 fresh-init policy; see AUDIT F24.)  
**Status:** Canonical Engineering Specification & Architecture Contract  
**Runtime:** Pure Python 3.9+ Standard Library (Zero External Dependencies)  

---

## 1. Sacred Invariants & Constraints

1. **Zero External Dependencies**: All subsystems (Persona Synthesizer, Merkle CRDT Mesh, Episodic Memory, Speculative Scheduler, AST Repair) execute exclusively using Python standard library modules (`socket`, `threading`, `queue`, `ast`, `hashlib`, `math`, `os`, `sys`, `subprocess`).
2. **Action Envelope Compliance**: Every interaction conforms to the invariant 3-part Action Envelope:
   - Line 1: `▶ NEXT ACTION: <command or file:line>`
   - Line 2: `State: [Pipeline: ... | Swarm: ...] FocusGate v3.1-PROD`
   - Line 3: `■ ACTIVE FOCUS: <micro-task summary>`
   - Max 3 body items, collapsible `<details>`, and `<2 min` `Next:` action.
3. **Token Economy Discipline**:
   - Declarative Facet Directives, **injected render**: $\le 400$ tokens (WINDOW), $\le 150$ tokens (EPHEMERAL). Enforced on all 19 facets by `tests/test_v33_facets.py` (v3.2 enforced it on 2). Whole-file hydrate (rules + playbook) is on demand, capped at 1500 tokens, and is not injected.
   - Swarm Actor Message Deltas: $\le 80$ tokens per payload.
   - Episodic Memory Injections: $\le 120$ tokens per prompt gotcha anchor.
   - Actor Working Memory Briefs: $\le 400$ tokens per active gate brief.
4. **Test Discovery Budget (target, not guarantee)**: the full suite should run clean in $\le 15.0$ s on reference hardware. Measured at v3.4: 747 tests, ~22 s on the audit machine (v3.3: 719 tests, ~23 s ; v3.2: 671 tests, ~18 s; v3.1: 630 tests, ~17 s). See AUDIT.md O1.
5. **Evidence Gate (v3.2)**: a gate is settled (`[x]`) only by `settle_gate`, which executes CHECK, requires exit 0 and an EXPECT match, rejects integrity errors (SELF_SATISFYING, MASKED_EXIT, VACUOUS_EXPECT, INVALID_EXPECT, UNFILLED_TEMPLATE), and under `--strict` requires a prior RED observation bound to the same CHECK+EXPECT fingerprint. Every observation is appended to a SHA-256 hash-chained `<ledger>.evidence.jsonl`. Overrides (`--force`, `--waive-red`) are logged.
6. **Single settlement path (v3.3)**: `core/gates/evidence.py` is the only module that turns `[ ]` into `[x]` (`settle_gate` for gates, `settle_spike` for spikes). `--swarm-wave` and the autonomous wave loop settle through it; a receipt is a claim, not proof. Enforced by a source scan in `tests/test_v33_architecture.py`.
7. **Facet depth (v3.3)**: every facet carries rules with definitions (not titles) and a playbook: >= 3 phases each with an observable EXIT, >= 2 lazy tells each with a DETECT and an INSTEAD, >= 1 gate template that passes `GateIntegrity`, >= 1 handoff to an existing facet. `--lint-facets` enforces it.
8. **One dispatcher (v3.4)**: every CLI command, early or not, is a registry entry resolved by `REGISTRY.resolve` in `(order, registration)` sequence. `scripts/focus-gate.py` is an entry point (<= 30 lines); `main()` in `core/cli/app.py` parses, resolves one command and runs it. Handlers return exit codes and never call `sys.exit`.
9. **No dead flags, no executed destructive CHECKs (v3.4)**: every parser flag is a command or a modifier that something reads; `observe()` refuses to execute a CHECK matching `core/sandbox/command_guard.py` (scoped `rm -rf /tmp/x` stays allowed).

---

## 2. Inherited v3.0 Components (Delivered Baseline)
- **Swarm Actor Message Mesh (`core/mesh/`)**: `SwarmActor`, `ActorMailbox`, `ActorMeshRouter`.
- **Merkle State Vector Consensus (`core/consensus/`)**: `VectorClock`, `MerkleStateVector`, `MerkleSyncCoordinator`.
- **Bidirectional MCP Mesh Hub (`core/mcp/`)**: Dual-role stdio server and client multiplexer.
- **Ephemeral Worktree Isolation & Saga Merges (`core/swarm/`)**: `ActorWorktreeManager`, `SagaMergeCoordinator`.
- **Context Compactor & Micro-Delta Bus (`core/compaction/`)**: `ActorContextCompactor`, `MicroDeltaBus`, `ProofTreeCompactor`.
- **Socratic Dialectic & Coherence Receipts (`core/dialectic/`)**: `SocraticMeshProtocol`, `AutonomousPeerReviewer`.
- **Unified Reactive Supervisor & Push IPC (`core/daemon/`)**: `UnifiedSwarmSupervisor`, `PushEventStream`.
- **Trajectory SFT Harvester (`core/harvest/`)**: `TrajectoryHarvester`, `DatasetExporter`.
- **Chaos Fault Injection & Recovery (`core/chaos/`)**: `ChaosMeshInjector`, `PartitionRecoveryCoordinator`.
- **Watchdog & Resource Throttling (`core/watchdog/`)**: `ASTLoopAnalyzer`, `CPUExecutionWatchdog`, `CPUResourceCircuitBreaker`.
- **Destructive Action Sandbox (`core/sandbox/`)**: `PathJailSandbox`, `CommandGuard`.
- **Polyglot Actor SDK (`core/sdk/`)**: `protocol_spec`, `FocusGateClient`, `ShellActorBridge`.
- **High-Throughput Performance Subsystem (`core/perf/`)**: `AtomicEventRingBuffer`, `HighThroughputWaveBarrier`.

---

## 3. Preview 1 Component Specifications (Loops 39–44)

### 3.1 Dynamic Adaptive Actor Persona Synthesis (`core/grid/persona_synthesizer.py`)
- **`PersonaSynthesizer`**:
  - Analyzes the task description, target filenames, and code AST to synthesize a domain-specific persona.
  - Produces an `ActorPersona`:
    - `role_id`: Unique identifier (e.g. `actor-sql-migrator-01`).
    - `domain`: Target specialty (`security`, `frontend`, `database`, `performance`, `general`).
    - `system_prompt`: Custom directive containing domain invariants and non-functional requirements.
    - `allowed_tools`: Constrained subset of tools matching the domain.
    - `verification_rules`: Tailored post-condition checks.
- **`DynamicSwarmActor`**:
  - Inherits from `SwarmActor`.
  - Configures behavior, mailbox filtering, and message handling dynamically based on `ActorPersona`.
- **`PersonaRegistry`**:
  - Manages active dynamic actor lifecycles and registers them into `ActorMeshRouter`.

### 3.2 Distributed Merkle CRDT & Grid Networking (`core/grid/crdt_mesh.py`)
- **`GridNode`**:
  - Pure stdlib TCP socket server allowing actors across multiple processes or machines to communicate.
  - **No TLS.** `core/grid/` contains no `ssl` usage, so transport encryption is not
    implemented. A TLS option was previously claimed here and in `SKILL.md`'s
    grid-node example; both were removed rather than shipped untested
    (v3.2 Loop 60). TLS transport is a v3.3 candidate, not a v3.1 capability.
- **`MerkleCRDTReplicator`**:
  - State-based CRDT replicating `MerkleStateVector` and event logs.
  - Resolves divergent branches deterministically using Lamport causal timestamps and state root hashes.

### 3.3 Episodic Immune Memory & Token-Efficient Retrieval (`core/memory/episodic_cache.py`)
- **`EpisodicMemoryStore`**:
  - In-memory pure-Python TF-IDF index and token hasher over settled task trajectories and remediation receipts.
- **`ImmuneMemoryRetriever`**:
  - Retrieves top-2 relevant past failure-and-repair episodes in $<5$ms ($\le 120$ tokens), injecting historical immune memory into agent briefs.

### 3.4 Speculative Parallel Wave Scheduling (`core/grid/speculative_scheduler.py`)
- **`SpeculativeWaveScheduler`**:
  - Predicts high-probability frontier transitions and pre-dispatches downstream actors in ephemeral speculative worktrees (`.focusgate/worktrees/spec-actor-<id>`).
  - Instantly promotes to main on parent success, or discards without penalty on parent failure.

### 3.5 Deterministic AST Self-Repair & Code Refactoring (`core/repair/ast_refactor.py`)
- **`ASTSelfRepairEngine`**:
  - Pure `ast.NodeTransformer` repairing syntax errors, inserting loop termination guards, and stripping shotgun error suppressions in $<2$ms without LLM API calls.

---

## 4. Preview 2 Component Specifications (Loops 45–50)

### 4.1 Byzantine Fault Detection & Quorum Consensus (`core/grid/byzantine_consensus.py`)
- **`QuorumVoteCollector`**: Aggregates SHA256-signed actor votes and checks against a strict 2/3 supermajority threshold.
- **`ByzantineDetector`**: Identifies equivocation, conflicting state vector clocks, and divergent state root proposals.

### 4.2 Dynamic Token Budgeting & Adaptive Compression (`core/compaction/adaptive_budget.py`)
- **`DynamicTokenBudgeter`**: Allocates domain-specific context ceilings based on role complexity and queue depth.
- **Mailbox Micro-Compactor**: Fast JIT compaction truncating intermediate message entries when mailbox exceeds $85\%$ capacity.

### 4.3 Swarm Partition Simulator & Chaos Recovery (`core/chaos/partition_sim.py`)
- **`PartitionSimulator`**: Isolates subset nodes, drops in-flight deltas, and validates causal convergence upon healing.

### 4.4 Cross-Node Worktree Migration (`core/grid/worktree_migrator.py`)
- **`WorktreeMigrator`**: Serializes worktree state and pending mailbox frames into portable wire archives for dynamic load rebalancing.

### 4.5 Deterministic AST Contract Synthesizer (`core/repair/contract_synthesizer.py`)
- **`ASTContractSynthesizer`**: Injects defensive type checks and None guards into function ASTs.

---

## 5. Production Component Specifications (Loops 51–56)

### 5.1 Swarm Actor Heartbeat & Liveness Watchdog (`core/grid/heartbeat_watchdog.py`)
- **`ActorHeartbeatRecord`**: Tracks heartbeat timestamps, active CPU time, and task states.
- **`DeadlockDetector`**: Evaluates resource dependency graphs using Tarjan or DFS cycle detection to break circular waits.
- **`SwarmHeartbeatMonitor`**: Supervises mesh actor liveness, emits warning receipts, and recycles hung actors.

### 5.2 Merkle Proof Verification & State Attestation (`core/consensus/merkle_attestation.py`)
- **`MerkleInclusionProof`**: Logarithmic proof path generation and verification against cryptographic Merkle state roots.
- **`StateAttestor`**: Multi-signature attestation collector and verifier across swarm epochs.

### 5.3 Autonomous Self-Evolving Rule & Directive Engine (`core/gates/directive_evolver.py`)
- **`DirectiveEvolver`**: Analyzes settled task receipts and failure clusters to generate token-bounded prompt directive refinements ($\le 400$ tokens).

### 5.4 High-Throughput Wire Binary Protocol (`core/sdk/wire_protocol.py`)
- **`StreamingWireFramer`**: High-speed binary framing protocol (`b"FG\x03\x01"`, 32-bit length, type tag, CRC32).

### 5.5 Infinite Loop Guardian & CPU Defense (`core/watchdog/infinite_loop_guardian.py`)
- **`InfiniteLoopGuardian`**: Static AST analyzer detecting unbounded while loops, unhalted recursion, and sleep-less polling loops to prevent CPU starvation.


---

## 6. v3.2 Evidence Gate (`core/gates/evidence.py`)
- **`GateIntegrity.analyze(check, expect) -> [Finding]`**: tokenizes the CHECK with `shlex`, splits top-level segments on `; && || | &`, recurses into `bash -c`, and reports errors (cannot serve as evidence) and warnings (weak evidence).
- **`EvidenceLog`**: append-only JSONL; each record carries `prev` and `hash = sha256(canonical(record))`; `verify()` returns `(ok, first_bad_line)`; `has_red(gate, fingerprint)`.
- **`fingerprint(check, expect)`**: SHA-256 prefix of the stripped pair; editing either invalidates prior red evidence.
- **Operations**: `settle_gate`, `baseline`, `run_gates`, `evidence_report`, `falsifiable_seed`.

---

## 7. v3.3 Deep Facets and Command Registry

- **Facet tiers.** Tier 1 (rules): `N. NAME: definition`, ordered most-critical-first; the injected render keeps a prefix under the ceiling and clips each definition to its operative clause. Tier 2 (playbook): `### Phases`, `### Lazy Tells`, `### Gate Templates`, `### Handoff`; grammar in `core/facets/playbook.py`, authoring guide in `references/facets.md`.
- **`FacetCatalog` (`core/facets/catalog.py`)** is the single seam for load, route, render, lint and hydrate. It re-stats the facet tree on access and reparses only on change. `AgentBrief`, the hydrate command, the router index and the lint command all cross it.
- **Router.** `match_facets` matches whole words with plain inflections (`s|es|ed|ing|ally|ly`) and ranks by evidence (distinct triggers, phrase length) before priority. `fix` no longer matches `prefix`.
- **Brief composition (`core/brief_composer.py`).** Facet rules, a context-tailored 4-pass block, the keyword fallback for unregistered facets, and the Evidence Protocol (`--baseline`, unchanged CHECK, `--check <id> --strict`).
- **Command registry (`core/cli/registry.py`).** A command is a function `handler(ctx) -> exit_code` registered with `@command`.

## 8. v3.4 One Dispatcher

- **Entry.** `scripts/focus-gate.py` (20 lines) -> `core/cli/app.py:main` -> `REGISTRY.resolve(ctx)` -> `handler(ctx)`. Early commands (`early=True`: swarm, daemon, MCP, merkle, sandbox, grid, checkpoints) run before the event store and kernel are built; the rest run after.
- **Modules.** `core/cli/commands/`: `distributed` (52 early routes, a table over `CLIDispatcher.dispatch_*`), `orchestration`, `history`, `verification`, `writing`, `audits`, `economy`, `focus`, `spikes`, `swarm_ops`, plus the v3.3 `facets`, `routing`, `evidence`, `ledger_views`, `scaffold`. Modules never import each other.
- **Moved to `core/`.** `core/cli/{parser,pipeline,intent,paths,documents}.py`, `core/focus_support.py`, `core/writing_suite.py`, `core/domain_audit.py`.
- **Rigor.** `SWALLOWED_EXCEPTION`: `except:` / `except Exception:` / `except BaseException:` whose body is only `pass` or `...`. Narrow handlers are not flagged.
- **Gate safety.** `DESTRUCTIVE_COMMAND` is an integrity error (lint, settle) and `observe()` never executes such a CHECK (baseline, run, check), with or without `--force`.

