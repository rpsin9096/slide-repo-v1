"""Ledger-root resolution (moved out of the CLI script in v3.4)."""
import os

from typing import Optional


def resolve_ledger_root(target_path: Optional[str] = None, explicit_root: Optional[str] = None) -> str:
    """Resolves the root namespace directory for ledgers, events, worktrees, and archives.
    Fixes ADR-0009 Wart B by eliminating hardcoded .focusgate assumptions."""
    if explicit_root:
        return os.path.abspath(explicit_root)
    if target_path:
        abs_path = os.path.abspath(target_path)
        parts = abs_path.split(os.sep)
        for i, p in enumerate(parts):
            if p.startswith(".") and any(k in p for k in ("focus", "gate", "design", "unlazy")):
                return os.sep + os.path.join(*parts[1:i+1])
        if os.path.isdir(abs_path) and os.path.basename(abs_path).startswith("."):
            return abs_path
        parent = os.path.dirname(abs_path)
        if os.path.basename(parent).startswith("."):
            return parent
    # v3.2 Loop 64. This used to be `os.path.abspath(".focusgate")` — relative to
    # the process cwd, with no guard. Run the CLI from inside .focusgate/sub/ and
    # the root became .focusgate/sub, so main()'s unconditional
    # `os.makedirs(ledger_root)` created .focusgate/sub/.focusgate/ and
    # SQLiteStorageAdapter dropped ledger.events.db plus -wal/-shm sidecars
    # inside it. It happened on EVERY command, before dispatch, because main()
    # builds the kernel and the event store for all of them. The nested tree was
    # committed: 14 of the 34 tracked artifacts lived inside
    # .focusgate/.focusgate/.
    #
    # resolve_root() climbs out of any state directory and prefers the git
    # root, so the state directory can never be created inside itself.
    from core.workspace_detector import WorkspaceDetector as _WSD
    return os.path.join(_WSD.resolve_root(), ".focusgate")
