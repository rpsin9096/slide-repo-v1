"""FocusGate CLI entry: parse, resolve one command from the registry, run it (v3.4)."""
import json
import os
import sys

from adapters.storage_adapter import SQLiteStorageAdapter
from core.cli.parser import build_parser
from core.cli.parser import known_flags
from core.cli.parser import print_help
from core.cli.paths import resolve_ledger_root
from core.cli.pipeline import AuditReplayMiddleware
from core.cli.pipeline import FocusDriverPipeline
from core.cli.pipeline import GuardrailMiddleware
from core.cli.registry import CommandContext
from core.cli.registry import REGISTRY, CommandContext
from core.kernel import FocusKernel
from plugins.cognitive_plugin import CognitivePlugin
from plugins.design_plugin import DesignPlugin
from plugins.engineering_plugin import EngineeringPlugin
from plugins.writing_plugin import WritingPlugin


def main():
    skill_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser = build_parser()
    args, unknown = parser.parse_known_args()

    raw_args = sys.argv[1:]
    is_json = args.json
    clean_args = [a for a in raw_args if a != '--json']

    if not clean_args or getattr(args, 'help', None) is not None or clean_args[0] in ('-h', '--help', 'help'):
        print_help()
        sys.exit(0)

    # Extract explicit --ledger-root if present
    explicit_root = None
    if '--ledger-root' in clean_args:
        idx = clean_args.index('--ledger-root')
        if idx + 1 < len(clean_args):
            explicit_root = clean_args[idx + 1]
            clean_args = clean_args[:idx] + clean_args[idx+2:]

    # v3.2: options of --check. Removed from clean_args so positional parsing is unchanged.
    opt_strict = '--strict' in clean_args
    opt_force = '--force' in clean_args
    opt_waive = None
    clean_args = [a for a in clean_args if a not in ('--strict', '--force')]
    if '--waive-red' in clean_args:
        idx = clean_args.index('--waive-red')
        if idx + 1 < len(clean_args):
            opt_waive = clean_args[idx + 1]
            clean_args = clean_args[:idx] + clean_args[idx + 2:]
        else:
            print("Error: --waive-red requires a reason", file=sys.stderr)
            sys.exit(1)

    cmd = clean_args[0] if clean_args else ""

    if getattr(args, 'version', None) is not None or cmd == '--version':
        # v3.2 Loop 65: read the single source, do not retype the identity.
        # This handler previously emitted four different answers (a JSON
        # "3.0", a "FocusGate v3.0-PREVIEW-1", a "preview" status, and a
        # banner naming v2.8 / v3.0), so the machine view and the human
        # view disagreed. `core.version` is the only place this is written.
        from core.version import VERSION, RELEASE_LABEL, STATUS
        if is_json:
            print(json.dumps({"version": VERSION, "release": RELEASE_LABEL,
                              "status": STATUS}))
        else:
            print("FocusGate %s (%s - %s)"
                  % (RELEASE_LABEL, "Autonomous Distributed Cognitive Swarm OS",
                     STATUS))
        sys.exit(0)

    ctx = CommandContext(
        args=args, argv=clean_args, is_json=is_json, cmd=cmd, ledger_root=None, event_store=None,
        skill_root=skill_root, explicit_root=explicit_root, strict=opt_strict, force=opt_force,
        waive=opt_waive, raw_args=raw_args, unknown=unknown, known_flags=known_flags)
    command = REGISTRY.resolve(ctx)
    if command is not None and command.early:
        sys.exit(command.handler(ctx))

    target_candidate = clean_args[1] if len(clean_args) > 1 and not clean_args[1].startswith("-") else None
    ledger_root = resolve_ledger_root(target_candidate, explicit_root)
    os.makedirs(ledger_root, exist_ok=True)

    # FocusKernel integration (Step A4)
    kernel = None
    if FocusKernel is not None:
        kernel = FocusKernel(ledger_root)
        for PluginClass in [CognitivePlugin, EngineeringPlugin, DesignPlugin, WritingPlugin]:
            if PluginClass is not None:
                kernel.register_plugin(PluginClass())
        kernel.boot()

    # Initialize Event Sourced Ledger with resolved namespace
    events_path = os.path.join(ledger_root, "ledger.events.jsonl")
    event_store = SQLiteStorageAdapter(events_path)

    # Initialize Composable Driver Pipeline
    pipeline = FocusDriverPipeline()
    pipeline.use(GuardrailMiddleware())
    pipeline.use(AuditReplayMiddleware(event_store))
    ctx.ledger_root, ctx.event_store, ctx.kernel, ctx.pipeline = ledger_root, event_store, kernel, pipeline
    ctx.target_candidate = target_candidate
    if command is not None:
        sys.exit(command.handler(ctx))

    print(f"Error: Unknown command '{cmd}'", file=sys.stderr)
    print_help()
    sys.exit(1)
