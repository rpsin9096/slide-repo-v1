"""Driver middleware pipeline (moved out of scripts/focus-gate.py in v3.4)."""
import re

from adapters.storage_adapter import SQLiteStorageAdapter
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


class DomainViolationError(Exception):
    """Raised when a Domain-Driven Design aggregate invariant is violated."""
    pass


class DriverContext:
    def __init__(self, command: str, args: List[str], cwd: str = "."):
        self.command = command
        self.args = args
        self.cwd = cwd
        self.blocked: bool = False
        self.block_reason: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}


class FocusDriverMiddleware:
    def process(self, ctx: DriverContext) -> None:
        raise NotImplementedError


class GuardrailMiddleware(FocusDriverMiddleware):
    def process(self, ctx: DriverContext) -> None:
        raw_cmd = " ".join([ctx.command] + ctx.args)
        if re.search(r'(?:^|\s)(?:--force|-f)\b', raw_cmd) or re.search(r'git\s+(?:push|reset\s+--hard|clean\s+-fd|branch\s+-D)\b', raw_cmd):
            ctx.blocked = True
            ctx.block_reason = "Blocked destructive git operation by GitGuardrails seam."


class AuditReplayMiddleware(FocusDriverMiddleware):
    def __init__(self, ledger_events: SQLiteStorageAdapter):
        self.ledger_events = ledger_events

    def process(self, ctx: DriverContext) -> None:
        if not ctx.blocked:
            self.ledger_events.append("DRIVER_COMMAND_EXECUTED", {
                "command": ctx.command,
                "args": ctx.args,
                "cwd": ctx.cwd
            })
            ctx.metadata["audit_logged"] = True


class FocusDriverPipeline:
    def __init__(self):
        self.middlewares: List[FocusDriverMiddleware] = []

    def use(self, mw: FocusDriverMiddleware) -> 'FocusDriverPipeline':
        self.middlewares.append(mw)
        return self

    def execute(self, ctx: DriverContext) -> DriverContext:
        for mw in self.middlewares:
            mw.process(ctx)
            if ctx.blocked:
                break
        return ctx
