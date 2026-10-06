# -*- coding: utf-8 -*-
"""Paleta UCP (unica) + tokens de TEXTO derivados por WCAG.

Regla unica del motor: el autor escribe contenido, el motor decide el color de
texto. Los hex de marca quedan intactos para GRAFICA (barras, reglas, flechas,
badges); solo el TEXTO migra a tokens derivados.
"""

from . import contrast as C
from .typography import FONTS as TYPOGRAPHY

BRAND = {
    'primary': '3854CC',
    'accent': 'D92A2B',
    'bg': 'F8F9FF',
    'text': '2B2C4A',
    'text_muted': '606383',
    'alert': 'B91C1C',
    'success': '1E8A5A',
    'border': 'D9DDF2',
    'card': 'FFFFFF',
    'soft': 'EEF0FF',
    'highlight': 'E0E4FF',
}

PALETTES = {'ucp': BRAND}


PALETTE_OVERRIDES = {}


class Palette:
    """Color de una tema: hex de marca + tokens de texto + helpers de tinta."""

    def __init__(self, key, brand, typography, overrides=None):
        self.key = key
        self.brand = dict(brand)
        self.typography = dict(typography)
        self.tokens = _derive(self.key, self.brand, overrides or {})

    def __getitem__(self, slot):
        """Acceso por slot de marca: pal['primary'], pal['soft']..."""
        return self.brand[slot]

    def on(self, fill):
        """Foreground legible para texto SOBRE un fill de color."""
        return C.pick(['FFFFFF', self.brand['text']], fill, C.WCAG_AA_TEXT) \
            or self.brand['text']

    def ink_accent(self):
        return self.tokens['ink_accent']

    def ok_ink(self):
        return self.tokens['ink_success']

    def subtitle(self):
        return self.tokens['subtitle_on_primary']


def _derive(key, brand, overrides):
    acc, pri = brand['accent'], brand['primary']

    def tok(name, candidates, surface, target, fallback):
        chosen = overrides.get(name) or C.pick(candidates, surface, target)
        if not chosen:
            chosen = C.shade_until(fallback, surface, target)
        return chosen

    return {
        'on_primary': tok('on_primary', [acc, 'FFFFFF', brand['highlight']],
                          pri, C.WCAG_AA_TEXT, 'FFFFFF'),
        'on_primary_soft': tok('on_primary_soft', [acc, brand['highlight'], 'FFFFFF'],
                               pri, C.WCAG_AA_TEXT, 'FFFFFF'),
        'on_accent': tok('on_accent', ['FFFFFF', brand['text']],
                         acc, C.WCAG_AA_TEXT, brand['text']),
        'ink_accent': tok('ink_accent', [acc], brand['soft'],
                          C.WCAG_AA_TEXT, acc),
        'ink_success': tok('ink_success', [brand['success']], brand['soft'],
                           C.WCAG_AA_TEXT, brand['success']),
        'on_success': tok('on_success', ['FFFFFF', brand['text']],
                          brand['success'], C.WCAG_AA_TEXT, brand['text']),
        'on_alert': tok('on_alert', ['FFFFFF', brand['text']],
                        brand['alert'], C.WCAG_AA_TEXT, brand['text']),
        'subtitle_on_primary': tok('subtitle_on_primary', [brand['highlight'], 'FFFFFF'],
                                   pri, C.WCAG_AA_TEXT, 'FFFFFF'),
    }


_CACHE = {}


def load_palette(key='ucp'):
    """Paleta por clave; falla ruidosamente si la clave no existe."""
    key = str(key or 'ucp').lower()
    if key not in PALETTES:
        raise ValueError(f'paleta desconocida {key!r}; disponible: {", ".join(PALETTES)}')
    if key not in _CACHE:
        _CACHE[key] = Palette(key, PALETTES[key], TYPOGRAPHY, PALETTE_OVERRIDES.get(key))
    return _CACHE[key]



def derive_tokens_for_display(key='ucp'):
    """Tokens de una clave de paleta para la tabla `schema tokens`."""
    key = str(key or 'ucp').lower()
    return _derive(key, PALETTES[key], PALETTE_OVERRIDES.get(key, {}))
