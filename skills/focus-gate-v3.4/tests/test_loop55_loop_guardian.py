#!/usr/bin/env python3
"""FocusGate v3.1 Loop 55 Test Suite — Full Workspace Anti-Cliché & Infinite Loop Safety Guardian."""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.watchdog.infinite_loop_guardian import InfiniteLoopGuardian


class TestInfiniteLoopGuardian(unittest.TestCase):
    def setUp(self):
        self.guardian = InfiniteLoopGuardian()

    def test_detect_unbounded_while_true(self):
        code = """
def bad_worker():
    while True:
        x = 1 + 1
"""
        issues = self.guardian.audit_source(code, "test_bad.py")
        self.assertGreaterEqual(len(issues), 1)
        self.assertEqual(issues[0]["category"], "UNBOUNDED_WHILE_LOOP")
        self.assertEqual(issues[0]["severity"], "CRITICAL")

    def test_clean_while_loop_with_break(self):
        code = """
def good_worker():
    while True:
        x = 1 + 1
        if x > 2:
            break
"""
        issues = self.guardian.audit_source(code, "test_good.py")
        self.assertEqual(len(issues), 0)

    def test_clean_while_loop_with_sleep(self):
        code = """
import time
def good_polling():
    while True:
        time.sleep(0.1)
        if condition():
            return
"""
        issues = self.guardian.audit_source(code, "test_sleep.py")
        self.assertEqual(len(issues), 0)

    def test_detect_sleepless_polling_loop(self):
        code = """
def tight_polling():
    while True:
        pass
"""
        issues = self.guardian.audit_source(code, "test_tight.py")
        self.assertGreaterEqual(len(issues), 1)
        self.assertIn("WHILE", issues[0]["category"])

    def test_detect_unguarded_recursion(self):
        code = """
def infinite_recurse(n):
    return infinite_recurse(n + 1)
"""
        issues = self.guardian.audit_source(code, "test_recurse.py")
        self.assertGreaterEqual(len(issues), 1)
        self.assertEqual(issues[0]["category"], "UNGUARDED_RECURSION")

    def test_clean_guarded_recursion(self):
        code = """
def safe_factorial(n):
    if n <= 1:
        return 1
    return n * safe_factorial(n - 1)
"""
        issues = self.guardian.audit_source(code, "test_fact.py")
        self.assertEqual(len(issues), 0)

    def test_remediation_injects_guard_counter(self):
        code = """
def runaway():
    while True:
        print("running")
"""
        remediated = self.guardian.remediate_source(code)
        self.assertIn("_loop_guard_", remediated)
        # Remediated code should now pass audit without critical issues
        issues = self.guardian.audit_source(remediated, "test_remediated.py")
        self.assertEqual(len(issues), 0)


class TestLoopGuardianCLI(unittest.TestCase):
    def test_cli_audit_loop_safety(self):
        import subprocess
        import json
        cmd = [
            sys.executable,
            os.path.join(ROOT, "scripts", "focus-gate.py"),
            "--audit-loop-safety",
            os.path.join(ROOT, "core", "sdk", "wire_protocol.py"),
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data.get("is_safe", True))


if __name__ == "__main__":
    unittest.main()
