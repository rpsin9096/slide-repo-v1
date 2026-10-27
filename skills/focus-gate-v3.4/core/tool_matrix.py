"""Deterministic Tool Selection Matrix & Pre-Patch Guard for FocusGate v2.8.

Evaluates operational context, target file bounds, and diff topology to select the
optimal tool on the first attempt, preventing trial-and-error patch failures.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import os
import ast
import json


class RecommendedTool(Enum):
    WRITE_TO_FILE = "write_to_file"
    REPLACE_FILE_CONTENT = "replace_file_content"
    VIEW_FILE = "view_file"
    GREP_SEARCH = "grep_search"
    RUN_COMMAND = "run_command"


@dataclass
class ToolDecision:
    """Deterministic tool recommendation and required pre-conditions."""
    tool: RecommendedTool
    confidence: float
    reason: str
    preconditions: List[str]
    suggested_params: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "LOW"  # LOW | MEDIUM | HIGH


@dataclass
class PatchPreconditionCheck:
    """Validation result checking whether a proposed patch will succeed on first attempt."""
    valid: bool
    reason: str
    file_exists: bool
    exact_match_found: bool
    occurrence_count: int
    matched_start_line: Optional[int] = None
    matched_end_line: Optional[int] = None
    suggested_expanded_range: Optional[Tuple[int, int]] = None
    whitespace_match_found: bool = False


class ASTSyntaxPreflightGuard:
    """Validates in-memory candidate file syntax before applying patches."""

    @classmethod
    def validate_syntax(cls, filename: str, content: str) -> Tuple[bool, str]:
        ext = os.path.splitext(filename)[1].lower()

        # 1. Python syntax check
        if ext == ".py":
            try:
                ast.parse(content, filename=filename)
                return True, ""
            except SyntaxError as e:
                return False, f"AST Pre-Flight Rejection: SyntaxError at line {e.lineno or 1}: {e.msg}"

        # 2. JSON syntax check
        if ext == ".json":
            try:
                json.loads(content)
                return True, ""
            except json.JSONDecodeError as e:
                return False, f"AST Pre-Flight Rejection: JSONDecodeError at line {e.lineno}: {e.msg}"

        # 3. TypeScript / JavaScript / Rust / Go bracket balance check
        if ext in {".ts", ".tsx", ".js", ".jsx", ".rs", ".go"}:
            balanced, err = cls._check_bracket_balance(content)
            if not balanced:
                return False, f"AST Pre-Flight Rejection: Unbalanced delimiter: {err}"

        return True, ""

    @staticmethod
    def _check_bracket_balance(content: str) -> Tuple[bool, str]:
        stack = []
        matching = {')': '(', '}': '{', ']': '['}
        i = 0
        n = len(content)
        line = 1
        col = 0
        in_single_str = False
        in_double_str = False
        in_template_str = False
        in_line_comment = False
        in_block_comment = False

        while i < n:
            ch = content[i]
            col += 1
            if ch == '\n':
                line += 1
                col = 0
                in_line_comment = False
                i += 1
                continue

            if in_line_comment:
                i += 1
                continue

            if in_block_comment:
                if ch == '*' and i + 1 < n and content[i + 1] == '/':
                    in_block_comment = False
                    i += 2
                    col += 1
                    continue
                i += 1
                continue

            if (in_single_str or in_double_str or in_template_str) and ch == '\\':
                i += 2
                col += 1
                continue

            if in_single_str:
                if ch == "'":
                    in_single_str = False
                i += 1
                continue

            if in_double_str:
                if ch == '"':
                    in_double_str = False
                i += 1
                continue

            if in_template_str:
                if ch == '`':
                    in_template_str = False
                i += 1
                continue

            if ch == '/' and i + 1 < n:
                if content[i + 1] == '/':
                    in_line_comment = True
                    i += 2
                    col += 1
                    continue
                elif content[i + 1] == '*':
                    in_block_comment = True
                    i += 2
                    col += 1
                    continue

            if ch == "'":
                in_single_str = True
                i += 1
                continue
            if ch == '"':
                in_double_str = True
                i += 1
                continue
            if ch == '`':
                in_template_str = True
                i += 1
                continue

            if ch in '({[':
                stack.append((ch, line, col))
            elif ch in ')}]':
                if not stack:
                    return False, f"Unexpected closing '{ch}' at line {line}:{col}"
                top, t_line, t_col = stack.pop()
                if matching[ch] != top:
                    return False, f"Mismatched closing '{ch}' at line {line}:{col} (opened '{top}' at line {t_line}:{t_col})"

            i += 1

        if stack:
            top, t_line, t_col = stack[-1]
            return False, f"Unclosed '{top}' from line {t_line}:{t_col}"

        return True, ""


class ToolSelectionMatrix:
    """Decision engine selecting the correct tool and verifying patch preconditions."""

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)

    def select_tool(
        self,
        intent: str,
        target_path: Optional[str] = None,
        estimated_diff_lines: int = 0,
        is_diagnostic: bool = False
    ) -> ToolDecision:
        """Determines the optimal tool based on intent, target state, and diff scope."""
        intent_lower = intent.lower()

        # 1. Diagnostic / Investigatory intent
        if is_diagnostic or any(k in intent_lower for k in ("view", "inspect", "read", "check lines", "where is", "find")):
            if target_path and os.path.isfile(os.path.join(self.workspace_root, target_path)):
                return ToolDecision(
                    tool=RecommendedTool.VIEW_FILE,
                    confidence=0.99,
                    reason="Target file exists and operation is read-only inspection",
                    preconditions=["Specify scoped StartLine and EndLine (<=800 lines)"],
                    risk_level="LOW"
                )
            return ToolDecision(
                tool=RecommendedTool.GREP_SEARCH,
                confidence=0.95,
                reason="Pattern search across workspace directory",
                preconditions=["Specify SearchPath and targeted Query regex/literal"],
                risk_level="LOW"
            )

        # 2. Execution intent
        if any(k in intent_lower for k in ("run", "test", "benchmark", "execute", "pytest", "compile")):
            return ToolDecision(
                tool=RecommendedTool.RUN_COMMAND,
                confidence=0.98,
                reason="Operational task requires shell invocation",
                preconditions=["Ensure command does not start with cd", "Provide appropriate WaitMsBeforeAsync"],
                risk_level="MEDIUM"
            )

        # 3. File Creation or Modification intent
        if not target_path:
            return ToolDecision(
                tool=RecommendedTool.WRITE_TO_FILE,
                confidence=0.70,
                reason="No target path specified; defaulting to file creation",
                preconditions=["Specify AbsolutePath for target file"],
                risk_level="HIGH"
            )

        full_path = target_path if os.path.isabs(target_path) else os.path.join(self.workspace_root, target_path)

        # Condition 3.1: File does not exist -> write_to_file
        if not os.path.exists(full_path):
            return ToolDecision(
                tool=RecommendedTool.WRITE_TO_FILE,
                confidence=1.0,
                reason=f"Target file '{os.path.basename(target_path)}' does not exist; new file creation required",
                preconditions=["Verify parent directory structure", "Set Overwrite=False"],
                suggested_params={"TargetFile": full_path, "Overwrite": False},
                risk_level="LOW"
            )

        # File exists: read file lines to calculate diff ratio
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            total_lines = max(1, len(content.splitlines()))
        except Exception:
            total_lines = 1

        diff_ratio = estimated_diff_lines / total_lines if total_lines > 0 else 1.0

        # Condition 3.2: Major rewrite (>80% lines) or tiny template (<15 lines)
        if diff_ratio > 0.80 or total_lines <= 15:
            return ToolDecision(
                tool=RecommendedTool.WRITE_TO_FILE,
                confidence=0.94,
                reason=f"High diff ratio ({diff_ratio:.1%}) or small file ({total_lines} lines); full rewrite preferred",
                preconditions=["Explicitly set Overwrite=True", "Verify complete replacement content integrity"],
                suggested_params={"TargetFile": full_path, "Overwrite": True},
                risk_level="MEDIUM"
            )

        # Condition 3.3: Surgical localized edit -> replace_file_content
        return ToolDecision(
            tool=RecommendedTool.REPLACE_FILE_CONTENT,
            confidence=0.97,
            reason=f"Surgical patch on existing file ({total_lines} lines, estimated {estimated_diff_lines} lines changed)",
            preconditions=[
                "Call view_file on [StartLine-3, EndLine+3] to ensure exact whitespace match",
                "Ensure TargetContent is unique within [StartLine, EndLine] range",
                "Do not make multiple parallel calls to the same file"
            ],
            suggested_params={"TargetFile": full_path, "AllowMultiple": False},
            risk_level="LOW"
        )

    def verify_patch_preconditions(
        self,
        target_path: str,
        search_block: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        replacement_block: Optional[str] = None,
        fuzzy_whitespace: bool = False
    ) -> PatchPreconditionCheck:
        """Validates that a proposed replace_file_content patch will succeed and enforces unlazy rigor."""
        # 1. Unlazy Rigor Check on candidate replacement content
        if replacement_block:
            from .unlazy_guard import ExecutionRigorGuard
            from .oracles.code_cliche_oracle import CodeClicheOracle
            rigor_res = ExecutionRigorGuard.scan_for_laziness(replacement_block, filename=target_path)
            # Swallowed exceptions are the shotgun-suppression tell: the code-cliche check below
            # rejects them with a dedicated message, so this stub check leaves them to it.
            violation_types = [v.violation_type for v in rigor_res.violations
                               if v.violation_type != "SWALLOWED_EXCEPTION"]
            if violation_types:
                return PatchPreconditionCheck(
                    valid=False,
                    reason=f"Unlazy Rigor Rejection: Proposed patch contains placeholder stubs ({', '.join(set(violation_types))})",
                    file_exists=True,
                    exact_match_found=False,
                    occurrence_count=0
                )

            # Bespoke Code Rigor Check (Shotgun suppression)
            code_res = CodeClicheOracle.audit_content(replacement_block, filename=target_path)
            violations = [f for f in code_res.findings if f.severity == "VIOLATION"]
            if violations:
                return PatchPreconditionCheck(
                    valid=False,
                    reason=f"Bespoke Code Rigor Rejection: {violations[0].description}",
                    file_exists=True,
                    exact_match_found=False,
                    occurrence_count=0
                )

        full_path = target_path if os.path.isabs(target_path) else os.path.join(self.workspace_root, target_path)

        if not os.path.exists(full_path):
            return PatchPreconditionCheck(
                valid=False,
                reason=f"Target file does not exist: {target_path}",
                file_exists=False,
                exact_match_found=False,
                occurrence_count=0
            )

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return PatchPreconditionCheck(
                valid=False,
                reason=f"Failed to read target file: {e}",
                file_exists=True,
                exact_match_found=False,
                occurrence_count=0
            )

        lines = content.splitlines()
        total_lines = len(lines)

        # If start_line and end_line are provided, check within that window
        search_window = content
        if start_line is not None and end_line is not None:
            s_idx = max(0, start_line - 1)
            e_idx = min(total_lines, end_line)
            search_window = "\n".join(lines[s_idx:e_idx])

        # Normalize line endings
        search_block_norm = search_block.replace("\r\n", "\n")
        search_window_norm = search_window.replace("\r\n", "\n")

        occurrences_in_window = search_window_norm.count(search_block_norm)

        if occurrences_in_window == 1:
            # Check indentation alignment: if search_block begins with whitespace, check if preceding chars on line are also whitespace
            pos = search_window_norm.find(search_block_norm)
            line_start_pos = search_window_norm.rfind("\n", 0, pos)
            prefix_on_line = search_window_norm[line_start_pos + 1:pos] if line_start_pos != -1 else search_window_norm[:pos]
            if prefix_on_line.strip() == "" and len(prefix_on_line) > 0 and (search_block_norm.startswith(" ") or search_block_norm.startswith("\t")):
                return PatchPreconditionCheck(
                    valid=False,
                    reason=f"Indentation mismatch: search block omitted {len(prefix_on_line)} leading spaces of indentation",
                    file_exists=True,
                    exact_match_found=False,
                    occurrence_count=0
                )

            # AST Pre-Flight Syntax Check
            if replacement_block:
                candidate_content = content.replace(search_block, replacement_block, 1)
                syntax_valid, syntax_err = ASTSyntaxPreflightGuard.validate_syntax(target_path, candidate_content)
                if not syntax_valid:
                    return PatchPreconditionCheck(
                        valid=False,
                        reason=syntax_err,
                        file_exists=True,
                        exact_match_found=True,
                        occurrence_count=1,
                        matched_start_line=start_line,
                        matched_end_line=end_line
                    )

            return PatchPreconditionCheck(
                valid=True,
                reason="Exact single-occurrence match verified within window",
                file_exists=True,
                exact_match_found=True,
                occurrence_count=1,
                matched_start_line=start_line,
                matched_end_line=end_line
            )

        if occurrences_in_window > 1:
            return PatchPreconditionCheck(
                valid=False,
                reason=f"TargetContent is not unique: found {occurrences_in_window} matches in window",
                file_exists=True,
                exact_match_found=True,
                occurrence_count=occurrences_in_window,
                suggested_expanded_range=(max(1, (start_line or 1) - 5), min(total_lines, (end_line or total_lines) + 5))
            )

        # Search across whole file if window failed (line drift detection)
        total_occurrences = content.replace("\r\n", "\n").count(search_block_norm)
        if total_occurrences == 1:
            # Find actual line numbers
            pos = content.find(search_block_norm)
            actual_start = content[:pos].count("\n") + 1
            actual_end = actual_start + search_block_norm.count("\n")
            return PatchPreconditionCheck(
                valid=False,
                reason=f"Exact match exists in file but outside requested window. True bounds: [{actual_start}, {actual_end}]",
                file_exists=True,
                exact_match_found=True,
                occurrence_count=1,
                matched_start_line=actual_start,
                matched_end_line=actual_end,
                suggested_expanded_range=(actual_start, actual_end)
            )

        # Check for whitespace / line-ending drift (trailing spaces, CRLF vs LF)
        block_lines_stripped = [l.rstrip() for l in search_block_norm.split("\n")]
        target_lines_stripped = [l.rstrip() for l in content.replace("\r\n", "\n").split("\n")]

        block_len = len(block_lines_stripped)
        ws_matches = []
        if block_len <= len(target_lines_stripped):
            for i in range(len(target_lines_stripped) - block_len + 1):
                if target_lines_stripped[i:i + block_len] == block_lines_stripped:
                    ws_matches.append((i + 1, i + block_len))

        if len(ws_matches) == 1:
            matched_s, matched_e = ws_matches[0]
            if fuzzy_whitespace:
                return PatchPreconditionCheck(
                    valid=True,
                    reason=f"Whitespace-normalized match found at lines [{matched_s}, {matched_e}] (trailing whitespace / line-ending variance)",
                    file_exists=True,
                    exact_match_found=False,
                    occurrence_count=1,
                    matched_start_line=matched_s,
                    matched_end_line=matched_e,
                    whitespace_match_found=True
                )
            else:
                return PatchPreconditionCheck(
                    valid=False,
                    reason=f"Match found with trailing whitespace / line-ending variance at lines [{matched_s}, {matched_e}] (exact byte match failed; check trailing spaces)",
                    file_exists=True,
                    exact_match_found=False,
                    occurrence_count=1,
                    matched_start_line=matched_s,
                    matched_end_line=matched_e,
                    whitespace_match_found=True
                )
        elif len(ws_matches) > 1:
            return PatchPreconditionCheck(
                valid=False,
                reason=f"Multiple whitespace-normalized matches found ({len(ws_matches)} occurrences) in file",
                file_exists=True,
                exact_match_found=False,
                occurrence_count=len(ws_matches),
                whitespace_match_found=True
            )

        return PatchPreconditionCheck(
            valid=False,
            reason="Exact character-for-character match not found in file (check leading indentation / whitespace)",
            file_exists=True,
            exact_match_found=False,
            whitespace_match_found=False,
            occurrence_count=0
        )
