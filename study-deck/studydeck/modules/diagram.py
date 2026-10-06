# -*- coding: utf-8 -*-
"""Renderers tier diagrama: linea de tiempo, ciclo, matriz 2x2 y piramide."""

import math
import re

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from ..contrast import ratio, shade_until, WCAG_AA_TEXT
from ..contracts import COLLOQUY_SPEAKERS, TIMELINE_MAX
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

def m_timeline(slide, d, pal, info):
    """Chronological axis with alternating milestone cards."""
    miles = d.get("milestones", [])[:TIMELINE_MAX]  # defensa silenciosa; el lint bloquea >cap
    ink = pal.ink_accent()
    n = max(len(miles), 1)
    y_mid, x0, x1 = 4.0, 1.0, 12.35
    rect(slide, x0, y_mid, x1 - x0, 0.035, fill=pal["accent"], rounded=False)
    span = (x1 - x0) / n
    for i, ms in enumerate(miles):
        cx = x0 + span * (i + 0.5)
        up = (i % 2 == 0)
        cw = min(span - 0.3, 2.6)
        ch = 1.7 if n <= 4 else 2.05
        fsz = 10.2 if n <= 4 else 9.3
        cy = (y_mid - 0.25 - ch) if up else y_mid + 0.25
        rect(slide, cx - 0.09, y_mid - 0.075, 0.18, 0.18, fill=pal["primary"], rounded=True, rad=0.5)
        if i == 0:  # jerarquía sin depender del color: anillo en el hito inicial
            ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - 0.13), Inches(y_mid - 0.135),
                                          Inches(0.26), Inches(0.26))
            ring.fill.background()
            ring.line.color.rgb = C(pal["accent"]); ring.line.width = Pt(1.5)
            ring.shadow.inherit = False
        if up:
            rect(slide, cx - 0.01, cy + ch, 0.02, (y_mid - 0.09) - (cy + ch), fill=pal["border"], rounded=False)
        else:
            rect(slide, cx - 0.01, y_mid + 0.11, 0.02, cy - (y_mid + 0.11), fill=pal["border"], rounded=False)
        rect(slide, cx - cw / 2, cy, cw, ch, fill=pal["card"], line=pal["border"], lw=0.6, rounded=True)
        rect(slide, cx - cw / 2, cy, cw, 0.05, fill=pal["accent"] if up else pal["primary"], rounded=False)
        tf = textframe(slide, cx - cw / 2 + 0.15, cy + 0.15, cw - 0.3, ch - 0.3)
        para(tf, ms.get("label", ""), 9.5, ink, bold=True, first=True, sp_after=2)
        para(tf, ms.get("title", ""), 12.0, pal["primary"], bold=True, font=FONT_TITLE, sp_after=3)
        if ms.get("desc"):
            para(tf, ms["desc"], fsz, pal["text"], line_sp=1.05)
    footnote(slide, pal, d)

def m_cycle_diagram(slide, d, pal, info):
    """Closed-loop process (3–6 nodes) con flechas de cuerda rotadas y hub opcional;
    geometría calibrada contra el solape con el centro."""
    nodes = d.get("nodes", [])
    sub_color = pal.subtitle()
    n = max(len(nodes), 1)
    cx = 6.666
    cy = 4.0 if n <= 4 else 3.85
    R = 2.35 if n <= 4 else 2.20
    card_w, card_h = 2.4, 1.15
    centers = []
    for i in range(n):
        rad = math.radians(-90 + i * (360.0 / n))
        centers.append((cx + R * math.cos(rad), cy + R * math.sin(rad) * 0.82))
    for i in range(n):
        x1, y1 = centers[i]
        x2, y2 = centers[(i + 1) % n]
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        vx, vy = mx - cx, my - cy
        dist = math.hypot(vx, vy) or 1.0
        mx += 0.5 * vx / dist; my += 0.5 * vy / dist  # push arrow outward, clear of hub
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        ar = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(mx - 0.22), Inches(my - 0.11), Inches(0.44), Inches(0.22))
        ar.rotation = ang
        ar.fill.solid(); ar.fill.fore_color.rgb = C(pal["accent"])
        ar.line.fill.background(); ar.shadow.inherit = False
    for i, (cxx, cyy) in enumerate(centers):
        nd = nodes[i]
        hi = nd.get("highlight", False)
        rect(slide, cxx - card_w / 2, cyy - card_h / 2, card_w, card_h,
             fill=pal["primary"] if hi else pal["card"],
             line=pal["accent"] if hi else pal["border"], lw=1.0 if hi else 0.6, rounded=True)
        tf = textframe(slide, cxx - card_w / 2 + 0.12, cyy - card_h / 2 + 0.1, card_w - 0.24, card_h - 0.2, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, nd.get("title", ""), 11.5, pal.tokens['on_primary'] if hi else pal["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=2)
        if nd.get("desc"):
            para(tf, nd["desc"], 9.5, sub_color if hi else pal["text"], line_sp=1.05)
    if d.get("center_label"):
        # Hub compacto para evitar solape con las tarjetas laterales.
        rect(slide, cx - 0.85, cy - 0.35, 1.7, 0.70, fill=pal["soft"], line=pal["accent"], lw=0.9, rounded=True, rad=0.12)
        tx(slide, cx - 0.75, cy - 0.35, 1.5, 0.70, d["center_label"], size=10, color=pal["primary"],
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
    footnote(slide, pal, d)

def m_quadrant_matrix(slide, d, pal, info):
    """2x2 matrix (TL, TR, BL, BR) with optional axis labels."""
    quads = d.get("quadrants", [])
    # Cuadrantes en el inicio estandar de contenido; la etiqueta del eje X
    # gana ~0.16in de aire sobre el footnote en vez de rozarlo.
    x0, y0, qw, qh, gap = 2.3, SAFE_Y0, 4.9, 2.35, 0.12
    if d.get("y_label"):
        lb = slide.shapes.add_textbox(Inches(0.66), Inches(y0), Inches(0.42), Inches(2 * qh + gap))
        tf = lb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = d["y_label"].upper()
        r.font.size = Pt(10); r.font.bold = True
        r.font.color.rgb = C(pal["text_muted"]); r.font.name = FONT_BODY
        lb.rotation = 270
    if d.get("x_label"):
        tx(slide, x0, y0 + 2 * qh + gap + 0.03, 2 * qw + gap, 0.22, d["x_label"].upper(),
           size=10, color=pal["text_muted"], align=PP_ALIGN.CENTER, bold=True)
    coords = [(x0, y0), (x0 + qw + gap, y0), (x0, y0 + qh + gap), (x0 + qw + gap, y0 + qh + gap)]
    accents = [pal["primary"], pal["accent"], pal["accent"], pal["primary"]]
    for (qx0, qy0), q, ac in zip(coords, quads, accents):
        rect(slide, qx0, qy0, qw, qh, fill=pal["card"], line=pal["border"], lw=0.6, rounded=True)
        rect(slide, qx0, qy0, qw, 0.05, fill=ac, rounded=False)
        tf = textframe(slide, qx0 + 0.2, qy0 + 0.15, qw - 0.4, qh - 0.3)
        para(tf, q.get("title", ""), 13.0, pal["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=4)
        for pt in q.get("points", []):
            para(tf, "• " + pt, 10.8, pal["text"], sp_after=3, line_sp=1.08)
    footnote(slide, pal, d)

def m_pyramid(slide, d, pal, info):
    """Step-pyramid hierarchy; levels[0] = base. Side annotations to the right."""
    levels = d.get("levels", [])
    n = max(len(levels), 1)
    base_w, cx = 8.2, 6.666
    lh = min(0.95, 4.6 / n)
    stack_h = n * lh + 0.08 * (n - 1)
    top0 = SAFE_Y0 + (4.95 - stack_h) / 2.0
    for i, lv in enumerate(levels):
        w = base_w * (i + 1) / n
        ly = top0 + stack_h - (i + 1) * lh - 0.08 * i
        hi = lv.get("highlight", False)
        lv_fill = pal["primary"] if hi else pal["card"]
        rect(slide, cx - w / 2, ly, w, lh, fill=lv_fill,
             line=pal["accent"] if hi else pal["border"], lw=0.8 if hi else 0.6, rounded=True)
        tx(slide, cx - w / 2 + 0.25, ly, w - 0.5, lh, lv.get("title", ""), size=12,
           color=pal.tokens['on_primary'] if hi else pal["primary"], bold=True, anchor=MSO_ANCHOR.MIDDLE,
           align=PP_ALIGN.CENTER, font=FONT_TITLE)
        if lv.get("desc"):
            tx(slide, cx + base_w / 2 + 0.25, ly, 1.6, lh, lv["desc"], size=9.5,
               color=pal["text_muted"], anchor=MSO_ANCHOR.MIDDLE, line_sp=1.05)
    footnote(slide, pal, d)


def _disable_smoothing(ser):
    """Apaga el suavizado SI la serie lo expone; False si python-pptx no lo tiene.

    El grafico sigue valido sin curva suavizada: el retorno dice si se aplico.
    """
    try:
        ser.smooth = False
        return True
    except (AttributeError, NotImplementedError):
        return False


def m_chart_data(slide, d, pal, info):
    """Native editable chart (bar/line) with scholarly interpretation panel."""
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
    ink = pal.ink_accent()
    cats = d.get("categories", [])
    series = d.get("series", [])
    is_bar = d.get("chart_type", "bar") != "line"
    data = CategoryChartData()
    data.categories = cats
    for s in series:
        data.add_series(s.get("name", ""), tuple(s.get("values", [])))
    with unmeasured():
        ctype = XL_CHART_TYPE.COLUMN_CLUSTERED if is_bar else XL_CHART_TYPE.LINE_MARKERS
        gf = slide.shapes.add_chart(ctype, Inches(SAFE_X0), Inches(1.6), Inches(8.1), Inches(4.85), data)
        chart = gf.chart
        chart.has_title = False
        chart.has_legend = len(series) > 1
        if chart.has_legend:
            chart.legend.position = XL_LEGEND_POSITION.BOTTOM
            chart.legend.include_in_layout = False
            chart.legend.font.size = Pt(10)
            chart.legend.font.name = FONT_BODY
            chart.legend.font.color.rgb = C(pal["text"])
        pal2 = [pal["primary"], pal["accent"]]
        for idx, ser in enumerate(chart.plots[0].series):
            col = C(pal2[idx % 2])
            if is_bar:
                ser.format.fill.solid()
                ser.format.fill.fore_color.rgb = col
                ser.format.line.fill.background()
            else:
                ser.format.line.color.rgb = col
                ser.format.line.width = Pt(2.5)
                _disable_smoothing(ser)
        chart.category_axis.tick_labels.font.size = Pt(10)
        chart.category_axis.tick_labels.font.name = FONT_BODY
        chart.category_axis.tick_labels.font.color.rgb = C(pal["text"])
        chart.value_axis.tick_labels.font.size = Pt(10)
        chart.value_axis.tick_labels.font.name = FONT_BODY
        chart.value_axis.tick_labels.font.color.rgb = C(pal["text"])
    rect(slide, 9.0, 1.6, 3.65, 4.85, fill=pal["card"], line=pal["border"], lw=0.6, rounded=True)
    rect(slide, 9.0, 1.6, 3.65, 0.05, fill=pal["accent"], rounded=False)
    tx(slide, 9.25, 1.78, 3.15, 0.3, T('reading'), size=10, color=ink, bold=True)
    tfi = textframe(slide, 9.25, 2.2, 3.15, 4.0)
    for i, ins in enumerate(d.get("insights", [])):
        para(tfi, "• " + ins, 10.8, pal["text"], first=(i == 0), sp_after=8, line_sp=1.12)
    footnote(slide, pal, d)
