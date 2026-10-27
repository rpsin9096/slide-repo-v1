#!/usr/bin/env python3
"""FocusGate v3.1 Loop 53 Test Suite — Autonomous Self-Evolving Rule & Directive Engine."""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.gates.directive_evolver import (
    RulePatchProposal,
    DirectiveEvolver,
)


class TestRulePatchProposal(unittest.TestCase):
    def test_proposal_token_safety(self):
        prop = RulePatchProposal(
            target_facet="codebase-design",
            issue_type="type_error",
            patch_type="APPEND_INVARIANT",
            content_diff="Invariant: All public functions must declare explicit type annotations.",
            estimated_tokens=15,
        )
        self.assertTrue(prop.is_safe(token_ceiling=400))

    def test_proposal_token_exceeded(self):
        prop = RulePatchProposal(
            target_facet="codebase-design",
            issue_type="buffer_overflow",
            patch_type="APPEND_INVARIANT",
            content_diff="Word " * 500,
            estimated_tokens=500,
        )
        self.assertFalse(prop.is_safe(token_ceiling=400))


class TestDirectiveEvolver(unittest.TestCase):
    def setUp(self):
        self.evolver = DirectiveEvolver()

    def test_telemetry_clustering(self):
        self.evolver.record_failure_telemetry("code-review", "type_error", "Missing parameter type")
        self.evolver.record_failure_telemetry("code-review", "type_error", "Return type None mismatch")
        self.evolver.record_failure_telemetry("frontend-design", "timeout", "Render hang")

        clusters = self.evolver.cluster_bottlenecks(min_frequency=2)
        self.assertIn("code-review:type_error", clusters)
        self.assertEqual(len(clusters["code-review:type_error"]), 2)
        self.assertNotIn("frontend-design:timeout", clusters)

    def test_synthesize_proposal(self):
        orig_directive = "Rule: Verify code cleanliness."
        proposal = self.evolver.synthesize_proposal(
            facet_id="code-review",
            error_class="type_error",
            original_directive=orig_directive,
        )
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.target_facet, "code-review")
        self.assertEqual(proposal.issue_type, "type_error")
        self.assertTrue(proposal.is_safe(400))
        self.assertIn("type", proposal.content_diff.lower())

    def test_apply_proposal(self):
        orig_directive = "Rule: Verify code cleanliness."
        proposal = self.evolver.synthesize_proposal(
            facet_id="code-review",
            error_class="timeout",
            original_directive=orig_directive,
        )
        new_directive = self.evolver.apply_proposal(proposal, orig_directive)
        self.assertIn(proposal.content_diff, new_directive)
        self.assertTrue(proposal.applied)


class TestDirectiveEvolverCLI(unittest.TestCase):
    def test_cli_evolve_directives(self):
        import subprocess
        import json
        cmd = [
            sys.executable,
            os.path.join(ROOT, "scripts", "focus-gate.py"),
            "--evolve-directives",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("proposals", data)
        self.assertIn("bottlenecks_detected", data)


if __name__ == "__main__":
    unittest.main()
