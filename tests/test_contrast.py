# -*- coding: utf-8 -*-
"""Contrato del motor WCAG: matiz, ratios, umbrales y la instrumentacion que
bloquea el build cuando un par texto/superficie queda bajo el minimo."""

import unittest

from studydeck import contrast as C


class TestLuminance(unittest.TestCase):
    def test_black_relative_luminance_is_zero(self):
        self.assertAlmostEqual(C.rel_lum("000000"), 0.0, places=6)

    def test_white_relative_luminance_is_one(self):
        self.assertAlmostEqual(C.rel_lum("FFFFFF"), 1.0, places=6)

    def test_leading_hash_is_accepted(self):
        self.assertEqual(C.rel_lum("#3854CC"), C.rel_lum("3854CC"))

    def test_ratio_black_on_white_is_maximum(self):
        self.assertAlmostEqual(C.ratio("000000", "FFFFFF"), 21.0, places=2)

    def test_ratio_is_symmetric(self):
        self.assertEqual(C.ratio("3854CC", "F8F9FF"), C.ratio("F8F9FF", "3854CC"))


class TestThresholds(unittest.TestCase):
    def test_body_text_requires_aa_text(self):
        self.assertEqual(C.required_ratio(12.0, False), C.WCAG_AA_TEXT)

    def test_large_text_requires_display_threshold(self):
        self.assertEqual(C.required_ratio(18.0, False), C.WCAG_AA_DISPLAY)

    def test_bold_fourteen_requires_display_threshold(self):
        self.assertEqual(C.required_ratio(14.0, True), C.WCAG_AA_DISPLAY)

    def test_thirteen_point_nine_bold_is_still_text(self):
        self.assertEqual(C.required_ratio(13.9, True), C.WCAG_AA_TEXT)


class TestSelection(unittest.TestCase):
    def test_pick_returns_first_candidate_that_passes(self):
        self.assertEqual(C.pick(["FFFFFF", "3854CC"], "3854CC", 4.5), "FFFFFF")

    def test_pick_returns_none_when_no_candidate_passes(self):
        self.assertIsNone(C.pick(["3854CC"], "3854CC", 4.5))

    def test_pick_skips_falsy_candidates(self):
        self.assertEqual(C.pick([None, "", "FFFFFF"], "3854CC", 4.5), "FFFFFF")

    def test_shade_until_reaches_ratio_keeping_hue_order(self):
        shaded = C.shade_until("1E8A5A", "FFFFFF", 4.5)
        self.assertGreaterEqual(C.ratio(shaded, "FFFFFF"), 4.5)
        self.assertLess(int(shaded[4:6], 16), 0x8A)


class TestSurfaceStack(unittest.TestCase):
    def test_topmost_painted_fill_wins(self):
        gate = C.ContrastGate()
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        gate.note_surface("3854CC", 2, 2, 4, 4)
        self.assertEqual(gate.surface_at(3, 3), "3854CC")

    def test_point_outside_every_surface_has_no_fill(self):
        gate = C.ContrastGate()
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        self.assertIsNone(gate.surface_at(30, 30))

    def test_none_coordinates_are_not_measured(self):
        gate = C.ContrastGate()
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        self.assertIsNone(gate.surface_at(None, None))

    def test_falsy_fill_is_not_a_surface(self):
        gate = C.ContrastGate()
        gate.note_surface(None, 0, 0, 10, 10)
        self.assertIsNone(gate.surface_at(1, 1))


class TestGateInstrumentation(unittest.TestCase):
    def test_low_contrast_pair_is_reported(self):
        gate = C.ContrastGate()
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        gate.log_text("9AA3C0", 12.0, False, px=5, py=5)
        fails = gate.failures()
        self.assertEqual(len(fails), 1)
        self.assertEqual(fails[0]["fg"], "9AA3C0")

    def test_passing_pair_is_not_reported(self):
        gate = C.ContrastGate()
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        gate.log_text("2B2C4A", 12.0, False, px=5, py=5)
        self.assertEqual(gate.failures(), [])

    def test_text_over_unknown_surface_is_skipped(self):
        gate = C.ContrastGate()
        gate.log_text("2B2C4A", 12.0, False, px=5, py=5)
        self.assertEqual(gate.failures(), [])

    def test_decorative_text_is_exempt(self):
        gate = C.ContrastGate()
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        gate.log_text("9AA3C0", 88.0, True, deco=True, px=5, py=5)
        self.assertEqual(gate.failures(), [])

    def test_unmeasured_block_suspends_native_text(self):
        gate = C.ContrastGate()
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        with gate.unmeasured():
            gate.log_text("9AA3C0", 12.0, False, px=5, py=5)
        self.assertEqual(gate.failures(), [])

    def test_unmeasured_restores_measurement_after_exit(self):
        gate = C.ContrastGate()
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        with gate.unmeasured():
            pass
        gate.log_text("9AA3C0", 12.0, False, px=5, py=5)
        self.assertEqual(len(gate.failures()), 1)

    def test_new_slide_clears_surfaces_but_keeps_the_deck_log(self):
        gate = C.ContrastGate()
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        gate.log_text("9AA3C0", 12.0, False, px=5, py=5)
        gate.new_slide()
        self.assertIsNone(gate.surface_at(5, 5))
        self.assertEqual(len(gate.failures()), 1)

    def test_violations_from_earlier_slides_survive(self):
        gate = C.ContrastGate()
        gate.begin_slide(2, "definition")
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        gate.log_text("9AA3C0", 12.0, False, px=5, py=5)
        gate.begin_slide(3, "section_divider")
        fails = gate.failures()
        self.assertEqual([f["slide"] for f in fails], [2])

    def test_failure_carries_slide_and_module_context(self):
        gate = C.ContrastGate()
        gate.begin_slide(7, "stat_card")
        gate.note_surface("EEF0FF", 0, 0, 10, 10)
        gate.log_text("9AA3C0", 12.0, False, px=5, py=5)
        fails = gate.failures()
        self.assertEqual((fails[0]["slide"], fails[0]["module"]), (7, "stat_card"))

    def test_display_text_is_allowed_a_lower_ratio(self):
        gate = C.ContrastGate()
        gate.note_surface("3854CC", 0, 0, 10, 10)
        gate.log_text("FFFFFF", 40.0, True, px=5, py=5)
        self.assertEqual(gate.failures(), [])


if __name__ == "__main__":
    unittest.main()