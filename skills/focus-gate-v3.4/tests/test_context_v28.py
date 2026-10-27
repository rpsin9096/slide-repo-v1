#!/usr/bin/env python3
"""FocusGate v2.8 Part 1 — Hybrid Context & Cache Discipline (TDD RED)."""
import os
import sys
import time
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V271_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V271_ROOT not in sys.path:
    sys.path.insert(0, V271_ROOT)

from core.context_bus import SharedContextBus, ContextDeltaEvent
from core.agent_brief import AgentBrief
from core.ephemeral_session import EphemeralSessionManager, GateReceipt
from core.tokens import estimate_tokens


class TestContextPolicyRouting(unittest.TestCase):
    def test_01_ephemeral_facets_are_sterile(self):
        from core.context_policy import FacetContextMode, mode_for_facet
        for facet in ("grilling", "writing-shape", "i-have-adhd", "writing-beats"):
            self.assertEqual(mode_for_facet(facet), FacetContextMode.EPHEMERAL, facet)

    def test_02_window_facets_keep_sliding_history(self):
        from core.context_policy import FacetContextMode, mode_for_facet
        for facet in ("engineering", "codebase-design", "frontend-design", "design-tokens", "diagnosing-bugs"):
            self.assertEqual(mode_for_facet(facet), FacetContextMode.WINDOW, facet)


class TestBusHydration(unittest.TestCase):
    def test_03_hydrate_skips_oversized_delta_instead_of_break(self):
        bus = SharedContextBus(workspace_root="/tmp/fg-v28-test-bus")
        bus._deltas.clear()
        bus._seen_ids.clear()
        bus.publish(ContextDeltaEvent.create("a", "RECEIPT", "old small delta"))
        big = "x" * (78 * 4)
        bus.publish(ContextDeltaEvent.create("b", "RECEIPT", big))
        bus.publish(ContextDeltaEvent.create("c", "RECEIPT", "new small delta"))
        bus.subscribe("agent-1", ["RECEIPT"])
        window = bus.hydrate_window("agent-1", max_tokens=80)
        contents = [d.content for d in window]
        self.assertIn("new small delta", contents)
        self.assertIn("old small delta", contents)

    def test_04_stage_ttl_evicts_stale_deltas(self):
        bus = SharedContextBus(workspace_root="/tmp/fg-v28-test-bus2")
        bus._deltas.clear()
        bus._seen_ids.clear()
        bus.publish(ContextDeltaEvent.create("g1", "RECEIPT", "stale gate delta"))
        d = bus._deltas[0]
        d.__dict__["timestamp"] = "2000-01-01T00:00:00+00:00"
        bus.publish(ContextDeltaEvent.create("g9", "RECEIPT", "fresh gate delta"))
        pruned = bus.evict_stale(max_stage_age=1, current_stage=5)
        self.assertGreaterEqual(pruned, 1)
        contents = [x.content for x in bus._deltas]
        self.assertNotIn("stale gate delta", contents)


class TestBriefCeiling(unittest.TestCase):
    def test_05_brief_dynamic_context_capped_at_400(self):
        receipts = [
            {"gate_id": f"gate-{i}", "status": "PASS", "key_findings": [f"finding {i} " * 20]}
            for i in range(10)
        ]
        brief = AgentBrief.create(
            gate_id="gate-6-review", facet="engineering",
            task_summary="Production implementation",
            acceptance_criteria=["CHECK: x", "EXPECT: y"],
            upstream_receipts=receipts,
        )
        prompt = brief.to_prompt()
        ctx_section = prompt.split("## Upstream Context")[1].split("## Mandatory")[0] if "## Upstream Context" in prompt else prompt
        self.assertLessEqual(estimate_tokens(ctx_section), 400)


class TestSterileEphemeral(unittest.TestCase):
    def test_06_no_ledger_fallback_for_unrelated_gate(self):
        mgr = EphemeralSessionManager(workspace_root="/tmp/fg-v28-test-sess")
        gate1 = {"id": "gate-1", "title": "t1", "check": "c1", "expect": "e1"}
        s1 = mgr.spawn_session("grilling", gate1)
        mgr.close_and_reap(s1.session_id, True, "done", artifacts=[], key_findings=["f1"])
        gate2 = {"id": "gate-99-unrelated", "title": "t2", "check": "c2", "expect": "e2"}
        s2 = mgr.spawn_session("grilling", gate2)
        self.assertIsNone(s2.ctx.upstream_receipt)


class TestCacheHygiene(unittest.TestCase):
    def test_07_retrieval_cache_ttl_expires(self):
        from core.ephemeral_retriever import EphemeralCache
        cache = EphemeralCache(cache_file=None)
        cache.set("k1", {"v": 1, "_ts": time.time() - 9999})
        self.assertIsNone(cache.get("k1", max_age_s=60))

    def test_08_prompt_ceiling_enforced(self):
        from core.token_economy import TokenEconomyGovernor
        gov = TokenEconomyGovernor(max_prompt_tokens=1500)
        big = "y" * (2000 * 4)
        was_compacted, compacted, tokens = gov.enforce_prompt_ceiling(big)
        self.assertTrue(was_compacted)
        self.assertLessEqual(tokens, 1500)


if __name__ == "__main__":
    unittest.main()
