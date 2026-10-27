"""FocusGate v3.1 — Speculative Wave Scheduling & Predictive Branching Tests (Loop 42).

Verifies speculative downstream actor dispatch, confidence-weighted branch
allocation, instant promotion upon parent verification, zero-cost discard on failure,
and CLI dispatch.

100% Python stdlib, zero external dependencies. Sub-50ms promotion transition.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import unittest

from core.grid.speculative_scheduler import (
    SpeculativeBranch,
    SpeculativeWaveScheduler,
)


class TestSpeculativeWaveScheduler(unittest.TestCase):
    """Verifies speculative worktree allocation, branch promotion, and failure discards."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="focus_spec_test_")
        self.scheduler = SpeculativeWaveScheduler(
            worktree_root=self.tmp_dir,
            min_confidence=0.65
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_schedule_speculative_wave_confidence_filter(self):
        # Two candidate transitions from Gate-3 (e.g. Gate-4 at 0.85, Gate-3B at 0.40)
        candidates = [
            ("gate-04-domain-aggregate", 0.85),
            ("gate-03b-spike-recovery", 0.40)
        ]
        branches = self.scheduler.schedule_speculative_wave("gate-03-tdd", candidates)

        # Only candidate >= 0.65 should be scheduled
        self.assertEqual(len(branches), 1)
        b = branches[0]
        self.assertEqual(b.predicted_gate, "gate-04-domain-aggregate")
        self.assertEqual(b.confidence_score, 0.85)
        self.assertEqual(b.status, "SPECULATIVE")
        self.assertTrue(os.path.exists(b.worktree_path))

    def test_instant_promotion_upon_parent_verification(self):
        candidates = [
            ("gate-04-domain-aggregate", 0.90),
            ("gate-04-alt-branch", 0.70)
        ]
        branches = self.scheduler.schedule_speculative_wave("gate-03-tdd", candidates)
        self.assertEqual(len(branches), 2)

        # Parent verification arrives: confirmed transition is gate-04-domain-aggregate
        t0 = time.perf_counter()
        promoted = self.scheduler.promote_speculative_branch("gate-03-tdd", "gate-04-domain-aggregate")
        latency_ms = (time.perf_counter() - t0) * 1000.0

        self.assertIsNotNone(promoted)
        self.assertEqual(promoted.status, "PROMOTED")
        self.assertLess(latency_ms, 50.0)

        # Verify competing speculative branch was discarded
        competing = [b for b in self.scheduler.branches.values() if b.predicted_gate == "gate-04-alt-branch"]
        self.assertEqual(len(competing), 1)
        self.assertEqual(competing[0].status, "DISCARDED")

    def test_zero_cost_discard_on_parent_failure(self):
        candidates = [("gate-04-domain-aggregate", 0.88)]
        branches = self.scheduler.schedule_speculative_wave("gate-03-tdd", candidates)
        self.assertEqual(len(branches), 1)
        wt_path = branches[0].worktree_path
        self.assertTrue(os.path.exists(wt_path))

        # Parent gate failed verification -> discard all speculative worktrees
        discarded_count = self.scheduler.discard_speculative_branches("gate-03-tdd", reason="Unit test failure in parent")
        self.assertEqual(discarded_count, 1)
        self.assertEqual(branches[0].status, "DISCARDED")
        # Worktree cleaned up to avoid wasting disk/CPU
        self.assertFalse(os.path.exists(wt_path))

    def test_active_branches_query(self):
        self.scheduler.schedule_speculative_wave("gate-01", [("gate-02", 0.80)])
        self.scheduler.schedule_speculative_wave("gate-02", [("gate-03", 0.75)])
        active = self.scheduler.get_active_branches()
        self.assertEqual(len(active), 2)


class TestSpeculativeSchedulerCLI(unittest.TestCase):
    """Verifies CLI flag --speculative-wave."""

    def test_cli_speculative_wave_json(self):
        from core.cli.dispatch import CLIDispatcher
        clean_args = ["--speculative-wave", "gate-03-tdd"]

        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = CLIDispatcher.dispatch_speculative_wave(clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(stdout.getvalue())
        self.assertIn("parent_gate", output)
        self.assertIn("speculative_branches", output)
