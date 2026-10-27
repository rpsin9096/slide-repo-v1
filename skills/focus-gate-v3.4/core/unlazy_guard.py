"""Execution Rigor Guard for FocusGate v2.8 (/unlazy protocol hardening).

Eliminates lackluster, superficial, and premature implementations by enforcing
strict completion criteria: rejecting placeholder stubs, TODOs, empty pass blocks,
and superficial test assertions before any gate or task can be certified.
Zero external dependencies (100% Python stdlib).
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import re


@dataclass
class RigorViolation:
    violation_type: str
    message: str
    line_number: Optional[int] = None
    snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.violation_type,
            "message": self.message,
            "line_number": self.line_number,
            "snippet": self.snippet
        }


@dataclass
class RigorInspectionResult:
    is_valid: bool
    violations: List[RigorViolation] = field(default_factory=list)
    checked_lines: int = 0

    @property
    def summary(self) -> str:
        if self.is_valid:
            return "RIGOR_PASS: Zero superficiality or placeholder patterns detected."
        types = [v.violation_type for v in self.violations]
        return f"RIGOR_REJECTED: Found {len(self.violations)} violation(s): {', '.join(set(types))}"


class ExecutionRigorGuard:
    """Enforces strict, non-lazy implementation standards across code diffs and outputs."""

    # Patterns indicating incomplete or placeholder work
    STUB_PATTERNS = [
        ("TODO_STUB", re.compile(r"\b(TODO|FIXME|XXX)\b(?!\s*[:=]\s*False)", re.IGNORECASE)),
        ("NOT_IMPLEMENTED_STUB", re.compile(r"\braise\s+NotImplementedError\b")),
        ("ELLIPSIS_STUB", re.compile(r"^\s*\.\.\.\s*(#.*)?$")),
        ("TRIVIAL_PASS", re.compile(r"^\s*pass\s*(#.*)?$")),
        ("DUMMY_ASSERT", re.compile(r"\bassert\s+(True|1\s*==\s*1)\b")),
        ("DUMMY_EXPECT", re.compile(r"\bexpect\s*\(\s*true\s*\)\s*\.\s*toBe\s*\(\s*true\s*\)", re.IGNORECASE)),
    ]

    # `except:` / `except Exception:` / `except BaseException:` whose whole body is pass or ... .
    # Narrow handlers (ImportError, FileNotFoundError, KeyError ...) are a legitimate idiom and are
    # not flagged; a broad handler that does nothing hides the failure the gate exists to surface.
    SWALLOW_RE = re.compile(
        r"^[ \t]*except(?:[ \t]+(?:Exception|BaseException)(?:[ \t]+as[ \t]+\w+)?)?[ \t]*:"
        r"(?:[ \t]*(?:pass|\.\.\.)[ \t]*(?:#.*)?$|[ \t]*(?:#.*)?\n[ \t]*(?:pass|\.\.\.)[ \t]*(?:#.*)?$)",
        re.MULTILINE,
    )

    # Function declaration followed immediately by pass / ... / return None (sync or async)
    EMPTY_FUNC_RE = re.compile(
        r"(?:async\s+)?def\s+[a-zA-Z0-9_]+\s*\([^)]*\)\s*(?:->[^:]*)?:\s*(?:\"\"\"[^\"]*\"\"\"\s*)?(?:pass|\.\.\.|return\s+None)\s*$",
        re.MULTILINE
    )

    # Empty JS/TS function declarations or arrow functions
    EMPTY_JS_FUNC_RE = re.compile(
        r"(?:async\s+)?(?:function\s+[a-zA-Z0-9_$]+\s*\([^)]*\)|const\s+[a-zA-Z0-9_$]+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)\s*\{\s*\}",
        re.MULTILINE
    )

    @classmethod
    def scan_for_laziness(cls, content: str, filename: str = "") -> RigorInspectionResult:
        """Inspects source code or diff chunks for laziness markers."""
        violations: List[RigorViolation] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()

            # Ignore pattern definitions inside scanner implementation
            if "STUB_PATTERNS" in line or "re.compile" in line:
                continue

            for v_type, pattern in cls.STUB_PATTERNS:
                if pattern.search(line):
                    # Check context: If 'pass' is inside an empty except or class definition, allow exception handling
                    if v_type == "TRIVIAL_PASS":
                        # If preceded by 'except' or 'class', allow as standard idiom
                        if idx > 1:
                            prev_line = lines[idx - 2].strip()
                            if prev_line.startswith(("except ", "except:", "class ")):
                                continue
                    violations.append(RigorViolation(
                        violation_type=v_type,
                        message=f"Forbidden laziness pattern '{v_type}' detected on line {idx}.",
                        line_number=idx,
                        snippet=stripped
                    ))

        for match in cls.SWALLOW_RE.finditer(content):
            line_no = content.count("\n", 0, match.start()) + 1
            violations.append(RigorViolation(
                violation_type="SWALLOWED_EXCEPTION",
                message=f"Broad exception handler on line {line_no} discards the failure; "
                        "catch the specific error or handle it.",
                line_number=line_no,
                snippet=match.group(0).strip().replace("\n", " ")
            ))

        # Check for empty function definitions (Python sync & async)
        for match in cls.EMPTY_FUNC_RE.finditer(content):
            snippet = match.group(0).strip().replace("\n", " ")
            violations.append(RigorViolation(
                violation_type="EMPTY_FUNCTION_STUB",
                message="Empty function stub found without real implementation.",
                snippet=snippet
            ))

        # Check for empty JavaScript/TypeScript functions
        for match in cls.EMPTY_JS_FUNC_RE.finditer(content):
            snippet = match.group(0).strip().replace("\n", " ")
            violations.append(RigorViolation(
                violation_type="EMPTY_FUNCTION_STUB",
                message="Empty JavaScript/TypeScript function stub found without real implementation.",
                snippet=snippet
            ))

        return RigorInspectionResult(
            is_valid=len(violations) == 0,
            violations=violations,
            checked_lines=len(lines)
        )

    @classmethod
    def validate_completion(
        cls,
        gate: Any,
        code_diff: str = "",
        test_output: str = ""
    ) -> Tuple[bool, List[str]]:
        """Validates that a gate is genuinely complete, rejecting partial or lazy outputs."""
        rejection_reasons: List[str] = []

        # 1. Diff Inspection: Reject stubs and placeholders in code changes
        if code_diff:
            diff_res = cls.scan_for_laziness(code_diff)
            if not diff_res.is_valid:
                for v in diff_res.violations:
                    rejection_reasons.append(f"[{v.violation_type}] {v.message} (snippet: '{v.snippet}')")

        # 2. Test Output Inspection: Reject skipped or empty test suites
        if test_output:
            if re.search(r"\b0\s+passed\b", test_output, re.IGNORECASE) and not re.search(r"\b[1-9]\d*\s+passed\b", test_output, re.IGNORECASE):
                rejection_reasons.append("[EMPTY_TEST_SUITE] Zero tests passed in test output.")
            if re.search(r"\b(all tests skipped|NO TESTS RAN)\b", test_output, re.IGNORECASE):
                rejection_reasons.append("[SKIPPED_SUITE] All verification tests were skipped.")

        # 3. Check Command Inspection: Reject trivial no-op commands
        check_cmd = getattr(gate, "check_cmd", None) or (gate.get("check") if isinstance(gate, dict) else None)
        if check_cmd:
            norm_cmd = check_cmd.strip().lower()
            trivial_cmds = [
                "true", "echo 0", "echo pass", "exit 0", ":",
                "echo ok", "echo true", "echo 1", "echo done", "exit", "return",
                "python -c ''", "python3 -c ''", 'python -c ""', 'python3 -c ""',
                "python3 -c 'exit(0)'", "python -c 'exit(0)'"
            ]
            if norm_cmd in trivial_cmds or any(norm_cmd == tc or norm_cmd.startswith(f"{tc} ") for tc in ["echo ok", "echo true", "echo 1", "echo done"]):
                rejection_reasons.append(f"[TRIVIAL_CHECK_COMMAND] Trivial verification command '{check_cmd}' is prohibited.")

        return (len(rejection_reasons) == 0, rejection_reasons)
