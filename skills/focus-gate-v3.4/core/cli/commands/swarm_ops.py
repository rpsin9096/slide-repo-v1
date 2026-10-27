"""Swarm status, provisioning and cleanup."""
import json
import sys

from core.cli.registry import CommandContext
from core.cli.registry import command
from core.worktree_runner import WorktreeRunner


def _match_swarm_status(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'swarm_status', None) is not None


@command('swarm-status', flags=('--swarm-status',), dest=None, summary='swarm-status command', matches=_match_swarm_status, order=285)
def swarm_status(ctx: CommandContext) -> int:
    """swarm-status command"""
    args = ctx.args
    is_json = ctx.is_json
    orchestrator = WorktreeRunner(".")
    wts = orchestrator.list_worktrees()
    if is_json:
        print(json.dumps(wts, indent=2))
    else:
        print(f"Active Swarm Worktrees ({len(wts)}):")
        for w in wts:
            print(f"  - Gate: {w['gate_id']} | Branch: {w['branch']} | Path: {w['path']}")
    return (0)


def _match_swarm_provision(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'swarm_provision', None) is not None


@command('swarm-provision', flags=('--swarm-provision',), dest=None, summary='swarm-provision command', matches=_match_swarm_provision, order=286)
def swarm_provision(ctx: CommandContext) -> int:
    """swarm-provision command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --swarm-provision <gate_id> [branch]", file=sys.stderr)
        return (1)
    g_id = clean_args[1]
    branch = clean_args[2] if len(clean_args) > 2 else None
    orchestrator = WorktreeRunner(".")
    ok, path = orchestrator.provision_worktree(g_id, branch)
    event_store.append("SWARM_WORKTREE_PROVISIONED", {"gate_id": g_id, "path": path, "branch": branch})
    if is_json:
        print(json.dumps({"success": ok, "gate_id": g_id, "path": path}))
    else:
        print(f"Provisioned worktree for {g_id} at {path}")
    return (0 if ok else 1)


def _match_swarm_clean(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'swarm_clean', None) is not None


@command('swarm-clean', flags=('--swarm-clean',), dest=None, summary='swarm-clean command', matches=_match_swarm_clean, order=287)
def swarm_clean(ctx: CommandContext) -> int:
    """swarm-clean command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --swarm-clean <gate_id>", file=sys.stderr)
        return (1)
    g_id = clean_args[1]
    orchestrator = WorktreeRunner(".")
    ok = orchestrator.clean_worktree(g_id)
    event_store.append("SWARM_WORKTREE_CLEANED", {"gate_id": g_id})
    if is_json:
        print(json.dumps({"success": ok, "gate_id": g_id}))
    else:
        print(f"Cleaned up worktree for {g_id}")
    return (0 if ok else 1)
