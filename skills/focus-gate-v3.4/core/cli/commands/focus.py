"""Focus-loop commands: seed, reorient, queue, deepen, re-pitch, templates."""
import json
import os
import sys

from core.cli.intent import TechnicalEnglishReframer
from core.cli.registry import CommandContext
from core.cli.registry import command
from core.focus_support import ActivationSeed
from core.focus_support import DistractionRecovery
from core.focus_support import SingleItemQueue
from core.gates import Ledger
from core.templates_embedded import EmbeddedTemplates


def _match_seed(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'seed', None) is not None


@command('seed', flags=('--seed',), dest=None, summary='seed command', matches=_match_seed, order=274)
def seed(ctx: CommandContext) -> int:
    """seed command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    target_dir = clean_args[1] if (len(clean_args) > 1 and not clean_args[1].startswith("-")) else ledger_root
    task_name = clean_args[2] if len(clean_args) > 2 else "Atomic Task"
    seed_file = ActivationSeed.scaffold(target_dir=target_dir, task_name=task_name)
    event_store.append("SEED_SCAFFOLDED", {"file": seed_file, "task": task_name})
    if is_json:
        print(json.dumps({"status": "SUCCESS", "seed_file": seed_file, "est_minutes": 2}, indent=2))
    else:
        print(f"Scaffolded 2-minute activation seed: {seed_file}")
        print(f"▶ NEXT ACTION: inspect {seed_file} and run initial check")
    return (0)


def _match_reorient(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'reorient', None) is not None


@command('reorient', flags=('--reorient',), dest=None, summary='reorient command', matches=_match_reorient, order=275)
def reorient(ctx: CommandContext) -> int:
    """reorient command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    target_ledger = clean_args[1] if len(clean_args) > 1 else os.path.join(ledger_root, "GATES.md")
    if not os.path.exists(target_ledger):
        seed_candidate = os.path.join(os.path.dirname(target_ledger), "GATES-SEED.md")
        if os.path.exists(seed_candidate):
            target_ledger = seed_candidate
        else:
            print(f"Error: Ledger file not found at {target_ledger}", file=sys.stderr)
            return (1)
    ledger = Ledger.from_file(target_ledger)
    snapshot = DistractionRecovery.reorient(ledger, target_ledger, event_store)
    event_store.append("REORIENTATION_SNAPSHOT", {"task": snapshot["task"], "active_gate": snapshot["active_gate_id"]})
    if is_json:
        print(json.dumps(snapshot, indent=2))
    else:
        print("=" * 80)
        print("⚡ FOCUSGATE REORIENTATION SNAPSHOT (3-SECOND RESUME)")
        print("=" * 80)
        print("1. WHAT YOU WERE DOING:")
        print(f"   Task: {snapshot['task']}")
        print(f"   Progress: [{snapshot['progress_bar']}] {snapshot['pct_complete']}% | ⚡ Streak: {snapshot['streak']} gates")
        print("\n2. WHERE YOU STOPPED:")
        print(f"   Last verified gate: {snapshot['last_verified_gate']}")
        print(f"   Current active gate: {snapshot['active_gate_id']}: {snapshot['active_gate_title']}")
        print(f"   Buffered frontier: {snapshot['buffered_count']} gates waiting")
        print("\n3. YOUR IMMEDIATE PHYSICAL NEXT ACTION (≤ 2 MIN):")
        print(f"   ▶ Run: {snapshot['next_command']}")
        print("=" * 80)
    return (0)


def _match_queue_next(ctx: CommandContext) -> bool:
    cmd = ctx.cmd
    return cmd in ('--queue-next', '--queue-status')


@command('queue-next', flags=('--queue-next', '--queue-status'), dest=None, summary='Outputs single active gate and buffers remaining DAG frontier.', matches=_match_queue_next, order=276)
def queue_next(ctx: CommandContext) -> int:
    """Outputs single active gate and buffers remaining DAG frontier."""
    clean_args = ctx.argv
    cmd = ctx.cmd
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    target_ledger = clean_args[1] if len(clean_args) > 1 else os.path.join(ledger_root, "GATES.md")
    if not os.path.exists(target_ledger):
        seed_candidate = os.path.join(os.path.dirname(target_ledger), "GATES-SEED.md")
        if os.path.exists(seed_candidate):
            target_ledger = seed_candidate
        else:
            print(f"Error: Ledger file not found at {target_ledger}", file=sys.stderr)
            return (1)
    ledger = Ledger.from_file(target_ledger)
    q_info = SingleItemQueue.evaluate(ledger)
    if is_json:
        print(json.dumps(q_info, indent=2))
    else:
        act = q_info['active']
        if act:
            print(f"ACTIVE GATE (In Flight):")
            print(f"  [ ] {act['id']}: {act['title']}")
            if act.get('check_cmd'):
                print(f"      CHECK:  {act['check_cmd']}")
                print(f"      EXPECT: {act['expect_pattern']}")
            print(f"\nBUFFERED FRONTIER: {q_info['buffered_count']} gates buffered (hidden from active view)")
            print(f"SETTLED: {q_info['settled_count']}/{q_info['total']} gates complete")
        else:
            print("QUEUE STATUS: All planned gates settled! Ready for audit/handoff.")
    return (0)


def _match_deepen(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'deepen', None) is not None


@command('deepen', flags=('--deepen',), dest=None, summary='deepen command', matches=_match_deepen, order=277)
def deepen(ctx: CommandContext) -> int:
    """deepen command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    level = clean_args[1] if len(clean_args) > 1 else "2"
    lvl_map = {"1": "L1 (Lean Action-First)", "2": "L2 (Structured Ledger)", "3": "L3 (Exhaustive Swarm)"}
    lvl_name = lvl_map.get(level, f"L{level}")
    if is_json:
        print(json.dumps({"deepen_level": level, "name": lvl_name}, indent=2))
    else:
        print(f"Depth tier set to: {lvl_name}")
    return (0)


def _match_export_templates(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'export_templates', None) is not None


@command('export-templates', flags=('--export-templates',), dest=None, summary='export-templates command', matches=_match_export_templates, order=278)
def export_templates(ctx: CommandContext) -> int:
    """export-templates command"""
    args = ctx.args
    clean_args = ctx.argv
    # Patch: same flag-guard as --init (see above).
    target_dir = ".focusgate/templates"
    if len(clean_args) > 1 and not clean_args[1].startswith("--"):
        target_dir = clean_args[1]
    os.makedirs(target_dir, exist_ok=True)
    with open(os.path.join(target_dir, "GATES.template.md"), "w") as f:
        f.write(EmbeddedTemplates.GATES_TASK_MD)
    with open(os.path.join(target_dir, "spike.ui.template.md"), "w") as f:
        f.write(EmbeddedTemplates.UI_PROTOTYPE_MD)
    with open(os.path.join(target_dir, "spike.logic.template.html"), "w") as f:
        f.write(EmbeddedTemplates.LOGIC_PROTOTYPE_HTML)
    print(f"Templates exported to {target_dir}")
    return (0)


def _match_re_pitch(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 're_pitch', None) is not None


@command('re-pitch', flags=('--re-pitch',), dest=None, summary='re-pitch command', matches=_match_re_pitch, order=291)
def re_pitch(ctx: CommandContext) -> int:
    """re-pitch command"""
    args = ctx.args
    clean_args = ctx.argv
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --re-pitch \"<text>\"", file=sys.stderr)
        return (1)
    text = clean_args[1]
    reframed = TechnicalEnglishReframer.re_pitch(text)
    print(reframed)
    return (0)
