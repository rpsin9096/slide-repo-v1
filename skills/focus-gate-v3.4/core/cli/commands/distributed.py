"""Early routes: swarm, daemon, MCP, merkle, sandbox, grid, checkpoints and friends.

These commands run before the ledger runtime (event store, kernel) is created, so they are
registered with `early=True`. The implementations stay in `CLIDispatcher.dispatch_*`
(core/cli/dispatch.py); this table replaces its 160-line if-chain (v3.4).
"""
from core.cli.registry import REGISTRY, Command, CommandContext

# (name, flag, dest, kind, argv_match, method, call_args, summary, position)
ROUTES = [
    ('mcp', '--mcp', 'mcp', 'bool', True, 'dispatch_mcp', (), 'Runs stdio JSON-RPC 2.0 Model Context Protocol (MCP) tool server.', 0),
    ('verify-merkle', '--verify-merkle', 'verify_merkle', 'none', True, 'dispatch_verify_merkle', ('clean_args', 'is_json'), 'Verifies cryptographic Merkle DAG parent links and state root integrity.', 1),
    ('watch', '--watch', 'watch', 'none', True, 'dispatch_watch', ('clean_args', 'is_json'), 'Starts reactive in-memory daemon file watcher (<15ms gate re-evaluation).', 2),
    ('heal', '--heal', 'heal', 'none', True, 'dispatch_heal', ('args', 'clean_args', 'is_json'), 'Autonomously diagnoses and remediates failing gates using isolated worktree and 3-attempt circuit breaker.', 3),
    ('actor-status', '--actor-status', 'actor_status', 'bool', True, 'dispatch_actor_status', ('is_json',), 'Inspects live swarm actors, states, and mailboxes.', 4),
    ('merkle-diff', '--merkle-diff', 'merkle_diff', 'none', True, 'dispatch_merkle_diff', ('clean_args', 'is_json'), 'Compares two Merkle event DAGs and reports state divergence.', 5),
    ('merkle-sync', '--merkle-sync', 'merkle_sync', 'none', True, 'dispatch_merkle_sync', ('clean_args', 'is_json'), 'Synchronizes remote Merkle DAG into local with causal ordering.', 6),
    ('mcp-hub', '--mcp-hub', 'mcp_hub', 'bool', True, 'dispatch_mcp_hub', ('clean_args', 'is_json'), 'Aggregates local and remote MCP servers into unified tool mesh.', 7),
    ('mcp-call', '--mcp-call', 'mcp_call', 'none', True, 'dispatch_mcp_call', ('clean_args', 'is_json'), 'Executes a namespaced tool across connected MCP servers.', 8),
    ('swarm-wave', '--swarm-wave', 'swarm_wave', 'none', True, 'dispatch_swarm_wave', ('clean_args', 'is_json'), 'Executes a parallel wave of DAG frontier gates across actors.', 9),
    ('swarm-run', '--swarm-run', 'swarm_run', 'none', True, 'dispatch_swarm_run', ('clean_args', 'is_json'), 'Iteratively drives swarm execution until complete convergence.', 10),
    ('swarm-worktree', '--swarm-worktree', 'swarm_worktree', 'none', True, 'dispatch_swarm_worktree', ('clean_args', 'is_json'), 'Provisions or inspects an isolated worktree for actor.', 11),
    ('swarm-merge', '--swarm-merge', 'swarm_merge', 'none', True, 'dispatch_swarm_merge', ('clean_args', 'is_json'), 'Executes atomic Saga merge of actor branch with rollback tombstone.', 12),
    ('actor-context', '--actor-context', 'actor_context', 'none', True, 'dispatch_actor_context', ('clean_args', 'is_json'), 'Inspects active sliding turn window and token budget for actor.', 13),
    ('compact-swarm', '--compact-swarm', 'compact_swarm', 'none', True, 'dispatch_compact_swarm', ('clean_args', 'is_json'), 'Collapses settled gate evidence into cryptographic proof tree archive.', 14),
    ('dialectic-review', '--dialectic-review', 'dialectic_review', 'none', True, 'dispatch_dialectic_review', ('clean_args', 'is_json'), 'Runs autonomous Socratic peer review on actor branch/gate.', 15),
    ('coherence-status', '--coherence-status', 'coherence_status', 'none', True, 'dispatch_coherence_status', ('clean_args', 'is_json'), 'Inspects status of signed Coherence Receipts.', 16),
    ('daemon-start', '--daemon-start', 'daemon_start', 'none', True, 'dispatch_daemon_start', ('clean_args', 'is_json'), 'Starts autonomous swarm supervisor daemon.', 17),
    ('daemon-status', '--daemon-status', 'daemon_status', 'bool', True, 'dispatch_daemon_status', ('clean_args', 'is_json'), 'Queries status of running swarm daemon over Unix socket.', 18),
    ('daemon-stop', '--daemon-stop', 'daemon_stop', 'bool', True, 'dispatch_daemon_stop', ('clean_args', 'is_json'), 'Stops background swarm supervisor daemon.', 19),
    ('daemon-stream', '--daemon-stream', 'daemon_stream', 'none', True, 'dispatch_daemon_stream', ('clean_args', 'is_json'), 'Streams live broadcast events from swarm supervisor daemon.', 20),
    ('daemon-events', '--daemon-events', 'daemon_events', 'none', True, 'dispatch_daemon_events', ('clean_args', 'is_json'), 'Queries recent broadcast events from swarm supervisor daemon.', 21),
    ('harvest-swarm', '--harvest-swarm', 'harvest_swarm', 'bool', True, 'dispatch_harvest_swarm', ('clean_args', 'is_json'), 'Harvests multi-agent swarm problem-solving traces.', 22),
    ('export-swarm-pack', '--export-swarm-pack', 'export_swarm_pack', 'none', True, 'dispatch_export_swarm_pack', ('clean_args', 'is_json'), 'Exports harvested swarm trajectories to fine-tuning pack (openai|claude|gemini).', 23),
    ('chaos-test', '--chaos-test', 'chaos_test', 'none', True, 'dispatch_chaos_test', ('clean_args', 'is_json'), 'Executes synthetic chaos injection and self-healing recovery test.', 24),
    ('chaos-report', '--chaos-report', 'chaos_report', 'bool', True, 'dispatch_chaos_report', ('clean_args', 'is_json'), 'Outputs mesh fault tolerance resilience report.', 25),
    ('audit-loop-safety', '--audit-loop-safety', 'audit_loop_safety', 'none', True, 'dispatch_audit_loop_safety', ('clean_args', 'is_json'), 'Audits Python files for infinite loop hazards and unhalting recursion.', 26),
    ('watchdog-run', '--watchdog-run', 'watchdog_run', 'none', True, 'dispatch_watchdog_run', ('clean_args', 'is_json'), 'Executes command guarded by CPU execution watchdog and timeout.', 27),
    ('verify-sandbox', '--verify-sandbox', 'verify_sandbox', 'bool', True, 'dispatch_verify_sandbox', ('clean_args', 'is_json'), 'Verifies sandbox path jail boundaries and command blacklist.', 28),
    ('sandbox-exec', '--sandbox-exec', 'sandbox_exec', 'none', True, 'dispatch_sandbox_exec', ('clean_args', 'is_json'), 'Executes command within security sandbox and command guardrails.', 29),
    ('sdk-schema', '--sdk-schema', 'sdk_schema', 'bool', True, 'dispatch_sdk_schema', ('clean_args', 'is_json'), 'Outputs polyglot JSON schema and type models for actor SDKs.', 30),
    ('sdk-ping', '--sdk-ping', 'sdk_ping', 'none', True, 'dispatch_sdk_ping', ('clean_args', 'is_json'), 'Pings supervisor daemon using native client SDK.', 31),
    ('barrier-bench', '--barrier-bench', 'barrier_bench', 'none', True, 'dispatch_barrier_bench', ('clean_args', 'is_json'), 'Benchmarks multi-actor wave barrier convergence latency.', 32),
    ('synthesize-persona', '--synthesize-persona', 'synthesize_persona', 'none', True, 'dispatch_synthesize_persona', ('clean_args', 'is_json'), 'Synthesizes domain-specific actor persona dynamically.', 33),
    ('grid-status', '--grid-status', 'grid_status', 'bool', True, 'dispatch_grid_status', ('clean_args', 'is_json'), 'Inspects distributed Merkle CRDT grid status and event count.', 34),
    ('grid-node', '--grid-node', 'grid_node', 'none', True, 'dispatch_grid_node', ('clean_args', 'is_json'), 'Starts distributed TCP grid socket node.', 35),
    ('memory-search', '--memory-search', 'memory_search', 'none', True, 'dispatch_memory_search', ('clean_args', 'is_json'), 'Searches episodic immune memory and prior failure modes.', 36),
    ('speculative-wave', '--speculative-wave', 'speculative_wave', 'none', True, 'dispatch_speculative_wave', ('clean_args', 'is_json'), 'Schedules speculative wave execution for downstream gates.', 37),
    ('auto-refactor', '--auto-refactor', 'auto_refactor', 'none', True, 'dispatch_auto_refactor', ('clean_args', 'is_json'), 'Deterministically refactors loops and shotgun exceptions.', 38),
    ('quorum-vote', '--quorum-vote', 'quorum_vote', 'none', True, 'dispatch_quorum_vote', ('clean_args', 'is_json'), 'Evaluates decentralized quorum voting across grid nodes.', 39),
    ('adaptive-budget', '--adaptive-budget', 'adaptive_budget', 'none', True, 'dispatch_adaptive_budget', ('clean_args', 'is_json'), 'Allocates domain-weighted context budget for an actor.', 40),
    ('simulate-partition', '--simulate-partition', 'simulate_partition', 'none', True, 'dispatch_simulate_partition', ('clean_args', 'is_json'), 'Simulates network partition and verifies CRDT recovery.', 41),
    ('migrate-task', '--migrate-task', 'migrate_task', 'none', True, 'dispatch_migrate_task', ('clean_args', 'is_json'), 'Live-migrates worktree task across grid nodes.', 42),
    ('synthesize-contract', '--synthesize-contract', 'synthesize_contract', 'none', True, 'dispatch_synthesize_contract', ('clean_args', 'is_json'), 'Synthesizes defensive type and non-null AST guards.', 43),
    ('swarm-liveness', '--swarm-liveness', 'swarm_liveness', 'none', True, 'dispatch_swarm_liveness', ('clean_args', 'is_json'), 'Monitors real-time actor heartbeat liveness and deadlocks.', 44),
    ('verify-attestation', '--verify-attestation', 'verify_attestation', 'none', True, 'dispatch_verify_attestation', ('clean_args', 'is_json'), 'Verifies cryptographic Merkle inclusion proofs and state attestations.', 45),
    ('evolve-directives', '--evolve-directives', 'evolve_directives', 'none', True, 'dispatch_evolve_directives', ('clean_args', 'is_json'), 'Proposes autonomous rule and prompt directive improvements.', 46),
    ('wire-bench', '--wire-bench', 'wire_bench', 'none', True, 'dispatch_wire_bench', ('clean_args', 'is_json'), 'Benchmarks high-throughput binary wire protocol framing.', 47),
    ('adversarial-audit', '--adversarial-audit', 'adversarial_audit', 'none', False, 'dispatch_adversarial_audit', ('args', 'clean_args', 'is_json'), 'Runs adversarial socratic tournament on architecture proposals.', 48),
    ('checkpoint', '--checkpoint', 'checkpoint', 'none', False, 'dispatch_create_checkpoint', ('args', 'clean_args', 'orch', 'is_json'), 'Creates an immutable production checkpoint of orchestrator state (defaults to v2.8-prod)', 49),
    ('restore-checkpoint', '--restore-checkpoint', 'restore_checkpoint', 'none', False, 'dispatch_restore_checkpoint', ('args', 'clean_args', 'orch', 'is_json'), 'Restores orchestrator state from a saved production checkpoint', 50),
    ('list-checkpoints', '--list-checkpoints', 'list_checkpoints', 'bool', False, 'dispatch_list_checkpoints', ('orch', 'is_json'), 'Lists all saved production checkpoints with integrity verification', 51),
]

_ARG = {"args": lambda c: c.args, "clean_args": lambda c: c.argv, "is_json": lambda c: c.is_json, "orch": lambda c: c.orch}


def _matcher(flag, dest, kind, argv_match):
    def matches(ctx: CommandContext) -> bool:
        val = getattr(ctx.args, dest, None if kind == "none" else False)
        hit = (val is not None) if kind == "none" else bool(val)
        return hit or (argv_match and flag in ctx.argv)
    return matches


def _handler(method, call_args):
    def handler(ctx: CommandContext) -> int:
        from core.cli.dispatch import CLIDispatcher
        return getattr(CLIDispatcher, method)(*[_ARG[a](ctx) for a in call_args])
    return handler


for _name, _flag, _dest, _kind, _argv, _method, _shape, _summary, _pos in ROUTES:
    REGISTRY.register(Command(_name, (_flag,), _dest, _summary, _handler(_method, _shape),
                              matches=_matcher(_flag, _dest, _kind, _argv), early=True, order=_pos))
