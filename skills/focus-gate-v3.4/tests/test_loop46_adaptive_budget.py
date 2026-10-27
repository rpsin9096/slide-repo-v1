"""FocusGate v3.1 — Dynamic Token Budgeting & Adaptive Compression Tests (Loop 46).

Verifies per-persona dynamic token window allocation, JIT mailbox micro-compaction,
warning threshold triggers, and CLI dispatch.

100% Python stdlib, zero external dependencies. Sub-5ms compaction latency.
"""

import os
import sys
import json
import time
import unittest

from core.compaction.adaptive_budget import (
    TokenBudgetSpec,
    DynamicTokenBudgeter,
    AdaptivePersonaCompressor,
)


class TestAdaptiveBudget(unittest.TestCase):
    """Verifies domain-weighted token allocations, mailbox tracking, and JIT compaction."""

    def setUp(self):
        self.budgeter = DynamicTokenBudgeter(default_model_ceiling=8192)
        self.compressor = AdaptivePersonaCompressor()

    def test_allocate_domain_weighted_budgets(self):
        sec_spec = self.budgeter.allocate_budget("sec-01", "security")
        db_spec = self.budgeter.allocate_budget("db-01", "database")
        fe_spec = self.budgeter.allocate_budget("fe-01", "frontend")

        # Security gets full window (8192), database gets 75% (6144), frontend gets 50% (4096)
        self.assertEqual(sec_spec.max_context_tokens, 8192)
        self.assertEqual(db_spec.max_context_tokens, 6144)
        self.assertEqual(fe_spec.max_context_tokens, 4096)

    def test_budget_warning_and_overflow_detection(self):
        spec = self.budgeter.allocate_budget("test-01", "frontend", model_ceiling=1000)
        # Frontend budget: 500 tokens. Warning at 80% (400 tokens).

        # Small payload: 100 words (~130 tokens) -> no warning
        text_small = "hello world " * 50
        is_over, is_warn = self.budgeter.check_budget(spec, text_small)
        self.assertFalse(is_over)
        self.assertFalse(is_warn)

        # Warning payload: 350 words (~455 tokens) -> warning triggered
        text_warn = "database schema query update index " * 70
        is_over, is_warn = self.budgeter.check_budget(spec, text_warn)
        self.assertFalse(is_over)
        self.assertTrue(is_warn)

        # Overflow payload: 500 words (~650 tokens) -> over budget
        text_overflow = "overflow error token limit exceeded " * 100
        is_over, is_warn = self.budgeter.check_budget(spec, text_overflow)
        self.assertTrue(is_over)

    def test_jit_mailbox_micro_compaction(self):
        messages = [
            {"role": "system", "content": "You are a SecurityActor guarding SQL queries."},
            {"role": "user", "content": "Step 1: Check table schemas for injection hazards."},
            {"role": "assistant", "content": "Ran AST taint analysis. No SQLi vulnerabilities found in user_dao."},
            {"role": "user", "content": "Step 2: Check password hashing salt entropy in auth module."},
            {"role": "assistant", "content": "Found sha256 without salt in legacy handler. Upgraded to argon2id."},
            {"role": "user", "content": "Step 3: Execute final verification test suite on auth endpoints."}
        ]

        t0 = time.perf_counter()
        compacted, stats = self.compressor.compact_mailbox(messages, target_tokens=100)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.assertLess(elapsed_ms, 5.0)
        self.assertLess(stats["compacted_tokens"], stats["original_tokens"])
        self.assertGreater(stats["compression_ratio"], 1.2)
        # Most recent user message preserved
        self.assertEqual(compacted[-1]["content"], messages[-1]["content"])
        # System directive preserved
        self.assertEqual(compacted[0]["role"], "system")


class TestAdaptiveBudgetCLI(unittest.TestCase):
    """Verifies CLI flag --adaptive-budget."""

    def test_cli_adaptive_budget_json(self):
        from core.cli.dispatch import CLIDispatcher
        clean_args = ["--adaptive-budget", "actor-sec-01", "--domain", "security"]

        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = CLIDispatcher.dispatch_adaptive_budget(clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(stdout.getvalue())
        self.assertIn("actor_id", output)
        self.assertIn("budget", output)
        self.assertEqual(output["budget"]["domain"], "security")
