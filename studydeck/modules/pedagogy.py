# -*- coding: utf-8 -*-
"""Renderers tier pedagogy y concept_map: objetivos Bloom, dialogo tutor, texto anotado, mapa conceptual, glosario y lecturas."""

import math
import re

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from ..contrast import ratio, shade_until, WCAG_AA_TEXT
from ..geometry import (
    CANVAS_H, CANVAS_W, CONTENT_W, SAFE_X0, SAFE_Y0,
    row_layout, stack_layout,
)
from ..i18n import T, bloom
from ..primitives import (
    C, bg, footnote, note_surface, para, pill, place_image, rect,
    set_fill_alpha, textframe, tx, unmeasured,
)
from ..typography import FONT_BODY, FONT_TITLE

def m_learning_objectives(slide, d, pal, info):
    """Bloom-verb numbered learning objectives with optional Bloom-level pills."""
    ink = pal.ink_accent()
    pill(slide, SAFE_X0, 1.28, 2.9, 0.34, T('objectives'), pal["soft"], pal["primary"])
    objs = d.get("objectives", [])
    n = max(len(objs), 1)
    gap = 0.14
    rh, y_first = stack_layout(2.15, 4.32, n, gap, cap=1.25)
    for i, obj in enumerate(objs):
        y = y_first + i * (rh + gap)
        rect(slide, SAFE_X0, y, CONTENT_W, rh, fill=pal["card"], line=pal["border"], lw=0.6, rounded=True)
        rect(slide, SAFE_X0, y, 0.07, rh, fill=pal["accent"], rounded=False)
        rect(slide, 0.9, y + rh / 2 - 0.22, 0.44, 0.44, fill=pal["primary"], line=None, rounded=True, rad=0.5)
        tx(slide, 0.9, y + rh / 2 - 0.22, 0.44, 0.44, str(i + 1), size=12, color=pal.tokens['on_primary'],
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        tf = textframe(slide, SAFE_Y0, y + 0.1, 8.85, rh - 0.2, anchor=MSO_ANCHOR.MIDDLE)
        p = tf.paragraphs[0]
        p.line_spacing = 1.12
        r1 = p.add_run(); r1.text = str(obj.get("verb", "")).upper() + " — "
        r1.font.size = Pt(11.5); r1.font.bold = True
        r1.font.color.rgb = C(pal["primary"]); r1.font.name = FONT_BODY
        r2 = p.add_run(); r2.text = str(obj.get("text", ""))
        r2.font.size = Pt(11.5); r2.font.color.rgb = C(pal["text"]); r2.font.name = FONT_BODY
        if obj.get("bloom"):
            pill(slide, 10.6, y + rh / 2 - 0.17, 1.85, 0.34,
                 bloom(str(obj["bloom"])).upper(), pal["soft"], ink, size=9)
    footnote(slide, pal, d)

def m_colloquy(slide, d, pal, info):
    """Tutorial dialogue: alternating tutor (primary, left) / student (card, right) turns."""
    turns = d.get("turns", [])
    n = max(len(turns), 1)
    gap = 0.12
    th, y_first = stack_layout(SAFE_Y0, 5.05, n, gap, cap=1.15)
    for i, t in enumerate(turns):
        y = y_first + i * (th + gap)
        is_tutor = str(t.get("speaker", "tutor")).lower() == "tutor"
        letter = T('tutor')[0] if is_tutor else T('student')[0]
        av_x = SAFE_X0 if is_tutor else 12.26
        av_fill = pal["primary"] if is_tutor else pal["accent"]
        av = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(av_x), Inches(y + th / 2 - 0.21),
                                    Inches(0.42), Inches(0.42))
        av.fill.solid(); av.fill.fore_color.rgb = C(av_fill)
        note_surface(av_fill, av_x, y + th / 2 - 0.21, 0.42, 0.42)
        av.line.fill.background(); av.shadow.inherit = False
        atf = av.text_frame
        atf.word_wrap = False
        atf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para(atf, letter, 12, pal.on(av_fill), bold=True, first=True, align=PP_ALIGN.CENTER, sp_after=0)
        bx = 1.25 if is_tutor else 4.3
        bw = 7.8
        rect(slide, bx, y, bw, th, fill=av_fill,
             line=None if is_tutor else pal["border"], lw=0.6, rounded=True)
        # El fg se deriva del FILL real: el texto oscuro fijo sobre el acento
        # daba 2.76-2.85:1 bajo UCP.
        tx(slide, bx + 0.25, y, bw - 0.5, th, t.get("text", ""), size=10.8,
           color=pal.on(av_fill), anchor=MSO_ANCHOR.MIDDLE, line_sp=1.12)
    footnote(slide, pal, d)

def m_annotated_passage(slide, d, pal, info):
    """Primary source text (serif, left) with numbered marginalia (right).
    Author embeds markers like [1] inside the passage; annotations carry matching refs."""
    ink = pal.ink_accent()
    rect(slide, SAFE_X0, SAFE_Y0, 7.3, 4.95, fill=pal["soft"], line=pal["border"], lw=0.5, rounded=True)
    tx(slide, 0.95, 1.75, 6.7, 4.15, d.get("passage", ""), size=13, color=pal["text"],
       italic=True, font=FONT_TITLE, line_sp=1.25)
    if d.get("source"):
        rect(slide, 0.95, 6.0, 1.2, 0.025, fill=pal["accent"], rounded=False)
        # El `text_muted` crudo sobre panel soft daba 4.23:1: se deriva tinta
        # legible del par (muted vs soft).
        src_col = pal["text_muted"] if ratio(pal["text_muted"], pal["soft"]) >= 4.5 \
            else shade_until(pal["text_muted"], pal["soft"], WCAG_AA_TEXT)
        tx(slide, 0.95, 6.08, 6.7, 0.3, "— " + d["source"], size=10,
           color=src_col, italic=True)
    tx(slide, 8.25, 1.28, 4.4, 0.3, T('marginalia'), size=9.5, color=ink, bold=True)
    anns = d.get("annotations", [])
    n = max(len(anns), 1)
    gap = 0.12
    ah, y_first = stack_layout(2.0, 4.55, n, gap, cap=1.05)
    for i, a in enumerate(anns):
        y = y_first + i * (ah + gap)
        rect(slide, 8.25, y, 4.4, ah, fill=pal["card"], line=pal["border"], lw=0.6, rounded=True)
        rect(slide, 8.25, y, 0.5, 0.5, fill=pal["accent"], line=None, rounded=True, rad=0.15)
        tx(slide, 8.25, y, 0.5, 0.5, str(a.get("ref", i + 1)), size=11, color=pal.on(pal["accent"]),
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        tx(slide, 8.9, y + 0.06, 3.65, ah - 0.12, a.get("note", ""), size=10, color=pal["text"],
           anchor=MSO_ANCHOR.MIDDLE, line_sp=1.1)
    footnote(slide, pal, d)

def m_concept_map(slide, d, pal, info):
    """Radial hub-and-spoke: central concept with 4-6 satellite nodes."""
    nodes = d.get("nodes", [])
    sub_color = pal.subtitle()
    n = max(len(nodes), 1)
    cx, cy = 6.666, 4.05
    rx, ry = 3.9, 2.0
    card_w, card_h = 2.5, 1.05
    centers = []
    for i in range(n):
        ang = math.radians(-90 + i * (360.0 / n))
        centers.append((cx + rx * math.cos(ang), cy + ry * math.sin(ang)))
    try:
        from pptx.enum.shapes import MSO_CONNECTOR
    except ImportError:
        MSO_CONNECTOR = None
    if MSO_CONNECTOR:
        for (nx, ny) in centers:
            vx, vy = nx - cx, ny - cy
            dist = math.hypot(vx, vy) or 1.0
            sx, sy = cx + vx / dist * 1.35, cy + vy / dist * 1.35
            conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                              Inches(sx), Inches(sy), Inches(nx), Inches(ny))
            conn.line.color.rgb = C(pal["border"])
            conn.line.width = Pt(1.5)
    rect(slide, cx - 1.25, cy - 0.5, 2.5, 1.0, fill=pal["primary"], line=None, rounded=True, rad=0.12)
    tx(slide, cx - 1.15, cy - 0.5, 2.3, 1.0, d.get("hub", ""), size=13, color=pal.tokens['on_primary'], bold=True,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
    for i, (nx, ny) in enumerate(centers):
        nd = nodes[i] if i < len(nodes) else {}
        hi = nd.get("highlight", False)
        px = min(max(nx - card_w / 2, SAFE_X0), CANVAS_W - SAFE_X0 - card_w)
        py = ny - card_h / 2
        rect(slide, px, py, card_w, card_h, fill=pal["primary"] if hi else pal["card"],
             line=pal["accent"] if hi else pal["border"], lw=1.0 if hi else 0.6, rounded=True)
        tf = textframe(slide, px + 0.15, py + 0.08, card_w - 0.3, card_h - 0.16, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, nd.get("title", ""), 11.5, pal.tokens['on_primary'] if hi else pal["primary"], bold=True,
             font=FONT_TITLE, first=True, sp_after=2, align=PP_ALIGN.CENTER)
        if nd.get("desc"):
            para(tf, nd["desc"], 9.5, sub_color if hi else pal["text"], line_sp=1.05, align=PP_ALIGN.CENTER)
    footnote(slide, pal, d)

def m_glossary(slide, d, pal, info):
    """Two-column terminology: bold serif terms with concise definitions."""
    terms = d.get("terms", [])
    n = len(terms)
    # Tag en banda superior (y=1.20) para no colisionar con los términos cuando per=5.
    pill(slide, 10.55, 1.28, 2.1, 0.34, T('glossary'), pal["soft"], pal["primary"])
    per = max((n + 1) // 2, 1)
    gap = 0.12
    # Arranque en 2.05 garantiza holgura bajo header+tag; centrado vertical vía stack_layout.
    # cap 1.35: con 5 terminos por columna la caja def quedaria en ~0.8in
    eh, y_first = stack_layout(2.05, 4.5, per, gap, cap=1.35)
    for ci, col in enumerate([terms[:per], terms[per:]]):
        cx = SAFE_X0 + ci * 6.12
        for j, e in enumerate(col):
            y = y_first + j * (eh + gap)
            tx(slide, cx, y, 5.88, 0.3, e.get("term", "").upper(), size=12, color=pal["primary"],
               bold=True, font=FONT_TITLE)
            tx(slide, cx, y + 0.34, 5.88, eh - 0.38, e.get("def", ""), size=10.5, color=pal["text"], line_sp=1.1)
            if j < len(col) - 1:
                rect(slide, cx, y + eh - 0.02, 5.88, 0.012, fill=pal["border"], rounded=False)
    footnote(slide, pal, d)

def _tag_color(tag, pal):
    """Difficulty tag -> pill color heuristic (advanced=alert, intro/essential=success, else accent)."""
    t = str(tag).lower()
    if any(k in t for k in ('adv', 'avan', 'fortg', 'esperto', 'avanz')):
        return pal["alert"]
    if any(k in t for k in ('intro', 'bás', 'bas', 'fund', 'esencial', 'essential', 'core', 'indispens')):
        return pal["success"]
    return pal["accent"]

def _tag_text(pc, pal):
    """Foreground del texto dentro de una pill según su fill."""
    if pc == pal["success"]:
        return pal.tokens['on_success']
    if pc == pal["alert"]:
        return pal.tokens['on_alert']
    return pal.tokens['on_accent']

def m_further_reading(slide, d, pal, info):
    """Graded reading list: color-coded difficulty pills + citation + annotation."""
    entries = d.get("entries", [])
    n = max(len(entries), 1)
    gap = 0.14
    rh, y_first = stack_layout(1.6, 4.95, n, gap, cap=1.2)
    for i, e in enumerate(entries):
        y = y_first + i * (rh + gap)
        rect(slide, SAFE_X0, y, CONTENT_W, rh, fill=pal["card"], line=pal["border"], lw=0.6, rounded=True)
        pc = _tag_color(e.get("tag", ""), pal)
        pill(slide, 0.85, y + rh / 2 - 0.17, 2.0, 0.34, e.get("tag", "").upper(), pc, _tag_text(pc, pal))
        tx(slide, 3.1, y + 0.1, 9.3, 0.35, e.get("title", ""), size=12, color=pal["primary"],
           bold=True, font=FONT_TITLE)
        if e.get("note"):
            tx(slide, 3.1, y + 0.52, 9.3, rh - 0.6, e.get("note", ""), size=10.5, color=pal["text"], line_sp=1.08)
    footnote(slide, pal, d)
