#!/usr/bin/env python3
"""FocusGate v2.8 Part 3 — Context Sufficiency & Pointer Resolution (TDD RED)."""
import os
import sys
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V271_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V271_ROOT not in sys.path:
    sys.path.insert(0, V271_ROOT)

from core.context_policy import richness_floor
from core.context_bus import SharedContextBus, ContextDeltaEvent
from core.agent_brief import AgentBrief
from core.tokens import estimate_tokens


class TestRichnessFloor(unittest.TestCase):
    def test_15_window_facets_require_richness_floor(self):
        for facet in ("engineering", "frontend-design", "codebase-design", "design-tokens"):
            self.assertGreaterEqual(richness_floor(facet), 120, facet)

    def test_16_ephemeral_facets_exempt_from_floor(self):
        for facet in ("grilling", "writing-shape", "i-have-adhd"):
            self.assertEqual(richness_floor(facet), 0, facet)


class TestDeltaResolution(unittest.TestCase):
    def _fresh_bus(self, root):
        bus = SharedContextBus(workspace_root=root)
        bus._deltas.clear()
        bus._seen_ids.clear()
        return bus

    def test_17_resolve_delta_returns_content_when_live(self):
        bus = self._fresh_bus("/tmp/fg-v28-p3-res-a")
        d = ContextDeltaEvent.create("gate-1", "RECEIPT", "auth uses JWT in httpOnly cookie")
        bus.publish(d)
        self.assertEqual(bus.resolve_delta(d.delta_id), "auth uses JWT in httpOnly cookie")

    def test_18_resolve_delta_returns_none_when_evicted(self):
        bus = self._fresh_bus("/tmp/fg-v28-p3-res-b")
        d = ContextDeltaEvent.create("gate-1", "RECEIPT", "stale finding text")
        bus.publish(d)
        bus._deltas[0].__dict__["timestamp"] = "2000-01-01T00:00:00+00:00"
        bus.evict_stale(max_stage_age=1, current_stage=5)
        self.assertIsNone(bus.resolve_delta(d.delta_id))

    def test_19_resolve_delta_unknown_id_returns_none(self):
        bus = self._fresh_bus("/tmp/fg-v28-p3-res-c")
        self.assertIsNone(bus.resolve_delta("deadbeef"))


class TestSummarizeToBudgetRenderer(unittest.TestCase):
    def _upstream_line(self, prompt, gate_id):
        for ln in prompt.splitlines():
            if ln.startswith(f"- {gate_id} ["):
                return ln
        return ""

    def test_20_resolver_presents_summary_not_bare_pointer(self):
        resolver = lambda did: "RESOLVED jwt httpOnly cookie with rotation"
        receipts = [{"gate_id": "gate-1", "status": "PASS",
                     "delta_id": "abcd1234efgh", "key_findings": ["x" * 200]}]
        brief = AgentBrief.create(gate_id="gate-2", facet="engineering", task_summary="t",
                                  acceptance_criteria=["CHECK: a"], upstream_receipts=receipts,
                                  delta_resolver=resolver)
        prompt = brief.to_prompt()
        self.assertIn("RESOLVED jwt httpOnly cookie", prompt)
        self.assertIn("abcd1234", prompt)
        self.assertNotIn("]: @", prompt)

    def test_21_resolver_miss_falls_back_to_findings(self):
        resolver = lambda did: None
        receipts = [{"gate_id": "gate-1", "status": "PASS",
                     "delta_id": "abcd1234efgh", "key_findings": ["fallback finding detail"]}]
        brief = AgentBrief.create(gate_id="gate-2", facet="engineering", task_summary="t",
                                  acceptance_criteria=["CHECK: a"], upstream_receipts=receipts,
                                  delta_resolver=resolver)
        prompt = brief.to_prompt()
        self.assertIn("fallback finding detail", prompt)
        self.assertNotIn("]: @", prompt)

    def test_22_no_resolver_never_emits_bare_pointer(self):
        receipts = [{"gate_id": "gate-1", "status": "PASS",
                     "delta_id": "abcd1234efgh", "key_findings": ["no resolver finding"]}]
        brief = AgentBrief.create(gate_id="gate-2", facet="engineering", task_summary="t",
                                  acceptance_criteria=["CHECK: a"], upstream_receipts=receipts)
        prompt = brief.to_prompt()
        self.assertIn("no resolver finding", prompt)
        self.assertNotIn("]: @", prompt)

    def test_23_window_single_dep_meets_richness_floor(self):
        body = "decision " + " ".join(str(i) for i in range(60))  # > 120 chars
        resolver = lambda did: body
        receipts = [{"gate_id": "gate-1", "status": "PASS", "delta_id": "abcd1234efgh"}]
        brief = AgentBrief.create(gate_id="gate-2", facet="engineering", task_summary="t",
                                  acceptance_criteria=["CHECK: a"], upstream_receipts=receipts,
                                  delta_resolver=resolver)
        prompt = brief.to_prompt()
        line = self._upstream_line(prompt, "gate-1")
        rendered_body = line.split("]: ", 1)[1].split(" (ref ", 1)[0]
        self.assertGreaterEqual(len(rendered_body), richness_floor("engineering"))


class TestOrchestratorResolverInjection(unittest.TestCase):
    def _kernel(self, root):
        from core.orchestrator_kernel import OrchestratorKernel
        k = OrchestratorKernel(workspace_root=root)
        k.context_bus._deltas.clear()
        k.context_bus._seen_ids.clear()
        return k

    def test_24_window_delta_content_resolved_not_elided(self):
        k = self._kernel("/tmp/fg-v28-p3-orch-a")
        d = ContextDeltaEvent.create("gate-prev", "RECEIPT", "prev finding schema normalized to 3NF")
        k.context_bus.publish(d)
        g = {"id": "gate-next", "title": "t", "facet": "engineering",
             "check": "c", "expect": "e", "depends_on": []}
        brief = k._build_brief(g, context_hash="h", stage_ctx=None)
        self.assertIsNotNone(brief.delta_resolver)
        prompt = brief.to_prompt()
        self.assertIn("schema normalized to 3NF", prompt)
        self.assertNotIn("]: @", prompt)

    def test_25_direct_dep_dangling_pointer_surfaces_findings(self):
        from core.agent_brief import AgentReceiptBundle
        k = self._kernel("/tmp/fg-v28-p3-orch-b")
        bundle = AgentReceiptBundle.create(
            gate_id="gate-prev", brief_id="b",
            gate_receipts=[{"gate_id": "gate-prev", "status": "PASS",
                            "key_findings": ["prev decided jwt auth model"]}],
            delta_ids=["ffffffffffffffff"])  # dangling id, not on bus
        k.active_bundles["gate-prev"] = bundle
        g = {"id": "gate-next", "title": "t", "facet": "engineering",
             "check": "c", "expect": "e", "depends_on": ["gate-prev"]}
        brief = k._build_brief(g, context_hash="h", stage_ctx=None)
        prompt = brief.to_prompt()
        self.assertIn("prev decided jwt auth model", prompt)
        self.assertNotIn("]: @", prompt)


from core.oracles.context_sufficiency_oracle import RichnessSufficiencyOracle


class TestRichnessSufficiencyOracle(unittest.TestCase):
    def _prompt(self, facet, upstream):
        return ("# FocusGate Sub-Agent Brief [x]\n## Gate Contract\ngate_id: gate-2\n"
                f"facet: {facet}\n\n## Upstream Context (from dependency gates)\n{upstream}\n"
                "\n## Mandatory Implementation Rigor Directive\n")

    def test_26_flags_bare_pointer(self):
        res = RichnessSufficiencyOracle.audit_prompt(
            self._prompt("engineering", "- gate-1 [PASS]: @abcd1234"))
        self.assertFalse(res["clean"])
        self.assertIn("BARE_POINTER", [f["kind"] for f in res["findings"]])

    def test_27_accepts_summarized_dependency(self):
        res = RichnessSufficiencyOracle.audit_prompt(
            self._prompt("engineering", "- gate-1 [PASS]: resolved auth schema to 3NF (ref @abcd1234)"))
        self.assertTrue(res["clean"])

    def test_28_flags_lost_summary_placeholder(self):
        res = RichnessSufficiencyOracle.audit_prompt(
            self._prompt("engineering", "- gate-1 [PASS]: (upstream gate-1 settled; no summary available)"))
        self.assertFalse(res["clean"])
        self.assertIn("LOST_SUMMARY", [f["kind"] for f in res["findings"]])


class TestDAGSufficiencySweep(unittest.TestCase):
    def _kernel(self, root):
        from core.orchestrator_kernel import OrchestratorKernel
        k = OrchestratorKernel(workspace_root=root)
        k.context_bus._deltas.clear()
        k.context_bus._seen_ids.clear()
        return k

    def test_29_six_gate_bespoke_dag_is_sufficient(self):
        from core.agent_brief import AgentReceiptBundle
        k = self._kernel("/tmp/fg-v28-p3-sweep")
        dag = [
            {"id": "g1", "title": "spec", "facet": "frontend-design", "check": "c", "expect": "e", "depends_on": []},
            {"id": "g2", "title": "tokens", "facet": "design-tokens", "check": "c", "expect": "e", "depends_on": ["g1"]},
            {"id": "g3", "title": "proto", "facet": "prototype", "check": "c", "expect": "e", "depends_on": ["g2"]},
            {"id": "g4", "title": "seam", "facet": "codebase-design", "check": "c", "expect": "e", "depends_on": ["g3"]},
            {"id": "g5", "title": "impl", "facet": "engineering", "check": "c", "expect": "e", "depends_on": ["g4"]},
            {"id": "g6", "title": "review", "facet": "code-review", "check": "c", "expect": "e", "depends_on": ["g5"]},
        ]
        for g in dag:
            brief = k._build_brief(g, context_hash="h", stage_ctx=None)
            self.assertIsNotNone(brief.delta_resolver, g["id"])
            prompt = brief.to_prompt()
            verdict = RichnessSufficiencyOracle.audit_prompt(prompt)
            self.assertTrue(verdict["clean"], f"{g['id']}: {verdict['findings']}")
            self.assertNotIn("]: @", prompt, g["id"])
            if "## Upstream Context" in prompt:
                sec = prompt.split("## Upstream Context")[1].split("## Mandatory")[0]
                self.assertLessEqual(estimate_tokens(sec), 400, g["id"])
            # settle this gate so successors see it on the bus + as a dependency bundle
            delta = ContextDeltaEvent.create(g["id"], "RECEIPT", f"{g['id']} locked: {g['title']} decisions")
            k.context_bus.publish(delta)
            k.active_bundles[g["id"]] = AgentReceiptBundle.create(
                gate_id=g["id"], brief_id="b",
                gate_receipts=[{"gate_id": g["id"], "status": "PASS",
                                "key_findings": [f"{g['id']} key finding for {g['title']}"]}],
                delta_ids=[delta.delta_id])


if __name__ == "__main__":
    unittest.main()
