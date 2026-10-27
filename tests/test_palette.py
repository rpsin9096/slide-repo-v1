# -*- coding: utf-8 -*-
"""Paleta UCP unica, tokens WCAG derivados y tipografia Montserrat."""

import unittest

from studydeck import contrast as C
from studydeck.palette import BRAND, PALETTES, load_palette


class TestScope(unittest.TestCase):
    def test_ucp_is_the_only_palette(self):
        self.assertEqual(list(PALETTES), ['ucp'])

    def test_unknown_palette_is_rejected(self):
        with self.assertRaises(ValueError):
            load_palette('oxford')

    def test_ucp_brand_hexes_are_canonical(self):
        self.assertEqual(BRAND['primary'], '3854CC')
        self.assertEqual(BRAND['accent'], 'D92A2B')
        self.assertEqual(BRAND['alert'], 'B91C1C')
        self.assertEqual(BRAND['success'], '1E8A5A')

    def test_typography_is_montserrat_only(self):
        pal = load_palette('ucp')
        self.assertEqual(pal.typography['title'], 'Montserrat')
        self.assertEqual(pal.typography['body'], 'Montserrat')

    def test_every_brand_slot_exists(self):
        pal = load_palette('ucp')
        for slot in ('primary', 'accent', 'bg', 'text', 'text_muted', 'alert',
                     'success', 'border', 'card', 'soft', 'highlight'):
            self.assertRegex(pal.brand[slot], r'^[0-9A-F]{6}$')


class TestDerivedTokens(unittest.TestCase):
    def setUp(self):
        self.pal = load_palette('ucp')

    def test_text_on_primary_is_white(self):
        self.assertEqual(self.pal.tokens['on_primary'], 'FFFFFF')

    def test_text_on_accent_is_white(self):
        self.assertEqual(self.pal.tokens['on_accent'], 'FFFFFF')

    def test_ink_accent_is_legible_on_soft(self):
        self.assertGreaterEqual(C.ratio(self.pal.tokens['ink_accent'],
                                        self.pal.brand['soft']), 4.5)

    def test_ink_accent_shifts_when_brand_red_is_unreadable(self):
        self.assertNotEqual(self.pal.tokens['ink_accent'], self.pal.brand['accent'])

    def test_ink_success_is_legible_on_soft(self):
        self.assertGreaterEqual(C.ratio(self.pal.tokens['ink_success'],
                                        self.pal.brand['soft']), 4.5)

    def test_brand_hexes_stay_intact_for_graphics(self):
        self.assertEqual(self.pal.brand['accent'], 'D92A2B')

    def test_every_token_is_readable_on_its_declared_surface(self):
        b, t = self.pal.brand, self.pal.tokens
        pairs = (
            (t['on_primary'], b['primary'], 4.5),
            (t['on_primary_soft'], b['primary'], 4.5),
            (t['on_accent'], b['accent'], 4.5),
            (t['ink_accent'], b['soft'], 4.5),
            (t['ink_success'], b['soft'], 4.5),
            (t['subtitle_on_primary'], b['primary'], 4.5),
            (t['on_alert'], b['alert'], 4.5),
            (b['text'], b['bg'], 4.5),
            (b['text_muted'], b['bg'], 4.5),
        )
        for fg, bg, need in pairs:
            with self.subTest(fg=fg, bg=bg):
                self.assertGreaterEqual(C.ratio(fg, bg), need)

    def test_on_success_token_reaches_text_threshold(self):
        b, t = self.pal.brand, self.pal.tokens
        self.assertGreaterEqual(C.ratio(t['on_success'], b['success']), 4.5)


class TestForegroundHelpers(unittest.TestCase):
    def setUp(self):
        self.pal = load_palette('ucp')

    def test_on_primary_fill_picks_white(self):
        self.assertEqual(self.pal.on(self.pal.brand['primary']), 'FFFFFF')

    def test_on_light_fill_picks_ink(self):
        self.assertEqual(self.pal.on(self.pal.brand['soft']), self.pal.brand['text'])

    def test_ink_accent_helper_returns_token(self):
        self.assertEqual(self.pal.ink_accent(), self.pal.tokens['ink_accent'])

    def test_ok_ink_helper_returns_success_token(self):
        self.assertEqual(self.pal.ok_ink(), self.pal.tokens['ink_success'])

    def test_subtitle_helper_returns_primary_token(self):
        self.assertEqual(self.pal.subtitle(), self.pal.tokens['subtitle_on_primary'])


if __name__ == "__main__":
    unittest.main()