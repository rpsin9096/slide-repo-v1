"""FocusGate v3.1 — Deterministic AST Self-Repair & Code Refactoring Tests (Loop 43).

Verifies AST-based deterministic code self-repair:
- Loop safety injection (prevents CPU-harming infinite spins)
- Anti-cliché shotgun exception remediation
- File in-place self-healing
- CLI dispatch (--auto-refactor)

100% Python stdlib (ast, ast.unparse), zero external dependencies.
"""

import os
import sys
import json
import tempfile
import unittest

from core.repair.ast_refactor import (
    ASTSelfRepairEngine,
    LoopSafetyTransformer,
    ShotgunExceptionTransformer,
)


class TestASTSelfRepairEngine(unittest.TestCase):
    """Verifies deterministic AST rewriting on dangerous or cliché code patterns."""

    def setUp(self):
        self.engine = ASTSelfRepairEngine()

    def test_clean_code_noop(self):
        code = "def compute(a, b):\n    return a + b\n"
        repaired, remediations = self.engine.repair_code(code)
        self.assertEqual(len(remediations), 0)
        self.assertIn("def compute(a, b):", repaired)

    def test_repair_unbounded_while_true(self):
        # A hazardous while True without cooperative yield
        code = (
            "def worker():\n"
            "    while True:\n"
            "        process_data()\n"
        )
        repaired, remediations = self.engine.repair_code(code)
        self.assertGreater(len(remediations), 0)
        self.assertTrue(any("loop" in r.lower() for r in remediations))
        # Verify cooperative yield time.sleep(0.001) or safety check was injected
        self.assertIn("time.sleep", repaired)

    def test_repair_blanket_exception_pass(self):
        code = (
            "def fetch():\n"
            "    try:\n"
            "        do_work()\n"
            "    except Exception:\n"
            "        pass\n"
        )
        repaired, remediations = self.engine.repair_code(code)
        self.assertGreater(len(remediations), 0)
        self.assertTrue(any("exception" in r.lower() for r in remediations))
        # Ensure shotgun 'except Exception:\n pass' is remediated
        self.assertNotIn("except Exception:\n        pass", repaired)

    def test_repair_file_in_place(self):
        code = (
            "def spin():\n"
            "    while True:\n"
            "        tick()\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            repaired, remediations = self.engine.repair_file(temp_path, in_place=True)
            self.assertGreater(len(remediations), 0)
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("time.sleep", content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestAutoRefactorCLI(unittest.TestCase):
    """Verifies CLI flag --auto-refactor."""

    def test_cli_auto_refactor_json(self):
        from core.cli.dispatch import CLIDispatcher
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def spin():\n    while True:\n        pass\n")
            temp_path = f.name

        try:
            clean_args = ["--auto-refactor", temp_path]
            import io
            import contextlib
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = CLIDispatcher.dispatch_auto_refactor(clean_args, is_json=True)

            self.assertEqual(code, 0)
            output = json.loads(stdout.getvalue())
            self.assertIn("file", output)
            self.assertIn("remediations", output)
            self.assertTrue(output["repaired"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
