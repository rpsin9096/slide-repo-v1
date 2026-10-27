"""FocusGate v3.3 -- Deep Facets regression suite.

Each class is the executable form of one v3.3 finding (see AUDIT.md):
  F1  the injected facet render carried rule *titles* only
  F2  13 of 19 facets exceeded the token ceiling the SPEC declares
  F3  routing was substring-based (`fix` matched `prefix`)
  F4  every brief re-parsed all facets from disk, silently
"""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
FACETS = os.path.join(ROOT, "facets")

SAMPLE = """# Facet Contract: demo (v3.3)
Context: Engineering | Mode: Demo | Eviction: On Gate Settle

```facet-meta
schema: 1
id: demo
summary: demo facet
priority: 5
mode: WINDOW
applies_when: ["demo"]
```

## Invariant Directives
1. FIRST_RULE: Reproduce the failure with one command before touching any source file.
2. SECOND_RULE: Keep the CHECK and EXPECT unchanged between the red run and the settle run.

## Playbook
### Phases
1. Reproduce | DO: Run the failing command and record its exit code. | EXIT: exit code is non-zero 3 of 3 runs.
2. Isolate | DO: Bisect to one file:line. | EXIT: `file:line` named in the ledger.
3. Fix | DO: Change the code, never the CHECK. | EXIT: `--check demo --strict` exits 0.
### Lazy Tells
- BLIND_GUARD | SAYS: "add a None check and move on" | DETECT: diff adds `if x is None` with no failing test | INSTEAD: write the failing input as a CHECK first.
- CHECK_EDIT | SAYS: "loosen the EXPECT so it passes" | DETECT: `--evidence` shows a new fingerprint | INSTEAD: fix the code and re-baseline.
### Gate Templates
```gate
- [ ] demo-repro: {behavior}
  CHECK: python3 -m unittest {module}
  EXPECT: \\nOK
```
### Handoff
- NEXT: code-review | WHEN: the gate is settled and the diff touches more than one module.
"""


class TestPlaybookParser(unittest.TestCase):
    def test_parses_every_section(self):
        from core.facets.playbook import parse_playbook
        pb = parse_playbook(SAMPLE)
        self.assertEqual([p.name for p in pb.phases], ["Reproduce", "Isolate", "Fix"])
        self.assertIn("exit code", pb.phases[0].exit)
        self.assertEqual([t.id for t in pb.tells], ["BLIND_GUARD", "CHECK_EDIT"])
        self.assertTrue(pb.tells[0].detect and pb.tells[0].instead and pb.tells[0].says)
        self.assertEqual(len(pb.templates), 1)
        self.assertTrue(pb.templates[0].check.startswith("python3 -m unittest"))
        self.assertEqual(pb.handoffs[0].next, "code-review")

    def test_none_when_no_playbook(self):
        from core.facets.playbook import parse_playbook
        self.assertIsNone(parse_playbook("# x\n\n## Invariant Directives\n1. A_B: some words here.\n"))

    def test_phase_without_exit_is_rejected_with_line_number(self):
        from core.facets.playbook import parse_playbook, PlaybookError
        bad = SAMPLE.replace(" | EXIT: `file:line` named in the ledger.", "")
        with self.assertRaises(PlaybookError) as cm:
            parse_playbook(bad)
        self.assertRegex(str(cm.exception), r"line \d+")

    def test_directives_carry_definitions(self):
        from core.facets.playbook import parse_directives
        ds = parse_directives(SAMPLE)
        self.assertEqual([d.name for d in ds], ["FIRST_RULE", "SECOND_RULE"])
        self.assertGreater(len(ds[0].definition.split()), 8)


class TestEveryFacetIsDeep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from core.facets.catalog import FacetCatalog
        cls.cat = FacetCatalog(FACETS)

    def test_catalog_lints_clean(self):
        self.assertEqual(self.cat.lint(), [])

    def test_all_nineteen_facets_present(self):
        self.assertEqual(len(self.cat.ids()), 19)

    def test_every_facet_has_playbook_depth(self):
        for fid in self.cat.ids():
            pb = self.cat.get(fid).playbook
            self.assertIsNotNone(pb, fid)
            self.assertGreaterEqual(len(pb.phases), 3, fid)
            self.assertGreaterEqual(len(pb.tells), 2, fid)
            self.assertGreaterEqual(len(pb.templates), 1, fid)
            self.assertGreaterEqual(len(pb.handoffs), 1, fid)

    def test_every_gate_template_passes_the_evidence_linter(self):
        from core.gates.evidence import GateIntegrity, errors_of
        for fid in self.cat.ids():
            for t in self.cat.get(fid).playbook.templates:
                check = re.sub(r"\{[a-z_]+\}", "x", t.check)
                expect = re.sub(r"\{[a-z_]+\}", "x", t.expect)
                self.assertEqual(errors_of(GateIntegrity.analyze(check, expect)), [], f"{fid}: {t.check}")

    def test_handoffs_never_dangle(self):
        ids = set(self.cat.ids())
        for fid in ids:
            for h in self.cat.get(fid).playbook.handoffs:
                self.assertIn(h.next, ids, f"{fid} -> {h.next}")

    def test_lint_flags_a_shallow_facet(self):
        tmp = tempfile.mkdtemp()
        try:
            d = os.path.join(tmp, "engineering")
            os.makedirs(d)
            shallow = SAMPLE.split("## Playbook")[0].replace("demo", "shallow")
            with open(os.path.join(d, "shallow.md"), "w", encoding="utf-8") as f:
                f.write(shallow)
            from core.facets.catalog import FacetCatalog
            problems = FacetCatalog(tmp).lint()
            self.assertTrue(any("NO_PLAYBOOK" in p for p in problems), problems)
        finally:
            shutil.rmtree(tmp)

    def test_whole_file_stays_under_tier_two_cap(self):
        for fid in self.cat.ids():
            self.assertLessEqual(self.cat.get(fid).tokens, 1500, fid)


class TestInjectedRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from core.facets.catalog import FacetCatalog
        cls.cat = FacetCatalog(FACETS)

    def _ceiling(self, fid):
        return 400 if self.cat.get(fid).contract.mode == "WINDOW" else 150

    def test_every_facet_fits_its_declared_ceiling(self):
        from core.tokens import estimate_tokens
        for fid in self.cat.ids():
            text = self.cat.render(fid, self._ceiling(fid))
            self.assertTrue(text.startswith(f"## Facet Directive: {fid}"), fid)
            self.assertLessEqual(estimate_tokens(text), self._ceiling(fid), fid)

    def test_no_bare_rule_titles(self):
        for fid in self.cat.ids():
            for line in self.cat.render(fid, self._ceiling(fid)).splitlines():
                self.assertIsNone(re.match(r"^- [A-Z][A-Z0-9_]*$", line), f"{fid}: {line}")

    def test_rules_carry_their_definition(self):
        text = self.cat.render("codebase-design", 400)
        m = re.search(r"- DEEP_MODULE: (.+)", text)
        self.assertIsNotNone(m)
        self.assertGreaterEqual(len(m.group(1)), 25)

    def test_window_render_names_a_lazy_tell(self):
        self.assertRegex(self.cat.render("diagnosing-bugs", 400), r"- AVOID [A-Z_]+: ")

    def test_order_survives_squeeze(self):
        # Directives are authored most-critical-first; a squeeze keeps a prefix.
        text = self.cat.render("writing-shape", 150)
        self.assertIn("ANTI_PROSE_CLICHE", text)

    def test_tiny_budget_renders_nothing(self):
        self.assertEqual(self.cat.render("unlazy", 39), "")

    def test_hydrate_depths(self):
        directive = self.cat.render("unlazy", 400)
        playbook = self.cat.render("unlazy", 4000, depth="playbook")
        self.assertIn("### Phases", playbook)
        self.assertGreater(len(playbook), len(directive))


class TestCatalogSeam(unittest.TestCase):
    def test_default_is_cached(self):
        from core.facets.catalog import FacetCatalog
        self.assertIs(FacetCatalog.default(), FacetCatalog.default())

    def test_edit_on_disk_is_seen_without_restart(self):
        from core.facets.catalog import FacetCatalog
        tmp = tempfile.mkdtemp()
        try:
            dst = os.path.join(tmp, "facets")
            shutil.copytree(FACETS, dst)
            cat = FacetCatalog(dst)
            before = cat.get("triage").contract.summary
            p = os.path.join(dst, "navigation", "triage.md")
            with open(p, encoding="utf-8") as fh:
                text = fh.read().replace(before, before + " EDITED")
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            st = os.stat(p)
            os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
            self.assertTrue(cat.get("triage").contract.summary.endswith("EDITED"))
        finally:
            shutil.rmtree(tmp)

    def test_briefs_do_not_reparse_facets_from_disk(self):
        import core.facet_contract as fc
        from core.agent_brief import AgentBrief
        mk = lambda: AgentBrief.create(gate_id="g", facet="unlazy", task_summary="t",
                                       acceptance_criteria=["CHECK: a"]).to_prompt()
        mk()  # warm
        calls = []
        orig = fc.parse_facet_file
        fc.parse_facet_file = lambda *a, **k: (calls.append(1), orig(*a, **k))[1]
        try:
            for _ in range(3):
                mk()
        finally:
            fc.parse_facet_file = orig
        self.assertEqual(calls, [])

    def test_unknown_facet_raises_with_available_list(self):
        from core.facets.catalog import FacetCatalog, UnknownFacet
        with self.assertRaises(UnknownFacet) as cm:
            FacetCatalog(FACETS).get("nope")
        self.assertIn("unlazy", str(cm.exception))


class TestRouterV2(unittest.TestCase):
    def _ids(self, q):
        from core.facet_router import matched_ids
        return matched_ids(q, top_k=6)

    def test_substrings_inside_words_do_not_route(self):
        self.assertNotIn("diagnosing-bugs", self._ids("update the prefix of the config key"))
        self.assertNotIn("diagnosing-bugs", self._ids("the autofix pipeline runs nightly"))
        self.assertNotIn("wayfinder", self._ids("this is an ideal layout"))
        self.assertNotIn("i-have-adhd", self._ids("keyboard shortcut for the editor"))

    def test_inflections_still_route(self):
        self.assertIn("diagnosing-bugs", self._ids("the login keeps crashing"))
        self.assertIn("diagnosing-bugs", self._ids("fixing the failing checkout"))
        self.assertIn("code-review", self._ids("reviewing the pull request"))

    def test_more_evidence_outranks_a_single_high_priority_hit(self):
        from core.facet_router import default_index, match_facets
        ranked = match_facets("seam adapter interface for a deep module", default_index(), top_k=4)
        self.assertEqual(ranked[0][0], "codebase-design")

    def test_golden_and_v33_sets_pass(self):
        for name in ("facet_triggers.json", "facet_routing_v33.json"):
            with open(os.path.join(ROOT, "evals", name), encoding="utf-8") as f:
                data = json.load(f)
            for case in data["queries"]:
                got = self._ids(case["query"])
                for must in case.get("must_include", []):
                    self.assertIn(must, got, f"{name}: {case['query']!r} -> {got}")
                for no in case.get("must_exclude", []):
                    self.assertNotIn(no, got, f"{name}: {case['query']!r} -> {got}")


if __name__ == "__main__":
    unittest.main()
