"""Tests for Loop 34: Infinite Loop Detection & CPU Resource Watchdog Engine.

Tests ASTLoopAnalyzer static detection of unhalting loops, CPUExecutionWatchdog
dynamic process/thread termination, and CPUResourceCircuitBreaker protection.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import time
import json
import io
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from contextlib import redirect_stdout
from typing import Dict, Any, List

from core.watchdog.ast_loop_analyzer import ASTLoopAnalyzer, LoopSafetyReport
from core.watchdog.cpu_watchdog import CPUExecutionWatchdog, CPUQuotaExceededError
from core.watchdog.circuit_breaker import CPUResourceCircuitBreaker


class TestASTLoopAnalyzer(unittest.TestCase):
    """Test static AST detection of infinite loops and runaway recursion."""

    def setUp(self):
        self.analyzer = ASTLoopAnalyzer()

    def test_detect_while_true_without_break(self):
        code = """
def runaway():
    while True:
        x = 1
"""
        report = self.analyzer.analyze_code(code)
        self.assertIsInstance(report, LoopSafetyReport)
        self.assertFalse(report.is_safe)
        self.assertGreater(len(report.issues), 0)
        self.assertEqual(report.issues[0].issue_type, "INFINITE_WHILE_TRUE")

    def test_allow_while_true_with_break_or_return(self):
        code = """
def safe_loop():
    while True:
        if ready():
            break
        return 42
"""
        report = self.analyzer.analyze_code(code)
        self.assertTrue(report.is_safe)
        self.assertEqual(len(report.issues), 0)

    def test_detect_unmodified_loop_variable(self):
        code = """
def stuck_loop():
    x = 0
    while x < 10:
        y = 20
"""
        report = self.analyzer.analyze_code(code)
        self.assertFalse(report.is_safe)
        issue_types = [i.issue_type for i in report.issues]
        self.assertIn("UNMODIFIED_LOOP_CONDITION", issue_types)

    def test_detect_unbounded_recursion(self):
        code = """
def infinite_recurse(n):
    return infinite_recurse(n + 1)
"""
        report = self.analyzer.analyze_code(code)
        self.assertFalse(report.is_safe)
        issue_types = [i.issue_type for i in report.issues]
        self.assertIn("UNBOUNDED_RECURSION", issue_types)


class TestCPUExecutionWatchdog(unittest.TestCase):
    """Test dynamic runtime CPU execution limits and runaway thread termination."""

    def setUp(self):
        self.watchdog = CPUExecutionWatchdog(default_timeout_sec=0.2, max_iterations=500)

    def test_watchdog_terminates_runaway_loop(self):
        def runaway_fn():
            i = 0
            while True:  # pragma: no-loop-check
                i += 1
                self.watchdog.checkpoint()

        with self.assertRaises(CPUQuotaExceededError):
            self.watchdog.execute_guarded(runaway_fn)

    def test_watchdog_allows_normal_execution(self):
        def quick_fn():
            total = 0
            for i in range(10):
                self.watchdog.checkpoint()
                total += i
            return total

        result = self.watchdog.execute_guarded(quick_fn)
        self.assertEqual(result, 45)

    def test_watchdog_timeout_on_tight_spin(self):
        def tight_spin():
            t_end = time.time() + 2.0
            while time.time() < t_end:  # pragma: no-loop-check
                pass  # tight spin without checkpoint

        with self.assertRaises(CPUQuotaExceededError):
            self.watchdog.execute_guarded(tight_spin, timeout_sec=0.1)


class TestCPUResourceCircuitBreaker(unittest.TestCase):
    """Test CPU resource circuit breaker states and tripping."""

    def test_circuit_breaker_trips_on_failures(self):
        cb = CPUResourceCircuitBreaker(failure_threshold=2, recovery_timeout=0.2)
        self.assertEqual(cb.state, "CLOSED")

        cb.record_violation("coder-01")
        self.assertEqual(cb.state, "CLOSED")

        cb.record_violation("coder-01")
        self.assertEqual(cb.state, "OPEN")
        self.assertFalse(cb.allow_execution("coder-01"))

        # Wait for recovery timeout
        time.sleep(0.25)
        self.assertTrue(cb.allow_execution("coder-01"))
        self.assertEqual(cb.state, "HALF_OPEN")

        cb.record_success("coder-01")
        self.assertEqual(cb.state, "CLOSED")


class TestWatchdogCLI(unittest.TestCase):
    """Test CLI dispatch for --audit-loop-safety and --watchdog-run."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="focusgate_wd_cli_")
        self.file_path = os.path.join(self.temp_dir, "clean.py")
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("def foo():\n    for i in range(5):\n        pass\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_audit_loop_safety_json(self):
        from core.cli.dispatch import CLIDispatcher

        args = SimpleNamespace(audit_loop_safety=[self.file_path], watchdog_run=None)
        clean_args = ["--audit-loop-safety", self.file_path, "--json"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLIDispatcher.dispatch(args, clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("is_safe", output)
        self.assertTrue(output["is_safe"])


if __name__ == '__main__':
    unittest.main()
