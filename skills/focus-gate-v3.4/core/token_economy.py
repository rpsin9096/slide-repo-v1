"""Deep Token Economy & Execution Output Governor for FocusGate v2.8.

Consolidates pre-dispatch prompt sanitization, ephemeral session token ceilings,
and dynamic test-output folding into a single deep module with minimal surface area.
Guarantees zero-waste token consumption during initial analysis and final testing.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, Optional, List
import os
import re
import warnings

# ANSI escape sequence remover
ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')


@dataclass
class TokenEfficiencyMetrics:
    """Quantitative performance and token economy metrics."""
    total_ephemeral_tokens: int
    projected_monolithic_tokens: int
    tokens_saved: int
    cost_reduction_pct: float
    total_sessions: int
    cache_hits: int
    cache_misses: int
    test_tokens_pruned: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_ephemeral_tokens": self.total_ephemeral_tokens,
            "projected_monolithic_tokens": self.projected_monolithic_tokens,
            "tokens_saved": self.tokens_saved,
            "cost_reduction_pct": round(self.cost_reduction_pct, 2),
            "total_sessions": self.total_sessions,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "test_tokens_pruned": self.test_tokens_pruned,
        }


@dataclass
class InboundVerdict:
    """Outcome of inbound prompt sanitization and token bounding."""
    sanitized_prompt: str
    original_tokens: int
    sanitized_tokens: int
    pruned_bytes: int
    was_truncated: bool
    allowed_prefetch_count: int = 1


@dataclass
class FoldedOutput:
    """Compact test output proof preserving root cause and auto-grep window."""
    folded_text: str
    original_tokens: int
    folded_tokens: int
    pruned_tokens: int
    log_file_path: Optional[str] = None
    root_cause: Optional[str] = None


class TokenEconomyGovernor:
    """Deep module governing prompt budgeting, token ceilings, and test trace folding."""

    def __init__(
        self,
        max_routing_tokens: int = 2000,
        max_prompt_tokens: int = 1500,
        max_test_output_tokens: int = 150,
        baseline_monolithic_tokens_per_step: int = 35000,
        workspace_root: str = "."
    ):
        self.max_routing_tokens = max_routing_tokens
        self.max_prompt_tokens = max_prompt_tokens
        self.max_test_output_tokens = max_test_output_tokens
        self.baseline_tokens = baseline_monolithic_tokens_per_step
        self.workspace_root = os.path.abspath(workspace_root)

        self.total_ephemeral_tokens = 0
        self.total_sessions = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.test_tokens_pruned = 0

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Standard heuristic token count (~4 characters per token)."""
        from .tokens import estimate_tokens as _estimate_tokens
        return _estimate_tokens(text)

    def sanitize_inbound(self, raw_query: str) -> InboundVerdict:
        """Sanitizes inbound prompt, stripping minified bundles and repetitive log cascades."""
        if not raw_query:
            return InboundVerdict("", 0, 0, 0, False)

        original_bytes = len(raw_query.encode("utf-8"))
        original_tokens = self.estimate_tokens(raw_query)
        was_modified = False

        # 1. Strip minified code blocks or long unbroken lines (>500 chars without whitespace)
        lines = raw_query.splitlines()
        sanitized_lines: List[str] = []
        for line in lines:
            if len(line) > 500 and (" " not in line[:100] or "\t" not in line[:100]):
                sanitized_lines.append(line[:120] + " ... [MINIFIED_CODE_STRIPPED]")
                was_modified = True
            else:
                sanitized_lines.append(line)

        filtered_text = "\n".join(sanitized_lines)

        # 2. Collapse repetitive stack traces / log lines (e.g. 4+ identical lines)
        collapsed_text = re.sub(r"(\b[^\n]+\n)\1{3,}", r"\1[REPETITIVE_LOG_LINES_STRIPPED]\n", filtered_text)
        if collapsed_text != filtered_text:
            was_modified = True
            filtered_text = collapsed_text

        # 3. Sliding token window ceiling enforcement
        current_tokens = self.estimate_tokens(filtered_text)
        if current_tokens > self.max_routing_tokens:
            was_modified = True
            max_chars = self.max_routing_tokens * 4
            head_chars = int(max_chars * 0.75)
            tail_chars = int(max_chars * 0.25)
            filtered_text = (
                filtered_text[:head_chars]
                + "\n\n... [EXCESS_CONTEXT_PRUNED_BY_TOKEN_GOVERNOR] ...\n\n"
                + filtered_text[-tail_chars:]
            )

        sanitized_bytes = len(filtered_text.encode("utf-8"))
        sanitized_tokens = self.estimate_tokens(filtered_text)
        pruned_bytes = max(0, original_bytes - sanitized_bytes)

        return InboundVerdict(
            sanitized_prompt=filtered_text,
            original_tokens=original_tokens,
            sanitized_tokens=sanitized_tokens,
            pruned_bytes=pruned_bytes,
            was_truncated=was_modified or (pruned_bytes > 0),
            allowed_prefetch_count=1
        )

    def enforce_prompt_ceiling(self, prompt: str) -> Tuple[bool, str, int]:
        """Validates that prompt does not exceed max_prompt_tokens; compacts if needed."""
        current_tokens = self.estimate_tokens(prompt)
        if current_tokens <= self.max_prompt_tokens:
            return False, prompt, current_tokens

        max_chars = self.max_prompt_tokens * 4
        head_chars = int(max_chars * 0.70)
        tail_chars = int(max_chars * 0.20)

        compacted = (
            prompt[:head_chars]
            + "\n\n... [EXCESS_CONTEXT_PRUNED_BY_TOKEN_GOVERNOR] ...\n\n"
            + prompt[-tail_chars:]
        )
        compacted_tokens = self.estimate_tokens(compacted)
        return True, compacted, compacted_tokens

    def fold_test_output(
        self,
        raw_output: str,
        exit_code: int = 0,
        session_id: Optional[str] = None,
        diagnostic_snippet: Optional[str] = None
    ) -> FoldedOutput:
        """Folds verbose test suite / build logs into a compact proof (<=150 tokens).

        Extracts root failure assertion, strips ANSI codes and passing suite noise,
        and persists the full raw output to .focusgate/logs/ for out-of-band inspection.
        """
        if not raw_output:
            return FoldedOutput(folded_text="PASS (No output)", original_tokens=0, folded_tokens=5, pruned_tokens=0)

        clean_text = ANSI_ESCAPE_RE.sub("", raw_output).strip()
        orig_tokens = self.estimate_tokens(clean_text)

        # Offload full trace to disk asynchronously/deterministically
        log_file_path = None
        if session_id:
            logs_dir = os.path.join(self.workspace_root, ".focusgate", "logs")
            try:
                os.makedirs(logs_dir, exist_ok=True)
                log_file_path = os.path.join(logs_dir, f"{session_id}.log")
                with open(log_file_path, "w", encoding="utf-8") as f:
                    f.write(clean_text)
            except (OSError, IOError):
                pass

        # If the test passed and is reasonably small, keep concise summary
        if exit_code == 0:
            if orig_tokens <= self.max_test_output_tokens:
                return FoldedOutput(
                    folded_text=clean_text,
                    original_tokens=orig_tokens,
                    folded_tokens=orig_tokens,
                    pruned_tokens=0,
                    log_file_path=log_file_path
                )
            summary_lines = [l for l in clean_text.splitlines() if any(k in l.lower() for k in ("passed", "ok", "ran", "success"))]
            summary = "\n".join(summary_lines[-3:]) if summary_lines else clean_text[-200:]
            folded = f"PASS: {summary}"
            f_tokens = self.estimate_tokens(folded)
            self.test_tokens_pruned += max(0, orig_tokens - f_tokens)
            return FoldedOutput(
                folded_text=folded,
                original_tokens=orig_tokens,
                folded_tokens=f_tokens,
                pruned_tokens=orig_tokens - f_tokens,
                log_file_path=log_file_path
            )

        # Failure folding: isolate error lines, assertion details, and traceback tail
        lines = clean_text.splitlines()
        extracted_errors: List[str] = []
        root_cause = None

        # Look for explicit error/assertion indicators
        for line in lines:
            ll = line.strip()
            if any(ll.startswith(p) for p in ("E   ", "AssertionError", "TypeError", "ValueError", "Error:", "FAILED", "FAIL:")):
                extracted_errors.append(ll)
                if not root_cause:
                    root_cause = ll

        if not extracted_errors:
            # Fallback to the last 6 lines of the trace
            extracted_errors = [l.strip() for l in lines[-6:] if l.strip()]
            root_cause = extracted_errors[-1] if extracted_errors else "Non-zero exit code"

        folded_parts = [
            f"FAIL (Exit Code {exit_code}):",
            "\n".join(extracted_errors[:4])
        ]

        if diagnostic_snippet:
            folded_parts.append(f"\n--- Diagnostic Context (Auto-Grep) ---\n{diagnostic_snippet}")

        if log_file_path:
            folded_parts.append(f"\n(Full raw log offloaded to: {os.path.basename(log_file_path)})")

        folded_text = "\n".join(folded_parts)
        # Guarantee token ceiling on folded output
        if self.estimate_tokens(folded_text) > self.max_test_output_tokens:
            folded_text = folded_text[:self.max_test_output_tokens * 4] + " ... [TRUNCATED]"

        folded_tokens = self.estimate_tokens(folded_text)
        pruned_tokens = max(0, orig_tokens - folded_tokens)
        self.test_tokens_pruned += pruned_tokens

        return FoldedOutput(
            folded_text=folded_text,
            original_tokens=orig_tokens,
            folded_tokens=folded_tokens,
            pruned_tokens=pruned_tokens,
            log_file_path=log_file_path,
            root_cause=root_cause
        )

    def record_session(self, tokens_used: int, cache_hit: bool = False) -> None:
        """Records an execution turn's token expenditure."""
        self.total_sessions += 1
        self.total_ephemeral_tokens += tokens_used
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def get_metrics(self) -> TokenEfficiencyMetrics:
        """Computes current token economy savings against monolithic baseline."""
        projected = self.total_sessions * self.baseline_tokens
        saved = max(0, projected - self.total_ephemeral_tokens)
        reduction_pct = (saved / projected * 100.0) if projected > 0 else 0.0

        return TokenEfficiencyMetrics(
            total_ephemeral_tokens=self.total_ephemeral_tokens,
            projected_monolithic_tokens=projected,
            tokens_saved=saved,
            cost_reduction_pct=reduction_pct,
            total_sessions=self.total_sessions,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses,
            test_tokens_pruned=self.test_tokens_pruned,
        )

    def format_report(self) -> str:
        """Generates a human-readable token economy audit report."""
        m = self.get_metrics()
        return (
            f"FocusGate Token Economy Audit:\n"
            f"  Total Ephemeral Tokens Used: {m.total_ephemeral_tokens:,}\n"
            f"  Test Output Tokens Pruned:   {m.test_tokens_pruned:,}\n"
            f"  Projected Monolithic Tokens: {m.projected_monolithic_tokens:,}\n"
            f"  Net Tokens Saved:            {m.tokens_saved:,}\n"
            f"  Cost Reduction Rate:         {m.cost_reduction_pct:.1f}%\n"
            f"  Ephemeral Sessions Closed:   {m.total_sessions}\n"
            f"  JIT Cache Hit Ratio:         {(m.cache_hits / (m.cache_hits + m.cache_misses) * 100.0) if (m.cache_hits + m.cache_misses) > 0 else 0.0:.1f}%\n"
        )


# Backward Compatibility Facades
class ContextBudgetGovernor:
    """Backward compatibility facade wrapping TokenEconomyGovernor for v2.4/v2.5 callers."""

    def __init__(self, max_routing_tokens: int = 2000, max_prefetch_facets: int = 1):
        self._governor = TokenEconomyGovernor(max_routing_tokens=max_routing_tokens)
        self.max_prefetch_facets = max_prefetch_facets

    def estimate_tokens(self, text: str) -> int:
        return self._governor.estimate_tokens(text)

    def sanitize_for_routing(self, raw_query: str) -> InboundVerdict:
        return self._governor.sanitize_inbound(raw_query)

    def should_allow_prefetch(self, candidate_count: int) -> bool:
        return False  # Speculative prefetch deprecated in v2.5.5


class EphemeralCostGovernor:
    """Backward compatibility facade wrapping TokenEconomyGovernor for v2.5 callers."""

    def __init__(self, max_prompt_tokens: int = 1500, baseline_monolithic_tokens_per_step: int = 35000):
        self._governor = TokenEconomyGovernor(
            max_prompt_tokens=max_prompt_tokens,
            baseline_monolithic_tokens_per_step=baseline_monolithic_tokens_per_step
        )
        self.max_prompt_tokens = max_prompt_tokens
        self.baseline_tokens = baseline_monolithic_tokens_per_step

    @property
    def total_ephemeral_tokens(self) -> int:
        return self._governor.total_ephemeral_tokens

    @property
    def total_sessions(self) -> int:
        return self._governor.total_sessions

    @property
    def cache_hits(self) -> int:
        return self._governor.cache_hits

    @property
    def cache_misses(self) -> int:
        return self._governor.cache_misses

    def estimate_tokens(self, text: str) -> int:
        return self._governor.estimate_tokens(text)

    def enforce_prompt_ceiling(self, prompt: str) -> Tuple[bool, str, int]:
        return self._governor.enforce_prompt_ceiling(prompt)

    def record_session(self, tokens_used: int, cache_hit: bool = False) -> None:
        self._governor.record_session(tokens_used, cache_hit)

    def get_metrics(self) -> TokenEfficiencyMetrics:
        return self._governor.get_metrics()

    def format_report(self) -> str:
        return self._governor.format_report()
