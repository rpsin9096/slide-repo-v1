#!/usr/bin/env python3
"""FocusGate v2.8 Part 2 — Prompt-as-Pointer + FILE_PATCH lifecycle (TDD RED)."""
import os
import sys
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V271_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V271_ROOT not in sys.path:
    sys.path.insert(0, V271_ROOT)

from core.context_bus import SharedContextBus, ContextDeltaEvent
from core.agent_brief import AgentBrief
from core.tokens import estimate_tokens


class TestFacetSubscriptions(unittest.TestCase):
    def test_09_subscriptions_per_facet(self):
        from core.context_policy import subscriptions_for
        eph = subscriptions_for("grilling")
        self.assertIn("RECEIPT", eph)
        self.assertNotIn("FILE_PATCH", eph)
        win = subscriptions_for("engineering")
        self.assertIn("FILE_PATCH", win)
        self.assertIn("DOMAIN_ANCHOR", win)

    def test_10_brief_budget_per_facet(self):
        from core.context_policy import brief_budget
        self.assertLessEqual(brief_budget("grilling"), 150)
        self.assertLessEqual(brief_budget("engineering"), 400)


class TestPromptAsPointer(unittest.TestCase):
    def test_11_upstream_shows_summary_plus_delta_ref_not_bare_pointer(self):
        # Re-contracted in v2.8 Part 3 (Micro-ADR-28.1). The original assertion
        # assertNotIn(full finding) encoded the elision-to-bare-pointer bug that
        # starved WINDOW sub-agents -> "lackluster" output. Corrected contract:
        # keep @ref as a trace, but ALWAYS carry a substantive summary; never a bare pointer.
        receipts = [
            {"gate_id": "gate-1", "status": "PASS",
             "key_findings": ["f" * 200], "delta_id": "abcd1234efgh5678"}
        ]
        brief = AgentBrief.create(
            gate_id="gate-2", facet="engineering",
            task_summary="t",
            acceptance_criteria=["CHECK: x", "EXPECT: y"],
            upstream_receipts=receipts,
        )
        prompt = brief.to_prompt()
        self.assertIn("abcd1234", prompt)      # @ref retained as a trace
        self.assertNotIn("]: @", prompt)       # never a bare pointer
        self.assertIn("f" * 100, prompt)       # substantive summary present, not elided

    def test_12_long_dag_stays_within_window_budget(self):
        receipts = [
            {"gate_id": f"gate-{i}", "status": "PASS",
             "key_findings": [f"finding {i} " * 30], "delta_id": f"d{i:08d}"}
            for i in range(15)
        ]
        brief = AgentBrief.create(
            gate_id="gate-16", facet="engineering",
            task_summary="t",
            acceptance_criteria=["CHECK: x", "EXPECT: y"],
            upstream_receipts=receipts,
        )
        prompt = brief.to_prompt()
        ctx = prompt.split("## Upstream Context")[1].split("## Mandatory")[0]
        self.assertLessEqual(estimate_tokens(ctx), 400)


class TestFilePatchLifecycle(unittest.TestCase):
    def test_13_publish_file_patch_helper(self):
        bus = SharedContextBus(workspace_root="/tmp/fg-v28-p2-bus")
        bus._deltas.clear()
        bus._seen_ids.clear()
        bus.publish_file_patch("gate-2", "src/a.py", "diff-head-xyz")
        types = [d.delta_type for d in bus._deltas]
        self.assertIn("FILE_PATCH", types)
        self.assertTrue(any("src/a.py" in d.content for d in bus._deltas))

    def test_14_evict_settled_gate_prunes_reorient(self):
        bus = SharedContextBus(workspace_root="/tmp/fg-v28-p2-bus2")
        bus._deltas.clear()
        bus._seen_ids.clear()
        bus.publish(ContextDeltaEvent.create("orchestrator", "REORIENT", "Dispatched sub-agent for gate-1"))
        bus.publish(ContextDeltaEvent.create("gate-1", "RECEIPT", "gate-1 done"))
        pruned = bus.evict_settled("gate-1")
        contents = " ".join(d.content for d in bus._deltas)
        self.assertGreaterEqual(pruned, 1)
        self.assertNotIn("Dispatched sub-agent for gate-1", contents)


if __name__ == "__main__":
    unittest.main()
