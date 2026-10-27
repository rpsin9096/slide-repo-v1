#!/usr/bin/env python3
"""FocusGate v2.8 Part 4 — Facet Contracts, Depth & Invocation Reliability (TDD)."""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
V271_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
if V271_ROOT not in sys.path:
    sys.path.insert(0, V271_ROOT)

from core.facet_contract import FacetContract, FacetContractError, parse_facet_file, load_contracts


SAMPLE = """# Facet Contract: diagnosing-bugs (v2.8)
Context: engineering | Mode: Hypothesis-first | Eviction: On Gate Settle

```facet-meta
schema: 1
id: diagnosing-bugs
summary: Deterministic reproduction, hypothesis-first debugging
priority: 10
mode: WINDOW
applies_when:
  - "bug"
  - "crash"
  - "flaky"
never_when:
  - "typo"
oracle:
  - "--run"
socratic:
  grounding: ["active gate contract", "file:line"]
  stems:
    - "What is your falsifiable hypothesis for {check}?"
  cap: 2
usability:
  seed: "Run the failing command; capture exit code."
  example: "exit=1 stderr=TypeError"
  criterion: "Repro command fails 3/3 before any fix."
```

## Invariant Directives
1. REPRO_FIRST: No fix without a deterministic reproduction command.
"""


class TestFacetContractParser(unittest.TestCase):
    def test_01_parse_scalars_lists_and_nested_sections(self):
        c = parse_facet_file(SAMPLE, filename="facets/engineering/diagnosing-bugs.md")
        self.assertEqual(c.id, "diagnosing-bugs")
        self.assertEqual(c.context, "engineering")
        self.assertEqual(c.mode, "WINDOW")
        self.assertEqual(c.summary, "Deterministic reproduction, hypothesis-first debugging")
        self.assertEqual(c.priority, 10)
        self.assertEqual(c.applies_when, ("bug", "crash", "flaky"))
        self.assertEqual(c.never_when, ("typo",))
        self.assertEqual(c.oracle, ("--run",))
        self.assertEqual(c.socratic_grounding, ("active gate contract", "file:line"))
        self.assertEqual(c.socratic_stems, ("What is your falsifiable hypothesis for {check}?",))
        self.assertEqual(c.socratic_cap, 2)
        self.assertEqual(c.seed, "Run the failing command; capture exit code.")
        self.assertEqual(c.example, "exit=1 stderr=TypeError")
        self.assertEqual(c.criterion, "Repro command fails 3/3 before any fix.")

    def test_02_inline_list_parses_identical_to_dash_list(self):
        inline = SAMPLE.replace(
            'applies_when:\n  - "bug"\n  - "crash"\n  - "flaky"',
            'applies_when: ["bug", "crash", "flaky"]',
        )
        c_inline = parse_facet_file(inline, filename="facets/engineering/diagnosing-bugs.md")
        c_dash = parse_facet_file(SAMPLE, filename="facets/engineering/diagnosing-bugs.md")
        self.assertEqual(c_inline.applies_when, c_dash.applies_when)

    def test_03_parse_missing_required_key_error_carries_file_and_line(self):
        broken = SAMPLE.replace("priority: 10\n", "")
        with self.assertRaises(FacetContractError) as ctx:
            parse_facet_file(broken, filename="facets/engineering/diagnosing-bugs.md")
        msg = str(ctx.exception)
        self.assertIn("facets/engineering/diagnosing-bugs.md", msg)
        self.assertIn("priority", msg)
        self.assertTrue(any(ch.isdigit() for ch in msg.split(":")[-1] + msg))

    def test_04_parse_unknown_top_level_key_rejected(self):
        broken = SAMPLE.replace("schema: 1", "schema: 1\nbogus_key: 3")
        with self.assertRaises(FacetContractError) as ctx:
            parse_facet_file(broken, filename="facets/engineering/diagnosing-bugs.md")
        self.assertIn("bogus_key", str(ctx.exception))

    def test_05_parse_id_must_equal_filename_stem(self):
        with self.assertRaises(FacetContractError) as ctx:
            parse_facet_file(SAMPLE, filename="facets/engineering/other-facet.md")
        self.assertIn("other-facet", str(ctx.exception))

    def test_06_parse_priority_outside_1_10_rejected(self):
        for bad in ("0", "11"):
            with self.assertRaises(FacetContractError):
                parse_facet_file(SAMPLE.replace("priority: 10", f"priority: {bad}"),
                                 filename="facets/engineering/diagnosing-bugs.md")

    def test_07_parse_empty_applies_when_rejected(self):
        broken = SAMPLE.replace('  - "bug"\n  - "crash"\n  - "flaky"\n', "")
        with self.assertRaises(FacetContractError) as ctx:
            parse_facet_file(broken, filename="facets/engineering/diagnosing-bugs.md")
        self.assertIn("applies_when", str(ctx.exception))

    def test_08_parse_crlf_line_endings_are_stripped(self):
        c = parse_facet_file(SAMPLE.replace("\n", "\r\n"),
                             filename="facets/engineering/diagnosing-bugs.md")
        self.assertEqual(c.id, "diagnosing-bugs")
        self.assertEqual(c.priority, 10)

    def test_09_parse_missing_fence_raises_contract_error(self):
        legacy = "# Facet Directive: old\nContext: cognitive | Mode: X | Eviction: On Gate Settle\n\n1. RULE\n"
        with self.assertRaises(FacetContractError):
            parse_facet_file(legacy, filename="facets/cognitive/old.md")

    def test_10_parse_socratic_cap_zero_parses(self):
        c = parse_facet_file(SAMPLE.replace("cap: 2", "cap: 0"),
                             filename="facets/engineering/diagnosing-bugs.md")
        self.assertEqual(c.socratic_cap, 0)

    def test_11_parse_mode_policy_mismatch_is_not_a_parse_error(self):
        # 'triage' is WINDOW in Part 4 contracts; parser must not consult context_policy.
        c = parse_facet_file(SAMPLE.replace("id: diagnosing-bugs", "id: triage")
                             .replace("diagnosing-bugs.md", "triage.md"),
                             filename="facets/navigation/triage.md")
        self.assertEqual(c.mode, "WINDOW")

    def test_12_parse_load_contracts_skips_legacy_fencedless_files(self):
        root = tempfile.mkdtemp(prefix="fg-p4-load-")
        try:
            eng = os.path.join(root, "engineering")
            nav = os.path.join(root, "navigation")
            os.makedirs(eng)
            os.makedirs(nav)
            with open(os.path.join(eng, "diagnosing-bugs.md"), "w", encoding="utf-8") as f:
                f.write(SAMPLE)
            with open(os.path.join(nav, "legacy.md"), "w", encoding="utf-8") as f:
                f.write("# Facet Directive: legacy\nContext: navigation | Mode: X | Eviction: none\n\n1. OLD RULE\n")
            contracts = load_contracts(root)
            self.assertEqual(list(contracts.keys()), ["diagnosing-bugs"])
            self.assertIsInstance(contracts["diagnosing-bugs"], FacetContract)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_13_retrofit_all_nineteen_contracts_load(self):
        contracts = load_contracts(os.path.join(V271_ROOT, "facets"))
        self.assertEqual(len(contracts), 19)
        self.assertEqual(
            sorted(contracts),
            ["banner-safe-zone", "code-review", "codebase-design", "design-tokens",
             "diagnosing-bugs", "focus-design", "frontend-design", "grilling",
             "i-have-adhd", "loop-me", "prototype", "triage", "ui-ux-pro-max",
             "unlazy", "wayfinder", "writing-beats", "writing-for-agents",
             "writing-fragments", "writing-shape"],
        )


from core.facet_router import load_index, match_facets


class TestGoldenRouting(unittest.TestCase):
    def test_20_golden_replay_includes_expected_facets(self):
        index = load_index()
        with open(os.path.join(V271_ROOT, "evals", "facet_triggers.json"), encoding="utf-8") as f:
            data = json.load(f)
        misses = []
        for case in data["queries"]:
            matched = [fid for fid, _prio in match_facets(case["query"], index, top_k=4)]
            for want in case["must_include"]:
                if want not in matched:
                    misses.append(f"{case['query']!r}: missing {want} (got {matched})")
        self.assertEqual(misses, [])
        print(f"OK ({len(data['queries'])}/{len(data['queries'])})")


def _make_golden_case(case_index, case):
    def test_golden_query(self):
        index = load_index()
        matched = [fid for fid, _prio in match_facets(case["query"], index, top_k=4)]
        for want in case["must_include"]:
            self.assertIn(want, matched, f"golden query {case_index}: {case['query']!r}")
    return test_golden_query


with open(os.path.join(V271_ROOT, "evals", "facet_triggers.json"), encoding="utf-8") as _f:
    _GOLDEN = json.load(_f)["queries"]
for _i, _case in enumerate(_GOLDEN, 1):
    setattr(TestGoldenRouting, f"test_21_golden_query_{_i:02d}", _make_golden_case(_i, _case))


class TestFacetBriefHydration(unittest.TestCase):
    def _kernel(self, root):
        from core.orchestrator_kernel import OrchestratorKernel
        k = OrchestratorKernel(workspace_root=root)
        k.context_bus._deltas.clear()
        k.context_bus._seen_ids.clear()
        return k

    def test_30_brief_window_facets_carry_facet_directive_section(self):
        from core.agent_brief import AgentReceiptBundle
        from core.context_bus import ContextDeltaEvent
        from core.oracles.context_sufficiency_oracle import RichnessSufficiencyOracle
        k = self._kernel("/tmp/fg-v28-p4-brief-a")
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
            prompt = brief.to_prompt()
            verdict = RichnessSufficiencyOracle.audit_prompt(prompt)
            self.assertTrue(verdict["clean"], f"{g['id']}: {verdict['findings']}")
            if g["facet"] != "engineering":
                self.assertIn(f"## Facet Directive: {g['facet']}", prompt, g["id"])
            delta = ContextDeltaEvent.create(g["id"], "RECEIPT", f"{g['id']} locked: {g['title']} decisions")
            k.context_bus.publish(delta)
            k.active_bundles[g["id"]] = AgentReceiptBundle.create(
                gate_id=g["id"], brief_id="b",
                gate_receipts=[{"gate_id": g["id"], "status": "PASS",
                                "key_findings": [f"{g['id']} key finding for {g['title']}"]}],
                delta_ids=[delta.delta_id])

    def test_31_brief_facet_directive_holds_token_ceiling(self):
        from core.agent_brief import AgentBrief
        from core.tokens import estimate_tokens
        long_findings = [{"gate_id": f"gate-{i}", "status": "PASS",
                          "delta_id": f"aa{0:04}bb", "key_findings": ["finding " * 30]} for i in range(6)]
        for facet, ceiling in (("frontend-design", 400), ("grilling", 150)):
            brief = AgentBrief.create(gate_id="gate-x", facet=facet, task_summary="t",
                                      acceptance_criteria=["CHECK: a"], upstream_receipts=long_findings)
            prompt = brief.to_prompt()
            dynamic = 0
            if "## Upstream Context" in prompt:
                dynamic += estimate_tokens(prompt.split("## Upstream Context")[1].split("## Facet Directive")[0].split("## Mandatory")[0])
            if "## Facet Directive:" in prompt:
                dynamic += estimate_tokens(prompt.split("## Facet Directive:")[1].split("## Mandatory")[0])
            self.assertLessEqual(dynamic, ceiling, facet)

    def test_32_brief_oversized_facet_section_flagged_by_oracle(self):
        from core.oracles.context_sufficiency_oracle import RichnessSufficiencyOracle
        fat = "\n".join([f"- RULE_{i}: " + "lorem ipsum dolor sit amet " * 20 for i in range(40)])
        prompt = ("# FocusGate Sub-Agent Brief [x]\n## Gate Contract\ngate_id: g1\n"
                  "facet: frontend-design\n\n"
                  "## Upstream Context (from dependency gates)\n- gate-0 [PASS]: locked tokens (ref @abcd1234)\n\n"
                  f"## Facet Directive: frontend-design\n{fat}\n\n"
                  "## Mandatory Implementation Rigor Directive\n")
        res = RichnessSufficiencyOracle.audit_prompt(prompt)
        self.assertFalse(res["clean"])
        self.assertIn("FACET_SECTION_OVERFLOW", [f["kind"] for f in res["findings"]])

    def test_33_brief_unregistered_facet_falls_back_without_crash(self):
        import io
        import contextlib
        from core.agent_brief import AgentBrief
        brief = AgentBrief.create(gate_id="g9", facet="bespoke-legacy-facet", task_summary="t",
                                  acceptance_criteria=["CHECK: a"])
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            prompt = brief.to_prompt()
        self.assertNotIn("## Facet Directive:", prompt)
        self.assertIn("## Gate Contract", prompt)


if __name__ == "__main__":
    unittest.main()
