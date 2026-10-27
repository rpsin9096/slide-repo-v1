"""FocusGate v3.0 — Destructive Command Guard.

Intercepts and blocks catastrophic shell command patterns (system wipes,
force pushes, fork bombs, raw disk writes, and host reboots).

100% Python stdlib, zero external dependencies.
"""

import re
from typing import Tuple, List


class BlockedCommandError(PermissionError):
    """Raised when an actor attempts to execute a destructive command."""
    pass


class CommandGuard:
    """Evaluates shell commands against destructive execution patterns."""

    BLOCKED_RULES: List[Tuple[re.Pattern, str]] = [
        (re.compile(r'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\s+(/|/\*|~|\$HOME|\.\./)', re.IGNORECASE), "Root deletion or uncontained recursive wipe"),
        (re.compile(r'rm\s+-rf\s+/', re.IGNORECASE), "Root deletion or uncontained recursive wipe"),
        (re.compile(r'git\s+push\s+.*(--force|-f\b)', re.IGNORECASE), "Destructive remote force push"),
        (re.compile(r':\(\)\s*\{\s*:\|:&\s*\};:', re.IGNORECASE), "Fork bomb denial of service"),
        (re.compile(r'\b(mkfs|fdisk|parted)\b', re.IGNORECASE), "Raw filesystem or partition mutation"),
        (re.compile(r'\bdd\s+if=', re.IGNORECASE), "Raw disk block overwrite"),
        (re.compile(r'\b(shutdown|reboot|poweroff|init\s+0)\b', re.IGNORECASE), "Host system shutdown or reboot")
    ]

    def is_destructive(self, command: str) -> Tuple[bool, str]:
        """Checks if a command matches any destructive command rule."""
        cmd = command.strip()
        for pattern, reason in self.BLOCKED_RULES:
            if pattern.search(cmd):
                return True, reason
        return False, ""

    def validate_command(self, command: str) -> None:
        """Raises BlockedCommandError if the command is destructive."""
        blocked, reason = self.is_destructive(command)
        if blocked:
            raise BlockedCommandError(f"Destructive action blocked: {reason} in '{command}'")
