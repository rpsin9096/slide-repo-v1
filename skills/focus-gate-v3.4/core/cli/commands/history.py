"""Event log, replay and rollback."""
import json
import sys
import time

from core.cli.registry import CommandContext
from core.cli.registry import command


def _match_events(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'events', None) is not None


@command('events', flags=('--events',), dest=None, summary='events command', matches=_match_events, order=282)
def events(ctx: CommandContext) -> int:
    """events command"""
    args = ctx.args
    event_store = ctx.event_store
    is_json = ctx.is_json
    events = [e.to_dict() for e in event_store.events]
    if is_json:
        print(json.dumps(events, indent=2))
    else:
        print(f"Chronological Event Sourced Log ({len(events)} events):")
        for e in events:
            print(f"  [v{e['version']}] {e['type']} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(e['timestamp']))})")
    return (0)


def _match_replay(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'replay', None) is not None


@command('replay', flags=('--replay',), dest=None, summary='replay command', matches=_match_replay, order=283)
def replay(ctx: CommandContext) -> int:
    """replay command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --replay <version>", file=sys.stderr)
        return (1)
    ver = int(clean_args[1])
    state = event_store.replay_to_version(ver)
    if is_json:
        print(json.dumps(state, indent=2))
    else:
        print(f"Replayed state snapshot at Version {ver}:")
        print(json.dumps(state, indent=2))
    return (0)


def _match_rollback(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'rollback', None) is not None


@command('rollback', flags=('--rollback',), dest=None, summary='rollback command', matches=_match_rollback, order=284)
def rollback(ctx: CommandContext) -> int:
    """rollback command"""
    args = ctx.args
    clean_args = ctx.argv
    event_store = ctx.event_store
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --rollback <version>", file=sys.stderr)
        return (1)
    ver = int(clean_args[1])
    rolled_state = event_store.rollback_to_version(ver)
    if is_json:
        print(json.dumps(rolled_state, indent=2))
    else:
        print(f"Successfully rolled back to version {ver}.")
        print(f"Active event stream truncated to {ver} events + 1 compensation record.")
    return (0)
