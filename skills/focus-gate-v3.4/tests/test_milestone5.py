#!/usr/bin/env python3
"""TDD Test Suite for FocusGate v2.7.1 Milestone 5:
Unified Anti-Cliche Multi-Oracle Suite & Architectural Ledger Harmonization.
"""

import os
import sys
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V271_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V271_ROOT not in sys.path:
    sys.path.insert(0, V271_ROOT)


class TestMilestone5UnifiedAntiClicheSuite(unittest.TestCase):

    def test_01_core_oracles_init_exports_all_oracles(self):
        """Verify core/oracles/__init__.py exports all oracles: cliche, prose_cliche, code_cliche, contrast, safe_zone, token_engine."""
        import core.oracles as oracles

        self.assertTrue(hasattr(oracles, "ClicheOracle"), "Missing ClicheOracle in core.oracles")
        self.assertTrue(hasattr(oracles, "ProseClicheOracle"), "Missing ProseClicheOracle in core.oracles")
        self.assertTrue(hasattr(oracles, "CodeClicheOracle"), "Missing CodeClicheOracle in core.oracles")
        self.assertTrue(hasattr(oracles, "ContrastOracle"), "Missing ContrastOracle in core.oracles")
        self.assertTrue(hasattr(oracles, "SafeZoneValidator"), "Missing SafeZoneValidator in core.oracles")
        self.assertTrue(hasattr(oracles, "DesignTokenEngine"), "Missing DesignTokenEngine in core.oracles")

    def test_02_unified_multi_oracle_audit_method(self):
        """Verify unified audit interface in core/oracles/unified_audit.py or ClicheOracle suite."""
        from core.oracles.unified_audit import UnifiedAuditOracle

        # Test prose detection via unified auditor
        prose_sample = "In conclusion, it is important to note that we delve into the tapestry."
        res = UnifiedAuditOracle.audit_text(prose_sample, file_type="markdown")
        self.assertFalse(res["clean"])
        self.assertEqual(res["category"], "prose")
        self.assertGreater(len(res["findings"]), 0)

        # Test code detection via unified auditor
        code_sample = "try:\n    do_something()\nexcept Exception:\n    pass\n"
        code_res = UnifiedAuditOracle.audit_text(code_sample, file_type="python")
        self.assertFalse(code_res["clean"])
        self.assertEqual(code_res["category"], "code")
        self.assertGreater(len(code_res["findings"]), 0)

        # Test clean content passes
        clean_code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        clean_res = UnifiedAuditOracle.audit_text(clean_code, file_type="python")
        self.assertTrue(clean_res["clean"])

    def test_03_cli_unified_audit_flag_registered(self):
        """Verify CLI has --audit-all flag that runs unified multi-oracle audit across paths."""
        import importlib.util
        script_path = os.path.join(V271_ROOT, "scripts", "focus-gate.py")
        spec = importlib.util.spec_from_file_location("focus_gate_cli_m5", script_path)
        fg_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fg_module)

        parser = fg_module.build_parser()
        # Verify --audit-all argument is present
        actions = [a.dest for a in parser._actions]
        self.assertIn("audit_all", actions, "CLI missing --audit-all flag in parser")


if __name__ == "__main__":
    unittest.main()
