"""Hexagonal Verification Oracle Adapters for FocusGate v2.8.

Provides typed interfaces and concrete adapters for shell checks, contrast verification,
safe-zone boundaries, and domain modeling compliance.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import subprocess
import os
import re

from core.oracles.contrast import ContrastOracle


class OraclePort(ABC):
    """Abstract outbound port for gate verification oracles."""

    @abstractmethod
    def verify(self, command: str, expected_output: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        pass


class ShellOracleAdapter(OraclePort):
    """Executes deterministic verification commands and tracer gates in local shell environment."""

    def __init__(self, timeout_sec: int = 15):
        self.timeout_sec = timeout_sec

    def verify(self, command: str, expected_output: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=cwd or os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=self.timeout_sec
            )
            out = res.stdout or ""
            if expected_output == "FAIL":
                passed = (res.returncode != 0)
            elif expected_output in ("PASS", "0"):
                passed = (res.returncode == 0)
            else:
                passed = (expected_output in out) or (res.returncode == 0 and not expected_output)

            return {
                "success": passed,
                "returncode": res.returncode,
                "output": out.strip()
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": 124,
                "output": f"Timeout expired ({self.timeout_sec}s)"
            }
        except (OSError, ValueError) as e:
            return {
                "success": False,
                "returncode": 1,
                "output": f"Oracle execution error: {str(e)}"
            }

    def execute_tracer(self, gate: Any, base_dir: str = ".") -> Tuple[bool, str, Dict[str, Any]]:
        """Executes a gate check command with bounded timeouts and directory isolation."""
        gate_id = getattr(gate, "id", str(gate))
        check_cmd = getattr(gate, "check_cmd", "")
        timeout = getattr(gate, "timeout", self.timeout_sec)
        expect_pattern = getattr(gate, "expect_pattern", None)
        gate_cwd = getattr(gate, "cwd", None)

        meta: Dict[str, Any] = {
            "gate_id": gate_id,
            "cmd": check_cmd,
            "timeout": timeout,
            "exit_code": None,
            "output": "",
            "passed": False,
            "reason": ""
        }
        if not check_cmd:
            meta["passed"] = True
            meta["reason"] = "manual_gate_skipped"
            return True, f"[-] Skip {gate_id}: Manual gate", meta

        resolved_cwd = os.path.join(base_dir, gate_cwd) if gate_cwd else base_dir
        try:
            res = subprocess.run(
                check_cmd,
                shell=True,
                cwd=resolved_cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            raw_out = (res.stdout + "\n" + res.stderr).strip()
            meta["exit_code"] = res.returncode
            meta["raw_output"] = raw_out
            meta["output"] = raw_out

            try:
                from core.token_economy import TokenEconomyGovernor
                gov = TokenEconomyGovernor(workspace_root=base_dir)
                folded = gov.fold_test_output(
                    raw_output=raw_out,
                    exit_code=res.returncode,
                    session_id=f"tracer_{gate_id}"
                )
                meta["output"] = folded.folded_text
                meta["log_file_path"] = folded.log_file_path
                meta["tokens_pruned"] = folded.pruned_tokens
            except (ImportError, OSError, ValueError, KeyError):
                pass

            if res.returncode != 0:
                meta["reason"] = f"non_zero_exit_{res.returncode}"
                return False, f"FAILED (exit code {res.returncode}): {meta['output']}", meta

            if expect_pattern:
                if not re.search(expect_pattern, raw_out):
                    meta["reason"] = f"expect_mismatch: {expect_pattern}"
                    return False, f"FAILED_EXPECT: pattern '{expect_pattern}' not found in output: {meta['output']}", meta

            meta["passed"] = True
            meta["reason"] = "ok"
            return True, "PASSED", meta
        except subprocess.TimeoutExpired:
            meta["reason"] = f"timeout_exceeded_{timeout}s"
            return False, f"TIMEOUT (exceeded {timeout}s bound)", meta
        except (OSError, ValueError) as e:
            meta["reason"] = str(e)
            return False, f"ERROR: {e}", meta


class ContrastOracleAdapter:
    """WCAG 2.1 relative luminance and contrast ratio evaluator."""

    @staticmethod
    def calculate_luminance(rgb: Tuple[int, int, int]) -> float:
        return ContrastOracle.relative_luminance(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)

    @classmethod
    def contrast_ratio(cls, rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
        l1 = cls.calculate_luminance(rgb1)
        l2 = cls.calculate_luminance(rgb2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    @classmethod
    def evaluate(cls, fg_rgb: Tuple[int, int, int], bg_rgb: Tuple[int, int, int], min_ratio: float = 4.5) -> Dict[str, Any]:
        ratio = cls.contrast_ratio(fg_rgb, bg_rgb)
        return {
            "ratio": round(ratio, 2),
            "passes_aa": ratio >= 4.5,
            "passes_aaa": ratio >= 7.0,
            "success": ratio >= min_ratio
        }

    @classmethod
    def verdict(cls, fg: str, bg: str) -> Dict[str, Any]:
        """Evaluates contrast ratio between hex strings and returns compliance report."""
        ratio = ContrastOracle.calculate_ratio(fg, bg)
        return {
            "fg": fg,
            "bg": bg,
            "ratio": round(ratio, 2),
            "pass_aa": ratio >= 4.5,
            "pass_aa_large": ratio >= 3.0,
            "pass_aaa": ratio >= 7.0,
            "pass_aaa_large": ratio >= 4.5,
        }
