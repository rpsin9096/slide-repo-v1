# -*- coding: utf-8 -*-
"""RENDER: monta o .pptx e devolve os pares que violaram WCAG.

O chamador decide se o arquivo sobrevive: com violacao de contraste o deck NAO
e entregue (o arquivo e apagado). Nao ha entrega parcial silenciosa.
"""

import os

from pptx import Presentation
from pptx.util import Inches

from . import primitives
from .contrast import ContrastGate
from .geometry import CANVAS_H, CANVAS_W
from .i18n import set_ui
from .registry import MODULES
from .contracts import _NO_HEADER_MODULES
from .primitives import footer, header, set_fallback_palette, set_gate
from .version import VERSION


def render(deck, out):
    """(n_slides, falhas_de_contraste) para um Deck carregado."""
    pal = deck.palette
    set_ui(deck.lang)
    gate = set_gate(ContrastGate())
    set_fallback_palette(pal)

    prs = Presentation()
    prs.slide_width = Inches(CANVAS_W)
    prs.slide_height = Inches(CANVAS_H)
    blank = prs.slide_layouts[6]

    for idx, data in enumerate(deck.slides, 1):
        module = str(data.get('module', ''))
        if module not in MODULES:
            raise KeyError(f'slide {idx}: modulo desconhecido {module!r}')
        gate.begin_slide(idx, module)
        slide = prs.slides.add_slide(blank)
        if module not in _NO_HEADER_MODULES:
            header(slide, pal, data)
            footer(slide, pal, idx, deck.course, deck.config)
        MODULES[module]['render'](slide, data, pal, deck.course_info)

    fails = gate.failures()
    if fails:
        try:
            os.remove(out)
        except OSError:
            pass
        return idx, fails
    prs.save(out)
    return idx, fails


def contrast_scan(deck):
    """Violacoes de contraste de um deck, sem escribir arquivo."""
    import tempfile
    from .lint import check
    errs = check(deck.slides, deck.lang, deck.images, deck.allow_terms)
    tmp = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False)
    tmp.close()
    try:
        _, fails = render(deck, tmp.name)
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass
    return errs, fails


def self_test(verbose=False):
    """Percorre os 35 modulos num fixture UCP e devolve [(module, status)]."""
    from .fixtures import fixture_slides
    out = []
    for slide in fixture_slides():
        name = str(slide.get('module'))
        from .manifest import Deck
        deck = Deck('<fixture>', [slide], {'course': 'StudyDeck'}, {'LANG': 'pt-BR'})
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False)
        tmp.close()
        try:
            _, fails = render(deck, tmp.name)
            ok = not fails
            detail = fails[0] if fails else None
        except Exception as exc:                       # noqa: BLE001 - self-test reporta
            ok, detail = False, f'{type(exc).__name__}: {exc}'
        finally:
            try:
                os.remove(tmp.name)
            except OSError:
                pass
        out.append((name, ok, detail))
    return out


def scan_contrast(deck):
    """Violacoes de contraste sem gravar nada (contraproduz o .pptx temporario)."""
    return contrast_scan(deck)[1]


__all__ = ['render', 'self_test', 'contrast_scan', 'scan_contrast', 'primitives', 'VERSION']