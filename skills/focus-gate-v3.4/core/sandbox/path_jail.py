"""FocusGate v3.0 — Path Jail Sandbox.

Confines actor file reads, writes, and deletions to the workspace root,
intercepting directory traversal attacks (../) and absolute path escape attempts.

100% Python stdlib, zero external dependencies.
"""

import os
from typing import Optional


class PathJailViolationError(ValueError):
    """Raised when an operation attempts to access paths outside the jail boundary."""
    pass


class PathJailSandbox:
    """Enforces directory jail boundaries on filesystem path resolution."""

    def __init__(self, root_path: Optional[str] = None):
        self.root_path = os.path.realpath(os.path.abspath(root_path or os.getcwd()))

    def resolve_safe_path(self, path: str) -> str:
        """Resolves path and guarantees it remains strictly inside jail boundary."""
        if not path:
            return self.root_path

        if os.path.isabs(path):
            candidate = os.path.realpath(os.path.abspath(path))
        else:
            candidate = os.path.realpath(os.path.abspath(os.path.join(self.root_path, path)))

        try:
            common = os.path.commonpath([self.root_path, candidate])
            if common != self.root_path:
                raise PathJailViolationError(
                    f"Path escape attempt blocked: '{path}' resolves outside jail '{self.root_path}'."
                )
        except (ValueError, OSError):
            raise PathJailViolationError(
                f"Invalid or unresolvable path escape attempt: '{path}'."
            )

        return candidate
