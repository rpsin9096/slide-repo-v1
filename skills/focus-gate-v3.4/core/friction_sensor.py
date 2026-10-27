"""Deep Cognitive Ergonomics & Proactive Friction Sensor for FocusGate v2.8.

Passively monitors prompt velocity, abort events, and error loops, and proactively
anticipates edge cases to synthesize autonomous unblocking remedies rather than
halting or falling back to superficial workarounds at the first sign of friction.
Zero external dependencies (100% Python stdlib).
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time
import re
import shlex


@dataclass
class AutonomousRemedy:
    remedy_type: str       # "PATH_AUTO_FIX" | "IMPORT_RESOLUTION" | "BOUNDARY_EDGE_CASE" | "PATCH_ALIGNMENT" | "DIAGNOSTIC_PROBE"
    hypothesis: str
    action_cmd: Optional[str] = None
    target_path: Optional[str] = None
    automated_fix_viable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "remedy_type": self.remedy_type,
            "hypothesis": self.hypothesis,
            "action_cmd": self.action_cmd,
            "target_path": self.target_path,
            "automated_fix_viable": self.automated_fix_viable
        }


@dataclass
class FrictionProfile:
    friction_index: float  # 0.0 (flow state) to 1.0 (severe paralysis)
    is_paralyzed: bool
    pacing_mode: str       # "FLOW" | "STANDARD" | "PROACTIVE_RECOVERY" | "SCAFFOLDING"
    repeat_error_count: int
    recommended_micro_step: Optional[str] = None
    active_remedy: Optional[AutonomousRemedy] = None


class FrictionSensor:
    """Passively detects cognitive friction and proactively drives autonomous problem solving."""

    def __init__(self, paralysis_threshold: float = 0.75):
        self.paralysis_threshold = paralysis_threshold
        self.prompt_history: List[Dict[str, Any]] = []
        self.consecutive_error_counts: Dict[str, int] = {}
        self.last_error_outputs: Dict[str, str] = {}
        self.abort_events: List[float] = []

    def record_prompt(self, text: str) -> None:
        self.prompt_history.append({
            "text": text,
            "timestamp": time.time()
        })
        if len(self.prompt_history) > 10:
            self.prompt_history.pop(0)

    def record_gate_result(self, gate_id: str, success: bool, output: str = "") -> None:
        if success:
            self.consecutive_error_counts[gate_id] = 0
            self.last_error_outputs.pop(gate_id, None)
        else:
            self.consecutive_error_counts[gate_id] = self.consecutive_error_counts.get(gate_id, 0) + 1
            if output:
                self.last_error_outputs[gate_id] = output

    def record_abort(self) -> None:
        self.abort_events.append(time.time())

    def anticipate_edge_cases(self, gate_id: str, error_output: str) -> List[str]:
        """Anticipates potential edge cases based on error signatures and code context."""
        edge_cases = []
        err = error_output.lower()

        if "filenotfounderror" in err or "no such file or directory" in err:
            edge_cases.append("Missing target directory or uninitialized workspace path.")
        if "modulenotfounderror" in err or "importerror" in err:
            edge_cases.append("Unlinked sys.path or missing local package __init__.py.")
        if "attributeerror: 'nonetype'" in err or "none has no attribute" in err:
            edge_cases.append("Nullable value dereference / unhandled initialization boundary.")
        if "indexerror" in err or "keyerror" in err:
            edge_cases.append("Empty collection or missing key boundary condition.")
        if "timed out" in err or "timeoutexpired" in err:
            edge_cases.append("Subprocess deadlock or unbounded I/O wait boundary.")
        if "indentationerror" in err or "syntaxerror" in err:
            edge_cases.append("Patch whitespace misalignment or syntax boundary violation.")

        if not edge_cases:
            edge_cases.append("General execution divergence from expected oracle invariant.")

        return edge_cases

    def resolve_friction_autonomously(self, gate_id: str, error_output: str) -> Optional[AutonomousRemedy]:
        """Synthesizes a concrete, proactive remediation plan rather than stopping at friction."""
        err = error_output.lower()

        # 1. Missing path / directory
        if "no such file or directory" in err or "filenotfounderror" in err:
            path_match = re.search(r"['\"]([^'\"]+)['\"]", error_output)
            target = path_match.group(1) if path_match else None
            return AutonomousRemedy(
                remedy_type="PATH_AUTO_FIX",
                hypothesis="Missing destination directory structure or file path.",
                action_cmd=f"mkdir -p $(dirname {shlex.quote(target)})" if target else "mkdir -p .focusgate",
                target_path=target,
                automated_fix_viable=True
            )

        # 2. Syntax / Patch Drift
        if "indentationerror" in err or "patch" in err:
            return AutonomousRemedy(
                remedy_type="PATCH_ALIGNMENT",
                hypothesis="Whitespace drift or indentation mismatch during code modification.",
                action_cmd="python3 -m py_compile $(git diff --name-only)",
                automated_fix_viable=True
            )

        # 3. Boundary / Null condition
        if "attributeerror: 'nonetype'" in err or "indexerror" in err or "keyerror" in err:
            return AutonomousRemedy(
                remedy_type="BOUNDARY_EDGE_CASE",
                hypothesis="Unhandled empty collection or None dereference at execution boundary.",
                action_cmd=None,
                automated_fix_viable=True
            )

        # 4. Standard diagnostic probe
        return AutonomousRemedy(
            remedy_type="DIAGNOSTIC_PROBE",
            hypothesis=f"Execution stalled with error: {error_output[:100]}",
            action_cmd="git status --porcelain",
            automated_fix_viable=True
        )

    def analyze_friction(self) -> FrictionProfile:
        now = time.time()
        weights = []

        # Factor 1: Repetitive Error Stalls on same gate
        max_repeats = max(self.consecutive_error_counts.values()) if self.consecutive_error_counts else 0
        stalled_gate = None
        for g_id, count in self.consecutive_error_counts.items():
            if count == max_repeats and count > 0:
                stalled_gate = g_id
                break

        if max_repeats >= 1:
            weights.append(min(1.0, max_repeats * 0.30))

        # Factor 2: Command Aborts within last 60 seconds
        recent_aborts = sum(1 for t in self.abort_events if (now - t) <= 60.0)
        if recent_aborts >= 2:
            weights.append(min(1.0, recent_aborts * 0.40))

        # Factor 3: Rapid Prompt Revisions
        if len(self.prompt_history) >= 2:
            p1 = self.prompt_history[-2]
            p2 = self.prompt_history[-1]
            interval = p2["timestamp"] - p1["timestamp"]
            len_ratio = len(p2["text"]) / (len(p1["text"]) or 1)
            if interval < 15.0 and 0.8 <= len_ratio <= 1.2:
                weights.append(0.70)

        friction_score = sum(weights) / len(weights) if weights else 0.0
        friction_score = round(min(1.0, friction_score), 2)
        is_paralyzed = friction_score >= self.paralysis_threshold

        active_remedy = None
        if stalled_gate and stalled_gate in self.last_error_outputs:
            active_remedy = self.resolve_friction_autonomously(
                stalled_gate,
                self.last_error_outputs[stalled_gate]
            )

        if is_paralyzed:
            mode = "PROACTIVE_RECOVERY"
            rec_step = active_remedy.hypothesis if active_remedy else "Deploy autonomous edge-case probe."
        elif friction_score < 0.25:
            mode = "FLOW"
            rec_step = None
        else:
            mode = "STANDARD"
            rec_step = active_remedy.hypothesis if active_remedy else None

        return FrictionProfile(
            friction_index=friction_score,
            is_paralyzed=is_paralyzed,
            pacing_mode=mode,
            repeat_error_count=max_repeats,
            recommended_micro_step=rec_step,
            active_remedy=active_remedy
        )
