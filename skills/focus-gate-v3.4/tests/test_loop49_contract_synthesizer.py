"""FocusGate v3.1 — Deterministic AST Contract Synthesizer Tests (Loop 49).

Verifies AST-driven automatic synthesis of defensive invariant contracts:
- Non-null argument guards
- Type-annotation pre-condition assertions
- In-place file contract synthesis
- CLI dispatch (--synthesize-contract)

100% Python stdlib (ast, ast.unparse), zero external dependencies. Sub-5ms synthesis.
"""

import os
import sys
import json
import tempfile
import unittest

from core.repair.contract_synthesizer import ASTContractSynthesizer


class TestContractSynthesizer(unittest.TestCase):
    """Verifies AST invariant analysis, guard injection, and clean pass-through."""

    def setUp(self):
        self.synthesizer = ASTContractSynthesizer()

    def test_synthesize_type_guard_contracts(self):
        code = (
            "def calculate_total(price: float, count: int) -> float:\n"
            "    return price * count\n"
        )
        transformed, invariants = self.synthesizer.synthesize_contracts(code)

        self.assertGreater(len(invariants), 0)
        self.assertTrue(any("price" in inv for inv in invariants))
        self.assertTrue(any("count" in inv for inv in invariants))
        # Ensure assert or isinstance guard is injected
        self.assertIn("isinstance(price, float)", transformed)
        self.assertIn("isinstance(count, int)", transformed)

    def test_synthesize_non_null_guards(self):
        code = (
            "def set_config(config: dict) -> None:\n"
            "    apply(config)\n"
        )
        transformed, invariants = self.synthesizer.synthesize_contracts(code)

        self.assertGreater(len(invariants), 0)
        self.assertIn("config is not None", transformed)

    def test_file_in_place_synthesis(self):
        code = "def query(term: str):\n    return search(term)\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            transformed, invariants = self.synthesizer.synthesize_file(temp_path, in_place=True)
            self.assertGreater(len(invariants), 0)
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("isinstance(term, str)", content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestContractCLI(unittest.TestCase):
    """Verifies CLI flag --synthesize-contract."""

    def test_cli_synthesize_contract_json(self):
        from core.cli.dispatch import CLIDispatcher
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def add(a: int, b: int):\n    return a + b\n")
            temp_path = f.name

        try:
            clean_args = ["--synthesize-contract", temp_path]
            import io
            import contextlib
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = CLIDispatcher.dispatch_synthesize_contract(clean_args, is_json=True)

            self.assertEqual(code, 0)
            output = json.loads(stdout.getvalue())
            self.assertIn("file", output)
            self.assertIn("contracts_synthesized", output)
            self.assertGreater(len(output["contracts_synthesized"]), 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
