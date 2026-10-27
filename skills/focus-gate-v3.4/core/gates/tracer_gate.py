"""FocusGate v2.9 — Domain Models & Core Gates.

Defines TracerGate and SpikeGate domain models for observable, command-backed
acceptance gates and disposable prototype spikes.

Zero external dependencies (100% Python standard library).
"""

from typing import Dict, Any, List, Optional


class TracerGate:
    """Represents an observable, command-backed production acceptance gate."""

    def __init__(self, gate_id: str, title: str, checked: bool = False, line_num: int = 0):
        self.id = gate_id
        self.title = title
        self.checked = checked
        self.line_num = line_num
        self.check_cmd: Optional[str] = None
        self.expect_pattern: Optional[str] = None
        self.timeout: int = 30
        self.cwd: Optional[str] = None
        self.deps: List[str] = []

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "checked": self.checked,
            "line_num": self.line_num,
            "check_cmd": self.check_cmd,
            "expect_pattern": self.expect_pattern,
            "timeout": self.timeout,
            "cwd": self.cwd,
            "deps": self.deps,
            "type": "production"
        }


class SpikeGate(TracerGate):
    """Represents a disposable prototype spike answering a design question."""

    def __init__(self, gate_id: str, title: str, checked: bool = False, line_num: int = 0):
        super().__init__(gate_id, title, checked, line_num)
        self.branch: str = "logic"  # "logic" or "ui"
        self.question: Optional[str] = None
        self.artifact: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "branch": self.branch,
            "question": self.question,
            "artifact": self.artifact,
            "type": "spike"
        })
        return d
