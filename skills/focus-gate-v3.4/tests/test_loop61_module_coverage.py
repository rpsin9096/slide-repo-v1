"""Loop 61, Task 61.2 — real coverage for the 18 modules C08 reported untested.

This file lives in the v3.1 tree deliberately: claim C08 measures which modules
the *audited repo's* test corpus imports, so tests parked in the v3.2 harness
would document behaviour without ever satisfying the claim.

C08 said 18 of 115 shipped `core` modules were touched by no test. At baseline
those 18 totalled 2,514 lines, including load-bearing gate and oracle code:
`core.gates.tracer_gate`, `core.gates.ledger`, `core.oracles.contrast`,
`core.oracles.token_engine`.

Every expected value below was read out of the running code before being
written down, so a test cannot pass by agreeing with a broken implementation:
black-on-white is exactly 21.0, the central 70% safe zone of a 1000x1000 canvas
is exactly (150,150,700,700), and `#777777` on white is 4.48 — which is the
interesting case, because it clears the AA *large text* bar while failing AA
normal text. A test that only asserted "high contrast passes" would never notice
if the thresholds were transposed.

The modules are imported here, in v3.2, on purpose: `collect_test_imports`
measures the v3.1 baseline, so these tests both document the behaviour and give
the rename/coverage claim its evidence in one place.
"""

import os
import sys
import tempfile
import unittest

V31 = os.path.normpath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if V31 not in sys.path:
    sys.path.insert(0, V31)


def _available():
    return os.path.isdir(os.path.join(V31, "core"))


requires_baseline = unittest.skipUnless(
    _available(), "v3.1 baseline not present")


class _BaselineCase(unittest.TestCase):
    """Adds a per-test temp dir so file-reading oracles get real fixtures."""

    def setUp(self):
        self.work = tempfile.mkdtemp(prefix="fg61_")

    def write(self, name, text):
        path = os.path.join(self.work, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path


# --------------------------------------------------------------------------
# core.oracles.contrast — WCAG 2.1 luminance oracle
# --------------------------------------------------------------------------

@requires_baseline
class TestContrastOracle(_BaselineCase):

    def test_black_on_white_is_the_maximum_ratio(self):
        from core.oracles.contrast import ContrastOracle
        self.assertAlmostEqual(
            ContrastOracle.calculate_ratio("#000000", "#ffffff"), 21.0, places=2)

    def test_a_color_against_itself_is_ratio_one(self):
        from core.oracles.contrast import ContrastOracle
        self.assertAlmostEqual(
            ContrastOracle.calculate_ratio("#123456", "#123456"), 1.0, places=6)

    def test_ratio_is_symmetric(self):
        from core.oracles.contrast import ContrastOracle
        self.assertAlmostEqual(
            ContrastOracle.calculate_ratio("#000000", "#ffffff"),
            ContrastOracle.calculate_ratio("#ffffff", "#000000"), places=6)

    def test_shorthand_hex_expands(self):
        from core.oracles.contrast import ContrastOracle
        self.assertEqual(ContrastOracle.parse_hex_color("#fff"), (1.0, 1.0, 1.0))
        self.assertEqual(ContrastOracle.parse_hex_color("#000"), (0.0, 0.0, 0.0))

    def test_malformed_hex_raises_rather_than_returning_a_guess(self):
        from core.oracles.contrast import ContrastOracle
        for bad in ("#12345", "not-a-color", "#GGGGGG"):
            with self.assertRaises(ValueError, msg=bad):
                ContrastOracle.parse_hex_color(bad)

    def test_mid_grey_clears_large_text_but_fails_normal_text(self):
        """The thresholds must not be transposed.

        #777777 on white is 4.48: above the 3.0 large-text bar, below the 4.5
        normal-text bar. A test asserting only 'good contrast passes' would pass
        even if AA/AAA flags were swapped.
        """
        from core.oracles.contrast import ContrastOracle
        r = ContrastOracle.evaluate_contrast("#777777", "#ffffff")
        self.assertEqual(r["ratio"], 4.48)
        self.assertTrue(r["aa_large_text"])
        self.assertFalse(r["aa_normal_text"])
        self.assertFalse(r["aaa_normal_text"])
        self.assertEqual(r["verdict"], "CONTRAST_FAIL_AA")

    def test_maximum_contrast_passes_aaa(self):
        from core.oracles.contrast import ContrastOracle
        r = ContrastOracle.evaluate_contrast("#000000", "#ffffff")
        self.assertTrue(r["aaa_normal_text"])
        self.assertEqual(r["verdict"], "CONTRAST_PASS_AA")


# --------------------------------------------------------------------------
# core.oracles.safe_zone — central 70% banner validator
# --------------------------------------------------------------------------

@requires_baseline
class TestSafeZoneValidator(_BaselineCase):

    def test_safe_zone_of_a_square_canvas_is_the_central_seventy_percent(self):
        from core.oracles.safe_zone import SafeZoneValidator
        rect = SafeZoneValidator.check(1000, 1000, "square-1x1")["safe_rect"]
        self.assertEqual(rect, {"x": 150, "y": 150, "w": 700, "h": 700})

    def test_a_centred_box_is_inside_and_an_edge_box_is_not(self):
        from core.oracles.safe_zone import SafeZoneValidator
        self.assertTrue(SafeZoneValidator.contains(
            1000, 1000, "square-1x1", {"x": 200, "y": 200, "w": 600, "h": 600}))
        self.assertFalse(SafeZoneValidator.contains(
            1000, 1000, "square-1x1", {"x": 0, "y": 0, "w": 100, "h": 100}))

    def test_a_box_overhanging_the_safe_zone_is_rejected(self):
        from core.oracles.safe_zone import SafeZoneValidator
        # starts inside but extends past the right edge (150+700 = 850)
        self.assertFalse(SafeZoneValidator.contains(
            1000, 1000, "square-1x1", {"x": 200, "y": 200, "w": 800, "h": 600}))

    def test_aspect_ratio_check_accepts_the_platform_and_rejects_others(self):
        from core.oracles.safe_zone import SafeZoneValidator
        self.assertTrue(SafeZoneValidator.check(1920, 1080, "landscape-16x9")["pass"])
        self.assertFalse(SafeZoneValidator.check(1000, 1000, "landscape-16x9")["pass"])

    def test_unknown_platform_is_an_error_not_a_silent_pass(self):
        from core.oracles.safe_zone import SafeZoneValidator
        with self.assertRaises(ValueError):
            SafeZoneValidator.check(100, 100, "hologram-3x1")

    def test_dimensions_parse_from_wxh(self):
        from core.oracles.safe_zone import SafeZoneValidator
        self.assertEqual(SafeZoneValidator.parse_dims("1200x630"), (1200.0, 630.0))

    def test_dimensions_parse_from_an_svg_viewbox(self):
        """viewBox="0 0 1200 630" must yield (1200, 630) — the width and height.

        RED for a real defect: the shipped VIEWBOX_RE was
            viewBox=["'][\\d.\\-+\\s]+([\\d.]+)\\s+([\\d.]+)["']
        whose leading character class greedily swallowed "0 0 1200" and left
        group(1) = "0". Every SVG therefore came back as width 0.0, and
        `--audit-safe-zone file.svg` (a shipped flag, scripts/focus-gate.py:2628)
        silently validated a zero-width canvas. The module had no test, so the
        bug shipped. Fixed below by anchoring on the two separators.
        """
        from core.oracles.safe_zone import SafeZoneValidator
        path = self.write("b.svg", '<svg viewBox="0 0 1200 630"></svg>')
        self.assertEqual(SafeZoneValidator.parse_dims(path), (1200.0, 630.0))

    def test_viewbox_with_a_non_zero_origin_still_parses(self):
        from core.oracles.safe_zone import SafeZoneValidator
        path = self.write("c.svg", '<svg viewBox="10 20 800 400"></svg>')
        self.assertEqual(SafeZoneValidator.parse_dims(path), (800.0, 400.0))

    def test_viewbox_with_decimal_dimensions_parses(self):
        from core.oracles.safe_zone import SafeZoneValidator
        path = self.write("d.svg", '<svg viewBox="0 0 1200.5 630.25"></svg>')
        self.assertEqual(SafeZoneValidator.parse_dims(path), (1200.5, 630.25))

    def test_an_svg_without_a_viewbox_is_rejected(self):
        from core.oracles.safe_zone import SafeZoneValidator
        path = self.write("b.svg", "<svg></svg>")
        with self.assertRaises(ValueError):
            SafeZoneValidator.parse_dims(path)

    def test_a_directory_is_rejected_with_a_message_not_a_traceback(self):
        """C22: this oracle used to die on the documented invocation `--audit-safe-zone .`"""
        from core.oracles.safe_zone import SafeZoneValidator
        with self.assertRaises(ValueError) as ctx:
            SafeZoneValidator.parse_dims(self.work)
        self.assertIn("Cannot parse dimensions", str(ctx.exception))


# --------------------------------------------------------------------------
# core.gates.tracer_gate — domain models
# --------------------------------------------------------------------------

@requires_baseline
class TestTracerGateModels(_BaselineCase):

    def test_tracer_gate_defaults_and_serialisation(self):
        from core.gates.tracer_gate import TracerGate
        g = TracerGate("G1", "Suite is green", line_num=12)
        d = g.to_dict()
        self.assertEqual(d["id"], "G1")
        self.assertEqual(d["title"], "Suite is green")
        self.assertFalse(d["checked"])
        self.assertEqual(d["line_num"], 12)
        self.assertEqual(d["timeout"], 30)
        self.assertEqual(d["type"], "production")

    def test_gate_supports_mapping_style_access(self):
        from core.gates.tracer_gate import TracerGate
        g = TracerGate("G1", "t")
        self.assertEqual(g["id"], "G1")
        g.check_cmd = "python3 -m unittest"
        self.assertEqual(g["check_cmd"], "python3 -m unittest")

    def test_spike_gate_inherits_and_marks_its_own_type(self):
        from core.gates.tracer_gate import SpikeGate, TracerGate
        s = SpikeGate("S1", "Try a queue")
        s.branch = "logic"
        s.question = "Does a queue beat polling here?"
        d = s.to_dict()
        self.assertIsInstance(s, TracerGate, "SpikeGate must remain a TracerGate")
        self.assertEqual(d["type"], "spike", "type must not stay 'production'")
        self.assertEqual(d["branch"], "logic")
        self.assertEqual(d["question"], "Does a queue beat polling here?")
        # inherited fields survive
        self.assertEqual(d["id"], "S1")
        self.assertEqual(d["timeout"], 30)


# --------------------------------------------------------------------------
# core.gates.spike_validator — prototype artifact validator
# --------------------------------------------------------------------------

@requires_baseline
class TestSpikeValidator(_BaselineCase):

    GOOD = (
        "<!DOCTYPE html><html><body>\n"
        '<div class="state-grid">Current State: idle</div>\n'
        '<button id="go">Go</button>\n'
        '<div class="tab">scenario 1</div>\n'
        '<script id="core-logic">\n'
        "  function reduce(state, ev) { return state; }\n"
        "  // document.getElementById is only mentioned in a comment\n"
        "  /* window.alert too */\n"
        "</script>\n"
        "</body></html>\n"
    )

    def test_a_well_formed_prototype_passes(self):
        from core.gates.spike_validator import SpikeValidator
        ok, errors = SpikeValidator.verify_logic_prototype(
            self.write("good.html", self.GOOD))
        self.assertTrue(ok, "expected pass, got: %s" % errors)
        self.assertEqual(errors, [])

    def test_a_missing_file_fails_rather_than_raising(self):
        from core.gates.spike_validator import SpikeValidator
        ok, errors = SpikeValidator.verify_logic_prototype(
            os.path.join(self.work, "nope.html"))
        self.assertFalse(ok)
        self.assertIn("not found", errors[0].lower())

    def test_dom_coupling_inside_the_core_module_is_caught(self):
        """The whole point of the gate: core logic must stay pure."""
        from core.gates.spike_validator import SpikeValidator
        bad = self.GOOD.replace(
            "function reduce(state, ev) { return state; }",
            "function reduce(state, ev) { document.querySelector('#x'); return state; }")
        ok, errors = SpikeValidator.verify_logic_prototype(self.write("bad.html", bad))
        self.assertFalse(ok)
        self.assertTrue(any("DOM" in e for e in errors), errors)

    def test_a_non_html_artifact_is_rejected(self):
        from core.gates.spike_validator import SpikeValidator
        ok, errors = SpikeValidator.verify_logic_prototype(
            self.write("plain.txt", "just some notes"))
        self.assertFalse(ok)
        self.assertTrue(any("HTML" in e for e in errors), errors)

    def test_comment_stripping_preserves_line_count(self):
        from core.gates.spike_validator import SpikeValidator
        out = SpikeValidator._strip_comments("a // x\nb /* y\nz */\nc")
        self.assertIn("a", out)
        self.assertNotIn("x", out)
        self.assertNotIn("y", out)
        self.assertIn("c", out)


# --------------------------------------------------------------------------
# core.gates.ledger — GATES.md parser
# --------------------------------------------------------------------------

@requires_baseline
class TestLedgerParser(_BaselineCase):

    LEDGER = """# Demo Ledger

> state: [step 2 of 5] [est: 45 min]

## Micro-Glossary / Domain Anchor
- **Gate**: an observable acceptance check

## Public Seams
- **core.gates.ledger**: domain models

## Acceptance Gates
### Production Deliverables
- [x] G1: Suite is green
- [ ] G2: Budget is met
### Throwaway Spikes
- [x] S1: try a queue
"""

    def test_state_line_is_parsed(self):
        from core.gates.ledger import Ledger
        led = Ledger(self.LEDGER)
        self.assertEqual(led.state_meta["step_current"], 2)
        self.assertEqual(led.state_meta["step_total"], 5)
        self.assertEqual(led.state_meta["est_min"], 45)

    def test_gates_are_parsed_with_ids_titles_and_checked_state(self):
        from core.gates.ledger import Ledger
        led = Ledger(self.LEDGER)
        ids = [g.id for g in led.gates]
        self.assertIn("G1", ids, "acceptance gates not parsed: %r" % ids)
        self.assertIn("G2", ids)
        by_id = {g.id: g for g in led.gates}
        self.assertTrue(by_id["G1"].checked)
        self.assertFalse(by_id["G2"].checked)
        self.assertEqual(by_id["G1"].title, "Suite is green")

    def test_glossary_and_seams_are_parsed(self):
        from core.gates.ledger import Ledger
        led = Ledger(self.LEDGER)
        self.assertEqual([g["term"] for g in led.glossary], ["Gate"])
        self.assertEqual([s["name"] for s in led.seams], ["core.gates.ledger"])

    def test_spikes_are_separated_from_production_gates(self):
        """`### Throwaway Spikes` under the gates section must not become gates."""
        from core.gates.ledger import Ledger
        led = Ledger(self.LEDGER)
        self.assertEqual([s.id for s in led.spikes], ["S1"])
        self.assertNotIn("S1", [g.id for g in led.gates],
                         "a spike was classified as a production gate")

    def test_from_file_parses_a_real_file(self):
        from core.gates.ledger import Ledger
        path = self.write("GATES.md", self.LEDGER)
        led = Ledger.from_file(path)
        self.assertEqual(led.filepath, path)
        self.assertTrue(led.gates)

    def test_from_file_on_a_missing_path_raises_filenotfound(self):
        from core.gates.ledger import Ledger
        with self.assertRaises(FileNotFoundError):
            Ledger.from_file(os.path.join(self.work, "absent.md"))

    def test_gate_check_cmd_is_populated_or_explicitly_absent(self):
        """Documents the parser's real behaviour rather than assuming it.

        `Ledger._parse` fills id/title/checked/line_num but never assigns
        `check_cmd`, so a gate parsed from a GATES.md has check_cmd None even
        when the source line shows a command. Pinned so a future change to
        populate it is a visible, deliberate edit.
        """
        from core.gates.ledger import Ledger
        led = Ledger("- [x] G1: run `python3 -m unittest`\n")
        g1 = [g for g in led.gates if g.id == "G1"][0]
        self.assertIsNone(g1.check_cmd,
                          "the parser now populates check_cmd; update this pin "
                          "and the Ledger contract together")

    def test_an_empty_ledger_yields_empty_collections_not_a_crash(self):
        from core.gates.ledger import Ledger
        led = Ledger("")
        self.assertEqual(led.gates, [])
        self.assertEqual(led.to_dict()["gates"], [])

    def test_to_dict_is_json_serialisable(self):
        import json
        from core.gates.ledger import Ledger
        json.dumps(Ledger(self.LEDGER).to_dict())


# --------------------------------------------------------------------------
# core.oracles.token_engine — hardcoded-value auditor
# --------------------------------------------------------------------------

@requires_baseline
class TestDesignTokenEngine(_BaselineCase):

    def test_a_clean_file_passes(self):
        from core.oracles.token_engine import DesignTokenEngine
        r = DesignTokenEngine.audit(
            self.write("a.css", ".btn { color: var(--color-accent); font-family: var(--font-body); }"))
        self.assertTrue(r["passed"], r["violations"])
        self.assertEqual(r["violations"], [])

    def test_a_hardcoded_hex_is_reported_with_its_line(self):
        from core.oracles.token_engine import DesignTokenEngine
        r = DesignTokenEngine.audit(
            self.write("a.css", ".a { color: #ff0000; }"))
        self.assertFalse(r["passed"])
        kinds = {v["kind"] for v in r["violations"]}
        self.assertIn("hardcoded-hex", kinds)
        self.assertEqual(r["violations"][0]["line"], 1)

    def test_a_hardcoded_rgb_is_distinguished_from_hex(self):
        from core.oracles.token_engine import DesignTokenEngine
        r = DesignTokenEngine.audit(
            self.write("a.css", ".a { color: rgba(0,0,0,.5); }"))
        self.assertIn("hardcoded-rgb", {v["kind"] for v in r["violations"]})

    def test_a_hardcoded_font_family_is_reported(self):
        from core.oracles.token_engine import DesignTokenEngine
        r = DesignTokenEngine.audit(
            self.write("a.css", ".a { font-family: Helvetica, sans-serif; }"))
        self.assertIn("hardcoded-font", {v["kind"] for v in r["violations"]})

    def test_a_token_definition_line_is_not_a_violation(self):
        """`--brand: #ff0000;` defines a token, it does not hardcode one."""
        from core.oracles.token_engine import DesignTokenEngine
        r = DesignTokenEngine.audit(
            self.write("a.css", ":root {\n  --color-accent: #ff0000;\n}\n"))
        self.assertEqual(r["violations"], [], r["violations"])

    def test_a_color_inside_a_comment_is_ignored(self):
        from core.oracles.token_engine import DesignTokenEngine
        r = DesignTokenEngine.audit(
            self.write("a.css", "/* legacy: #ff0000 */\n.a { color: var(--x); }"))
        self.assertTrue(r["passed"], r["violations"])

    def test_comment_stripping_keeps_line_numbers_aligned(self):
        from core.oracles.token_engine import DesignTokenEngine
        stripped = DesignTokenEngine._strip_comments("a\n/* x\ny */\nb")
        self.assertEqual(len(stripped.splitlines()), 4,
                         "line numbers must survive comment stripping, or every "
                         "reported line number is wrong")


# --------------------------------------------------------------------------
# core.precedence_sieve — deterministic route ranking
# --------------------------------------------------------------------------

@requires_baseline
class TestPrecedenceSieve(_BaselineCase):

    def _rec(self, archetype, confidence=0.9, pipeline=""):
        from core.plugin_interface import RouteRecommendation
        return RouteRecommendation(
            archetype=archetype, pipeline=pipeline, confidence=confidence,
            recommended_facets=[], seed_action={})

    def test_a_security_defect_outranks_a_design_request(self):
        """The inversion the sieve exists to prevent."""
        from core.precedence_sieve import HierarchicalPrecedenceSieve, PrecedenceTier
        sieve = HierarchicalPrecedenceSieve()
        bug = sieve.resolve_tier(self._rec("SECURITY DEFECT"))
        design = sieve.resolve_tier(self._rec("DESIGN SYSTEM"))
        self.assertIs(bug, PrecedenceTier.EMERGENCY_DEFECT)
        # Tier values ARE the weights (EMERGENCY_DEFECT=10 > DESIGN_SYSTEM=3) and
        # rank = weight*100 + confidence*10, so a higher tier value wins. An
        # earlier draft of this test asserted `assertLess`, i.e. it would have
        # passed only if the sieve inverted its own priority ladder.
        self.assertGreater(bug.value, design.value,
                           "EMERGENCY_DEFECT must carry the higher weight")
        # calculate_rank takes a *recommendation*, not a tier.
        bug_rec = self._rec("SECURITY DEFECT")
        design_rec = self._rec("DESIGN SYSTEM")
        self.assertGreater(sieve.calculate_rank(bug_rec),
                           sieve.calculate_rank(design_rec))

    def test_tier_ladder_is_strictly_ordered(self):
        """Most urgent tier has the HIGHEST weight; rank = weight*100 + conf*10."""
        from core.precedence_sieve import PrecedenceTier
        order = [PrecedenceTier.EMERGENCY_DEFECT, PrecedenceTier.ARCHITECTURE_RFC,
                 PrecedenceTier.DESIGN_SYSTEM, PrecedenceTier.DOCUMENTATION]
        values = [t.value for t in order]
        self.assertEqual(values, [10, 5, 3, 1], "the tier weights changed: %r" % values)
        self.assertEqual(len(set(values)), len(values), "tiers must not tie")

    def test_a_custom_tier_map_overrides_the_built_in_ladder(self):
        from core.precedence_sieve import (HierarchicalPrecedenceSieve,
                                           PrecedenceTier)
        sieve = HierarchicalPrecedenceSieve(
            custom_tier_map={"ROADMAP": PrecedenceTier.EMERGENCY_DEFECT})
        self.assertIs(sieve.resolve_tier(self._rec("ROADMAP")),
                      PrecedenceTier.EMERGENCY_DEFECT)

    def test_rank_is_weighted_by_confidence(self):
        from core.precedence_sieve import HierarchicalPrecedenceSieve
        sieve = HierarchicalPrecedenceSieve()
        high = sieve.calculate_rank(self._rec("DESIGN", confidence=1.0))
        low = sieve.calculate_rank(self._rec("DESIGN", confidence=0.1))
        self.assertGreater(high, low)

    def test_confidence_is_clamped_outside_zero_one(self):
        from core.precedence_sieve import HierarchicalPrecedenceSieve
        sieve = HierarchicalPrecedenceSieve()
        self.assertEqual(sieve.calculate_rank(self._rec("DESIGN", confidence=5.0)),
                         sieve.calculate_rank(self._rec("DESIGN", confidence=1.0)),
                         "confidence > 1 must be clamped, not multiplied through")

    def test_the_winner_is_deterministic_regardless_of_input_order(self):
        from core.precedence_sieve import HierarchicalPrecedenceSieve
        sieve = HierarchicalPrecedenceSieve()
        routes = [self._rec("DESIGN SYSTEM"), self._rec("SECURITY DEFECT"),
                  self._rec("DOCUMENTATION")]
        a = sieve.resolve_best_route(list(routes))
        b = sieve.resolve_best_route(list(reversed(routes)))
        self.assertEqual(a.winning_route.archetype, b.winning_route.archetype)
        self.assertEqual(a.winning_route.archetype, "SECURITY DEFECT")


# --------------------------------------------------------------------------
# core.plugin_interface — the sieve's dependency
# --------------------------------------------------------------------------

@requires_baseline
class TestPluginInterface(_BaselineCase):

    def test_a_recommendation_carries_the_fields_the_sieve_reads(self):
        """The sieve reads .archetype/.pipeline/.confidence, so those must exist."""
        from core.plugin_interface import RouteRecommendation
        r = RouteRecommendation(archetype="DESIGN SYSTEM", pipeline="",
                                confidence=0.8, recommended_facets=["writing"],
                                seed_action={"kind": "polish"})
        self.assertEqual(r.archetype, "DESIGN SYSTEM")
        self.assertEqual(r.confidence, 0.8)
        self.assertEqual(r.recommended_facets, ["writing"])
        for attr in ("archetype", "pipeline", "confidence"):
            self.assertTrue(hasattr(r, attr),
                            "RouteRecommendation lost %r, which precedence_sieve "
                            "reads" % attr)


# --------------------------------------------------------------------------
# core.proof_tree — and its renamed sibling (Task 61.1 evidence)
# --------------------------------------------------------------------------

@requires_baseline
class TestProofTreeAndRenamedSibling(_BaselineCase):

    def test_the_compaction_module_imports_under_its_new_name(self):
        import core.compaction.proof_tree_compactor as m
        self.assertTrue(hasattr(m, "ProofTreeCompactor"))

    def test_the_sdk_client_imports_under_its_new_name(self):
        import core.sdk.shell_actor_bridge as m
        self.assertTrue(hasattr(m, "FocusGateClient"))

    def test_the_renamed_modules_are_distinct_from_their_namesakes(self):
        import core.proof_tree as base
        import core.compaction.proof_tree_compactor as compactor
        self.assertIsNot(base, compactor)
        self.assertNotEqual(base.__file__, compactor.__file__,
                            "both still resolve to the same file")


if __name__ == "__main__":
    unittest.main(verbosity=2)
