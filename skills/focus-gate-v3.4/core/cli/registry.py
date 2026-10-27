"""Command registry: declarative CLI commands behind one seam (v3.3).

`main()` in scripts/focus-gate.py used to be a ~2100-line chain of
`if getattr(args, ...)` branches. A command now lives in `core/cli/commands/`
as a function `handler(ctx) -> exit_code`, registered with `@command`. Adding
a command is one function; `main()` only builds the context and dispatches.

Migration is incremental (strangler): commands not yet moved still run from the
legacy chain, and `tests/test_v33_architecture.py` ratchets the size of that
chain down. Command modules must not import each other; shared behavior goes
into `core/`, so each module can move or be deleted on its own.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class CommandContext:
    args: Any                      # argparse namespace
    argv: List[str]                # raw argv minus --json/--strict/--force/--ledger-root/--waive-red
    is_json: bool
    ledger_root: Optional[str] = None   # None for early commands: the ledger runtime is not built yet
    event_store: Any = None
    skill_root: str = ""
    cmd: str = ""                  # first token of argv
    kernel: Any = None
    pipeline: Any = None
    raw_args: Any = None
    unknown: Any = None
    target_candidate: Optional[str] = None
    orch: Any = None
    explicit_root: Optional[str] = None
    strict: bool = False
    force: bool = False
    waive: Optional[str] = None
    known_flags: Callable[[], set] = field(default=lambda: set())

    @property
    def cli_path(self) -> str:
        import os
        return os.path.join(self.skill_root, "scripts", "focus-gate.py")

    def positionals(self, drop_options: Tuple[str, ...] = ("--depth",)) -> List[str]:
        """argv after the command flag, minus value-taking options named in `drop_options`."""
        out, skip = [], False
        for tok in self.argv[1:]:
            if skip:
                skip = False
            elif tok in drop_options:
                skip = True
            else:
                out.append(tok)
        return out


@dataclass(frozen=True)
class Command:
    name: str
    flags: Tuple[str, ...]
    dest: Optional[str]
    summary: str
    handler: Callable[[CommandContext], int]
    matches: Optional[Callable[[CommandContext], bool]] = None   # predicate; else flags/dest decide
    early: bool = False   # runs before the ledger runtime (event store, kernel) is created
    order: int = 100      # resolution order: early routes 0-99, flag commands 100, legacy chain 200+


class CommandRegistry:
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._loaded = False

    def register(self, cmd: Command) -> Command:
        if cmd.name in self._commands:
            raise ValueError(f"command {cmd.name!r} registered twice")
        self._commands[cmd.name] = cmd
        return cmd

    def _load(self) -> None:
        if not self._loaded:
            self._loaded = True
            import core.cli.commands  # noqa: F401  (import registers every module)

    def commands(self) -> List[Command]:
        self._load()
        return list(self._commands.values())

    def flags(self) -> set:
        return {f for c in self.commands() for f in c.flags}

    def resolve(self, ctx: CommandContext, early_only: bool = False) -> Optional[Command]:
        """First matching command in (order, registration) sequence."""
        ordered = sorted(enumerate(self.commands()), key=lambda p: (p[1].order, p[0]))
        for _i, c in ordered:
            if early_only and not c.early:
                continue
            if c.matches is not None:
                if c.matches(ctx):
                    return c
            elif ctx.cmd in c.flags or (c.dest and getattr(ctx.args, c.dest, None) is not None):
                return c
        return None


REGISTRY = CommandRegistry()


def command(name: str, flags: Tuple[str, ...], dest: Optional[str], summary: str,
            matches: Optional[Callable[[CommandContext], bool]] = None, order: int = 100):
    def deco(fn: Callable[[CommandContext], int]):
        REGISTRY.register(Command(name, tuple(flags), dest, summary, fn, matches=matches, order=order))
        return fn
    return deco
