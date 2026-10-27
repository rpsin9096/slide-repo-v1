"""Orchestrator and agent lifecycle commands."""
import json
import os
import sys

from core.agent_brief import AgentReceiptBundle
from core.cli.registry import CommandContext
from core.cli.registry import command
from core.orchestrator_kernel import OrchestratorKernel


def _match_orchestrate(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'orchestrate', None) is not None


@command('orchestrate', flags=('--orchestrate',), dest=None, summary='orchestrate command', matches=_match_orchestrate, order=232)
def orchestrate(ctx: CommandContext) -> int:
    """orchestrate command"""
    if ctx.args.preview and ctx.args.dispatch:   # validate before any side effect (no orchestrator state is created)
        print("[Error] --preview and --dispatch are opposites; pass one (dispatch is the default).", file=sys.stderr)
        return 2
    args = ctx.args
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    raw_task = args.orchestrate
    task_query = " ".join(raw_task) if isinstance(raw_task, list) and raw_task else "Autonomous Multi-Agent Task"
    if OrchestratorKernel is None:
        print("[Error] OrchestratorKernel not available", file=sys.stderr)
        return (1)
    orch = OrchestratorKernel(ledger_root)
    stages = orch.plan_decomposition(task_query)

    if args.preview:
        if is_json:
            print(json.dumps({"pipeline": orch.aggregate.pipeline, "planned_stages": stages, "frontier_buffer": [g for g in orch.aggregate.gates.values() if not g.get("depends_on")]}, indent=2))
        else:
            print("=" * 80)
            print(f"FOCUSGATE v2.8 MASTER ORCHESTRATOR PREVIEW: {orch.aggregate.pipeline}")
            print("=" * 80)
            print(f"Objective: {task_query}")
            print(f"\nPlanned Acceptance Gate DAG ({len(stages)} stages):")
            for idx, s in enumerate(stages, 1):
                deps_str = f" (depends on: {', '.join(s.get('deps', []))})" if s.get("deps") else " (ROOT / UNBLOCKED)"
                print(f"  {idx}. [{s['facet']}] {s['gate_id']}: {s['title']}{deps_str}")
            print(f"\n[Preview Mode] 0 sub-agents dispatched. Use --dispatch to spawn frontier briefs.")
            print("=" * 80)
        return (0)

    briefs = orch.dispatch_frontier()
    if is_json:
        print(json.dumps({
            "pipeline": orch.aggregate.pipeline,
            "stages": stages,
            "dispatched_count": len(briefs),
            "briefs": [b.to_dict() for b in briefs]
        }, indent=2))
    else:
        print("=" * 80)
        print(f"FOCUSGATE v2.8 MASTER ORCHESTRATOR DISPATCH: {orch.aggregate.pipeline}")
        print("=" * 80)
        print(f"Objective: {task_query}")
        print(f"Dispatched Frontier Sub-Agents ({len(briefs)} active slots):")
        for b in briefs:
            print(f"\n  • Agent Brief ID: {b.brief_id[:8]} -> Gate: {b.gate_id} [{b.facet}]")
            print(f"    Task: {b.task_summary}")
            print(f"    Worktree: .focusgate/worktrees/agent-{b.gate_id}")
            print(f"    System Prompt: .focusgate/worktrees/agent-{b.gate_id}/AGENT_PROMPT.md")
        print("\n[✓] Frontier briefs compiled and dispatched for external AI sessions.")
        print("=" * 80)
    return (0)


def _match_agent_settle(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'agent_settle', None) is not None


@command('agent-settle', flags=('--agent-settle',), dest=None, summary='agent-settle command', matches=_match_agent_settle, order=233)
def agent_settle(ctx: CommandContext) -> int:
    """agent-settle command"""
    args = ctx.args
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    raw_gate = args.agent_settle
    if not raw_gate:
        print("Usage: focus-gate.py --agent-settle <gate_id> --receipt <receipt.json>", file=sys.stderr)
        return (1)
    gate_id = raw_gate[0] if isinstance(raw_gate, list) else str(raw_gate)
    receipt_path = args.receipt[0] if args.receipt and isinstance(args.receipt, list) else (args.receipt or "")

    if not receipt_path or not os.path.exists(receipt_path):
        print(f"[Error] Receipt file not found: {receipt_path}", file=sys.stderr)
        return (1)

    with open(receipt_path, "r", encoding="utf-8") as f:
        receipt_data = json.load(f)

    orch = OrchestratorKernel(ledger_root)
    brief = orch.dispatched_briefs.get(gate_id)
    brief_id = brief.brief_id if brief else "external-agent"

    bundle = AgentReceiptBundle.create(
        gate_id=gate_id,
        brief_id=brief_id,
        gate_receipts=[receipt_data] if isinstance(receipt_data, dict) else receipt_data,
        artifacts_produced=receipt_data.get("artifacts_produced", []) if isinstance(receipt_data, dict) else [],
        patch_contents=[receipt_data.get("output", "")] if isinstance(receipt_data, dict) else []
    )

    verdict = orch.receive_bundle(bundle)
    if is_json:
        print(json.dumps({"gate_id": gate_id, "bundle_id": bundle.bundle_id, "verified": verdict.verified, "verdict": verdict.to_dict()}, indent=2))
    else:
        status_icon = "✓" if verdict.verified else "✗"
        print(f"[{status_icon}] Agent Settle Evaluation for {gate_id}: {'VERIFIED' if verdict.verified else 'REJECTED'}")
        if verdict.failed_criteria:
            print(f"    Failed criteria: {', '.join(verdict.failed_criteria)}")
        else:
            print(f"    Bundle ID: {bundle.bundle_id}")
            print(f"    Next Action: python3 focus-gate.py --agent-merge {gate_id}")
    return (0 if verdict.verified else 1)


def _match_orchestrator_verify(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'orchestrator_verify', None) is not None


@command('orchestrator-verify', flags=('--orchestrator-verify',), dest=None, summary='orchestrator-verify command', matches=_match_orchestrator_verify, order=234)
def orchestrator_verify(ctx: CommandContext) -> int:
    """orchestrator-verify command"""
    args = ctx.args
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    raw_id = args.orchestrator_verify
    if not raw_id:
        print("Usage: focus-gate.py --orchestrator-verify <bundle_id_or_gate_id>", file=sys.stderr)
        return (1)
    target_id = raw_id[0] if isinstance(raw_id, list) else str(raw_id)
    orch = OrchestratorKernel(ledger_root)

    bundle = orch.active_bundles.get(target_id)
    if not bundle:
        b_file = os.path.join(orch._bundles_dir, f"{target_id}.json")
        if os.path.exists(b_file):
            with open(b_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                bundle = AgentReceiptBundle(
                    bundle_id=d["bundleId"],
                    gate_id=d["gateId"],
                    brief_id=d["briefId"],
                    gate_receipts=d["gateReceipts"],
                    delta_ids=d.get("deltaIds", []),
                    artifacts_produced=d["artifactsProduced"],
                    patch_hashes=d["patchHashes"],
                    status=d.get("status", "PENDING")
                )
    if not bundle:
        print(f"[Error] Bundle not found for: {target_id}", file=sys.stderr)
        return (1)

    verdict = orch.receive_bundle(bundle)
    if is_json:
        print(json.dumps({"bundle_id": bundle.bundle_id, "verified": verdict.verified, "verdict": verdict.to_dict()}, indent=2))
    else:
        print(f"Orchestrator Coherence Verdict for {bundle.gate_id} ({bundle.bundle_id[:8]}):")
        print(f"  Status: {'PASS' if verdict.verified else 'FAIL'} (Compliance: {verdict.compliance_score}%)")
        for c in verdict.passed_criteria:
            print(f"  [✓] {c}")
        for c in verdict.failed_criteria:
            print(f"  [!] {c}")
    return (0 if verdict.verified else 1)


def _match_agent_merge(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'agent_merge', None) is not None


@command('agent-merge', flags=('--agent-merge',), dest=None, summary='agent-merge command', matches=_match_agent_merge, order=235)
def agent_merge(ctx: CommandContext) -> int:
    """agent-merge command"""
    args = ctx.args
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    raw_gate = args.agent_merge
    if not raw_gate:
        print("Usage: focus-gate.py --agent-merge <gate_id>", file=sys.stderr)
        return (1)
    target_gate = raw_gate[0] if isinstance(raw_gate, list) else str(raw_gate)
    orch = OrchestratorKernel(ledger_root)
    ok = orch.merge_results(target_gate)
    if is_json:
        print(json.dumps({"gate_id": target_gate, "merged": ok}))
    else:
        if ok:
            print(f"[✓] Successfully merged agent branch for {target_gate} and settled gate.")
        else:
            print(f"[!] Failed to merge {target_gate}. DLQ tombstone escalated.", file=sys.stderr)
    return (0 if ok else 1)


def _match_agent_status(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'agent_status', None) is not None


@command('agent-status', flags=('--agent-status',), dest=None, summary='agent-status command', matches=_match_agent_status, order=236)
def agent_status(ctx: CommandContext) -> int:
    """agent-status command"""
    args = ctx.args
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    orch = OrchestratorKernel(ledger_root)
    mon = orch.monitor_agents()
    deltas = orch.context_bus.get_all_deltas()
    if is_json:
        print(json.dumps({"monitoring": mon, "context_bus_deltas": [d.to_dict() for d in deltas]}, indent=2))
    else:
        print("=" * 80)
        print("FOCUSGATE v2.8 SUB-AGENT ORCHESTRATOR STATUS")
        print("=" * 80)
        print(f"Active Dispatched Agents: {mon['active_count']}")
        print(f"Timed Out Agents: {mon['timed_out_count']}")
        for a in mon["agents"]:
            t_flag = "[TIMED OUT]" if a["timed_out"] else "[ACTIVE]"
            print(f"  • {a['gate_id']} [{a['facet']}]: {t_flag} elapsed: {a['elapsed_s']}s / max: {a['timeout_s']}s")
        print(f"\nSharedContextBus Broadcast Stream ({len(deltas)} deltas recorded):")
        for d in deltas[-5:]:
            print(f"  - [{d.delta_type}] from {d.source_agent} (~{d.payload_tokens} tokens): {d.content[:70]}")
    return (0)


def _match_stage_status(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'stage_status', False)


@command('stage-status', flags=('--stage-status',), dest=None, summary='stage-status command', matches=_match_stage_status, order=237)
def stage_status(ctx: CommandContext) -> int:
    """stage-status command"""
    args = ctx.args
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    orch = OrchestratorKernel(ledger_root)
    vec = orch.aggregate.get_state_vector()
    stages_data = [s.to_dict() for s in orch.stage_definitions] if orch.stage_definitions else orch.aggregate.stages
    if is_json:
        print(json.dumps({"pipeline": vec["pipeline"], "active_stage": vec["stage"], "stage_index": vec.get("stage_index", 1), "stages": stages_data}, indent=2))
    else:
        print("=" * 80)
        print(f"FOCUSGATE v2.8 STAGE VERIFICATION MATRIX: {vec['pipeline']}")
        print("=" * 80)
        print(f"Active Stage Anchor: {vec['stage']}")
        print(f"Active Gate: {vec['active_gate']} (Queue: {vec['queue_depth']} pending)")
        print("\nStage Progress Matrix:")
        for idx, s in enumerate(stages_data, 1):
            s_name = s.get("name") or s.get("title") or s.get("stage_id", f"Stage-{idx}")
            s_status = s.get("status", "PENDING")
            icon = "[✓]" if s_status == "VERIFIED" else ("[▶]" if idx == vec.get("stage_index", 1) else "[ ]")
            print(f"  {icon} Stage {idx}: {s_name} [{s_status}]")
        print("=" * 80)
    return (0)


def _match_verify_stage(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'verify_stage', None) is not None


@command('verify-stage', flags=('--verify-stage',), dest=None, summary='verify-stage command', matches=_match_verify_stage, order=238)
def verify_stage(ctx: CommandContext) -> int:
    """verify-stage command"""
    args = ctx.args
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    raw_stage = args.verify_stage
    target_stage_id = raw_stage[0] if isinstance(raw_stage, list) and raw_stage else str(raw_stage)
    orch = OrchestratorKernel(ledger_root)
    target_def = next((s for s in orch.stage_definitions if s.stage_id == target_stage_id or str(s.index) == str(target_stage_id)), None)
    if not target_def:
        print(f"Error: Stage '{target_stage_id}' not found.", file=sys.stderr)
        return (1)
    ok, reasons = orch.verify_stage(target_stage_id)
    if is_json:
        print(json.dumps({"stage_id": target_def.stage_id, "verified": ok, "reasons": reasons, "status": target_def.status}, indent=2))
    else:
        print(f"Stage Verification Matrix for {target_def.name}: {'PASS' if ok else 'FAIL'}")
        if not ok:
            for r in reasons:
                print(f"  [!] {r}")
    return (0 if ok else 1)
