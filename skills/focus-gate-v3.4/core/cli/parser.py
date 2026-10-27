"""Argument parser and help text (moved out of the CLI script in v3.4)."""
import argparse


def print_help():
    help_text = """FocusGate @VERSION@ (Evidence Gate + Deep Facets: gates close only on observed evidence).

Usage:
  python3 focus-gate.py [command] [options]

JIT Hydration & Hybrid Routing (v3.1):
  --hydrate-facet <name>            Hydrates compact declarative micro-directive for facet.
  --list-facets                     Lists all facets across 5 Bounded Contexts with trigger counts.
  --lint-facets                     Lints facet contracts: collisions, zero triggers, mode mismatch, dead oracle flags.
  --synthesize-pipeline "<task>"    Fast-path deterministic classifier (<5ms, 0 tokens).
  -p "<task>"                       Short alias for --synthesize-pipeline.
  --audit-adapter                   Audits distilled Student LoRA router adapter integrity & checksum.
  --distilled-route "<task>"        Routes task description through distilled Student LoRA router.
  --export-colab-pack [dir]         Exports verified trajectory dataset and turnkey Colab training pack.

Design Verification & Governance:
  --audit-contrast <fg> <bg>        Calculates WCAG 2.1 relative luminance and contrast ratio.
  --audit-tokens <path>             Audits CSS/TSX/HTML files for unanchored hardcoded styling.
  --sync-tokens <brand_md> [--out]  Parses brand markdown and generates design tokens CSS.
  --audit-safe-zone <spec> ...      Validates elements against safe-zone bounding box.
  --audit-context-sufficiency <f>   Audits AGENT_PROMPT.md briefs for bare @pointers / lost summaries.

Domain-Driven Design Governance:
  --audit-domain [dir]              Audits workspace against CONTEXT.md and checks positive steering.
  --validate-contracts [events]     Validates ledger.events.jsonl against typed event schemas.

Writing Suite Commands (v3.1):
  --fragment "<text>" [path]        Appends unstructured thought to FRAGMENTS.md.
  --brief <gate_id> [--out path]    Compiles task into machine-readable subagent brief.
  --shape [fragments] [--out path]  Initiates concept-grounded technical spec shaping session.
  --beat [beats_file]               Proposes candidate next narrative beats.

Meta-Orchestrator & Cognitive Scaffolding (v3.1):
  --seed [dir] [task_name]          Scaffolds .focusgate/GATES-SEED.md with 2-minute micro-action.
  --reorient [ledger]               Restores working memory in <3s answering What, Where, and Next Action.
  --queue-next [ledger]             Outputs single active gate and buffers remaining DAG frontier.
  --queue-status [ledger]           Displays active gate status and buffered count.
  --deepen [1|2|3]                  Zooms depth level (L1 Action, L2 Structured Ledger, L3 Swarm/Audit).
  --ledger-root <dir>               Explicitly sets ledger namespace root (fixes ADR-0009 Wart B).

Master Orchestrator & Sub-Agents (v3.1):
  --orchestrate "<task>" [--preview|--dispatch] Decomposes plan into AgentBriefs and dispatches.
  --agent-settle <gate_id> --receipt <path>      Sub-agent signals completion with GateReceipt.
  --orchestrator-verify <bundle_id>              Evaluates cross-agent coherence criteria.
  --agent-merge <gate_id>                        Merges verified sub-agent output into main.
  --agent-status                                 Monitors active sub-agents and bus deltas.
  --checkpoint [NAME]                            Creates an immutable production checkpoint of orchestrator state.
  --restore-checkpoint <name>                    Restores orchestrator state from a saved production checkpoint.
  --list-checkpoints                             Lists all saved production checkpoints with integrity verification.

Execution Rigor & Ephemeral Architecture:
  --unlazy-rigor [path]             Audits workspace/files for fake completion, placeholders, and stubs.
  --select-tool <intent>            Deterministic tool selection matrix evaluating intent and preconditions.
  --patch-lint <file> <block>       Pre-validates patch block preconditions before applying edits.
  --slice-facet <facet> <section>   Extracts targeted section from facet directive (<300 tokens).
  --retrieve-snippet <file> <pat>   On-demand regex grep search with line-windowed snippet formatting.
  --ephemeral-run <cmd>             Executes isolated gate check within sandboxed ephemeral session.
  --handoff <target> <json>         Encapsulates inter-skill delta packet handoff.
  --audit-handoffs                  Audits handoff event log for ACL contract conformance.
  --harvest-trajectories            Extracts verified execution trajectories into SFT dataset.
  --harvest-swarm [dir]             Harvests multi-agent swarm problem-solving traces.
  --export-swarm-pack [fmt]         Exports harvested swarm trajectories to fine-tuning pack (openai|claude|gemini).

Universal Verification & Anti-Cliché Governance (v3.1):
  --verify-wave [--json]            Runs complete end-to-end wave verification across all invariant gates.
  --verify-stage <stage_id>         Validates intra-stage verification matrix criteria before frontier dispatch.
  --stage-status [--json]           Displays stage matrix status and intra-stage completion evidence.
  --audit-all <path> [--json]       Unified multi-oracle audit (prose, code, design) across path or directory.
  --audit-prose-cliche <path>       Detects AI writing tells (throat-clearing, buzzwords, sycophancy).
  --audit-code-cliche <path>        Detects junk-drawer utils and shotgun error suppression.
  --audit-design-cliche <path>      Detects AI design tells (cliché icons, purple gradients, generic cards).
  --adversarial-audit "<prop>"      Runs adversarial socratic tournament on architecture proposals.
  --dialectic-review <actor> <gate> Runs autonomous Socratic peer review on actor branch/gate.
  --coherence-status [gate_id]      Inspects status of signed Coherence Receipts.
  --audit-loop-safety <path>        Audits Python files for infinite loop hazards and unhalting recursion.
  --watchdog-run <cmd>              Executes command guarded by CPU execution watchdog and timeout.
  --mcp                             Runs stdio JSON-RPC 2.0 Model Context Protocol (MCP) tool server.
  --mcp-hub [config]                Aggregates local and remote MCP servers into unified tool mesh.
  --mcp-call <srv> <tool> <args>    Executes a namespaced tool across connected MCP servers.
  --watch [dir]                     Starts reactive in-memory daemon file watcher (<15ms gate re-evaluation).
  --heal <gate_id> [--file <f>]     Autonomously diagnoses and remediates failing gates.
  --actor-status [--json]           Inspects live swarm actors, states, and mailboxes.
  --daemon-start [sock]             Starts autonomous swarm supervisor daemon.
  --daemon-status [sock] [--json]   Queries status of running swarm daemon over Unix socket.
  --daemon-stop [sock] [--json]     Stops background swarm supervisor daemon.
  --daemon-stream [sock] [--json]   Streams live broadcast events from swarm supervisor daemon.
  --daemon-events [sock] [--json]   Queries recent broadcast events from swarm supervisor daemon.
  --sdk-schema [--ts|--rust|--json] Outputs polyglot JSON schema and type models for actor SDKs.
  --sdk-ping [sock] [--json]        Pings supervisor daemon using native client SDK.
  --barrier-bench [n] [--json]      Benchmarks multi-actor wave barrier convergence latency.
  --synthesize-persona "<brief>"    Synthesizes domain-specific actor persona dynamically.
  --grid-status [--json]            Inspects distributed Merkle CRDT grid status and event count.
  --grid-node [port]                Starts distributed TCP grid socket node.
  --memory-search "<query>" [--json] Searches episodic immune memory and prior failure modes.
  --speculative-wave [gate] [--json] Schedules speculative wave execution for downstream gates.
  --auto-refactor <path> [--json]   Deterministically refactors loops and shotgun exceptions.
  --quorum-vote [gate] [--nodes n]  Evaluates decentralized quorum voting across grid nodes.
  --adaptive-budget [actor] [--json] Allocates domain-weighted context budget for an actor.
  --simulate-partition [ms] [--json] Simulates network partition and verifies CRDT recovery.
  --migrate-task <id> <node> [--json] Live-migrates worktree task across grid nodes.
  --synthesize-contract <f> [--json] Synthesizes defensive type and non-null AST guards.


Core Commands:
  --init [dir]                      Scaffolds .focusgate/GATES.md with domain anchors.
  --status [ledger] [--json]        Displays state vector and gate status.
  --next [ledger] [--json]          Prints next recommended action and state header.
  --header [ledger] [--json]        Synthesizes Line 1 action and Line 2 state header.
  --run [ledger] [--json]           Executes check commands for all runnable gates.
  --check <gate_id> [ledger]        Runs the gate CHECK; marks [x] only if it passes. [--strict] [--force] [--waive-red "<why>"]
  --baseline [ledger]               Runs open gates BEFORE the work; records which are RED (evidence for --strict).
  --evidence [ledger]               Shows the hash-chained evidence log and verifies it is untampered.
  --lint [ledger] [--json]          Lints working memory bounds, anchors, and gates.
  --export-templates [dir]          Dumps embedded templates to standalone directory.

Prototype Spikes:
  --scaffold-spike <logic|ui> <name> "<question>" [ledger]
  --verify-spike <artifact-path> [--json]
  --settle-spike <name> "<adr>" [ledger]

Candidate 1: Event-Sourced Ledger & Replay:
  --events [ledger] [--json]        Dumps append-only JSONL event stream.
  --replay <version> [ledger]       Deterministically reconstructs state at version.
  --rollback <version> [ledger]     Rolls back event stream to version with compensation event.
  --verify-merkle [path]            Verifies cryptographic Merkle DAG parent links and state root integrity.
  --merkle-diff <f1> <f2>           Compares two Merkle event DAGs and reports state divergence.
  --merkle-sync <loc> <rem> [--out] Synchronizes remote Merkle DAG into local with causal ordering.

Candidate 2: Git Worktree Swarm Orchestrator:
  --frontier [ledger] [--json]      Returns unblocked DAG frontier gates ready for parallel execution.
  --swarm-wave [ledger] [--json]    Executes a parallel wave of DAG frontier gates across actors.
  --swarm-run [ledger] [--json]     Iteratively drives swarm execution until complete convergence.
  --swarm-worktree <actor_id>       Provisions or inspects an isolated worktree for actor.
  --swarm-merge <actor> <gate>      Executes atomic Saga merge of actor branch with rollback tombstone.
  --swarm-provision <gate_id> [b]   Allocates an isolated git worktree for gate_id.
  --swarm-clean <gate_id>           Prunes and cleans up worktree after merge.
  --swarm-status [--json]           Lists active worktrees and mapped gates.
  --chaos-test [profile]            Executes synthetic chaos injection and self-healing recovery test.
  --chaos-report [--json]           Outputs mesh fault tolerance resilience report.

Candidate 3: Smart-Zone Context Compactor:
  --compact [ledger] [--json]       Archives settled gates to .focusgate/ARCHIVE.md (<150k token defense).
  --estimate-tokens <file|text>     Calculates fast heuristic token count.
  --actor-context <actor_id>        Inspects active sliding turn window and token budget for actor.
  --compact-swarm [ledger]          Collapses settled gate evidence into cryptographic proof tree archive.

Candidate 4 & Intelligence Suite:
  --guard "<command>" [--json]      Verifies command safety against destructive git guardrails.
  --verify-sandbox [--json]         Verifies sandbox path jail boundaries and command blacklist.
  --sandbox-exec "<command>"        Executes command within security sandbox and command guardrails.
  --install-guardrails [repo]       Installs commit/push hooks for destructive safety.
  --lint-grounding <doc> [ledger]   Lints document against grounded glossary terms.
  --compile-spec <spec> [--out o]   Compiles markdown spec into DAG-connected GATES.md.
  --re-pitch "<text>"               Reframes pitch into ASD-STE100 Simplified Technical English.
  --route "<query>" [--json]        Autonomous router classifying intent and selecting pipeline.
  --retro [ledger] [--json]         Generates retrospective audit of settled ledger.
  --version                         Prints engine version and release label.
  --help                            Displays this guide.
"""
    from core.version import VERSION
    help_text = help_text.replace("@VERSION@", "v" + VERSION)
    print(help_text)


def build_parser():
    parser = argparse.ArgumentParser(
        description='FocusGate v2.8 (Single-Source Facet Lifecycle & Wave Verification Release).',
        add_help=False
    )
    parser.add_argument('--json', action='store_true', help='Output in JSON format')

    grp_Master_Orchestrator = parser.add_argument_group('Master Orchestrator & Sub-Agents (v2.8)')
    grp_Master_Orchestrator.add_argument('--mcp', action='store_true', help='Runs stdio JSON-RPC 2.0 Model Context Protocol (MCP) tool server.')
    grp_Master_Orchestrator.add_argument('--mcp-hub', action='store_true', help='Aggregates local and remote MCP servers into unified tool mesh.')
    grp_Master_Orchestrator.add_argument('--mcp-call', nargs='*', default=None, help='Executes a namespaced tool across connected MCP servers.')
    grp_Master_Orchestrator.add_argument('--watch', nargs='*', default=None, help='Starts reactive in-memory daemon file watcher (<15ms gate re-evaluation).')
    grp_Master_Orchestrator.add_argument('--heal', nargs='*', default=None, help='Autonomously diagnoses and remediates failing gates using isolated worktree and 3-attempt circuit breaker.')
    grp_Master_Orchestrator.add_argument('--actor-status', action='store_true', help='Inspects live swarm actors, states, and mailboxes.')
    grp_Master_Orchestrator.add_argument('--daemon-start', nargs='*', default=None, help='Starts autonomous swarm supervisor daemon.')
    grp_Master_Orchestrator.add_argument('--daemon-status', nargs='*', default=None, help='Queries status of running swarm daemon over Unix socket.')
    grp_Master_Orchestrator.add_argument('--daemon-stop', nargs='*', default=None, help='Stops background swarm supervisor daemon.')
    grp_Master_Orchestrator.add_argument('--daemon-stream', nargs='*', default=None, help='Streams live broadcast events from swarm supervisor daemon.')
    grp_Master_Orchestrator.add_argument('--daemon-events', nargs='*', default=None, help='Queries recent broadcast events from swarm supervisor daemon.')
    grp_Master_Orchestrator.add_argument('--sdk-schema', action='store_true', help='Outputs polyglot JSON schema and type models for actor SDKs.')
    grp_Master_Orchestrator.add_argument('--sdk-ping', nargs='*', default=None, help='Pings supervisor daemon using native client SDK.')
    grp_Master_Orchestrator.add_argument('--barrier-bench', nargs='*', default=None, help='Benchmarks multi-actor wave barrier convergence latency.')
    grp_Master_Orchestrator.add_argument('--synthesize-persona', nargs='*', default=None, help='Synthesizes domain-specific actor persona dynamically.')
    grp_Master_Orchestrator.add_argument('--grid-status', action='store_true', help='Inspects distributed Merkle CRDT grid status and event count.')
    grp_Master_Orchestrator.add_argument('--grid-node', nargs='*', default=None, help='Starts distributed TCP grid socket node.')
    grp_Master_Orchestrator.add_argument('--memory-search', nargs='*', default=None, help='Searches episodic immune memory and prior failure modes.')
    grp_Master_Orchestrator.add_argument('--limit', type=int, default=None, help='With --memory-search: maximum number of matches to return (default 5).')
    grp_Master_Orchestrator.add_argument('--speculative-wave', nargs='*', default=None, help='Schedules speculative wave execution for downstream gates.')
    grp_Master_Orchestrator.add_argument('--auto-refactor', nargs='*', default=None, help='Deterministically refactors loops and shotgun exceptions.')
    grp_Master_Orchestrator.add_argument('--dry-run', action='store_true', default=False, help='With --auto-refactor: report the proposed repairs WITHOUT writing to disk.')
    grp_Master_Orchestrator.add_argument('--quorum-vote', nargs='*', default=None, help='Evaluates decentralized quorum voting across grid nodes.')
    grp_Master_Orchestrator.add_argument('--adaptive-budget', nargs='*', default=None, help='Allocates domain-weighted context budget for an actor.')
    grp_Master_Orchestrator.add_argument('--simulate-partition', nargs='*', default=None, help='Simulates network partition and verifies CRDT recovery.')
    grp_Master_Orchestrator.add_argument('--migrate-task', nargs='*', default=None, help='Live-migrates worktree task across grid nodes.')
    grp_Master_Orchestrator.add_argument('--synthesize-contract', nargs='*', default=None, help='Synthesizes defensive type and non-null AST guards.')
    grp_Master_Orchestrator.add_argument('--swarm-liveness', nargs='*', default=None, help='Monitors real-time actor heartbeat liveness and deadlocks.')
    grp_Master_Orchestrator.add_argument('--verify-attestation', nargs='*', default=None, help='Verifies cryptographic Merkle inclusion proofs and state attestations.')
    grp_Master_Orchestrator.add_argument('--evolve-directives', nargs='*', default=None, help='Proposes autonomous rule and prompt directive improvements.')
    grp_Master_Orchestrator.add_argument('--wire-bench', nargs='*', default=None, help='Benchmarks high-throughput binary wire protocol framing.')
    grp_Master_Orchestrator.add_argument('--orchestrate', nargs='*', default=None, help='Decompose plan and orchestrate sub-agents')
    grp_Master_Orchestrator.add_argument('--preview', action='store_true', help='Preview planned sub-agent DAG without dispatch')
    grp_Master_Orchestrator.add_argument('--dispatch', action='store_true', help='Dispatch unblocked frontier sub-agents')
    grp_Master_Orchestrator.add_argument('--agent-settle', nargs='*', default=None, help='Sub-agent signals completion with receipt JSON')
    grp_Master_Orchestrator.add_argument('--receipt', nargs='*', default=None, help='Path to receipt file for --agent-settle')
    grp_Master_Orchestrator.add_argument('--orchestrator-verify', nargs='*', default=None, help='Runs cross-agent coherence verification on bundle')
    grp_Master_Orchestrator.add_argument('--agent-merge', nargs='*', default=None, help='Merges verified sub-agent branch into main')
    grp_Master_Orchestrator.add_argument('--agent-status', nargs='*', default=None, help='Inspects active sub-agent timeouts and bus activity')
    grp_Master_Orchestrator.add_argument('--stage-status', action='store_true', help='Displays active stage and intra-stage matrix verification status')
    grp_Master_Orchestrator.add_argument('--verify-stage', nargs='*', default=None, help='Evaluates intra-stage verification matrix for stage_id')
    grp_Master_Orchestrator.add_argument('--verify-wave', action='store_true', help='Runs every verifier (index, contracts, tokens, help, stage, sufficiency, production) and prints ONE aggregate verdict (v2.8).')
    grp_Master_Orchestrator.add_argument('--checkpoint', nargs='?', const='v2.8-prod', default=None, help='Creates an immutable production checkpoint of orchestrator state (defaults to v2.8-prod)')
    grp_Master_Orchestrator.add_argument('--restore-checkpoint', nargs='*', default=None, help='Restores orchestrator state from a saved production checkpoint')
    grp_Master_Orchestrator.add_argument('--list-checkpoints', action='store_true', help='Lists all saved production checkpoints with integrity verification')
    grp_Master_Orchestrator.add_argument('--audit-production', action='store_true', help='Runs complete audit of v2.8 production readiness')

    grp_JIT_Hydration___Hybrid_Routing__v2_8_ = parser.add_argument_group('JIT Hydration & Hybrid Routing (v2.8)')
    grp_JIT_Hydration___Hybrid_Routing__v2_8_.add_argument('--hydrate-facet', nargs='*', default=None, help='Hydrates compact declarative micro-directive for facet.')
    grp_JIT_Hydration___Hybrid_Routing__v2_8_.add_argument('--depth', default=None, choices=['directive', 'playbook', 'full'], help='With --hydrate-facet: directive (injected rules), playbook (rules + process), full (whole file; default).')
    grp_JIT_Hydration___Hybrid_Routing__v2_8_.add_argument('--list-facets', nargs='*', default=None, help='Lists all facets across 5 Bounded Contexts with trigger counts.')
    grp_JIT_Hydration___Hybrid_Routing__v2_8_.add_argument('--lint-facets', nargs='*', default=None, help='Lints facet contracts: collisions, zero triggers, mode mismatch, dead oracle flags.')
    grp_JIT_Hydration___Hybrid_Routing__v2_8_.add_argument('--synthesize-pipeline', nargs='*', default=None, help='Fast-path deterministic classifier (<5ms, 0 tokens).')
    grp_JIT_Hydration___Hybrid_Routing__v2_8_.add_argument('-p', nargs='*', default=None, help='Short alias for --synthesize-pipeline.')
    grp_JIT_Hydration___Hybrid_Routing__v2_8_.add_argument('--audit-adapter', action='store_true', help='Audits distilled Student LoRA router adapter integrity, parameter counts, and SHA-256 weight checksum.')
    grp_JIT_Hydration___Hybrid_Routing__v2_8_.add_argument('--audit-model', action='store_true', help='Alias for --audit-adapter.')
    grp_JIT_Hydration___Hybrid_Routing__v2_8_.add_argument('--distilled-route', nargs='*', default=None, help='Routes task description through distilled Student LoRA router with Invariant Action Envelope.')
    grp_JIT_Hydration___Hybrid_Routing__v2_8_.add_argument('--export-colab-pack', nargs='*', default=None, help='Exports verified trajectory dataset and turnkey Google Colab training pack.')

    grp_Design_Verification___Governance = parser.add_argument_group('Design Verification & Governance')
    grp_Design_Verification___Governance.add_argument('--audit-contrast', nargs='*', default=None, help='Calculates WCAG 2.1 relative luminance and contrast ratio.')
    grp_Design_Verification___Governance.add_argument('--audit-tokens', nargs='*', default=None, help='Audits CSS/TSX/HTML files for unanchored hardcoded styling.')
    grp_Design_Verification___Governance.add_argument('--sync-tokens', nargs='*', default=None, help='Parses brand markdown and generates design tokens CSS.')
    grp_Design_Verification___Governance.add_argument('--audit-safe-zone', nargs='*', default=None, help='Validates elements against safe-zone bounding box.')
    grp_Design_Verification___Governance.add_argument('--audit-design-cliche', nargs='*', default=None, help='Audits CSS/HTML/TSX files for 5 canonical AI design tells.')
    grp_Design_Verification___Governance.add_argument('--audit-prose-cliche', nargs='*', default=None, help='Audits text/Markdown files for AI writing and prose tells.')
    grp_Design_Verification___Governance.add_argument('--audit-code-cliche', nargs='*', default=None, help='Audits Python files for shallow architecture and shotgun error tells.')
    grp_Design_Verification___Governance.add_argument('--adversarial-audit', nargs='*', default=None, help='Runs adversarial socratic tournament on architecture proposals.')
    grp_Design_Verification___Governance.add_argument('--dialectic-review', nargs='*', default=None, help='Runs autonomous Socratic peer review on actor branch/gate.')
    grp_Design_Verification___Governance.add_argument('--coherence-status', nargs='*', default=None, help='Inspects status of signed Coherence Receipts.')
    grp_Design_Verification___Governance.add_argument('--audit-loop-safety', nargs='*', default=None, help='Audits Python files for infinite loop hazards and unhalting recursion.')
    grp_Design_Verification___Governance.add_argument('--watchdog-run', nargs='*', default=None, help='Executes command guarded by CPU execution watchdog and timeout.')
    grp_Design_Verification___Governance.add_argument('--audit-all', nargs='*', default=None, help='Audits workspace across prose, code, and design using unified multi-oracle engine.')
    grp_Design_Verification___Governance.add_argument('--audit-context-sufficiency', nargs='*', default=None, help='Audits generated AGENT_PROMPT.md briefs for context sufficiency (no bare @pointers / lost summaries) — v2.8 Part 3.')

    grp_Domain_Driven_Design_Governance = parser.add_argument_group('Domain-Driven Design Governance')
    grp_Domain_Driven_Design_Governance.add_argument('--audit-domain', nargs='*', default=None, help='Audits workspace against CONTEXT.md and checks positive steering.')
    grp_Domain_Driven_Design_Governance.add_argument('--validate-contracts', nargs='*', default=None, help='Validates ledger.events.jsonl against typed event schemas.')

    grp_Writing_Suite_Commands__v1_5_1_ = parser.add_argument_group('Writing Suite Commands (v1.5.1)')
    grp_Writing_Suite_Commands__v1_5_1_.add_argument('--fragment', nargs='*', default=None, help='Appends unstructured thought to FRAGMENTS.md.')
    grp_Writing_Suite_Commands__v1_5_1_.add_argument('--brief', nargs='*', default=None, help='Compiles task into machine-readable subagent brief.')
    grp_Writing_Suite_Commands__v1_5_1_.add_argument('--shape', nargs='*', default=None, help='Initiates concept-grounded technical spec shaping session.')
    grp_Writing_Suite_Commands__v1_5_1_.add_argument('--beat', nargs='*', default=None, help='Proposes candidate next narrative beats.')

    grp_Meta_Orchestrator___Cognitive_Scaffolding__v1_5_ = parser.add_argument_group('Meta-Orchestrator & Cognitive Scaffolding (v1.5)')
    grp_Meta_Orchestrator___Cognitive_Scaffolding__v1_5_.add_argument('--seed', nargs='*', default=None, help='Scaffolds .focusgate/GATES-SEED.md with 2-minute micro-action.')
    grp_Meta_Orchestrator___Cognitive_Scaffolding__v1_5_.add_argument('--reorient', nargs='*', default=None, help='Restores working memory in <3s answering What, Where, and Next Action.')
    grp_Meta_Orchestrator___Cognitive_Scaffolding__v1_5_.add_argument('--queue-next', nargs='*', default=None, help='Outputs single active gate and buffers remaining DAG frontier.')
    grp_Meta_Orchestrator___Cognitive_Scaffolding__v1_5_.add_argument('--queue-status', nargs='*', default=None, help='Displays active gate status and buffered count.')
    grp_Meta_Orchestrator___Cognitive_Scaffolding__v1_5_.add_argument('--deepen', nargs='*', default=None, help='Zooms depth level (L1 Action, L2 Structured Ledger, L3 Swarm/Audit).')
    grp_Meta_Orchestrator___Cognitive_Scaffolding__v1_5_.add_argument('--ledger-root', nargs='*', default=None, help='Explicitly sets ledger namespace root (fixes ADR-0009 Wart B).')

    grp_Core_Commands = parser.add_argument_group('Core Commands')
    grp_Core_Commands.add_argument('--init', nargs='*', default=None, help='Scaffolds .focusgate/GATES.md with domain anchors.')
    grp_Core_Commands.add_argument('--status', nargs='*', default=None, help='Displays state vector and gate status.')
    grp_Core_Commands.add_argument('--next', nargs='*', default=None, help='Prints next recommended action and state header.')
    grp_Core_Commands.add_argument('--header', nargs='*', default=None, help='Synthesizes Line 1 action and Line 2 state header.')
    grp_Core_Commands.add_argument('--run', nargs='*', default=None, help='Executes check commands for all runnable gates.')
    grp_Core_Commands.add_argument('--check', nargs='*', default=None, help='Executes the gate CHECK and, only if it passes, marks the gate [x]. Options: --strict, --force, --waive-red <reason>.')
    grp_Core_Commands.add_argument('--baseline', nargs='*', default=None, help='Runs every open gate once BEFORE the work and records which are red (evidence for --strict).')
    grp_Core_Commands.add_argument('--evidence', nargs='*', default=None, help='Shows the hash-chained evidence log and verifies it was not altered.')
    grp_Core_Commands.add_argument('--strict', action='store_true', default=False, help='With --check: require a prior red observation of this exact CHECK/EXPECT.')
    grp_Core_Commands.add_argument('--force', action='store_true', default=False, help='With --check: override integrity errors (logged in the evidence log).')
    grp_Core_Commands.add_argument('--waive-red', default=None, help='With --check --strict: waive the red requirement with a recorded reason.')
    grp_Core_Commands.add_argument('--lint', nargs='*', default=None, help='Lints working memory bounds, anchors, and gates.')
    grp_Core_Commands.add_argument('--export-templates', nargs='*', default=None, help='Dumps embedded templates to standalone directory.')

    grp_Prototype_Spikes = parser.add_argument_group('Prototype Spikes')
    grp_Prototype_Spikes.add_argument('--scaffold-spike', nargs='*', default=None, help='Scaffolds an interactive prototype spike template.')
    grp_Prototype_Spikes.add_argument('--verify-spike', nargs='*', default=None, help='Verifies prototype spike assertions and DOM invariants.')
    grp_Prototype_Spikes.add_argument('--settle-spike', nargs='*', default=None, help='Settles completed prototype spike evidence and generates receipt.')

    grp_Candidate_1__Event_Sourced_Ledger___Replay = parser.add_argument_group('Candidate 1: Event-Sourced Ledger & Replay')
    grp_Candidate_1__Event_Sourced_Ledger___Replay.add_argument('--events', nargs='*', default=None, help='Dumps append-only JSONL event stream.')
    grp_Candidate_1__Event_Sourced_Ledger___Replay.add_argument('--replay', nargs='*', default=None, help='Deterministically reconstructs state at version.')
    grp_Candidate_1__Event_Sourced_Ledger___Replay.add_argument('--rollback', nargs='*', default=None, help='Rolls back event stream to version with compensation event.')
    grp_Candidate_1__Event_Sourced_Ledger___Replay.add_argument('--verify-merkle', nargs='*', default=None, help='Verifies cryptographic Merkle DAG parent links and state root integrity.')
    grp_Candidate_1__Event_Sourced_Ledger___Replay.add_argument('--merkle-diff', nargs='*', default=None, help='Compares two Merkle event DAGs and reports state divergence.')
    grp_Candidate_1__Event_Sourced_Ledger___Replay.add_argument('--merkle-sync', nargs='*', default=None, help='Synchronizes remote Merkle DAG into local with causal ordering.')

    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator = parser.add_argument_group('Candidate 2: Git Worktree Swarm Orchestrator')
    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator.add_argument('--frontier', nargs='*', default=None, help='Returns unblocked DAG frontier gates ready for parallel execution.')
    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator.add_argument('--swarm-wave', nargs='*', default=None, help='Executes a parallel wave of DAG frontier gates across actors.')
    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator.add_argument('--swarm-run', nargs='*', default=None, help='Iteratively drives swarm execution until complete convergence.')
    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator.add_argument('--swarm-worktree', nargs='*', default=None, help='Provisions or inspects an isolated worktree for actor.')
    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator.add_argument('--swarm-merge', nargs='*', default=None, help='Executes atomic Saga merge of actor branch with rollback tombstone.')
    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator.add_argument('--swarm-provision', nargs='*', default=None, help='Allocates an isolated git worktree for gate_id.')
    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator.add_argument('--swarm-clean', nargs='*', default=None, help='Prunes and cleans up worktree after merge.')
    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator.add_argument('--swarm-status', nargs='*', default=None, help='Lists active worktrees and mapped gates.')
    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator.add_argument('--chaos-test', nargs='*', default=None, help='Executes synthetic chaos injection and self-healing recovery test.')
    grp_Candidate_2__Git_Worktree_Swarm_Orchestrator.add_argument('--chaos-report', action='store_true', help='Outputs mesh fault tolerance resilience report.')

    grp_Candidate_3__Smart_Zone_Context_Compactor = parser.add_argument_group('Candidate 3: Smart-Zone Context Compactor')
    grp_Candidate_3__Smart_Zone_Context_Compactor.add_argument('--compact', nargs='*', default=None, help='Archives settled gates to .focusgate/ARCHIVE.md (<150k token defense).')
    grp_Candidate_3__Smart_Zone_Context_Compactor.add_argument('--estimate-tokens', nargs='*', default=None, help='Calculates fast heuristic token count.')
    grp_Candidate_3__Smart_Zone_Context_Compactor.add_argument('--actor-context', nargs='*', default=None, help='Inspects active sliding turn window and token budget for actor.')
    grp_Candidate_3__Smart_Zone_Context_Compactor.add_argument('--compact-swarm', nargs='*', default=None, help='Collapses settled gate evidence into cryptographic proof tree archive.')

    grp_Candidate_4___Intelligence_Suite = parser.add_argument_group('Candidate 4 & Intelligence Suite')
    grp_Candidate_4___Intelligence_Suite.add_argument('--guard', nargs='*', default=None, help='Verifies command safety against destructive git guardrails.')
    grp_Candidate_4___Intelligence_Suite.add_argument('--verify-sandbox', action='store_true', help='Verifies sandbox path jail boundaries and command blacklist.')
    grp_Candidate_4___Intelligence_Suite.add_argument('--sandbox-exec', nargs='*', default=None, help='Executes command within security sandbox and command guardrails.')
    grp_Candidate_4___Intelligence_Suite.add_argument('--lint-grounding', nargs='*', default=None, help='Lints document against grounded glossary terms.')
    grp_Candidate_4___Intelligence_Suite.add_argument('--compile-spec', nargs='*', default=None, help='Compiles markdown spec into DAG-connected GATES.md.')
    grp_Candidate_4___Intelligence_Suite.add_argument('--re-pitch', nargs='*', default=None, help='Reframes pitch into ASD-STE100 Simplified Technical English.')
    grp_Candidate_4___Intelligence_Suite.add_argument('--route', nargs='*', default=None, help='Autonomous router classifying intent and selecting pipeline.')
    grp_Candidate_4___Intelligence_Suite.add_argument('--version', nargs='*', default=None,
                        help='Prints engine version and release label (read from core/version.py).')
    grp_Candidate_4___Intelligence_Suite.add_argument('--help', nargs='*', default=None, help='Displays this guide.')

    grp_Execution_Rigor___Ephemeral_Architecture = parser.add_argument_group('Execution Rigor & Ephemeral Architecture')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--unlazy-rigor', nargs='*', default=None, help='Audits workspace/files for fake completion, placeholders, and superficial stubs.')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--select-tool', nargs='*', default=None, help='Deterministic tool selection matrix evaluating intent and preconditions.')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--patch-lint', nargs='*', default=None, help='Pre-validates patch block preconditions before applying edits.')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--slice-facet', nargs='*', default=None, help='Extracts targeted section from facet directive (<300 tokens).')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--retrieve-snippet', nargs='*', default=None, help='On-demand regex grep search with line-windowed snippet formatting.')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--ephemeral-run', nargs='*', default=None, help='Executes isolated gate check within sandboxed ephemeral session.')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--handoff', nargs='*', default=None, help='Encapsulates inter-skill delta packet handoff.')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--audit-handoffs', nargs='*', default=None, help='Audits handoff event log for ACL contract conformance.')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--harvest-trajectories', nargs='*', default=None, help='Extracts verified execution trajectories into SFT dataset.')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--harvest-swarm', nargs='*', default=None, help='Harvests multi-agent swarm problem-solving traces.')
    grp_Execution_Rigor___Ephemeral_Architecture.add_argument('--export-swarm-pack', nargs='*', default=None, help='Exports harvested swarm trajectories to fine-tuning pack (openai|claude|gemini).')
    return parser


def known_flags() -> set:
    """Every option string the parser accepts."""
    return {o for a in build_parser()._actions for o in a.option_strings}
