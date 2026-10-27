# -*- coding: utf-8 -*-
"""Lienzo 16:9, zona segura canonica y los dos helpers de reparto."""

import unittest

from studydeck import geometry as G


class TestCanvas(unittest.TestCase):
    def test_canvas_is_16_9_widescreen(self):
        self.assertAlmostEqual(G.CANVAS_W / G.CANVAS_H, 16 / 9, places=3)

    def test_canvas_matches_pptx_standard_inches(self):
        self.assertEqual((G.CANVAS_W, G.CANVAS_H), (13.333, 7.500))

    def test_safe_origin_is_canonical(self):
        self.assertEqual((G.SAFE_X0, G.SAFE_Y0), (0.650, 1.550))

    def test_content_width_fits_inside_canvas(self):
        self.assertLess(G.SAFE_X0 + G.CONTENT_W, G.CANVAS_W)

    def test_content_band_starts_at_safe_origin(self):
        self.assertEqual(G.content_top(), G.SAFE_Y0)

    def test_content_band_ends_above_footer(self):
        self.assertLessEqual(G.SAFE_Y0 + G.CONTENT_H, G.FOOTER_Y)


class TestStackLayout(unittest.TestCase):
    def test_row_height_divides_zone_minus_gaps(self):
        h, _y = G.stack_layout(1.0, 3.0, 3, 0.2)
        self.assertAlmostEqual(h, (3.0 - 0.4) / 3, places=6)

    def test_cap_wins_over_even_division(self):
        h, _y = G.stack_layout(1.0, 9.0, 2, 0.2, cap=1.0)
        self.assertEqual(h, 1.0)

    def test_group_is_vertically_centred(self):
        h, y = G.stack_layout(1.0, 3.0, 2, 0.2)
        self.assertAlmostEqual(y + (h * 2 + 0.2) / 2, 2.5, places=6)

    def test_single_item_fills_zone_without_cap(self):
        h, y = G.stack_layout(1.0, 3.0, 1, 0.2)
        self.assertAlmostEqual((h, y), (3.0, 1.0), places=6)

    def test_single_item_is_centred_under_cap(self):
        h, y = G.stack_layout(1.0, 3.0, 1, 0.2, cap=1.0)
        self.assertAlmostEqual(y, 2.0, places=6)

    def test_zero_items_does_not_divide_by_zero(self):
        h, y = G.stack_layout(1.0, 3.0, 0, 0.2)
        self.assertGreater(h, 0)
        self.assertIsInstance(y, float)


class TestRowLayout(unittest.TestCase):
    def test_item_width_subtracts_all_gaps(self):
        w, _x = G.row_layout(0.0, 12.0, 4, 0.25)
        self.assertAlmostEqual(w, (12.0 - 0.75) / 4, places=6)

    def test_uncentred_row_starts_at_origin(self):
        _w, x = G.row_layout(0.65, 12.0, 3, 0.2)
        self.assertEqual(x, 0.65)

    def test_centred_row_is_offset_from_origin(self):
        _w, x = G.row_layout(0.65, 12.0, 3, 0.2, center=True)
        self.assertGreater(x, 0.65)

    def test_centred_row_is_horizontally_balanced(self):
        w, x = G.row_layout(0.65, 12.0, 3, 0.2, center=True)
        self.assertAlmostEqual(x + (w * 3 + 0.4) / 2, 0.65 + 6.0, places=6)

    def test_single_item_never_exceeds_band(self):
        w, _x = G.row_layout(0.65, 12.0, 1, 0.2)
        self.assertLessEqual(w, 12.0)


if __name__ == "__main__":
    unittest.main()