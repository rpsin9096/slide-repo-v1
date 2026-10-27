"""Token economy, tool selection, snippets, harvesting and distilled routing."""
import json
import os
import subprocess
import sys

from core.cli.intent import AutonomousRouter
from core.cli.registry import CommandContext
from core.cli.registry import command
from core.compaction import SmartZoneCompactor
from core.ephemeral_retriever import EphemeralContextRetriever
from core.kernel import FocusKernel
from core.orchestrator_kernel import OrchestratorKernel
from core.token_economy import EphemeralCostGovernor
from core.token_economy import TokenEconomyGovernor
from core.tool_matrix import ToolSelectionMatrix
from plugins.cognitive_plugin import CognitivePlugin
from plugins.design_plugin import DesignPlugin
from plugins.engineering_plugin import EngineeringPlugin
from plugins.writing_plugin import WritingPlugin


def _match_cost_report(ctx: CommandContext) -> bool:
    cmd = ctx.cmd
    return cmd in ('--cost-report', '--token-economy')


@command('cost-report', flags=('--cost-report', '--token-economy'), dest=None, summary='cost-report command', matches=_match_cost_report, order=263)
def cost_report(ctx: CommandContext) -> int:
    """cost-report command"""
    cmd = ctx.cmd
    is_json = ctx.is_json
    gov = TokenEconomyGovernor(workspace_root=os.getcwd()) if TokenEconomyGovernor else (EphemeralCostGovernor() if EphemeralCostGovernor else None)
    if is_json:
        metrics = gov.get_metrics().to_dict() if gov else {}
        print(json.dumps(metrics, indent=2))
    else:
        if gov:
            print(gov.format_report())
        else:
            print("TokenEconomyGovernor not loaded.", file=sys.stderr)
    return (0)


def _match_select_tool(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'select_tool', None) is not None


@command('select-tool', flags=('--select-tool',), dest=None, summary='select-tool command', matches=_match_select_tool, order=264)
def select_tool(ctx: CommandContext) -> int:
    """select-tool command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --select-tool '<intent>' [--target <file>] [--diff-lines <N>]", file=sys.stderr)
        return (1)
    intent = clean_args[1]
    target_path = None
    diff_lines = 0
    for i, a in enumerate(clean_args):
        if a in ('--target', '-t') and i + 1 < len(clean_args):
            target_path = clean_args[i + 1]
        elif a in ('--diff-lines', '-d') and i + 1 < len(clean_args):
            diff_lines = int(clean_args[i + 1])
    if ToolSelectionMatrix:
        matrix = ToolSelectionMatrix(workspace_root=os.getcwd())
        decision = matrix.select_tool(intent, target_path=target_path, estimated_diff_lines=diff_lines)
        if is_json:
            print(json.dumps({
                "tool": decision.tool.value,
                "confidence": decision.confidence,
                "reason": decision.reason,
                "preconditions": decision.preconditions,
                "suggested_params": decision.suggested_params,
                "risk_level": decision.risk_level
            }, indent=2))
        else:
            print(f"Recommended Tool: {decision.tool.value} (Confidence: {decision.confidence:.0%})")
            print(f"Risk Level:       {decision.risk_level}")
            print(f"Reason:           {decision.reason}")
            print("Preconditions:")
            for p in decision.preconditions:
                print(f"  - {p}")
    else:
        print("ToolSelectionMatrix not loaded.", file=sys.stderr)
    return (0)


def _match_retrieve_snippet(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'retrieve_snippet', None) is not None


@command('retrieve-snippet', flags=('--retrieve-snippet',), dest=None, summary='retrieve-snippet command', matches=_match_retrieve_snippet, order=267)
def retrieve_snippet(ctx: CommandContext) -> int:
    """retrieve-snippet command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --retrieve-snippet <pattern> [--path <path>] [--max <N>]", file=sys.stderr)
        return (1)
    pattern = clean_args[1]
    path_scope = "."
    max_matches = 5
    for i, a in enumerate(clean_args):
        if a in ('--path', '-p') and i + 1 < len(clean_args):
            path_scope = clean_args[i + 1]
        elif a in ('--max', '-m') and i + 1 < len(clean_args):
            max_matches = int(clean_args[i + 1])
    if EphemeralContextRetriever:
        retriever = EphemeralContextRetriever(workspace_root=os.getcwd())
        matches = retriever.grep_source(pattern, path_scope, max_matches=max_matches)
        if is_json:
            print(json.dumps([{"file": m.file_path, "line": m.line_number, "content": m.line_content} for m in matches], indent=2))
        else:
            print(retriever.format_grep_for_prompt(matches))
    else:
        print("EphemeralContextRetriever not available.", file=sys.stderr)
        return (1)
    return (0)


def _match_slice_facet(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'slice_facet', None) is not None


@command('slice-facet', flags=('--slice-facet',), dest=None, summary='slice-facet command', matches=_match_slice_facet, order=268)
def slice_facet(ctx: CommandContext) -> int:
    """slice-facet command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --slice-facet <facet_name> [--section <header>]", file=sys.stderr)
        return (1)
    facet_name = clean_args[1]
    section = None
    for i, a in enumerate(clean_args):
        if a in ('--section', '-s') and i + 1 < len(clean_args):
            section = clean_args[i + 1]
    if EphemeralContextRetriever:
        retriever = EphemeralContextRetriever(workspace_root=os.getcwd())
        sliced = retriever.slice_directive(facet_name, section)
        if is_json:
            print(json.dumps(sliced.to_dict(), indent=2))
        else:
            print(f"[{sliced.facet}] Section: {sliced.section} (~{sliced.tokens} tokens)")
            print("-" * 50)
            print(sliced.content)
    else:
        print("EphemeralContextRetriever not available.", file=sys.stderr)
        return (1)
    return (0)


def _match_ephemeral_run(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'ephemeral_run', None) is not None


@command('ephemeral-run', flags=('--ephemeral-run',), dest=None, summary='ephemeral-run command', matches=_match_ephemeral_run, order=269)
def ephemeral_run(ctx: CommandContext) -> int:
    """ephemeral-run command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    kernel = ctx.kernel
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --ephemeral-run <gate_id>", file=sys.stderr)
        return (1)
    gate_id = clean_args[1]
    if not FocusKernel:
        print("FocusKernel not available.", file=sys.stderr)
        return (1)
    kernel = FocusKernel(workspace_root=os.getcwd())
    if EngineeringPlugin:
        kernel.register_plugin(EngineeringPlugin())
    if CognitivePlugin:
        kernel.register_plugin(CognitivePlugin())
    if DesignPlugin:
        kernel.register_plugin(DesignPlugin())
    if WritingPlugin:
        kernel.register_plugin(WritingPlugin())
    kernel.boot()
    res = kernel.execute_active_gate(gate_id)
    if is_json:
        print(json.dumps({
            "gate_id": res.gate_id,
            "success": res.success,
            "output": res.output,
            "receipt": res.receipt.to_dict() if res.receipt else None
        }, indent=2))
    else:
        status_tag = "PASS" if res.success else "FAIL"
        print(f"Ephemeral Execution [{status_tag}]: Gate {res.gate_id}")
        if res.receipt:
            print(f"Receipt Session: {res.receipt.session_id} | Hash: {res.receipt.evidence_hash} | Elapsed: {res.receipt.elapsed_ms}ms")
        print(f"Output: {res.output}")
    return (0 if res.success else 1)


def _match_harvest_trajectories(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'harvest_trajectories', None) is not None


@command('harvest-trajectories', flags=('--harvest-trajectories',), dest=None, summary='harvest-trajectories command', matches=_match_harvest_trajectories, order=270)
def harvest_trajectories(ctx: CommandContext) -> int:
    """harvest-trajectories command"""
    args = ctx.args
    clean_args = ctx.argv
    ledger_root = ctx.ledger_root
    events_path = clean_args[1] if len(clean_args) > 1 and not clean_args[1].startswith("-") else os.path.join(ledger_root, "ledger.events.jsonl")
    harvester_script = os.path.join(ctx.skill_root, "scripts", "harvest_trajectories.py")
    if os.path.exists(harvester_script):
        subprocess.run([sys.executable, harvester_script, "--events", events_path])
    else:
        print(f"Trajectory harvester script not found at {harvester_script}", file=sys.stderr)
        return (1)
    return (0)


def _match_audit_adapter(ctx: CommandContext) -> bool:
    args = ctx.args
    cmd = ctx.cmd
    return cmd in ('--audit-adapter', '--audit-model') or getattr(args, 'audit_adapter', False) or getattr(args, 'audit_model', False)


@command('audit-adapter', flags=('--audit-adapter', '--audit-model'), dest=None, summary='Audits distilled Student LoRA router adapter integrity, parameter counts, and SHA-256 weight checksum.', matches=_match_audit_adapter, order=271)
def audit_adapter(ctx: CommandContext) -> int:
    """Audits distilled Student LoRA router adapter integrity, parameter counts, and SHA-256 weight checksum."""
    args = ctx.args
    cmd = ctx.cmd
    is_json = ctx.is_json
    skill_root = ctx.skill_root
    from adapters.model_adapter import LoRAModelAdapter
    adapter = LoRAModelAdapter(repo_root=skill_root)
    report = adapter.verify_integrity()
    if is_json:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 80)
        print("FOCUSGATE v2.8 DISTILLED STUDENT ROUTER ADAPTER AUDIT")
        print("=" * 80)
        print(f"  Adapter Status:       {'VERIFIED (Clean)' if report['valid'] else 'INVALID / MISSING'}")
        print(f"  Adapter Directory:    {report.get('adapter_dir') or 'None'}")
        print(f"  Base Model:           {report.get('base_model', 'N/A')}")
        print(f"  Architecture:         {report.get('peft_type', 'N/A')} (r={report.get('r', 0)}, alpha={report.get('lora_alpha', 0)})")
        target_mods = ', '.join(report.get('target_modules', [])) if report.get('target_modules') else 'N/A'
        print(f"  Target Modules:       {target_mods}")
        print(f"  Tensor Count:         {report.get('tensor_count', 0)} tensors")
        total_p = report.get('trainable_parameters', 0)
        print(f"  Trainable Parameters: {total_p:,} ({total_p/1e6:.2f}M)")
        print(f"  Weights SHA-256:      {report.get('checksum', 'N/A')}")
        print(f"  Neural Runtime:       {'AVAILABLE (PyTorch / PEFT)' if report.get('neural_runtime_available') else 'Pure Stdlib Mode (Zero-Dependency)'}")
        if report.get("errors"):
            print("  Verification Errors:")
            for err in report["errors"]:
                print(f"    - {err}")
        print("=" * 80)
    return (0 if report["valid"] else 1)


def _match_distilled_route(ctx: CommandContext) -> bool:
    args = ctx.args
    cmd = ctx.cmd
    return cmd == '--distilled-route' or getattr(args, 'distilled_route', None) is not None


@command('distilled-route', flags=('--distilled-route',), dest=None, summary='Routes task description through distilled Student LoRA router with Invariant Action Envelope.', matches=_match_distilled_route, order=272)
def distilled_route(ctx: CommandContext) -> int:
    """Routes task description through distilled Student LoRA router with Invariant Action Envelope."""
    args = ctx.args
    clean_args = ctx.argv
    cmd = ctx.cmd
    event_store = ctx.event_store
    is_json = ctx.is_json
    skill_root = ctx.skill_root
    raw_task = getattr(args, 'distilled_route', None)
    task_desc = ""
    if isinstance(raw_task, list) and raw_task:
        task_desc = " ".join(raw_task)
    elif isinstance(raw_task, str) and raw_task:
        task_desc = raw_task
    elif len(clean_args) > 1 and not clean_args[1].startswith("-"):
        task_desc = clean_args[1]

    if not task_desc:
        print('Usage: focus-gate.py --distilled-route "<task_description>"', file=sys.stderr)
        return (1)

    from adapters.model_adapter import LoRAModelAdapter
    adapter = LoRAModelAdapter(repo_root=skill_root)
    routed = adapter.route(task_desc)
    event_store.append("DISTILLED_ROUTE_EXECUTED", {
        "query": task_desc,
        "pipeline": routed.get("pipeline"),
        "routed_by": routed.get("routed_by"),
        "checksum": routed.get("adapter_checksum")
    })
    if is_json:
        print(json.dumps(routed, indent=2))
    else:
        print(f"[FocusGate v2.8] Distilled Route for: '{task_desc}'")
        print(f"Router Engine: {routed['routed_by']} (Checksum: {routed.get('adapter_checksum', '')[:12]})\n")
        print(routed["action_envelope"])
    return (0)


def _match_export_colab_pack(ctx: CommandContext) -> bool:
    args = ctx.args
    cmd = ctx.cmd
    return cmd == '--export-colab-pack' or getattr(args, 'export_colab_pack', None) is not None


@command('export-colab-pack', flags=('--export-colab-pack',), dest=None, summary='Exports verified trajectory dataset and turnkey Google Colab training pack.', matches=_match_export_colab_pack, order=273)
def export_colab_pack(ctx: CommandContext) -> int:
    """Exports verified trajectory dataset and turnkey Google Colab training pack."""
    args = ctx.args
    clean_args = ctx.argv
    cmd = ctx.cmd
    event_store = ctx.event_store
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    raw_dir = getattr(args, 'export_colab_pack', None)
    target_dir = None
    if isinstance(raw_dir, list) and raw_dir:
        target_dir = raw_dir[0]
    elif isinstance(raw_dir, str) and raw_dir:
        target_dir = raw_dir
    elif len(clean_args) > 1 and not clean_args[1].startswith("-"):
        target_dir = clean_args[1]

    orch = OrchestratorKernel(ledger_root)
    pack_res = orch.export_colab_pack(export_dir=target_dir)
    event_store.append("COLAB_PACK_EXPORTED", pack_res)

    if is_json:
        print(json.dumps(pack_res, indent=2))
    else:
        print("=" * 80)
        print("FOCUSGATE v2.8.1 GOOGLE COLAB TRAINING PACK EXPORTER")
        print("=" * 80)
        print(f"  Export Directory:  {pack_res['export_dir']}")
        print(f"  Trajectories:      {pack_res['record_count']} records ({pack_res['dataset_path']})")
        print(f"  Base Foundation:   {pack_res['base_model']} ({pack_res['peft_type']})")
        print(f"  Colab Script:      {pack_res['script_path']}")
        print("=" * 80)
        print("\n[✓] Pack ready. Upload to Google Drive / Colab T4 GPU to train.")
    return (0 if pack_res.get("success") else 1)


def _match_estimate_tokens(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'estimate_tokens', None) is not None


@command('estimate-tokens', flags=('--estimate-tokens',), dest=None, summary='estimate-tokens command', matches=_match_estimate_tokens, order=288)
def estimate_tokens(ctx: CommandContext) -> int:
    """estimate-tokens command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --estimate-tokens <file_or_text>", file=sys.stderr)
        return (1)
    target = clean_args[1]
    tokens = SmartZoneCompactor.estimate_tokens(target)
    if is_json:
        print(json.dumps({"target": target, "tokens": tokens}))
    else:
        print(f"Estimated tokens: {tokens}")
    return (0)


def _match_compact(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'compact', None) is not None


@command('compact', flags=('--compact',), dest=None, summary='compact command', matches=_match_compact, order=289)
def compact(ctx: CommandContext) -> int:
    """compact command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    is_json = ctx.is_json
    ledger_path = clean_args[1] if len(clean_args) > 1 else '.focusgate/GATES.md'
    res = SmartZoneCompactor.compact(ledger_path)
    if res["compacted"]:
        event_store.append("GATES_ARCHIVED", {
            "archived_ids": res.get("archived_ids", []),
            "freed_tokens": res.get("freed_tokens", 0)
        })
    if is_json:
        print(json.dumps(res, indent=2))
    else:
        if res["compacted"]:
            print(f"Smart-Zone Compaction Complete:")
            print(f"  - Archived: {res['archived_count']} gates/spikes to {res['archive_path']}")
            print(f"  - Tokens freed: ~{res['freed_tokens']}")
        else:
            print(f"No compaction needed: {res['reason']}")
    return (0)


def _match_route(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'route', None) is not None


@command('route', flags=('--route',), dest=None, summary='route command', matches=_match_route, order=290)
def route(ctx: CommandContext) -> int:
    """route command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --route \"<query>\"", file=sys.stderr)
        return (1)
    query = clean_args[1]
    routing = AutonomousRouter.route_query(query)
    if is_json:
        print(json.dumps(routing, indent=2))
    else:
        print(f"Pipeline: {routing['pipeline']} (confidence: {routing['confidence']})")
        print(f"Next: {routing['next_command']}")
    return (0)
