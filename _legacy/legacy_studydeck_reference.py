#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
=============================================================================
STUDYDECK v1.0 — MOTOR DE DECKS DE ESTUDIO (sucesor lean de OMC Kit v9.6.1)
=============================================================================
Filosofía "don't build without need": misma calidad visual (35 módulos
calibrados · tokens WCAG · gate de contraste) SIN la maquinaria de publicación
académica (ledger ATU, floors de variedad, huella estadística de idioma,
preflight-cache, audit.md, imggen/imgprep, perfiles coercitivos).

Comandos: check · schema · new · ingest · lint · build · all · contrast

Las 3 invariantes (las únicas):
  1. Contraste WCAG en TODO texto (token o derivado del fill real) —
     violación al fin del render BLOQUEA el build.
  2. Deriva pt-BR→es-ES BLOQUEA lint cuando CONFIG["LANG"] es español
     (excepciones de falsos positivos probadas en self-test).
     Otros idiomas: sin guard (no hay evidencia de necesidad).
  3. Contrato por slide: requeridos no vacíos, presupuestos de caracteres,
     fit tipográfico, imagen válida si existe. Nada se fabrica para cumplir
     reglas (ya no hay reglas que lo pidan).

Convenciones heredadas del kit: comentarios y mensajes en español ·
fail-fast lint→build · manifest = COURSE_INFO/CONFIG/SLIDES · geometría
13.333×7.5 con asimetría 0.65/0.683 CANÓNICA (decisión v9.C — no corregir).
Elección de módulos: por el campo `when` de cada módulo (`schema all`),
no por recetas de scaffold cerradas.
"""

import sys
import os
import re as _re
import math as _math
import tempfile as _tf
import json as _json
import types as _types
import unicodedata

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
except ImportError:
    print('[StudyDeck] Falta python-pptx. Instale en el venv del proyecto:')
    print('  uv pip install python-pptx Pillow    # ó: pip install python-pptx Pillow')
    sys.exit(1)

VERSION = 'STUDYDECK v1.0'

# Tipografía por tema (la fija _apply_fonts antes de lint/render).
FONT_TITLE = "Georgia"
FONT_BODY = "Calibri"

# Ancho medio de glifo como fracción del pt (por fuente) — estimador de ajuste.
_CHAR_W_BY_FONT = {"Montserrat": 0.57, "Georgia": 0.50, "Calibri": 0.47}
_CHAR_W_DEFAULT = 0.50


# Collegiate Palettes
PALETTES = {
    "oxford": {
        "primary": "002147", "accent": "B08D57", "bg": "FAF9F6", "text": "1C2430",
        "text_muted": "616A75", "alert": "8B0000", "success": "1B5E20",
        "border": "DCD8CE", "card": "FFFFFF", "soft": "F3EFE6", "highlight": "EAE4D5",
    },
    "harvard": {
        "primary": "A51C30", "accent": "B88B4A", "bg": "FBFBF9", "text": "21272A",
        "text_muted": "6A737D", "alert": "9E0000", "success": "2E6930",
        "border": "E2DDD4", "card": "FFFFFF", "soft": "F5F0E8", "highlight": "ECE4D8",
    },
    "yale": {
        "primary": "0F4D92", "accent": "C5A059", "bg": "FAFAFA", "text": "1E293B",
        "text_muted": "64748B", "alert": "991B1B", "success": "166534",
        "border": "DCE2EA", "card": "FFFFFF", "soft": "EEF2F6", "highlight": "E2E8F0",
    },
    "cambridge": {
        "primary": "1B365D", "accent": "007788", "bg": "F8FAF9", "text": "1C2833",
        "text_muted": "5D6D7E", "alert": "922B21", "success": "196F3D",
        "border": "D4E1DF", "card": "FFFFFF", "soft": "EDF4F2", "highlight": "DCECE8",
    },
    "ucp": {
        "primary": "3854CC", "accent": "D92A2B", "bg": "F8F9FF", "text": "2B2C4A",
        "text_muted": "606383", "alert": "B91C1C", "success": "1E8A5A",
        "border": "D9DDF2", "card": "FFFFFF", "soft": "EEF0FF", "highlight": "E0E4FF",
    }
}


# ===================== P0 — NÚCLEO DE CONTRASTE (WCAG) =====================
# v9.1/A2 — umbrales WCAG como constantes (antes hardcodeados ~10×)
WCAG_AA_TEXT = 4.5     # texto normal
WCAG_AA_DISPLAY = 3.0  # texto grande/display (>=18pt o bold >=14pt)

def _rel_lum(hexc):
    hexc = str(hexc).lstrip('#')
    def ch(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(int(hexc[i:i+2], 16)) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def _ratio(fg, bgc):
    l1, l2 = sorted((_rel_lum(fg), _rel_lum(bgc)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

def _pick(candidates, surface, target):
    """Primer candidato que cumple el ratio sobre `surface`; None si ninguno."""
    for cand in candidates:
        if cand and _ratio(cand, surface) >= target:
            return cand
    return None

def _shade_until(hexcolor, surface, target, max_steps=12):
    """Oscurece el tono conservando matiz hasta alcanzar el ratio objetivo."""
    c = str(hexcolor).lstrip('#')
    for step in range(1, max_steps + 1):
        f = 1.0 - step * 0.07
        c = ''.join(f'{max(0, round(int(c[i:i+2], 16) * f)):02X}' for i in (0, 2, 4))
        if _ratio(c, surface) >= target:
            return c
    return c

# Overrides manuales por tema (control fino sin tocar el motor).
PALETTE_OVERRIDES = {
    # 'oxford': {'ink_accent': '7A5F33'},
}

def derive_tokens(key, P):
    """Tokens de TEXTO derivados por tema. Hex de marca intactos para gráfica."""
    ov = dict(PALETTE_OVERRIDES.get(key, {}))
    acc, pri = P["accent"], P["primary"]
    t = {}
    # Texto sobre fill primario: prefiere el acento de marca SI es legible
    # (preserva oro-sobre-navy de Oxford); si no, blanco/highlight/tinta.
    t['on_primary'] = ov.get('on_primary') or (
        _pick([acc], pri, WCAG_AA_TEXT) or _pick(["FFFFFF", P["highlight"], P["text"]], pri, WCAG_AA_TEXT) or "FFFFFF")
    t['on_primary_soft'] = ov.get('on_primary_soft') or (
        _pick([acc, P["highlight"], "FFFFFF"], pri, WCAG_AA_TEXT) or "FFFFFF")
    # Texto sobre fill de acento: oro -> tinta; rojo/teal -> blanco.
    t['on_accent'] = ov.get('on_accent') or (
        _pick(["FFFFFF", P["text"]], acc, WCAG_AA_TEXT) or P["text"])
    # Acento COMO texto sobre superficies claras: deriva a bronce/tinta si hace falta.
    t['ink_accent'] = ov.get('ink_accent') or (
        _pick([acc], P["soft"], WCAG_AA_TEXT) or _shade_until(acc, P["soft"], WCAG_AA_TEXT))
    t['ink_success'] = ov.get('ink_success') or (
        _pick([P["success"]], P["soft"], WCAG_AA_TEXT) or _shade_until(P["success"], P["soft"], WCAG_AA_TEXT))
    # v9.A — sobre fills de color MEDIO (verde/rojo de marca) el blanco puede quedarse
    # en 3-4.4:1 (ucp success #1E8A5A da 4.34 con blanco): se oscurece la TINTA hasta
    # cumplir 4.5 en vez de aceptar un par bajo. El fill de marca queda intacto.
    t['on_success'] = ov.get('on_success') or (
        _pick(["FFFFFF", P["text"]], P["success"], WCAG_AA_TEXT)
        or _shade_until(P["text"], P["success"], WCAG_AA_TEXT))
    t['on_alert'] = ov.get('on_alert') or (
        _pick(["FFFFFF", P["text"]], P["alert"], WCAG_AA_TEXT) or P["text"])
    t['subtitle_on_primary'] = ov.get('subtitle_on_primary') or (
        _pick([P["highlight"], "FFFFFF"], pri, WCAG_AA_TEXT) or "FFFFFF")
    return t

# Tokens activos (se fijan en _render / cmd_contrast; vacío fuera de render).
TOK = {}

def _set_tokens(pal_key):
    global TOK
    TOK = derive_tokens(pal_key, PALETTES.get(pal_key, PALETTES['oxford']))

def _on(P, fill):
    """Foreground legible para texto SOBRE un fill de color dado."""
    return _pick(["FFFFFF", P["text"]], fill, WCAG_AA_TEXT) or P["text"]

def _ink(P):
    """Tinta de acento legible sobre superficies claras (v9.B/F3)."""
    return TOK.get('ink_accent', P["accent"])

def _sub_primary():
    return TOK.get('subtitle_on_primary', "D8E2EC")

def _ok_ink(P):
    return TOK.get('ink_success', P["success"])

def pill(slide, x, y, w, h, text, fill, fg, size=8.5, font=None, rad=0.12):
    """Píldora/badge: rect redondeado + texto centrado en negrita sobre la MISMA caja
    (v9.B/F1 — 11 sitios idénticos en renderers)."""
    if font is None:
        font = FONT_BODY
    rect(slide, x, y, w, h, fill=fill, line=None, rounded=True, rad=rad)
    tx(slide, x, y, w, h, text, size=size, color=fg,
       bold=True, align=PP_ALIGN.CENTER, font=font)

# Helpers legados (misma firma que v7.9.5; ahora token-backed).
def _fg_on_primary(P, fallback=None):
    return TOK.get('on_primary') or (fallback or P["accent"])

def _fg_on_primary_soft(P):
    return TOK.get('on_primary_soft') or P["accent"]


# ===================== INSTRUMENTACIÓN DE CONTRASTE (siempre activa) =====================
# Colección barata durante el render; la evaluación ocurre UNA vez al final.
# Sin env vars ni contextmanagers: el gate no es opcional (invariante 1).
_CONTRAST_LOG = []            # dict(fg,bg,size,bold,slide,module) — solo texto medible
_SURFACE_STACK = []           # (x, y, w, h, fill) por diapositiva, orden de pintado
_CTX = {"slide": 0, "module": "?"}

def _note_surface(fill, x, y, w, h):
    if fill:
        _SURFACE_STACK.append((float(x), float(y), float(w), float(h), str(fill)))

def _surface_at(px, py):
    """Relleno visible bajo el punto: último rect pintado que lo contiene."""
    if px is None:
        return None
    for x, y, w, h, fill in reversed(_SURFACE_STACK):
        if x <= px <= x + w and y <= py <= y + h:
            return fill
    return None

def _required_ratio(size, bold):
    return WCAG_AA_DISPLAY if (size >= 18 or (bold and size >= 14)) else WCAG_AA_TEXT

_NATIVE_TEXT = False         # True dentro de _unmeasured(): tablas/gráficos nativos

def _log_text(fg, size, bold, deco, px=None, py=None):
    """Registra texto medible contra la superficie efectiva bajo su centro.
    Fuera del gate: decorativos (deco=True) y el texto NATIVO de tablas/gráficos
    python-pptx (dentro de _unmeasured), cuyo render real hace PowerPoint."""
    if not (str(fg) and not deco and not _NATIVE_TEXT):
        return
    surf = _surface_at(px, py)
    if surf:
        _CONTRAST_LOG.append({'fg': str(fg), 'bg': surf, 'size': float(size),
                              'bold': bool(bold),
                              'slide': _CTX["slide"], 'module': _CTX["module"]})

def _contrast_failures():
    out = []
    for e in _CONTRAST_LOG:
        req = _required_ratio(e['size'], e['bold'])
        r = _ratio(e['fg'], e['bg'])
        if r < req:
            out.append({'slide': e['slide'], 'module': e['module'], 'fg': e['fg'],
                        'bg': e['bg'], 'ratio': round(r, 2), 'required': req})
    return out


from contextlib import contextmanager as _ctxmgr

@_ctxmgr
def _unmeasured():
    """Suspende la medición de contraste para el texto NATIVO de tablas/charts
    python-pptx (PowerPoint los pinta). Todo lo demás pasa por el gate siempre-on."""
    global _NATIVE_TEXT
    prev = _NATIVE_TEXT
    _NATIVE_TEXT = True
    try:
        yield
    finally:
        _NATIVE_TEXT = prev


CANVAS_W, CANVAS_H = 13.333, 7.500
SAFE_X0, SAFE_Y0 = 0.650, 1.550
SAFE_X1 = CANVAS_W - SAFE_X0          # 12.683 (documental)
CONTENT_W = 12.0                      # de-facto: x=SAFE_X0 + w=12.0 → borde 12.65

def C(h):
    return RGBColor.from_string(h)

def rect(slide, x, y, w, h, fill=None, line=None, lw=0.5, rounded=True, rad=0.04):
    """Refined box helper with gentle, professional corner rounding."""
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        try: shp.adjustments[0] = rad
        except Exception: pass
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = C(fill)
        _note_surface(fill, x, y, w, h)
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = C(line)
        shp.line.width = Pt(lw)
    shp.shadow.inherit = False
    return shp

def tx(slide, x, y, w, h, text, size=13, color="1C2430", bold=False, italic=False,
       align=None, font=None, anchor=None, sp_after=3, line_sp=1.08, deco=False):
    if font is None:
        font = FONT_BODY
    if align is None: align = PP_ALIGN.LEFT
    if anchor is None: anchor = MSO_ANCHOR.TOP
    _log_text(color, size, bold, deco, x + w / 2.0, y + h / 2.0)
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    lines = text.split("\n") if isinstance(text, str) else text
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(sp_after)
        p.line_spacing = line_sp
        r = p.add_run()
        r.text = ln
        f = r.font
        f.size = Pt(size)
        f.bold = bold
        f.italic = italic
        f.color.rgb = C(color)
        f.name = font
    return box

def para(tf, text, size, color, bold=False, italic=False, align=None,
         font=None, sp_before=0, sp_after=3, first=False, line_sp=1.08, deco=False):
    if font is None:
        font = FONT_BODY
    if align is None: align = PP_ALIGN.LEFT
    box = getattr(tf, '_omc_box', None)
    if box:
        _log_text(color, size, bold, deco, box[0] + box[2] / 2.0, box[1] + box[3] / 2.0)
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(sp_before)
    p.space_after = Pt(sp_after)
    p.line_spacing = line_sp
    r = p.add_run()
    r.text = text
    f = r.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = C(color)
    f.name = font
    return p

def textframe(slide, x, y, w, h, anchor=None):
    if anchor is None: anchor = MSO_ANCHOR.TOP
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    try: tf._omc_box = (float(x), float(y), float(w), float(h))
    except Exception: pass
    return tf

def bg(slide, P, color=None):
    rect(slide, 0, 0, CANVAS_W, 7.5, fill=color or P["bg"], line=None, rounded=False)

def header(slide, P, data, idx):
    """Scholarly editorial header with discrete category kicker and serif title."""
    kicker = data.get("kicker", "")
    title = data.get("title", "")
    if kicker:
        tx(slide, SAFE_X0, 0.32, 11.0, 0.28, kicker.upper(), size=9.5,
           color=_ink(P), bold=True, font=FONT_BODY)
    tx(slide, SAFE_X0, 0.58, CONTENT_W, SAFE_X0, title, size=23, color=P["primary"], bold=True, font=FONT_TITLE)
    rect(slide, SAFE_X0, 1.28, 1.3, 0.03, fill=P["accent"], rounded=False)
    rect(slide, 1.98, 1.29, 10.7, 0.01, fill=P["border"], rounded=False)

def footer(slide, P, idx, course, config=None):
    """Discreet editorial slide footer — SHOW_FOOTER / SHOW_SLIDE_NUMBER toggles (default True)."""
    config = config or {}
    legacy = config.get('SHOW_REFERENCES')  # alias v7.8: una bandera controlaba pie + número
    show_footer = config.get('SHOW_FOOTER', True if legacy is None else legacy)
    show_number = config.get('SHOW_SLIDE_NUMBER', True if legacy is None else legacy)
    if show_footer:
        course_str = course.upper() if course else T('footer')
        tx(slide, SAFE_X0, 7.10, 8.5, 0.28, course_str, size=8.5, color=P["text_muted"], font=FONT_BODY)
    if show_number:
        tx(slide, 11.8, 7.10, 0.9, 0.28, f"§ {idx:02d}", size=9.0, color=P["text_muted"],
           align=PP_ALIGN.RIGHT, font=FONT_TITLE, bold=True)

def footnote(slide, P, data, y=6.75):
    fn = data.get("footnote", "")
    credit = data.get("credit", "")
    combined = fn
    if credit and not fn:
        combined = T('source').format(c=credit)
    elif credit and fn and credit not in fn:
        combined = T('join').format(f=fn, c=credit)
    if combined:
        tx(slide, SAFE_X0, y, CONTENT_W, 0.28, combined, size=9.0, color=P["text_muted"], italic=True)

def stack_layout(y0, zone_h, n, gap, cap=None):
    """Capped row height + vertically centered top offset for card stacks."""
    n = max(n, 1)
    row_h = (zone_h - gap * (n - 1)) / n
    if cap:
        row_h = min(row_h, cap)
    return row_h, y0 + (zone_h - (row_h * n + gap * (n - 1))) / 2.0

def row_layout(x0, total_w, n, gap, center=False):
    """v9.B/F5 — hermano horizontal de stack_layout: ancho de ítem + x de inicio.
    center=True centra el grupo dentro de total_w (caso mnemonic)."""
    n = max(n, 1)
    item_w = min((total_w - gap * (n - 1)) / n, total_w) if not center else \
        min(1.35, (total_w - gap * (n - 1)) / n)
    start_x = x0
    if center:
        total = item_w * n + gap * (n - 1)
        start_x = x0 + (total_w - total) / 2.0
    return item_w, start_x


# Image metadata cache: each file opened with PIL exactly once per process.
_IMG_CACHE = {}

def _image_size(path):
    if path in _IMG_CACHE:
        return _IMG_CACHE[path]
    from PIL import Image as _PILImage
    with _PILImage.open(path) as _im:
        size = _im.size
    _IMG_CACHE[path] = size
    return size



def _place_image(slide, path, x, y, w, h, P=None):
    """Places an image with an academic framed border."""
    iw, ih = _image_size(path)
    ar = iw / float(ih)
    box_ar = w / float(h)
    if ar > box_ar:
        pw, ph = w, w / ar
    else:
        pw, ph = h * ar, h
    px = x + (w - pw) / 2.0
    py = y + (h - ph) / 2.0
    if P:
        rect(slide, px - 0.04, py - 0.04, pw + 0.08, ph + 0.08, fill=P["card"],
             line=P["border"], lw=0.75, rounded=True, rad=0.02)
    slide.shapes.add_picture(path, Inches(px), Inches(py), Inches(pw), Inches(ph))

def _set_fill_alpha(shape, opacity_pct):
    """Apply transparency to a solid-filled shape (opacity_pct: 0-100). Needed for venn overlap."""
    from pptx.oxml.ns import qn
    from lxml import etree
    spPr = shape._element.spPr
    sF = spPr.find(qn('a:solidFill'))
    if sF is None:
        return
    clr = sF.find(qn('a:srgbClr'))
    if clr is None:
        return
    for old in clr.findall(qn('a:alpha')):
        clr.remove(old)
    etree.SubElement(clr, qn('a:alpha'), val=str(int(opacity_pct * 1000)))


# ===================== MODULE RENDERERS — CORE & CLASSIC SET =====================

def m_title(slide, d, P, info):
    """Academic title slide with crest layout — supports optional author."""
    bg(slide, P, P["primary"])
    rect(slide, 0, 0, CANVAS_W, 0.18, fill=P["accent"], rounded=False)
    rect(slide, 0, 7.32, CANVAS_W, 0.18, fill=P["accent"], rounded=False)
    rect(slide, 0.8, 0.7, 11.733, 6.1, fill=None, line=P["accent"], lw=1.0, rounded=True, rad=0.03)
    course_name = d.get("course", info.get("course", T('course_default')))
    title_txt = d.get("title") or course_name or T('course_default')  # fallback: course as title
    course_color = _fg_on_primary(P)        # token on_primary
    inst_color = _fg_on_primary_soft(P)     # token on_primary_soft
    sub_color = _sub_primary()
    tx(slide, 1.2, 1.35, 10.933, 0.4, course_name.upper(), size=12, color=course_color,
       bold=True, align=PP_ALIGN.CENTER, font=FONT_BODY)
    tx(slide, 1.2, 2.1, 10.933, 2.1, title_txt, size=38, color="FFFFFF",
       bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE, line_sp=1.08)
    rect(slide, 5.86, 4.45, 1.6, 0.03, fill=P["accent"], rounded=False)
    tx(slide, 1.5, 4.75, 10.333, 0.7, d.get("subtitle", ""), size=15, color=sub_color,
       align=PP_ALIGN.CENTER, italic=True, font=FONT_BODY)
    inst = d.get("institution", info.get("institution", T('institution_default')))
    tx(slide, 1.5, 5.85, 10.333, 0.4, inst.upper(), size=10, color=inst_color,
       align=PP_ALIGN.CENTER, font=FONT_BODY, bold=True)
    author = d.get("author", info.get("author", ""))
    if author:
        tx(slide, 1.5, 6.25, 10.333, 0.35, author, size=11, color="FFFFFF",
           align=PP_ALIGN.CENTER, font=FONT_BODY, italic=True)

def m_section_divider(slide, d, P, info):
    """Section transition divider — supports optional author. BG = primario (UCP: azul estándar #3854CC)."""
    bg(slide, P, P["primary"])
    rect(slide, 0, 0, 0.4, 7.5, fill=P["accent"], rounded=False)
    style = d.get("divider_style", T('chapter'))
    sub_color = _sub_primary()
    if style:
        tx(slide, 1.2, 1.5, 11.0, 0.5, style.upper(), size=14, color=_fg_on_primary(P),
           bold=True, align=PP_ALIGN.LEFT, font=FONT_BODY)
    tx(slide, 1.2, 2.2, 11.0, 1.8, d.get("section_title", ""), size=36, color="FFFFFF",
       bold=True, align=PP_ALIGN.LEFT, font=FONT_TITLE, line_sp=1.1)
    rect(slide, 1.2, 4.25, 2.0, 0.03, fill=P["accent"], rounded=False)
    tx(slide, 1.2, 4.6, 10.5, 1.5, d.get("section_subtitle", ""), size=15, color=sub_color,
       align=PP_ALIGN.LEFT, italic=True, line_sp=1.2, font=FONT_BODY)
    author = d.get("author", info.get("author", ""))
    if author:
        tx(slide, 1.2, 6.3, 10.5, 0.35, author, size=11, color=_fg_on_primary_soft(P),
           align=PP_ALIGN.LEFT, font=FONT_BODY, italic=True)

def m_definition(slide, d, P, info):
    """Academic thesis/definition module with structured proposition cards."""
    img = bool(d.get("image"))
    cw = 7.6 if img else CONTENT_W
    rect(slide, SAFE_X0, SAFE_Y0, cw, 1.45, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    rect(slide, SAFE_X0, SAFE_Y0, 0.09, 1.45, fill=P["primary"], rounded=False)
    pill(slide, 0.95, 1.68, 1.6, 0.24, T('central'), P["soft"], P["primary"], rad=0.08)
    tx(slide, 0.95, 1.98, cw - 0.5, 0.95, d.get("main_statement", ""), size=15.5,
       color=P["primary"], bold=True, font=FONT_TITLE, line_sp=1.1)
    y = 3.15
    if d.get("elaboration"):
        rect(slide, SAFE_X0, y, cw, 0.85, fill=P["soft"], line=P["border"], lw=0.4, rounded=True)
        tx(slide, 0.85, y + 0.12, cw - 0.4, SAFE_X0, d["elaboration"], size=12.0,
           color=P["text"], line_sp=1.15, font=FONT_BODY)
        y += 1.0
    kps = d.get("key_points", [])
    if kps:
        n = len(kps)
        gap = 0.22
        w = (cw - gap * (n - 1)) / n
        ch = 6.6 - y
        for i, kp in enumerate(kps):
            x = SAFE_X0 + i * (w + gap)
            rect(slide, x, y, w, ch, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
            rect(slide, x, y, w, 0.05, fill=P["accent"], rounded=False)
            tf = textframe(slide, x + 0.2, y + 0.18, w - 0.4, ch - 0.3)
            para(tf, kp.get("title", ""), 12.5, P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=4)
            para(tf, kp.get("desc", ""), 11.0, P["text"], line_sp=1.1)
    if img:
        _place_image(slide, d["image"], 8.45, SAFE_Y0, 4.2, 5.0, P)
    footnote(slide, P, d)

def m_flow_diagram(slide, d, P, info):
    """Linear pathway; steps with decision:True render as diamonds (straight arrow = YES,
    bottom corridor bypass to step i+2 = NO, labeled by that step's `desc`)."""
    steps = d.get("steps", [])
    expl = d.get("explanation", "")
    yes_color = _ok_ink(P)
    sub_color = _sub_primary()
    h = 3.6 if expl else 4.6
    y = 1.65
    n = max(len(steps), 1)
    aw = 0.35
    w = (CONTENT_W - aw * (n - 1)) / n
    yb = y + h + 0.22  # NO-branch corridor
    for i, st in enumerate(steps):
        x = SAFE_X0 + i * (w + aw)
        hi = st.get("highlight", False)
        dec = bool(st.get("decision"))
        if dec:
            dsz = min(w * 0.92, h * 0.72)
            dx, dy = x + (w - dsz) / 2.0, y + (h - dsz) / 2.0
            dm = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(dx), Inches(dy), Inches(dsz), Inches(dsz))
            dm.fill.solid(); dm.fill.fore_color.rgb = C(P["card"])
            _note_surface(P["card"], dx, dy, dsz, dsz)
            dm.line.color.rgb = C(P["accent"]); dm.line.width = Pt(1.2)
            dm.shadow.inherit = False
            tf = dm.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = Inches(0.04)
            para(tf, st.get("title", ""), 10.5, P["primary"], bold=True, font=FONT_TITLE,
                 first=True, align=PP_ALIGN.CENTER, sp_after=0, line_sp=1.0)
        else:
            rect(slide, x, y, w, h, fill=(P["primary"] if hi else P["card"]),
                 line=(P["accent"] if hi else P["border"]), lw=1.0 if hi else 0.6, rounded=True)
            badge_bg = P["accent"] if hi else P["soft"]
            badge_fg = _on(P, P["accent"]) if hi else P["primary"]
            pill(slide, x + 0.18, y + 0.18, 0.8, 0.28, st.get("label", f"{T('phase')} {i+1}").upper(),
             badge_bg, badge_fg, size=9, rad=0.08)
            tf = textframe(slide, x + 0.2, y + 0.58, w - 0.4, h - 0.75)
            para(tf, st.get("title", ""), 13.5, "FFFFFF" if hi else P["primary"], bold=True,
                 font=FONT_TITLE, first=True, sp_after=6)
            para(tf, st.get("desc", ""), 11.0, sub_color if hi else P["text"], line_sp=1.1)
        if i < n - 1:
            ax, ay = x + w + 0.05, y + (h / 2.0) - 0.12
            ar = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(ax), Inches(ay), Inches(aw - 0.1), Inches(0.24))
            ar.fill.solid(); ar.fill.fore_color.rgb = C(P["accent"])
            ar.line.fill.background(); ar.shadow.inherit = False
            bypass = dec and (i < n - 2) and not expl
            if dec:
                tx(slide, ax - 0.12, ay - 0.3, 0.6, 0.24, T("yes"), size=8.5,
                   color=yes_color, bold=True, align=PP_ALIGN.CENTER)
                if bypass:  # NO branch: elbow under the row to card i+2
                    xc = x + w / 2.0
                    xt = SAFE_X0 + (i + 2) * (w + aw) + w / 2.0
                    rect(slide, xc - 0.0125, y + h + 0.02, 0.025, yb - (y + h) - 0.02, fill=P["alert"], rounded=False)
                    rect(slide, min(xc, xt), yb, abs(xt - xc), 0.025, fill=P["alert"], rounded=False)
                    up = slide.shapes.add_shape(MSO_SHAPE.UP_ARROW, Inches(xt - 0.09), Inches(y + h + 0.04), Inches(0.18), Inches(0.18))
                    up.fill.solid(); up.fill.fore_color.rgb = C(P["alert"])
                    up.line.fill.background(); up.shadow.inherit = False
                    # v8.3: caption DEBAJO del corredor — antes colisionaba con la línea
                    tx(slide, (xc + xt) / 2.0 - 0.8, yb + 0.06, 1.6, 0.24,
                       st.get("desc") or T("no"), size=8.5, color=P["alert"], bold=True, align=PP_ALIGN.CENTER)
                elif st.get("desc"):
                    # v8.3: sin bypass el corredor no existe; banda reservada a y+h+0.30
                    tx(slide, x + 0.05, y + h + 0.30, w - 0.1, 0.5, st["desc"], size=9.0,
                       color=P["text_muted"], align=PP_ALIGN.CENTER, line_sp=1.0)
        elif dec and st.get("desc"):
            # Decision as final step: no outgoing arrow — show NO-branch caption below.
            tx(slide, x + 0.05, y + h + 0.30, w - 0.1, 0.5, st["desc"], size=9.0,
               color=P["text_muted"], align=PP_ALIGN.CENTER, line_sp=1.0)
    if expl:
        ey = y + h + 0.25
        rect(slide, SAFE_X0, ey, CONTENT_W, 6.6 - ey, fill=P["soft"], line=P["border"], lw=0.5, rounded=True)
        tx(slide, 0.9, ey + 0.1, 11.5, 6.4 - ey, expl, size=11.5, color=P["text"],
           line_sp=1.12, anchor=MSO_ANCHOR.MIDDLE)
    footnote(slide, P, d, y=6.78)

def _render_table_academic(slide, d, P, y_top=1.6, header_key="headers", rows_key="rows"):
    """Oxford/Lancet academic table styling with crisp horizontal rules and soft fills.
    Superficie marcada desconocida durante la tabla: el gate no mide celdas nativas."""
    headers = d.get(header_key, [])
    rows = d.get(rows_key, [])
    if not headers:
        raise KeyError(f"missing '{header_key}' (tabla con rows_key='{rows_key}')")
    with _unmeasured():
        takeaway = d.get("takeaway", "")
        tbl_h = (4.3 if takeaway else 4.9)
        gf = slide.shapes.add_table(len(rows) + 1, len(headers),
                                    Inches(SAFE_X0), Inches(y_top), Inches(CONTENT_W), Inches(tbl_h))
        table = gf.table
        cw = d.get("col_widths")
        if cw and len(cw) == len(headers):
            total = sum(cw)
            for j, wgt in enumerate(cw):
                table.columns[j].width = Inches(CONTENT_W * wgt / total)
        for j, htxt in enumerate(headers):
            cell = table.cell(0, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = C(P["primary"])
            cell.margin_left = cell.margin_right = Inches(0.14)
            cell.margin_top = cell.margin_bottom = Inches(0.08)
            tf = cell.text_frame
            tf.word_wrap = True
            para(tf, str(htxt).upper(), 11.0, "FFFFFF", bold=True, font=FONT_TITLE, first=True, sp_after=0)
        for i, row in enumerate(rows):
            is_even = (i % 2 == 0)
            row_bg = P["card"] if is_even else P["soft"]
            for j in range(len(headers)):
                val = row[j] if j < len(row) else ""
                cell = table.cell(i + 1, j)
                cell.fill.solid()
                cell.fill.fore_color.rgb = C(row_bg)
                cell.margin_left = cell.margin_right = Inches(0.14)
                cell.margin_top = cell.margin_bottom = Inches(0.06)
                tf = cell.text_frame
                tf.word_wrap = True
                is_lead = (j == 0)
                para(tf, str(val), 11.0, P["primary"] if is_lead else P["text"],
                     bold=is_lead, font=FONT_BODY, first=True, sp_after=0, line_sp=1.05)
    if takeaway:
        y = y_top + tbl_h + 0.2
        rect(slide, SAFE_X0, y, CONTENT_W, 0.58, fill=P["soft"], line=P["accent"], lw=0.9, rounded=True)
        tx(slide, 0.9, y + 0.05, 11.5, 0.48, T('takeaway') + takeaway,
           size=11.5, color=P["primary"], bold=True, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)

def m_comparison_table(slide, d, P, info):
    _render_table_academic(slide, d, P)
    footnote(slide, P, d, y=6.85)

def m_synthesis_grid(slide, d, P, info):
    _render_table_academic(slide, d, P, rows_key="matrix_data")
    footnote(slide, P, d, y=6.85)

def m_stat_card(slide, d, P, info):
    """Impactful hero metric slide with clinical narrative support."""
    rect(slide, SAFE_X0, SAFE_Y0, 4.4, 4.95, fill=P["primary"], line=None, rounded=True)
    rect(slide, SAFE_X0, SAFE_Y0, 4.4, 0.06, fill=P["accent"], rounded=False)
    tx(slide, 0.85, 2.2, 4.0, 1.6, d.get("stat_num", ""), size=52, color=_fg_on_primary(P),
       bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE)
    # Barra divisoria centrada respecto al bloque del dígito (x .85 w 4.0 → centro 2.85).
    rect(slide, 2.25, 4.0, 1.2, 0.025, fill=P["accent"], rounded=False)
    tx(slide, 0.9, 4.25, 3.9, 1.8, d.get("stat_title", ""), size=13.5, color="FFFFFF",
       align=PP_ALIGN.CENTER, line_sp=1.15, font=FONT_BODY)
    img = bool(d.get("image"))
    bw = 3.6 if img else 7.3
    bx = 4.25 if img else 5.35
    blocks = d.get("narrative_blocks", [])
    n = max(len(blocks), 1)
    gap = 0.2
    bh = (4.95 - gap * (n - 1)) / n
    for i, b in enumerate(blocks):
        y = SAFE_Y0 + i * (bh + gap)
        rect(slide, bx, y, bw, bh, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, bx, y, 0.06, bh, fill=P["accent"], rounded=False)
        tf = textframe(slide, bx + 0.25, y + 0.12, bw - 0.45, bh - 0.24, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, b.get("title", ""), 12.5, P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=3)
        para(tf, b.get("desc", ""), 11.0, P["text"], line_sp=1.1)
    if img:
        _place_image(slide, d["image"], 8.05, SAFE_Y0, 4.6, 4.95, P)
    footnote(slide, P, d)

def m_checklist(slide, d, P, info):
    """Clinical protocol verification checklist."""
    items = d.get("items", [])
    ok_color = _ok_ink(P)
    n = max(len(items), 1)
    gap = 0.16
    ih, y_first = stack_layout(SAFE_Y0, 4.95, n, gap, cap=1.0)
    rw = 7.5 if d.get("image") else CONTENT_W
    for i, it in enumerate(items):
        y = y_first + i * (ih + gap)
        checked = it.get("checked", True)
        mark, mcol = ("✓", ok_color) if checked else ("✕", P["alert"])
        rect(slide, SAFE_X0, y, rw, ih, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, 0.85, y + (ih / 2.0) - 0.18, 0.36, 0.36, fill=P["soft"], line=mcol, lw=1.2, rounded=True, rad=0.08)
        tx(slide, 0.85, y + (ih / 2.0) - 0.20, 0.36, 0.36, mark, size=14, color=mcol, bold=True, align=PP_ALIGN.CENTER)
        tf = textframe(slide, 1.4, y + 0.08, rw - 0.85, ih - 0.16, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, it.get("label", ""), 12.5, P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=2)
        if it.get("desc"):
            para(tf, it["desc"], 10.8, P["text"], line_sp=1.05)
    if d.get("image"):
        _place_image(slide, d["image"], 8.35, SAFE_Y0, 4.3, 4.95, P)
    footnote(slide, P, d)

def m_fixed_schema_card(slide, d, P, info):
    """Structured diagnostic criteria / entity schema."""
    fields = d.get("fields", [])
    n = max(len(fields), 1)
    gap = 0.16
    fh, y_first = stack_layout(SAFE_Y0, 4.95, n, gap, cap=1.1)
    for i, f in enumerate(fields):
        y = y_first + i * (fh + gap)
        rect(slide, SAFE_X0, y, 3.4, fh, fill=P["primary"], line=None, rounded=True)
        tx(slide, 0.85, y, 3.0, fh, f.get("label", "").upper(), size=11.0, color=_on(P, P["primary"]),
           bold=True, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        rect(slide, 4.15, y, 8.5, fh, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        tx(slide, 4.35, y, 8.1, fh, f.get("value", ""), size=11.5, color=P["text"],
           anchor=MSO_ANCHOR.MIDDLE, line_sp=1.1)
    footnote(slide, P, d)

def _render_column_card(slide, P, x, w, card, accent_color):
    rect(slide, x, SAFE_Y0, w, 4.95, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    rect(slide, x, SAFE_Y0, w, 0.48, fill=accent_color, rounded=False)
    tx(slide, x + 0.25, 1.62, w - 0.5, 0.35, card.get("header", "").upper(), size=10.5,
       color=_on(P, accent_color), bold=True, font=FONT_BODY)
    tx(slide, x + 0.25, 2.15, w - 0.5, 0.55, card.get("title", ""), size=15.0,
       color=P["primary"], bold=True, font=FONT_TITLE)
    tf = textframe(slide, x + 0.25, 2.75, w - 0.5, 3.6)
    for i, pt in enumerate(card.get("points", [])):
        para(tf, "• " + pt, 11.2, P["text"], first=(i == 0), sp_after=7, line_sp=1.1)

def m_side_by_side(slide, d, P, info):
    """Dichotomous comparative module (e.g., Condition A vs Condition B)."""
    m_w = 5.88
    _render_column_card(slide, P, SAFE_X0, m_w, d.get("left_card", {}), P["primary"])
    _render_column_card(slide, P, 6.77, m_w, d.get("right_card", {}), P["accent"])
    footnote(slide, P, d)

def m_taxonomy_tree(slide, d, P, info):
    """Hierarchical classification tree."""
    cats = d.get("categories", [])
    ink = _ink(P)
    n = max(len(cats), 1)
    gap = 0.28
    w, _x0 = row_layout(SAFE_X0, CONTENT_W, n, gap)
    root = d.get("root", d.get("title", ""))
    rect(slide, 4.15, 1.5, 5.0, 0.55, fill=P["primary"], line=None, rounded=True)
    tx(slide, 4.25, 1.5, 4.8, 0.55, root.upper(), size=12.5, color="FFFFFF", bold=True,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
    rect(slide, 6.64, 2.05, 0.02, 0.35, fill=P["accent"], rounded=False)
    rect(slide, SAFE_X0 + w / 2, 2.4, CONTENT_W - w, 0.02, fill=P["accent"], rounded=False)
    for i, c in enumerate(cats):
        x = SAFE_X0 + i * (w + gap)
        rect(slide, x + w / 2 - 0.01, 2.4, 0.02, 0.3, fill=P["accent"], rounded=False)
        rect(slide, x, 2.7, w, 3.85, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, x, 2.7, w, 0.45, fill=P["soft"], rounded=False)
        tx(slide, x + 0.15, 2.75, w - 0.3, 0.35, c.get("name", "").upper(), size=11.0,
           color=P["primary"], bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE)
        tf = textframe(slide, x + 0.2, 3.25, w - 0.4, 3.2)
        para(tf, c.get("property", ""), 11.0, ink, italic=True, font=FONT_BODY, first=True, sp_after=6)
        for ex in c.get("examples", []):
            para(tf, "• " + ex, 10.5, P["text"], sp_after=4, line_sp=1.08)
    footnote(slide, P, d)

def m_algorithm(slide, d, P, info):
    """Clinical algorithmic cascade with decision medallions."""
    steps = d.get("steps", [])
    n = max(len(steps), 1)
    gap = 0.16
    sh, y_first = stack_layout(SAFE_Y0, 4.95, n, gap, cap=1.2)
    for i, st in enumerate(steps):
        y = y_first + i * (sh + gap)
        hi = st.get("highlight", False)
        med_fill = P["accent"] if hi else P["primary"]
        rect(slide, SAFE_X0, y, 0.9, sh, fill=med_fill, line=None, rounded=True)
        tx(slide, SAFE_X0, y, 0.9, sh, st.get("label", f"{i+1:02d}"), size=16, color=_on(P, med_fill),
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        if i < n - 1:
            rect(slide, 1.09, y + sh, 0.02, gap, fill=P["border"], rounded=False)
        rect(slide, 1.7, y, 10.95, sh, fill=P["card"],
             line=P["accent"] if hi else P["border"], lw=1.0 if hi else 0.6, rounded=True)
        tf = textframe(slide, 1.95, y + 0.08, 10.4, sh - 0.16, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, st.get("title", ""), 12.5, P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=2)
        if st.get("desc"):
            para(tf, st["desc"], 10.8, P["text"], line_sp=1.05)
    footnote(slide, P, d)

def m_case_block(slide, d, P, info):
    """NEJM-styled clinical vignette presentation card."""
    img = bool(d.get("image"))
    ink = _ink(P)
    lw = 4.6 if img else 5.85
    rx = 5.45 if img else 6.75
    rw = 4.6 if img else 5.9
    tw = lw - 0.4
    rect(slide, SAFE_X0, SAFE_Y0, lw, 2.15, fill=P["primary"], line=None, rounded=True)
    tx(slide, 0.85, 1.7, tw, 0.25, T('vignette'), size=9.5, color=_fg_on_primary(P),
       bold=True, font=FONT_BODY)
    tx(slide, 0.85, 1.98, tw, 1.6, d.get("case_stem", ""), size=11.5, color="FFFFFF", line_sp=1.1, font=FONT_BODY)
    rect(slide, SAFE_X0, 3.85, lw, 2.65, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    tf = textframe(slide, 0.85, 4.0, tw, 2.4)
    para(tf, T('findings'), 10.0, ink, bold=True, font=FONT_BODY, first=True, sp_after=5)
    for fdg in d.get("findings", []):
        para(tf, "• " + fdg, 10.5 if img else 11.0, P["text"], sp_after=3, line_sp=1.05)
    rect(slide, rx, SAFE_Y0, rw, 2.15, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    tf_r = textframe(slide, rx + 0.25, 1.7, rw - 0.5, 1.9)
    para(tf_r, T('reasoning'), 10.0, ink, bold=True, font=FONT_BODY, first=True, sp_after=4)
    para(tf_r, d.get("reasoning", ""), 10.8, P["text"], line_sp=1.1)
    rect(slide, rx, 3.85, rw, 1.15, fill=P["soft"], line=P["accent"], lw=0.9, rounded=True)
    tf_d = textframe(slide, rx + 0.25, 3.95, rw - 0.5, 0.95, anchor=MSO_ANCHOR.MIDDLE)
    para(tf_d, T('diagnosis'), 9.5, P["alert"], bold=True, first=True, sp_after=2)
    para(tf_d, d.get("diagnosis", ""), 12.5, P["primary"], bold=True, font=FONT_TITLE)
    rect(slide, rx, 5.15, rw, 1.35, fill=P["accent"], line=None, rounded=True)
    pearl_fg = _on(P, P["accent"])
    tf_p = textframe(slide, rx + 0.25, 5.25, rw - 0.5, 1.15, anchor=MSO_ANCHOR.MIDDLE)
    para(tf_p, T('pearl'), 9.5, pearl_fg, bold=True, first=True, sp_after=2)
    para(tf_p, d.get("clinical_pearl", ""), 10.8, pearl_fg, line_sp=1.08)
    if img:
        _place_image(slide, d["image"], 10.25, SAFE_Y0, 2.4, 4.95, P)
    footnote(slide, P, d)

def m_figure(slide, d, P, info):
    """Full-bleed clinical figure showcase."""
    _place_image(slide, d["image"], SAFE_X0, SAFE_Y0, CONTENT_W, 4.75, P)
    caption_txt = d.get("caption", "")
    if caption_txt:
        tx(slide, SAFE_X0, 6.4, CONTENT_W, 0.28, caption_txt, size=10.0, color=P["text"], italic=True)
    footnote(slide, P, d, y=6.75)

# ===================== MODULE RENDERERS — DIAGRAM EXTENSIONS =====================

_TIMELINE_MAX = 5  # v8.3/v8.4: cap único compartido por renderer y contrato lint

def m_timeline(slide, d, P, info):
    """Chronological axis with alternating milestone cards."""
    miles = d.get("milestones", [])[:_TIMELINE_MAX]  # defensa silenciosa; el lint bloquea >cap
    ink = _ink(P)
    n = max(len(miles), 1)
    y_mid, x0, x1 = 4.0, 1.0, 12.35
    rect(slide, x0, y_mid, x1 - x0, 0.035, fill=P["accent"], rounded=False)
    span = (x1 - x0) / n
    for i, ms in enumerate(miles):
        cx = x0 + span * (i + 0.5)
        up = (i % 2 == 0)
        cw = min(span - 0.3, 2.6)
        ch = 1.7 if n <= 4 else 2.05
        fsz = 10.2 if n <= 4 else 9.3
        cy = (y_mid - 0.25 - ch) if up else y_mid + 0.25
        rect(slide, cx - 0.09, y_mid - 0.075, 0.18, 0.18, fill=P["primary"], rounded=True, rad=0.5)
        if i == 0:  # jerarquía sin depender del color: anillo en el hito inicial
            ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - 0.13), Inches(y_mid - 0.135),
                                          Inches(0.26), Inches(0.26))
            ring.fill.background()
            ring.line.color.rgb = C(P["accent"]); ring.line.width = Pt(1.5)
            ring.shadow.inherit = False
        if up:
            rect(slide, cx - 0.01, cy + ch, 0.02, (y_mid - 0.09) - (cy + ch), fill=P["border"], rounded=False)
        else:
            rect(slide, cx - 0.01, y_mid + 0.11, 0.02, cy - (y_mid + 0.11), fill=P["border"], rounded=False)
        rect(slide, cx - cw / 2, cy, cw, ch, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, cx - cw / 2, cy, cw, 0.05, fill=P["accent"] if up else P["primary"], rounded=False)
        tf = textframe(slide, cx - cw / 2 + 0.15, cy + 0.15, cw - 0.3, ch - 0.3)
        para(tf, ms.get("label", ""), 9.5, ink, bold=True, first=True, sp_after=2)
        para(tf, ms.get("title", ""), 12.0, P["primary"], bold=True, font=FONT_TITLE, sp_after=3)
        if ms.get("desc"):
            para(tf, ms["desc"], fsz, P["text"], line_sp=1.05)
    footnote(slide, P, d)

def m_cycle_diagram(slide, d, P, info):
    """Closed-loop process (3–6 nodes) con flechas de cuerda rotadas y hub opcional;
    geometría calibrada contra el solape con el centro."""
    nodes = d.get("nodes", [])
    sub_color = _sub_primary()
    n = max(len(nodes), 1)
    cx = 6.666
    cy = 4.0 if n <= 4 else 3.85
    R = 2.35 if n <= 4 else 2.20
    card_w, card_h = 2.4, 1.15
    centers = []
    for i in range(n):
        rad = _math.radians(-90 + i * (360.0 / n))
        centers.append((cx + R * _math.cos(rad), cy + R * _math.sin(rad) * 0.82))
    for i in range(n):
        x1, y1 = centers[i]
        x2, y2 = centers[(i + 1) % n]
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        vx, vy = mx - cx, my - cy
        dist = _math.hypot(vx, vy) or 1.0
        mx += 0.5 * vx / dist; my += 0.5 * vy / dist  # push arrow outward, clear of hub
        ang = _math.degrees(_math.atan2(y2 - y1, x2 - x1))
        ar = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(mx - 0.22), Inches(my - 0.11), Inches(0.44), Inches(0.22))
        ar.rotation = ang
        ar.fill.solid(); ar.fill.fore_color.rgb = C(P["accent"])
        ar.line.fill.background(); ar.shadow.inherit = False
    for i, (cxx, cyy) in enumerate(centers):
        nd = nodes[i]
        hi = nd.get("highlight", False)
        rect(slide, cxx - card_w / 2, cyy - card_h / 2, card_w, card_h,
             fill=P["primary"] if hi else P["card"],
             line=P["accent"] if hi else P["border"], lw=1.0 if hi else 0.6, rounded=True)
        tf = textframe(slide, cxx - card_w / 2 + 0.12, cyy - card_h / 2 + 0.1, card_w - 0.24, card_h - 0.2, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, nd.get("title", ""), 11.5, "FFFFFF" if hi else P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=2)
        if nd.get("desc"):
            para(tf, nd["desc"], 9.5, sub_color if hi else P["text"], line_sp=1.05)
    if d.get("center_label"):
        # Hub compacto para evitar solape con las tarjetas laterales.
        rect(slide, cx - 0.85, cy - 0.35, 1.7, 0.70, fill=P["soft"], line=P["accent"], lw=0.9, rounded=True, rad=0.12)
        tx(slide, cx - 0.75, cy - 0.35, 1.5, 0.70, d["center_label"], size=10, color=P["primary"],
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
    footnote(slide, P, d)

def m_quadrant_matrix(slide, d, P, info):
    """2x2 matrix (TL, TR, BL, BR) with optional axis labels."""
    quads = d.get("quadrants", [])
    # v8.3: cuadrantes suben a y0=SAFE_Y0 (inicio estándar de contenido) — la etiqueta X
    # gana ~0.16in de aire sobre el footnote en vez de rozarlo.
    x0, y0, qw, qh, gap = 2.3, SAFE_Y0, 4.9, 2.4, 0.12
    if d.get("y_label"):
        lb = slide.shapes.add_textbox(Inches(0.35), Inches(y0), Inches(0.5), Inches(2 * qh + gap))
        tf = lb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = d["y_label"].upper()
        r.font.size = Pt(10); r.font.bold = True
        r.font.color.rgb = C(P["text_muted"]); r.font.name = FONT_BODY
        lb.rotation = 270
    if d.get("x_label"):
        tx(slide, x0, y0 + 2 * qh + gap + 0.12, 2 * qw + gap, 0.3, d["x_label"].upper(),
           size=10, color=P["text_muted"], align=PP_ALIGN.CENTER, bold=True)
    coords = [(x0, y0), (x0 + qw + gap, y0), (x0, y0 + qh + gap), (x0 + qw + gap, y0 + qh + gap)]
    accents = [P["primary"], P["accent"], P["accent"], P["primary"]]
    for (qx0, qy0), q, ac in zip(coords, quads, accents):
        rect(slide, qx0, qy0, qw, qh, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, qx0, qy0, qw, 0.05, fill=ac, rounded=False)
        tf = textframe(slide, qx0 + 0.2, qy0 + 0.15, qw - 0.4, qh - 0.3)
        para(tf, q.get("title", ""), 13.0, P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=4)
        for pt in q.get("points", []):
            para(tf, "• " + pt, 10.8, P["text"], sp_after=3, line_sp=1.08)
    footnote(slide, P, d)

def m_pyramid(slide, d, P, info):
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
        lv_fill = P["primary"] if hi else P["card"]
        rect(slide, cx - w / 2, ly, w, lh, fill=lv_fill,
             line=P["accent"] if hi else P["border"], lw=0.8 if hi else 0.6, rounded=True)
        tx(slide, cx - w / 2 + 0.25, ly, w - 0.5, lh, lv.get("title", ""), size=12,
           color="FFFFFF" if hi else P["primary"], bold=True, anchor=MSO_ANCHOR.MIDDLE,
           align=PP_ALIGN.CENTER, font=FONT_TITLE)
        if lv.get("desc"):
            tx(slide, cx + base_w / 2 + 0.25, ly, 1.6, lh, lv["desc"], size=9.5,
               color=P["text_muted"], anchor=MSO_ANCHOR.MIDDLE, line_sp=1.05)
    footnote(slide, P, d)

# ===================== MODULE RENDERERS — SCHOLARLY PACK =====================

def m_quote_block(slide, d, P, info):
    """Epigraph: seminal quotation in scholarly serif with attribution."""
    tx(slide, 1.0, 1.45, 1.4, 1.3, '\u201C', size=88, color=P["accent"], bold=True,
       font=FONT_TITLE, deco=True)  # ornamento exento del gate
    tx(slide, 2.2, 1.9, 9.4, 2.3, d.get("quote", ""), size=20, color=P["text"], italic=True,
       font=FONT_TITLE, align=PP_ALIGN.CENTER, line_sp=1.25)
    rect(slide, 5.87, 4.45, 1.6, 0.03, fill=P["accent"], rounded=False)
    tx(slide, 2.2, 4.65, 9.4, 0.35, "— " + d.get("author", "").upper(), size=13, color=P["primary"],
       bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE)
    src = " · ".join(x for x in (d.get("source", ""), d.get("year", "")) if x)
    if src:
        tx(slide, 2.2, 5.02, 9.4, 0.3, src, size=10.5, color=P["text_muted"],
           italic=True, align=PP_ALIGN.CENTER)
    if d.get("context"):
        rect(slide, 2.2, 5.55, 9.4, 0.8, fill=P["soft"], line=P["border"], lw=0.4, rounded=True)
        tx(slide, 2.45, 5.66, 8.9, 0.6, d["context"], size=10.5, color=P["text"],
           align=PP_ALIGN.CENTER, line_sp=1.1)
    footnote(slide, P, d)

def m_socratic_question(slide, d, P, info):
    """Oxford tutorial prompt: hero question + numbered reasoning scaffold."""
    ink = _ink(P)
    ov = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.75), Inches(1.8), Inches(1.5), Inches(1.5))
    ov.fill.solid(); ov.fill.fore_color.rgb = C(P["primary"])
    _note_surface(P["primary"], 0.75, 1.8, 1.5, 1.5)
    ov.line.color.rgb = C(P["accent"]); ov.line.width = Pt(1.5)
    ov.shadow.inherit = False
    otf = ov.text_frame
    otf.word_wrap = False
    otf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(otf, "?", 44, "FFFFFF", bold=True, font=FONT_TITLE, first=True, align=PP_ALIGN.CENTER, sp_after=0)
    tx(slide, 2.55, 1.75, 9.9, 0.3, T('tutorial'), size=10, color=ink, bold=True)
    tx(slide, 2.55, 2.1, 9.9, 1.6, d.get("question", ""), size=20, color=P["primary"],
       italic=True, font=FONT_TITLE, line_sp=1.2)
    if d.get("context"):
        tx(slide, 2.55, 3.75, 9.9, 0.45, d["context"], size=10.5,
           color=P["text_muted"], line_sp=1.15)
    sc = d.get("scaffold", [])
    n = len(sc)
    if n:
        gap = 0.25
        w, sx = row_layout(SAFE_X0, CONTENT_W, n, gap)
        for i, s in enumerate(sc):
            x = sx + i * (w + gap)
            rect(slide, x, 4.35, w, 1.75, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
            rect(slide, x, 4.35, w, 0.05, fill=P["accent"], rounded=False)
            bd = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.18), Inches(4.55), Inches(0.4), Inches(0.4))
            bd.fill.solid(); bd.fill.fore_color.rgb = C(P["primary"])
            _note_surface(P["primary"], x + 0.18, 4.55, 0.4, 0.4)
            bd.line.fill.background(); bd.shadow.inherit = False
            btf = bd.text_frame
            btf.word_wrap = False
            btf.vertical_anchor = MSO_ANCHOR.MIDDLE
            para(btf, str(i + 1), 12, "FFFFFF", bold=True, first=True, align=PP_ALIGN.CENTER, sp_after=0)
            tf = textframe(slide, x + 0.7, 4.55, w - 0.9, 1.4)
            para(tf, s, 10.8, P["text"], first=True, line_sp=1.12)
    if d.get("reading"):
        tx(slide, SAFE_X0, 6.42, CONTENT_W, 0.3, d["reading"], size=9.5, color=P["text_muted"], italic=True)
    footnote(slide, P, d)

def m_oxford_union(slide, d, P, info):
    """Union-style motion debate: motion banner, proposition vs opposition, verdict."""
    rect(slide, SAFE_X0, 1.5, CONTENT_W, 1.15, fill=P["primary"], line=None, rounded=True)
    tx(slide, 0.95, 1.62, 11.4, 0.28, T('house'), size=9.5, color=_fg_on_primary(P), bold=True)
    tx(slide, 0.95, 1.92, 11.4, 0.68, '"' + d.get("motion", "") + '"', size=17, color="FFFFFF",
       bold=True, font=FONT_TITLE, line_sp=1.05)
    for x, key, bar in ((SAFE_X0, 'pro_card', P["primary"]), (6.77, 'con_card', P["accent"])):
        card = d.get(key, {})
        rect(slide, x, 2.9, 5.88, 2.95, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, x, 2.9, 5.88, 0.44, fill=bar, rounded=False)
        tx(slide, x + 0.25, 2.97, 5.38, 0.32, card.get("title", "").upper(), size=10.5,
           color=_on(P, bar), bold=True)
        tf = textframe(slide, x + 0.25, 3.5, 5.38, 2.2)
        for i, p in enumerate(card.get("points", [])):
            para(tf, "• " + p, 11.0, P["text"], first=(i == 0), sp_after=6, line_sp=1.1)
    rect(slide, SAFE_X0, 6.05, CONTENT_W, 0.6, fill=P["soft"], line=P["accent"], lw=0.9, rounded=True)
    tx(slide, 0.9, 6.1, 11.5, 0.5, T('verdict') + " " + d.get("verdict", ""), size=11,
       color=P["primary"], bold=True, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
    footnote(slide, P, d, y=6.85)

def m_evidence_card(slide, d, P, info):
    """Landmark trial appraisal: PICO rows + effect hero + limitation strip."""
    rect(slide, SAFE_X0, 1.5, CONTENT_W, 0.95, fill=P["primary"], line=None, rounded=True)
    tx(slide, 0.95, 1.6, 9.0, 0.5, d.get("study_name", ""), size=17, color="FFFFFF",
       bold=True, font=FONT_TITLE)
    if d.get("year"):
        rect(slide, 10.85, 1.64, 1.5, 0.38, fill=P["accent"], line=None, rounded=True, rad=0.12)
        tx(slide, 10.85, 1.64, 1.5, 0.38, str(d["year"]), size=11, color=_on(P, P["accent"]),
           bold=True, align=PP_ALIGN.CENTER)
    design_color = _fg_on_primary_soft(P)   # token on_primary_soft
    pico_color = _fg_on_primary(P)          # token on_primary
    tx(slide, 0.95, 2.06, 9.6, 0.3, d.get("design", "").upper(), size=9.5, color=design_color, bold=True)
    rows = [(l, d.get(f, "")) for l, f in (('P', 'population'), ('I', 'intervention'),
            ('C', 'comparison'), ('O', 'outcome')) if d.get(f)]
    rh, gp = 0.85, 0.12
    for i, (ltr, txt) in enumerate(rows):
        y = 2.65 + i * (rh + gp)
        rect(slide, SAFE_X0, y, 0.55, 0.55, fill=P["primary"], line=None, rounded=True, rad=0.15)
        tx(slide, SAFE_X0, y, 0.55, 0.55, ltr, size=15, color=pico_color, bold=True,
           align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        tx(slide, 1.35, y, 6.5, rh, txt, size=11.0, color=P["text"], line_sp=1.1)
    rect(slide, 8.15, 2.65, 4.5, 1.7, fill=P["accent"], line=None, rounded=True)
    hero_fg = _on(P, P["accent"])
    tx(slide, 8.3, 2.82, 4.2, 0.9, d.get("effect", ""), size=36, color=hero_fg,
       bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE)
    tx(slide, 8.35, 3.78, 4.1, 0.45, d.get("effect_desc", ""), size=10.5, color=hero_fg,
       align=PP_ALIGN.CENTER, line_sp=1.05)
    if d.get("limitation"):
        rect(slide, 8.15, 4.55, 4.5, 1.85, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, 8.15, 4.55, 0.06, 1.85, fill=P["alert"], rounded=False)
        tx(slide, 8.4, 4.7, 4.0, 0.28, T('limitation'), size=9, color=P["alert"], bold=True)
        tx(slide, 8.4, 5.0, 4.0, 1.3, d["limitation"], size=10.5, color=P["text"], line_sp=1.1)
    footnote(slide, P, d, y=6.85)  # credit = full citation (Vancouver)

def m_viva_question(slide, d, P, info):
    """Viva voce: question card, model answer, examiner's note."""
    ink = _ink(P)
    rect(slide, SAFE_X0, SAFE_Y0, 5.7, 4.95, fill=P["primary"], line=None, rounded=True)
    tx(slide, 0.95, 1.75, 5.1, 0.3, T('viva'), size=10, color=_fg_on_primary(P), bold=True)
    if d.get("difficulty"):
        pill(slide, 0.95, 2.13, 1.7, 0.34, d["difficulty"].upper(), P["accent"], _on(P, P["accent"]))
    tx(slide, 0.95, 2.65, 5.1, 3.6, d.get("prompt", ""), size=16, color="FFFFFF",
       font=FONT_TITLE, line_sp=1.2)
    rect(slide, 6.55, SAFE_Y0, 6.1, 2.75, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    tx(slide, 6.8, 1.72, 5.6, 0.3, T('model_answer'), size=10, color=ink, bold=True)
    tx(slide, 6.8, 2.12, 5.6, 2.0, d.get("model_answer", ""), size=11.5, color=P["text"], line_sp=1.12)
    rect(slide, 6.55, 4.5, 6.1, 2.0, fill=P["soft"], line=P["border"], lw=0.6, rounded=True)
    rect(slide, 6.55, 4.5, 0.06, 2.0, fill=P["alert"], rounded=False)
    tx(slide, 6.8, 4.65, 5.6, 0.3, T('examiner'), size=10, color=P["alert"], bold=True)
    tx(slide, 6.8, 5.02, 5.6, 1.35, d.get("examiner_note", ""), size=10.8, color=P["text"], line_sp=1.1)
    footnote(slide, P, d)

def m_mnemonic_card(slide, d, P, info):
    """Acronym expansion: letter medallions + aligned terms + clinical use panel."""
    ink = _ink(P)
    acr = d.get("acronym", "")
    exp = d.get("expansion", [])
    n = max(len(acr), 1)
    gap = 0.15
    cw = min(1.35, (CONTENT_W - gap * (n - 1)) / n)
    total = cw * n + gap * (n - 1)
    x0 = SAFE_X0 + (CONTENT_W - total) / 2.0
    if d.get("domain"):
        pill(slide, 10.55, 1.20, 2.1, 0.34, d["domain"].upper(), P["soft"], P["primary"])
    for i, ch in enumerate(acr):
        x = x0 + i * (cw + gap)
        rect(slide, x, 1.95, cw, 0.95, fill=P["primary"], line=None, rounded=True, rad=0.12)
        tx(slide, x, 1.95, cw, 0.95, ch.upper(), size=28, color="FFFFFF", bold=True,
           align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        tx(slide, x - 0.15, 3.0, cw + 0.3, 0.8, exp[i] if i < len(exp) else "", size=9.5,
           color=P["text"], align=PP_ALIGN.CENTER, line_sp=1.05)
    rect(slide, SAFE_X0, 4.1, CONTENT_W, 1.7, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    rect(slide, SAFE_X0, 4.1, CONTENT_W, 0.05, fill=P["accent"], rounded=False)
    tx(slide, 0.95, 4.28, 11.4, 0.3, T('clinical_use'), size=10, color=ink, bold=True)
    tx(slide, 0.95, 4.62, 11.4, 1.05, d.get("usage", ""), size=12, color=P["text"], line_sp=1.15)
    footnote(slide, P, d)

def m_etymology(slide, d, P, info):
    """Philological deconstruction: colored term fragments + root cards."""
    roots = d.get("roots", [])
    frags = d.get("fragments", [])
    ink = _ink(P)
    tf = textframe(slide, SAFE_X0, 1.85, CONTENT_W, 1.25)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    frag_cols = [P["primary"], ink]  # v8.3: sin alert rojo decorativo (semántica falsa)
    parts = frags if (frags and len(frags) == len(roots)) else [d.get("term", "")]
    for i, fr in enumerate(parts):
        r = p.add_run()
        r.text = fr
        r.font.size = Pt(40)
        r.font.bold = True
        r.font.name = FONT_TITLE
        r.font.color.rgb = C(frag_cols[i % 3] if len(parts) > 1 else P["primary"])
    rect(slide, 5.87, 3.2, 1.6, 0.03, fill=P["accent"], rounded=False)
    n = max(len(roots), 1)
    gap = 0.3
    w, sx = row_layout(SAFE_X0, CONTENT_W, n, gap)
    for i, rt in enumerate(roots):
        x = sx + i * (w + gap)
        rect(slide, x, 3.5, w, 1.85, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, x, 3.5, w, 0.05, fill=P["accent"], rounded=False)
        tfc = textframe(slide, x + 0.2, 3.68, w - 0.4, SAFE_Y0)
        para(tfc, rt.get("part", ""), 15, P["primary"], bold=True, font=FONT_TITLE, first=True,
             sp_after=3, align=PP_ALIGN.CENTER)
        para(tfc, T('origin') + " · " + rt.get("origin", "").upper(), 9, ink, bold=True,
             sp_after=5, align=PP_ALIGN.CENTER)
        para(tfc, rt.get("meaning", ""), 10.5, P["text"], line_sp=1.1, align=PP_ALIGN.CENTER)
    rect(slide, SAFE_X0, 5.6, CONTENT_W, 0.8, fill=P["soft"], line=P["border"], lw=0.4, rounded=True)
    tx(slide, 0.9, 5.68, 11.5, 0.28, T('modern_use'), size=9.5, color=ink, bold=True)
    tx(slide, 0.9, 5.96, 11.5, 0.38, d.get("modern", ""), size=11.5, color=P["primary"], bold=True)
    footnote(slide, P, d)

def m_venn_diagram(slide, d, P, info):
    """Set overlap (2-3 translucent circles); 'shared' = intersection zone (con halo)."""
    sets_l = d.get("sets", [])
    shared = d.get("shared", [])
    n = len(sets_l)
    def _circle(cx, cy, r, color):
        ov = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r), Inches(cy - r),
                                    Inches(2 * r), Inches(2 * r))
        ov.fill.solid(); ov.fill.fore_color.rgb = C(color)
        ov.line.color.rgb = C(P["border"]); ov.line.width = Pt(1.25)
        ov.shadow.inherit = False
        _set_fill_alpha(ov, 42)
    def _halo(cx, cy, w, h):
        shp = rect(slide, cx - w / 2 - 0.05, cy - h / 2 - 0.05, w + 0.10, h + 0.10,
                   fill=P["card"], line=None, rounded=True, rad=0.10)
        _set_fill_alpha(shp, 88)
    def _items(cx, cy, w, h, items, size=10.5):
        if not items:
            return
        tfi = textframe(slide, cx - w / 2, cy - h / 2, w, h, anchor=MSO_ANCHOR.MIDDLE)
        for i, it in enumerate(items):
            para(tfi, "• " + it, size, P["text"], first=(i == 0), sp_after=4,
                 line_sp=1.08, align=PP_ALIGN.CENTER)
    def _label(cx, y, text):
        tx(slide, cx - 1.35, y, 2.7, 0.32, str(text).upper(), size=11, color=P["primary"],
           bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE)
    if n == 3:
        for (cx, cyy), col in zip(((6.666, 3.0), (5.35, 4.85), (7.98, 4.85)),
                                  (P["primary"], P["accent"], P["primary"])):
            _circle(cx, cyy, 1.5, col)
        _label(6.666, 1.5, sets_l[0].get("label", ""))
        _label(5.35, 6.45, sets_l[1].get("label", ""))
        _label(7.98, 6.45, sets_l[2].get("label", ""))
        # v8.3: zonas de ítems ampliadas y fuente menor — 3-4 ítems ya no desbordan la lente
        _items(6.666, 2.40, 1.9, 1.3, sets_l[0].get("items", []), size=9.5)
        _items(4.50, 5.42, 1.7, 1.5, sets_l[1].get("items", []), size=9.5)
        _items(8.83, 5.42, 1.7, 1.5, sets_l[2].get("items", []), size=9.5)
        _halo(6.666, 4.3, 1.35, 0.95)
        _items(6.666, 4.3, 1.35, 0.95, shared, size=9.0)
    else:
        _circle(5.55, 4.1, 1.85, P["primary"])
        _circle(7.78, 4.1, 1.85, P["accent"])
        _label(5.55, 1.95, sets_l[0].get("label", "") if sets_l else "")
        _label(7.78, 1.95, sets_l[1].get("label", "") if len(sets_l) > 1 else "")
        _items(4.6, 4.1, 1.8, 2.0, sets_l[0].get("items", []) if sets_l else [])
        _items(8.73, 4.1, 1.8, 2.0, sets_l[1].get("items", []) if len(sets_l) > 1 else [])
        _halo(6.665, 4.1, 1.45, 2.1)
        _items(6.665, 4.1, 1.45, 2.1, shared, size=9.5)
    footnote(slide, P, d)

def m_chart_data(slide, d, P, info):
    """Native editable chart (bar/line) with scholarly interpretation panel."""
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
    ink = _ink(P)
    cats = d.get("categories", [])
    series = d.get("series", [])
    is_bar = d.get("chart_type", "bar") != "line"
    data = CategoryChartData()
    data.categories = cats
    for s in series:
        data.add_series(s.get("name", ""), tuple(s.get("values", [])))
    with _unmeasured():
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
        pal2 = [P["primary"], P["accent"]]
        for idx, ser in enumerate(chart.plots[0].series):
            col = C(pal2[idx % 2])
            if is_bar:
                ser.format.fill.solid()
                ser.format.fill.fore_color.rgb = col
                ser.format.line.fill.background()
            else:
                ser.format.line.color.rgb = col
                ser.format.line.width = Pt(2.5)
                try:
                    ser.smooth = False
                except Exception:
                    pass
        chart.category_axis.tick_labels.font.size = Pt(10)
        chart.category_axis.tick_labels.font.name = FONT_BODY
        chart.value_axis.tick_labels.font.size = Pt(10)
        chart.value_axis.tick_labels.font.name = FONT_BODY
    rect(slide, 9.0, 1.6, 3.65, 4.85, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    rect(slide, 9.0, 1.6, 3.65, 0.05, fill=P["accent"], rounded=False)
    tx(slide, 9.25, 1.78, 3.15, 0.3, T('reading'), size=10, color=ink, bold=True)
    tfi = textframe(slide, 9.25, 2.2, 3.15, 4.0)
    for i, ins in enumerate(d.get("insights", [])):
        para(tfi, "• " + ins, 10.8, P["text"], first=(i == 0), sp_after=8, line_sp=1.12)
    footnote(slide, P, d)

def m_references(slide, d, P, info):
    """Vancouver-style numbered bibliography in two balanced columns."""
    refs = d.get("refs", [])
    ink = _ink(P)
    n = len(refs)
    pill(slide, 10.85, 1.20, 1.8, 0.34, f"{T('references')} · {n}", P["soft"], P["primary"])
    per = max((n + 1) // 2, 1)
    for ci, col in enumerate([refs[:per], refs[per:]]):
        cx = SAFE_X0 + ci * 6.15
        for j, ref in enumerate(col):
            y = 2.05 + j * 0.88
            tx(slide, cx, y, 0.45, 0.35, f"{ci * per + j + 1}.", size=12, color=ink,
               bold=True, font=FONT_TITLE)
            tx(slide, cx + 0.5, y, 5.35, 0.9, ref, size=10.5, color=P["text"], line_sp=1.1)
    footnote(slide, P, d)

def m_authority_card(slide, d, P, info):
    """Hall-portrait biography: framed image, name, dates, bio, legacy."""
    ink = _ink(P)
    _place_image(slide, d["image"], SAFE_X0, SAFE_Y0, 3.7, 4.95, P)
    tx(slide, 4.75, 1.7, 7.8, 0.6, d.get("name", ""), size=24, color=P["primary"],
       bold=True, font=FONT_TITLE)
    if d.get("dates"):
        tx(slide, 4.75, 2.38, 7.8, 0.3, d["dates"], size=11, color=ink, bold=True)
    if d.get("epithet"):
        tx(slide, 4.75, 2.72, 7.8, 0.35, d["epithet"], size=11.5, color=P["text_muted"], italic=True)
    tx(slide, 4.75, 3.2, 7.8, 2.4, d.get("bio", ""), size=11.5, color=P["text"], line_sp=1.18)
    if d.get("legacy"):
        rect(slide, 4.75, 5.75, 7.8, 0.75, fill=P["soft"], line=P["border"], lw=0.5, rounded=True)
        rect(slide, 4.75, 5.75, 0.06, 0.75, fill=P["accent"], rounded=False)
        tx(slide, 5.0, 5.83, 7.3, 0.28, T('legacy'), size=9, color=ink, bold=True)
        tx(slide, 5.0, 6.1, 7.3, 0.35, d["legacy"], size=10.5, color=P["primary"], bold=True)
    footnote(slide, P, d)

# ===================== MODULE RENDERERS — PEDAGOGY PACK =====================

def m_learning_objectives(slide, d, P, info):
    """Bloom-verb numbered learning objectives with optional Bloom-level pills."""
    ink = _ink(P)
    pill(slide, SAFE_X0, 1.20, 2.9, 0.34, T('objectives'), P["soft"], P["primary"])
    objs = d.get("objectives", [])
    n = max(len(objs), 1)
    gap = 0.14
    rh, y_first = stack_layout(2.15, 4.5, n, gap, cap=1.25)
    for i, obj in enumerate(objs):
        y = y_first + i * (rh + gap)
        rect(slide, SAFE_X0, y, CONTENT_W, rh, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, SAFE_X0, y, 0.07, rh, fill=P["accent"], rounded=False)
        rect(slide, 0.9, y + rh / 2 - 0.22, 0.44, 0.44, fill=P["primary"], line=None, rounded=True, rad=0.5)
        tx(slide, 0.9, y + rh / 2 - 0.22, 0.44, 0.44, str(i + 1), size=12, color="FFFFFF",
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        tf = textframe(slide, SAFE_Y0, y + 0.1, 8.85, rh - 0.2, anchor=MSO_ANCHOR.MIDDLE)
        p = tf.paragraphs[0]
        p.line_spacing = 1.12
        r1 = p.add_run(); r1.text = str(obj.get("verb", "")).upper() + " — "
        r1.font.size = Pt(11.5); r1.font.bold = True
        r1.font.color.rgb = C(P["primary"]); r1.font.name = FONT_BODY
        r2 = p.add_run(); r2.text = str(obj.get("text", ""))
        r2.font.size = Pt(11.5); r2.font.color.rgb = C(P["text"]); r2.font.name = FONT_BODY
        if obj.get("bloom"):
            pill(slide, 10.6, y + rh / 2 - 0.17, 1.85, 0.34,
                 bloom_t(str(obj["bloom"])).upper(), P["soft"], ink, size=8)
    footnote(slide, P, d)

def m_colloquy(slide, d, P, info):
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
        av_fill = P["primary"] if is_tutor else P["accent"]
        av = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(av_x), Inches(y + th / 2 - 0.21),
                                    Inches(0.42), Inches(0.42))
        av.fill.solid(); av.fill.fore_color.rgb = C(av_fill)
        _note_surface(av_fill, av_x, y + th / 2 - 0.21, 0.42, 0.42)
        av.line.fill.background(); av.shadow.inherit = False
        atf = av.text_frame
        atf.word_wrap = False
        atf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para(atf, letter, 12, _on(P, av_fill), bold=True, first=True, align=PP_ALIGN.CENTER, sp_after=0)
        bx = 1.25 if is_tutor else 4.3
        bw = 7.8
        rect(slide, bx, y, bw, th, fill=av_fill,
             line=None if is_tutor else P["border"], lw=0.6, rounded=True)
        # v9.A: fg derivado del FILL real (antes texto oscuro fijo sobre accent
        # fallaba en cambridge/ucp: 2.85 y 2.76).
        tx(slide, bx + 0.25, y, bw - 0.5, th, t.get("text", ""), size=10.8,
           color=_on(P, av_fill), anchor=MSO_ANCHOR.MIDDLE, line_sp=1.12)
    footnote(slide, P, d)

def m_annotated_passage(slide, d, P, info):
    """Primary source text (serif, left) with numbered marginalia (right).
    Author embeds markers like [1] inside the passage; annotations carry matching refs."""
    ink = _ink(P)
    rect(slide, SAFE_X0, SAFE_Y0, 7.3, 4.95, fill=P["soft"], line=P["border"], lw=0.5, rounded=True)
    tx(slide, 0.95, 1.75, 6.7, 4.15, d.get("passage", ""), size=13, color=P["text"],
       italic=True, font=FONT_TITLE, line_sp=1.25)
    if d.get("source"):
        rect(slide, 0.95, 6.0, 1.2, 0.025, fill=P["accent"], rounded=False)
        # v9.A: text_muted crudo sobre panel soft daba 4.23-4.24 en harvard/yale;
        # se deriva tinta legible del par (muted vs soft).
        src_col = P["text_muted"] if _ratio(P["text_muted"], P["soft"]) >= 4.5 \
            else _shade_until(P["text_muted"], P["soft"], WCAG_AA_TEXT)
        tx(slide, 0.95, 6.08, 6.7, 0.3, "— " + d["source"], size=10,
           color=src_col, italic=True)
    tx(slide, 8.25, 1.20, 4.4, 0.3, T('marginalia'), size=9.5, color=ink, bold=True)
    anns = d.get("annotations", [])
    n = max(len(anns), 1)
    gap = 0.12
    ah, y_first = stack_layout(2.0, 4.55, n, gap, cap=1.05)
    for i, a in enumerate(anns):
        y = y_first + i * (ah + gap)
        rect(slide, 8.25, y, 4.4, ah, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, 8.25, y, 0.5, 0.5, fill=P["accent"], line=None, rounded=True, rad=0.15)
        tx(slide, 8.25, y, 0.5, 0.5, str(a.get("ref", i + 1)), size=11, color=_on(P, P["accent"]),
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        tx(slide, 8.9, y + 0.06, 3.65, ah - 0.12, a.get("note", ""), size=10, color=P["text"],
           anchor=MSO_ANCHOR.MIDDLE, line_sp=1.1)
    footnote(slide, P, d)

def m_concept_map(slide, d, P, info):
    """Radial hub-and-spoke: central concept with 4-6 satellite nodes."""
    nodes = d.get("nodes", [])
    sub_color = _sub_primary()
    n = max(len(nodes), 1)
    cx, cy = 6.666, 4.05
    rx, ry = 3.9, 2.0
    card_w, card_h = 2.5, 1.05
    centers = []
    for i in range(n):
        ang = _math.radians(-90 + i * (360.0 / n))
        centers.append((cx + rx * _math.cos(ang), cy + ry * _math.sin(ang)))
    try:
        from pptx.enum.shapes import MSO_CONNECTOR
    except ImportError:
        MSO_CONNECTOR = None
    if MSO_CONNECTOR:
        for (nx, ny) in centers:
            vx, vy = nx - cx, ny - cy
            dist = _math.hypot(vx, vy) or 1.0
            sx, sy = cx + vx / dist * 1.35, cy + vy / dist * 1.35
            conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                              Inches(sx), Inches(sy), Inches(nx), Inches(ny))
            conn.line.color.rgb = C(P["border"])
            conn.line.width = Pt(1.5)
    rect(slide, cx - 1.25, cy - 0.5, 2.5, 1.0, fill=P["primary"], line=None, rounded=True, rad=0.12)
    tx(slide, cx - 1.15, cy - 0.5, 2.3, 1.0, d.get("hub", ""), size=13, color="FFFFFF", bold=True,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
    for i, (nx, ny) in enumerate(centers):
        nd = nodes[i] if i < len(nodes) else {}
        hi = nd.get("highlight", False)
        px = min(max(nx - card_w / 2, SAFE_X0), CANVAS_W - SAFE_X0 - card_w)
        py = ny - card_h / 2
        rect(slide, px, py, card_w, card_h, fill=P["primary"] if hi else P["card"],
             line=P["accent"] if hi else P["border"], lw=1.0 if hi else 0.6, rounded=True)
        tf = textframe(slide, px + 0.15, py + 0.08, card_w - 0.3, card_h - 0.16, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, nd.get("title", ""), 11.5, "FFFFFF" if hi else P["primary"], bold=True,
             font=FONT_TITLE, first=True, sp_after=2, align=PP_ALIGN.CENTER)
        if nd.get("desc"):
            para(tf, nd["desc"], 9.5, sub_color if hi else P["text"], line_sp=1.05, align=PP_ALIGN.CENTER)
    footnote(slide, P, d)

def m_glossary(slide, d, P, info):
    """Two-column terminology: bold serif terms with concise definitions."""
    terms = d.get("terms", [])
    n = len(terms)
    # Tag en banda superior (y=1.20) para no colisionar con los términos cuando per=5.
    pill(slide, 10.55, 1.20, 2.1, 0.34, T('glossary'), P["soft"], P["primary"])
    per = max((n + 1) // 2, 1)
    gap = 0.12
    # Arranque en 2.05 garantiza holgura bajo header+tag; centrado vertical vía stack_layout.
    # v8.3: cap 1.35 — con 5 términos/columna la caja def quedaba en ~0.8in para 130 car.
    eh, y_first = stack_layout(2.05, 4.5, per, gap, cap=1.35)
    for ci, col in enumerate([terms[:per], terms[per:]]):
        cx = SAFE_X0 + ci * 6.12
        for j, e in enumerate(col):
            y = y_first + j * (eh + gap)
            tx(slide, cx, y, 5.88, 0.3, e.get("term", "").upper(), size=12, color=P["primary"],
               bold=True, font=FONT_TITLE)
            tx(slide, cx, y + 0.34, 5.88, eh - 0.38, e.get("def", ""), size=10.5, color=P["text"], line_sp=1.1)
            if j < len(col) - 1:
                rect(slide, cx, y + eh - 0.02, 5.88, 0.012, fill=P["border"], rounded=False)
    footnote(slide, P, d)

def _tag_color(tag, P):
    """Difficulty tag -> pill color heuristic (advanced=alert, intro/essential=success, else accent)."""
    t = str(tag).lower()
    if any(k in t for k in ('adv', 'avan', 'fortg', 'esperto', 'avanz')):
        return P["alert"]
    if any(k in t for k in ('intro', 'bás', 'bas', 'fund', 'esencial', 'essential', 'core', 'indispens')):
        return P["success"]
    return P["accent"]

def _tag_text(pc, P):
    """Foreground del texto dentro de una pill según su fill."""
    if pc == P["success"]:
        return TOK.get('on_success', "FFFFFF")
    if pc == P["alert"]:
        return TOK.get('on_alert', "FFFFFF")
    return TOK.get('on_accent', "FFFFFF")

def m_further_reading(slide, d, P, info):
    """Graded reading list: color-coded difficulty pills + citation + annotation."""
    entries = d.get("entries", [])
    n = max(len(entries), 1)
    gap = 0.14
    rh, y_first = stack_layout(1.6, 4.95, n, gap, cap=1.2)
    for i, e in enumerate(entries):
        y = y_first + i * (rh + gap)
        rect(slide, SAFE_X0, y, CONTENT_W, rh, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        pc = _tag_color(e.get("tag", ""), P)
        pill(slide, 0.85, y + rh / 2 - 0.17, 2.0, 0.34, e.get("tag", "").upper(), pc, _tag_text(pc, P))
        tx(slide, 3.1, y + 0.1, 9.3, 0.35, e.get("title", ""), size=12, color=P["primary"],
           bold=True, font=FONT_TITLE)
        if e.get("note"):
            tx(slide, 3.1, y + 0.52, 9.3, rh - 0.6, e.get("note", ""), size=10.5, color=P["text"], line_sp=1.08)
    footnote(slide, P, d)


I18N = {
 'es-ES': {'central': 'ENUNCIADO CENTRAL', 'chapter': 'CAPÍTULO', 'phase': 'FASE',
   'takeaway': 'CONCLUSIÓN EDITORIAL:  ', 'source': 'Fuente / Crédito: {c}',
   'join': '{f}  •  Crédito: {c}', 'vignette': 'VIÑETA CLÍNICA',
   'findings': 'HALLAZGOS CLÍNICOS & PRUEBAS', 'reasoning': 'JUICIO DIAGNÓSTICO & RAZONAMIENTO',
   'diagnosis': 'DIAGNÓSTICO DEFINITIVO', 'pearl': 'PERLA CLÍNICA',
   'footer': 'SERIE DE MONOGRAFÍAS ACADÉMICAS', 'yes': 'SÍ', 'no': 'NO',
   'course_default': 'PROGRAMA DE FORMACIÓN CLÍNICA AVANZADA',
   'institution_default': 'FACULTAD DE MEDICINA • PROGRAMA ACADÉMICO',
   'house': 'LA CÁMARA SOSTIENE QUE', 'proposition': 'PROPOSICIÓN', 'opposition': 'OPOSICIÓN',
   'verdict': 'VEREDICTO DEL MODERADOR:', 'tutorial': 'PREGUNTA TUTORIAL',
   'scaffold': 'ANDAMIAJE DE RAZONAMIENTO', 'clinical_use': 'USO CLÍNICO',
   'model_answer': 'RESPUESTA MODELO', 'examiner': 'NOTA DEL EXAMINADOR',
   'reading': 'LECTURA DE LOS DATOS', 'shared': 'COMPARTIDO', 'origin': 'ORIGEN',
   'modern_use': 'ACEPCIÓN ACTUAL', 'limitation': 'LIMITACIÓN', 'legacy': 'LEGADO',
   'references': 'REFERENCIAS', 'viva': 'VIVA VOCE',
   'objectives': 'OBJETIVOS DE APRENDIZAJE', 'tutor': 'TUTOR', 'student': 'ESTUDIANTE',
   'marginalia': 'MARGINALIA', 'glossary': 'GLOSARIO', 'further_reading': 'LECTURAS RECOMENDADAS'},
 'en-US': {'central': 'CENTRAL STATEMENT', 'chapter': 'CHAPTER', 'phase': 'PHASE',
   'takeaway': 'EDITORIAL TAKEAWAY:  ', 'source': 'Source / Credit: {c}',
   'join': '{f}  •  Credit: {c}', 'vignette': 'CLINICAL VIGNETTE',
   'findings': 'CLINICAL FINDINGS & TESTS', 'reasoning': 'DIAGNOSTIC REASONING & JUDGMENT',
   'diagnosis': 'DEFINITIVE DIAGNOSIS', 'pearl': 'CLINICAL PEARL',
   'footer': 'ACADEMIC MONOGRAPH SERIES', 'yes': 'YES', 'no': 'NO',
   'course_default': 'ADVANCED CLINICAL TRAINING PROGRAM',
   'institution_default': 'FACULTY OF MEDICINE • ACADEMIC PROGRAM',
   'house': 'THIS HOUSE BELIEVES THAT', 'proposition': 'PROPOSITION', 'opposition': 'OPPOSITION',
   'verdict': "MODERATOR'S VERDICT:", 'tutorial': 'TUTORIAL QUESTION',
   'scaffold': 'REASONING SCAFFOLD', 'clinical_use': 'CLINICAL USE',
   'model_answer': 'MODEL ANSWER', 'examiner': "EXAMINER'S NOTE",
   'reading': 'READING THE DATA', 'shared': 'SHARED', 'origin': 'ORIGIN',
   'modern_use': 'MODERN MEANING', 'limitation': 'LIMITATION', 'legacy': 'LEGACY',
   'references': 'REFERENCES', 'viva': 'VIVA VOCE',
   'objectives': 'LEARNING OBJECTIVES', 'tutor': 'TUTOR', 'student': 'STUDENT',
   'marginalia': 'MARGINALIA', 'glossary': 'GLOSSARY', 'further_reading': 'FURTHER READING'},
 'pt-BR': {'central': 'DECLARAÇÃO CENTRAL', 'chapter': 'CAPÍTULO', 'phase': 'FASE',
   'takeaway': 'CONCLUSÃO EDITORIAL:  ', 'source': 'Fonte / Crédito: {c}',
   'join': '{f}  •  Crédito: {c}', 'vignette': 'VINHETA CLÍNICA',
   'findings': 'ACHADOS CLÍNICOS & EXAMES', 'reasoning': 'RACIOCÍNIO DIAGNÓSTICO',
   'diagnosis': 'DIAGNÓSTICO DEFINITIVO', 'pearl': 'PÉROLA CLÍNICA',
   'footer': 'SÉRIE DE MONOGRAFIAS ACADÊMICAS', 'yes': 'SIM', 'no': 'NÃO',
   'course_default': 'PROGRAMA DE FORMAÇÃO CLÍNICA AVANÇADA',
   'institution_default': 'FACULDADE DE MEDICINA • PROGRAMA ACADÊMICO',
   'house': 'A CÂMARA ACREDITA QUE', 'proposition': 'PROPOSIÇÃO', 'opposition': 'OPOSIÇÃO',
   'verdict': 'VEREDITO DO MODERADOR:', 'tutorial': 'QUESTÃO DE TUTORIA',
   'scaffold': 'ANDAIME DE RACIOCÍNIO', 'clinical_use': 'USO CLÍNICO',
   'model_answer': 'RESPOSTA MODELO', 'examiner': 'NOTA DO EXAMINADOR',
   'reading': 'LEITURA DOS DADOS', 'shared': 'COMUM', 'origin': 'ORIGEM',
   'modern_use': 'ACEPÇÃO ATUAL', 'limitation': 'LIMITAÇÃO', 'legacy': 'LEGADO',
   'references': 'REFERÊNCIAS', 'viva': 'VIVA VOCE',
   'objectives': 'OBJETIVOS DE APRENDIZAGEM', 'tutor': 'TUTOR', 'student': 'ESTUDANTE',
   'marginalia': 'MARGINALIA', 'glossary': 'GLOSSÁRIO', 'further_reading': 'LEITURAS RECOMENDADAS'},
 'fr-FR': {'central': 'ÉNONCÉ CENTRAL', 'chapter': 'CHAPITRE', 'phase': 'PHASE',
   'takeaway': 'CONCLUSION ÉDITORIALE :  ', 'source': 'Source / Crédit : {c}',
   'join': '{f}  •  Crédit : {c}', 'vignette': 'VIGNETTE CLINIQUE',
   'findings': 'SIGNES CLINIQUES & TESTS', 'reasoning': 'RAISONNEMENT DIAGNOSTIQUE',
   'diagnosis': 'DIAGNOSTIC DÉFINITIF', 'pearl': 'PERLE CLINIQUE',
   'footer': 'SÉRIE DE MONOGRAPHIES ACADÉMIQUES', 'yes': 'OUI', 'no': 'NON',
   'course_default': 'PROGRAMME DE FORMATION CLINIQUE AVANCÉE',
   'institution_default': 'FACULTÉ DE MÉDECINE • PROGRAMME ACADÉMIQUE',
   'house': 'CETTE ASSEMBLÉE ESTIME QUE', 'proposition': 'POUR', 'opposition': 'CONTRE',
   'verdict': 'VERDICT DU MODÉRATEUR :', 'tutorial': 'QUESTION DE TUTORAT',
   'scaffold': 'ÉCHAFAUDAGE DE RAISONNEMENT', 'clinical_use': 'USAGE CLINIQUE',
   'model_answer': 'RÉPONSE TYPE', 'examiner': "NOTE DE L'EXAMINATEUR",
   'reading': 'LECTURE DES DONNÉES', 'shared': 'COMMUN', 'origin': 'ORIGINE',
   'modern_use': 'SENS ACTUEL', 'limitation': 'LIMITE', 'legacy': 'HÉRITAGE',
   'references': 'RÉFÉRENCES', 'viva': 'VIVA VOCE',
   'objectives': 'OBJECTIFS PÉDAGOGIQUES', 'tutor': 'TUTEUR', 'student': 'ÉTUDIANT',
   'marginalia': 'MARGINALIA', 'glossary': 'GLOSSAIRE', 'further_reading': 'LECTURES RECOMMANDÉES'},
 'de-DE': {'central': 'KERNAUSSAGE', 'chapter': 'KAPITEL', 'phase': 'PHASE',
   'takeaway': 'REDAKTIONELLES FAZIT:  ', 'source': 'Quelle / Credit: {c}',
   'join': '{f}  •  Credit: {c}', 'vignette': 'KLINISCHER FALLBERICHT',
   'findings': 'KLINISCHE BEFUNDE & TESTS', 'reasoning': 'DIAGNOSTISCHE BEURTEILUNG',
   'diagnosis': 'DEFINITIVE DIAGNOSE', 'pearl': 'KLINISCHE PERLE',
   'footer': 'AKADEMISCHE MONOGRAPHIENREIHE', 'yes': 'JA', 'no': 'NEIN',
   'course_default': 'PROGRAMM FÜR KLINISCHE FORTBILDUNG',
   'institution_default': 'FAKULTÄT FÜR MEDIZIN • AKADEMISCHES PROGRAMM',
   'house': 'DAS HAUS IST DER ANSICHT, DASS', 'proposition': 'PRO', 'opposition': 'CONTRA',
   'verdict': 'URTEIL DES MODERATORS:', 'tutorial': 'TUTORIALFRAGE',
   'scaffold': 'DENKGERÜST', 'clinical_use': 'KLINISCHE ANWENDUNG',
   'model_answer': 'MUSTERANTWORT', 'examiner': 'ANMERKUNG DES PRÜFERS',
   'reading': 'DATENINTERPRETATION', 'shared': 'GEMEINSAM', 'origin': 'URSPRUNG',
   'modern_use': 'HEUTIGE BEDEUTUNG', 'limitation': 'EINSCHRÄNKUNG', 'legacy': 'VERMÄCHTNIS',
   'references': 'LITERATUR', 'viva': 'VIVA VOCE',
   'objectives': 'LERNZIELE', 'tutor': 'TUTOR', 'student': 'STUDENT',
   'marginalia': 'MARGINALIEN', 'glossary': 'GLOSSAR', 'further_reading': 'WEITERFÜHRENDE LITERATUR'},
 'it-IT': {'central': 'ENUNCIATO CENTRALE', 'chapter': 'CAPITOLO', 'phase': 'PHASE',
   'takeaway': 'CONCLUSIONE EDITORIALE:  ', 'source': 'Fonte / Credito: {c}',
   'join': '{f}  •  Credito: {c}', 'vignette': 'CASO CLINICO',
   'findings': 'RISCONTRI CLINICI & TEST', 'reasoning': 'GIUDIZIO DIAGNOSTICO',
   'diagnosis': 'DIAGNOSI DEFINITIVA', 'pearl': 'PERLA CLINICA',
   'footer': 'SERIE DI MONOGRAFIE ACCADEMICHE', 'yes': 'SÌ', 'no': 'NO',
   'course_default': 'PROGRAMMA DI FORMAZIONE CLINICA AVANZATA',
   'institution_default': 'FACOLTÀ DI MEDICINA • PROGRAMMA ACCADEMICO',
   'house': "L'ASSEMBLEA RITIENE CHE", 'proposition': 'PRO', 'opposition': 'CONTRO',
   'verdict': 'VERDITTIVO DEL MODERATORE:', 'tutorial': 'DOMANDA TUTORIALE',
   'scaffold': 'IMPALCATURA DI RAGIONAMENTO', 'clinical_use': 'USO CLINICO',
   'model_answer': 'RISPOSTA MODELLO', 'examiner': "NOTA DELL'ESAMINATORE",
   'reading': 'LETTURA DEI DATI', 'shared': 'COMUNE', 'origin': 'ORIGINE',
   'modern_use': 'ACCEZIONE ATTUALE', 'limitation': 'LIMITAZIONE', 'legacy': 'EREDITÀ',
   'references': 'RIFERIMENTI', 'viva': 'VIVA VOCE',
   'objectives': 'OBIETTIVI DI APPRENDIMENTO', 'tutor': 'TUTOR', 'student': 'STUDENTE',
   'marginalia': 'MARGINALIA', 'glossary': 'GLOSSARIO', 'further_reading': 'LETTURE CONSIGLIATE'},
}
BLOOM_I18N = {
 'en-US': {'remember':'remember','understand':'understand','apply':'apply','analyze':'analyze','evaluate':'evaluate','create':'create'},
 'es-ES': {'remember':'recordar','understand':'comprender','apply':'aplicar','analyze':'analizar','evaluate':'evaluar','create':'crear'},
 'pt-BR': {'remember':'lembrar','understand':'entender','apply':'aplicar','analyze':'analisar','evaluate':'avaliar','create':'criar'},
 'fr-FR': {'remember':'se souvenir','understand':'comprendre','apply':'appliquer','analyze':'analyser','evaluate':'évaluer','create':'créer'},
 'de-DE': {'remember':'erinnern','understand':'verstehen','apply':'anwenden','analyze':'analysieren','evaluate':'bewerten','create':'erschaffen'},
 'it-IT': {'remember':'ricordare','understand':'comprendere','apply':'applicare','analyze':'analizzare','evaluate':'valutare','create':'creare'},
}

# ---- Acceso unificado: tabla plana arriba, cero packs derivados ----
# El idioma es EL QUE EL AUTOR FIJE en CONFIG["LANG"]; default es-ES.
_LANG = 'es-ES'

def set_lang(lang):
    global _LANG
    _LANG = lang if lang in I18N else 'es-ES'

def T(key):
    pack = I18N.get(_LANG) or I18N['es-ES']
    val = pack.get(key) or I18N['es-ES'].get(key)
    return val if val is not None else str(key)

def bloom_t(key):
    b = BLOOM_I18N.get(_LANG) or BLOOM_I18N['en-US']
    return b.get(str(key).lower(), str(key))


# --- Contrato de deriva: portugués infiltrando decks es-ES (único par probado).
PTBR_DRIFT = [
    (r'[a-záéíóúüñãõ]*ç[a-záéíóúüñãõ]*', 'es-ES no usa "ç" (pt -ção -> es -ción)'),
    (r'\bchumbo\b', 'plomo'),
    (r'\blinha\b', 'línea'),
    (r'\blivres?\b', 'libre(s)'),
    (r'\bapoptose\b', 'apoptosis'),
    (r'\bnecrose\b', 'necrosis'),
    (r'\bfibrose\b', 'fibrosis'),
    (r'\bexames?\b', 'examen(es)'),
    (r'\bintensidade\b', 'intensidad'),
    (r'\bduração\b', 'duración'),
    (r'\bcondições\b', 'condiciones'),
    (r'\bsequ[êe]ncia(s)?\b', 'secuencia(s)'),
    (r'\bacidose\b', 'acidosis'),
    (r'\befeitos\b', 'efectos'),
    (r'\bnão\b', 'no'),
    (r'\biônica(s)?\b', 'iónica(s)'),
    (r'\biônicos\b', 'iónicos'),
    (r'\bcromossomos?\b', 'cromosoma(s)'),
    (r'\bcritérios?\b', 'criterio(s)'),
    (r'\bfalha\b', 'falla'),
    (r'\btumefa\b', 'hinchazón / tumefacción'),
    (r'\bextravasamentos?\b', 'extravasamiento'),
    (r'\bconteúdos?\b', 'contenido(s)'),
    (r'\bcérebro\b', 'cerebro'),
    (r'\boxigênio\b', 'oxígeno'),
    (r'\bcálcio\b', 'calcio'),
    (r'\bcorpos\b', 'cuerpos'),
    (r'\bmassa\b', 'masa'),
    (r'\bmorte\b', 'muerte'),
    (r'\bmorrer\b', 'morir'),
    (r'\bviscosidade\b', 'viscosidad'),
    (r'\btermolábeis\b', 'termolábiles'),
    (r'\bhemácias\b', 'hematíes / eritrocitos'),
    (r'\bdor\b', 'dolor'),
    (r'\bfebre\b', 'fiebre'),
    (r'\bachados\b', 'hallazgos'),
    (r'\bestágios?\b', 'estadio(s) / fase(s)'),
    (r'\bdebridamento\b', 'desbridamiento'),
    (r'\bbaço\b', 'bazo'),
    (r'\bfígado\b', 'hígado'),
    (r'\brins?\b', 'riñón / riñones'),
    (r'\bpulmão\b', 'pulmón'),
    (r'\bpulmões\b', 'pulmones'),
    (r'\bsangue\b', 'sangre'),
    (r'\bquadro\b', 'cuadro'),
    (r'\bdoenças?\b', 'enfermedad(es)'),
]

# Guard vigente SOLO para español (único par con fuentes reales probadas).
# Además del léxico: morfología pt exclusiva (-ção/-ções/-dade singular).
DRIFT_CONTRACTS = {'es-ES': list(PTBR_DRIFT) + [
    (r'\b\w+ção\b', 'pt -ção -> es -ción'),
    (r'\b\w+ções\b', 'pt -ções -> es -ciones'),
    (r'\b\w+dade\b', 'pt -dade -> es -dad'),
]}

# Otros idiomas declarados: sin guard — no hay evidencia de necesidad (decisión v1).
DRIFT_WORD_EXCEPTIONS = {
    # Palabras legítimas del español que el léxico marcaría por error (lección v9.F).
    'es-ES': {'modalidades', 'velocidades', 'ciudades'},
}

_DRIFT_COMPILED = {}
_TOKEN_RE = _re.compile(r'[^\W\d_]+', _re.UNICODE)

def _norm(text):
    """Normalización canónica (NFC + lower)."""
    return unicodedata.normalize('NFC', str(text)).lower()

def _drift_patterns(lang):
    if lang not in _DRIFT_COMPILED:
        _DRIFT_COMPILED[lang] = [(_re.compile(p), fix)
                                 for p, fix in DRIFT_CONTRACTS.get(lang, [])]
    return _DRIFT_COMPILED[lang]

def _drift_hits(text, lang):
    """[(palabra, corrección)] de infiltración detectada en el idioma declarado."""
    pats = _drift_patterns(lang)
    if not pats:
        return []
    norm = _norm(text)
    word_exc = DRIFT_WORD_EXCEPTIONS.get(lang, set())
    found = []
    for pat, fix in pats:
        for m in pat.finditer(norm):
            w = m.group(0)
            if w not in word_exc:
                found.append((w, fix))
    return found


def est_height(text, width_in, size_pt, line_sp=1.1, sp_after=3, font=None):
    if not text:
        return 0.0
    # v9.1/A6: leer el global en el CUERPO (no default-arg) — un default captura
    # el valor al importar y los cambios de _apply_fonts no se propagan.
    if font is None:
        font = FONT_BODY
    char_w = _CHAR_W_BY_FONT.get(font, _CHAR_W_DEFAULT)
    cpl = max(1, int((width_in * 72.0) / (size_pt * char_w)))
    lines = 0
    for seg in str(text).split('\n'):
        cur, ln = 0, 1
        for wd in seg.split(' '):
            wl = len(wd) + (1 if cur else 0)
            if cur + wl > cpl and cur:
                ln += 1; cur = len(wd)
            else:
                cur += wl
        lines += ln
    return lines * size_pt * line_sp * 1.02 / 72.0 + sp_after / 72.0


FIT_RULES = {  # module -> callable(d) -> [(field, box_w_in, box_h_in, font_pt)]
 'title':          lambda d: [('title', 10.933, 2.1, 38.0)],
 'section_divider':lambda d: [('section_title', 11.0, 1.8, 36.0), ('section_subtitle', 10.5, 1.5, 15.0)],
 'definition':     lambda d: [('main_statement', (7.1 if d.get('image') else 11.5), 0.95, 15.5),
                              ('elaboration', (7.2 if d.get('image') else 11.6), SAFE_X0, CONTENT_W)],
 'stat_card':      lambda d: [('stat_title', 3.9, 1.8, 13.5)],
 'case_block':     lambda d: [('case_stem', (4.2 if d.get('image') else 5.45), 1.6, 11.5),
                              ('reasoning', (4.1 if d.get('image') else 5.4), 1.9, 10.8),
                              ('clinical_pearl', (4.1 if d.get('image') else 5.4), 1.15, 10.8)],
 'quote_block':    lambda d: [('quote', 9.4, 2.3, 20.0)],
 'socratic_question': lambda d: [('question', 9.9, 1.6, 20.0)],
 'oxford_union':   lambda d: [('motion', 11.4, 0.68, 17.0)],
 'viva_question':  lambda d: [('prompt', 5.1, 3.6, 16.0), ('model_answer', 5.6, 2.0, 11.5)],
 'authority_card': lambda d: [('bio', 7.8, 2.4, 11.5)],
 'evidence_card':  lambda d: [('population', 6.5, 0.85, 11.0), ('intervention', 6.5, 0.85, 11.0),
                              ('comparison', 6.5, 0.85, 11.0), ('outcome', 6.5, 0.85, 11.0)],
 'annotated_passage': lambda d: [('passage', 6.7, 4.15, 13.0)],
}


_BLOOM_VERBS = ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')



COMMON = {'kicker': 55, 'title': 75, 'footnote': 140}



_NO_HEADER_MODULES = ('title', 'section_divider')
_NO_HEADER_MODULES = ('title', 'section_divider')


_COLLOQUY_SPEAKERS = ('tutor', 'student')  # v9.1/A2


_FIGURE_CAPTION_MIN = 15  # pie analítico mínimo (v8.4)


_IMG_MIN_B, _IMG_MAX_B, _IMG_MIN_PX = 20000, 4000000, 300



B = {
 'title':            {'title': 80, 'subtitle': 100, 'course': 70, 'institution': 70, 'author': 70},
 'figure':           {'caption': 110, 'credit': 130},
 'section_divider':  {'section_title': 70, 'section_subtitle': 180, 'divider_style': 40, 'author': 70},
 'definition':       {'main_statement': 240, 'elaboration': 260, 'footnote': 120,
                      'caption': 110, 'credit': 130,
                      '_list': ('key_points', 2, 3, {'title': 45, 'desc': 150})},
 'flow_diagram':     {'explanation': 340,
                      '_list': ('steps', 3, 4, {'label': 12, 'title': 35, 'desc': 170}),
                      '_desc_by_count': ('steps', {3: 220, 4: 170}),
                      '_highlight': ('steps', 1, 1),
                      '_decision_flow': (2, 40)},
 'comparison_table': {'takeaway': 140, '_table': ('rows', 3, 4, 3, 4, 160)},
 'synthesis_grid':   {'takeaway': 140, '_table': ('matrix_data', 3, 3, 3, 3, 220)},
 'stat_card':        {'stat_num': 10, 'stat_title': 120, 'caption': 110, 'credit': 130,
                      '_list': ('narrative_blocks', 1, 3, {'title': 45, 'desc': 180})},
 'checklist':        {'_list': ('items', 2, 5, {'label': 65, 'desc': 150}),
                      'caption': 110, 'credit': 130},
 'fixed_schema_card':{'_list': ('fields', 2, 5, {'label': 30, 'value': 170})},
 'side_by_side':     {'_cards': ({'header': 35, 'title': 50}, 3, 4, 125)},
 'taxonomy_tree':    {'root': 50,
                      '_list': ('categories', 2, 3, {'name': 30, 'property': 65}),
                      '_examples': (3, 90)},
 'algorithm':        {'_list': ('steps', 2, 4, {'title': 70, 'desc': 200}),
                      '_highlight': ('steps', 0, 1)},
 'case_block':       {'case_stem': 240, 'reasoning': 250, 'diagnosis': 50,
                      'clinical_pearl': 160, '_strlist': ('findings', 2, 5, 80),
                      'caption': 110, 'credit': 130},
 'timeline':         {'_list': ('milestones', 3, _TIMELINE_MAX, {'label': 20, 'title': 40, 'desc': 110}),
                      '_desc_by_count': ('milestones', {3: 110, 4: 95, 5: 70})},
 'cycle_diagram':    {'center_label': 40,
                      '_list': ('nodes', 3, 6, {'title': 40, 'desc': 90}),
                      '_highlight': ('nodes', 0, 2)},
 'quadrant_matrix':  {'x_label': 45, 'y_label': 45, '_quads': (40, 2, 5, 110)},
 'pyramid':          {'_list': ('levels', 3, 5, {'title': 55, 'desc': 90}),
                      '_highlight': ('levels', 0, 1)},
 'quote_block':      {'quote': 260, 'author': 60, 'source': 90, 'year': 12, 'context': 160},
 'socratic_question':{'question': 220, 'context': 160, 'reading': 130,
                      '_strlist': ('scaffold', 2, 4, 90)},
 'oxford_union':     {'motion': 140, 'verdict': 160,
                      '_debate': ({'title': 30}, 2, 4, 110)},
 'evidence_card':    {'study_name': 60, 'design': 60, 'population': 140, 'intervention': 140,
                      'comparison': 140, 'outcome': 140, 'effect': 14, 'effect_desc': 120,
                      'limitation': 160, 'year': 10, 'credit': 130},
 'viva_question':    {'prompt': 220, 'model_answer': 260, 'examiner_note': 180, 'difficulty': 12},
 'mnemonic_card':    {'acronym': 8, 'usage': 200, 'domain': 30,
                      '_acronym': ('expansion', 30)},
 'etymology':        {'term': 30, 'modern': 160,
                      '_list': ('roots', 2, 3, {'part': 20, 'origin': 20, 'meaning': 70})},
 'venn_diagram':     {'_venn': (30, 2, 4, 45, 1, 3, 45)},
 'chart_data':       {'chart_type': 6, 'credit': 130,
                      '_chart': (2, 8, 1, 2, 30, 2, 3, 120, 25)},
 'references':       {'_strlist': ('refs', 3, 10, 160)},
 'authority_card':   {'name': 60, 'dates': 30, 'epithet': 80, 'bio': 300,
                      'legacy': 120, 'caption': 110, 'credit': 130},
 'learning_objectives': {'_objectives': (3, 6, 25, 130)},
 'colloquy':         {'_colloquy': (4, 8, 160)},
 'annotated_passage':{'passage': 520, 'source': 90,
                      '_list': ('annotations', 2, 5, {'ref': 6, 'note': 110})},
 'concept_map':      {'hub': 40,
                      '_list': ('nodes', 4, 6, {'title': 35, 'desc': 80}),
                      '_highlight': ('nodes', 0, 2)},
 'glossary':         {'_list': ('terms', 4, 10, {'term': 30, 'def': 130})},
 'further_reading':  {'_list': ('entries', 3, 6, {'title': 90, 'tag': 20, 'note': 100})},
}


REQUIRED_NONEMPTY = {
    'title':            ['title'],
    'figure':           ['image', 'caption', 'credit'],
    'section_divider':  ['section_title'],
    'definition':       ['main_statement'],
    'flow_diagram':     [],
    'comparison_table': ['headers'],
    'synthesis_grid':   ['headers'],
    'stat_card':        ['stat_num', 'stat_title'],
    'checklist':        [],
    'fixed_schema_card':[],
    'side_by_side':     [],
    'taxonomy_tree':    ['root'],
    'algorithm':        [],
    'case_block':       ['case_stem', 'reasoning', 'diagnosis', 'clinical_pearl'],
    'timeline':         [],
    'cycle_diagram':    [],
    'quadrant_matrix':  [],
    'pyramid':          [],
    'quote_block':      ['quote', 'author'],
    'socratic_question':['question'],
    'oxford_union':     ['motion', 'verdict'],
    'evidence_card':    ['study_name', 'design', 'population', 'intervention', 'outcome', 'effect', 'credit'],
    'viva_question':    ['prompt', 'model_answer', 'examiner_note'],
    'mnemonic_card':    ['acronym', 'usage'],
    'etymology':        ['term', 'modern'],
    'venn_diagram':     [],
    'chart_data':       [],
    'references':       [],
    'authority_card':   ['image', 'name', 'bio'],
    'learning_objectives': [],
    'colloquy':         [],
    'annotated_passage':['passage'],
    'concept_map':      ['hub'],
    'glossary':         [],
    'further_reading':  [],
}


MODULE_GOTCHAS = {
 'comparison_table': 'La 1.ª columna de headers ES la columna de criterio: cada fila '
                     'debe tener exactamente len(headers) celdas.',
 'synthesis_grid':   'NO tiene columna de etiqueta implícita. matrix_data es una malla '
                     'de 3 filas x len(headers) celdas; la 1.ª celda ya es la 1.ª columna.',
 'flow_diagram':     'Exactamente 1 paso con highlight=True. Si algún paso lleva '
                     'decision=True, NO puede existir la clave explanation, y desc pasa '
                     'a ser la etiqueta de la rama NO (máx. 40 car.).',
 'etymology':        'fragments debe concatenarse EXACTAMENTE en term y tener el mismo '
                     'número de elementos que roots.',
 'mnemonic_card':    'len(expansion) debe ser igual a len(acronym): un término por letra.',
 'chart_data':       'chart_type solo admite "bar" o "line"; cada series.values debe tener '
                     'la misma longitud que categories y ser numérico.',
 'venn_diagram':     'shared representa SOLO la intersección; 2-3 conjuntos.',
 'learning_objectives': 'bloom debe ser remember|understand|apply|analyze|evaluate|create.',
 'colloquy':         'speaker debe ser exactamente "tutor" o "student".',
 'figure':           'image debe ser .jpg/.jpeg/.png existente, 20 KB-4 MB y >= 300 px de '
                     'lado menor. Ejecute `imgprep work/imgs` antes del lint. '
                     'caption ANALÍTICO (15-110 car.): describa qué muestra la figura, '
                     'no la decore.',
 'authority_card':   'Requiere retrato: mismas reglas de imagen que figure.',
 'case_block':       'findings es una lista de STRINGS cortas (no dicts).',
 'annotated_passage':'Los marcadores [1], [2]... del passage deben existir en annotations.ref.',
}


OPTIONAL_MODULES = ['timeline', 'cycle_diagram', 'quadrant_matrix', 'pyramid',
    'quote_block', 'socratic_question', 'oxford_union', 'evidence_card',
    'viva_question', 'mnemonic_card', 'etymology', 'venn_diagram',
    'chart_data', 'references', 'authority_card',
    'learning_objectives', 'colloquy', 'annotated_passage', 'concept_map',
    'glossary', 'further_reading']


# ===================== LINTER & LANGUAGE DRIFT CONTRACTS =====================
# NOTE: caption/credit limits aligned with the OMC protocol (110/130).
B = {
 'title':            {'title': 80, 'subtitle': 100, 'course': 70, 'institution': 70, 'author': 70},
 'figure':           {'caption': 110, 'credit': 130},
 'section_divider':  {'section_title': 70, 'section_subtitle': 180, 'divider_style': 40, 'author': 70},
 'definition':       {'main_statement': 240, 'elaboration': 260, 'footnote': 120,
                      'caption': 110, 'credit': 130,
                      '_list': ('key_points', 2, 3, {'title': 45, 'desc': 150})},
 'flow_diagram':     {'explanation': 340,
                      '_list': ('steps', 3, 4, {'label': 12, 'title': 35, 'desc': 170}),
                      '_desc_by_count': ('steps', {3: 220, 4: 170}),
                      '_highlight': ('steps', 1, 1),
                      '_decision_flow': (2, 40)},
 'comparison_table': {'takeaway': 140, '_table': ('rows', 3, 4, 3, 4, 160)},
 'synthesis_grid':   {'takeaway': 140, '_table': ('matrix_data', 3, 3, 3, 3, 220)},
 'stat_card':        {'stat_num': 10, 'stat_title': 120, 'caption': 110, 'credit': 130,
                      '_list': ('narrative_blocks', 1, 3, {'title': 45, 'desc': 180})},
 'checklist':        {'_list': ('items', 2, 5, {'label': 65, 'desc': 150}),
                      'caption': 110, 'credit': 130},
 'fixed_schema_card':{'_list': ('fields', 2, 5, {'label': 30, 'value': 170})},
 'side_by_side':     {'_cards': ({'header': 35, 'title': 50}, 3, 4, 125)},
 'taxonomy_tree':    {'root': 50,
                      '_list': ('categories', 2, 3, {'name': 30, 'property': 65}),
                      '_examples': (3, 90)},
 'algorithm':        {'_list': ('steps', 2, 4, {'title': 70, 'desc': 200}),
                      '_highlight': ('steps', 0, 1)},
 'case_block':       {'case_stem': 240, 'reasoning': 250, 'diagnosis': 50,
                      'clinical_pearl': 160, '_strlist': ('findings', 2, 5, 80),
                      'caption': 110, 'credit': 130},
 'timeline':         {'_list': ('milestones', 3, _TIMELINE_MAX, {'label': 20, 'title': 40, 'desc': 110}),
                      '_desc_by_count': ('milestones', {3: 110, 4: 95, 5: 70})},
 'cycle_diagram':    {'center_label': 40,
                      '_list': ('nodes', 3, 6, {'title': 40, 'desc': 90}),
                      '_highlight': ('nodes', 0, 2)},
 'quadrant_matrix':  {'x_label': 45, 'y_label': 45, '_quads': (40, 2, 5, 110)},
 'pyramid':          {'_list': ('levels', 3, 5, {'title': 55, 'desc': 90}),
                      '_highlight': ('levels', 0, 1)},
 'quote_block':      {'quote': 260, 'author': 60, 'source': 90, 'year': 12, 'context': 160},
 'socratic_question':{'question': 220, 'context': 160, 'reading': 130,
                      '_strlist': ('scaffold', 2, 4, 90)},
 'oxford_union':     {'motion': 140, 'verdict': 160,
                      '_debate': ({'title': 30}, 2, 4, 110)},
 'evidence_card':    {'study_name': 60, 'design': 60, 'population': 140, 'intervention': 140,
                      'comparison': 140, 'outcome': 140, 'effect': 14, 'effect_desc': 120,
                      'limitation': 160, 'year': 10, 'credit': 130},
 'viva_question':    {'prompt': 220, 'model_answer': 260, 'examiner_note': 180, 'difficulty': 12},
 'mnemonic_card':    {'acronym': 8, 'usage': 200, 'domain': 30,
                      '_acronym': ('expansion', 30)},
 'etymology':        {'term': 30, 'modern': 160,
                      '_list': ('roots', 2, 3, {'part': 20, 'origin': 20, 'meaning': 70})},
 'venn_diagram':     {'_venn': (30, 2, 4, 45, 1, 3, 45)},
 'chart_data':       {'chart_type': 6, 'credit': 130,
                      '_chart': (2, 8, 1, 2, 30, 2, 3, 120, 25)},
 'references':       {'_strlist': ('refs', 3, 10, 160)},
 'authority_card':   {'name': 60, 'dates': 30, 'epithet': 80, 'bio': 300,
                      'legacy': 120, 'caption': 110, 'credit': 130},
 'learning_objectives': {'_objectives': (3, 6, 25, 130)},
 'colloquy':         {'_colloquy': (4, 8, 160)},
 'annotated_passage':{'passage': 520, 'source': 90,
                      '_list': ('annotations', 2, 5, {'ref': 6, 'note': 110})},
 'concept_map':      {'hub': 40,
                      '_list': ('nodes', 4, 6, {'title': 35, 'desc': 80}),
                      '_highlight': ('nodes', 0, 2)},
 'glossary':         {'_list': ('terms', 4, 10, {'term': 30, 'def': 130})},
 'further_reading':  {'_list': ('entries', 3, 6, {'title': 90, 'tag': 20, 'note': 100})},
}
COMMON = {'kicker': 55, 'title': 75, 'footnote': 140}

REQUIRED_NONEMPTY = {
    'title':            ['title'],
    'figure':           ['image', 'caption', 'credit'],
    'section_divider':  ['section_title'],
    'definition':       ['main_statement'],
    'flow_diagram':     [],
    'comparison_table': ['headers'],
    'synthesis_grid':   ['headers'],
    'stat_card':        ['stat_num', 'stat_title'],
    'checklist':        [],
    'fixed_schema_card':[],
    'side_by_side':     [],
    'taxonomy_tree':    ['root'],
    'algorithm':        [],
    'case_block':       ['case_stem', 'reasoning', 'diagnosis', 'clinical_pearl'],
    'timeline':         [],
    'cycle_diagram':    [],
    'quadrant_matrix':  [],
    'pyramid':          [],
    'quote_block':      ['quote', 'author'],
    'socratic_question':['question'],
    'oxford_union':     ['motion', 'verdict'],
    'evidence_card':    ['study_name', 'design', 'population', 'intervention', 'outcome', 'effect', 'credit'],
    'viva_question':    ['prompt', 'model_answer', 'examiner_note'],
    'mnemonic_card':    ['acronym', 'usage'],
    'etymology':        ['term', 'modern'],
    'venn_diagram':     [],
    'chart_data':       [],
    'references':       [],
    'authority_card':   ['image', 'name', 'bio'],
    'learning_objectives': [],
    'colloquy':         [],
    'annotated_passage':['passage'],
    'concept_map':      ['hub'],
    'glossary':         [],
    'further_reading':  [],
}



def _v_list(val, d, m, loc0, over, errs, spec=None):
    key, lo, hi, fl = val
    items = d.get(key, [])
    if spec and '_desc_by_count' in spec and spec['_desc_by_count'][0] == key:
        dl = spec['_desc_by_count'][1].get(len(items))
        if dl: fl = dict(fl, desc=dl)
    if not lo <= len(items) <= hi:
        errs.append(f'{loc0}.{key}: {len(items)} ítems, esperado {lo}-{hi}')
    for j, it in enumerate(items):
        for fk, flim in fl.items():
            over(f'{loc0}.{key}[{j}].{fk}', it.get(fk, ''), flim)

def _v_strlist(val, d, m, loc0, over, errs):
    key, lo, hi, lim = val
    items = d.get(key, [])
    if not lo <= len(items) <= hi:
        errs.append(f'{loc0}.{key}: {len(items)} ítems, esperado {lo}-{hi}')
    for s_ in items: over(f'{loc0}.{key}', s_, lim)

def _v_examples(val, d, m, loc0, over, errs):
    mx, lim = val
    for j, c in enumerate(d.get('categories', [])):
        exs = c.get('examples', [])
        if len(exs) > mx:
            errs.append(f'{loc0}.categories[{j}].examples: {len(exs)} > {mx}')
        for e in exs: over(f'{loc0}.categories[{j}].examples', e, lim)

def _v_sided_cards(val, d, m, loc0, over, errs, sides):
    fl, plo, phi, plim = val
    for side in sides:
        c = d.get(side, {})
        for fk, flim in fl.items():
            over(f'{loc0}.{side}.{fk}', c.get(fk, ''), flim)
        pts = c.get('points', [])
        if not plo <= len(pts) <= phi:
            errs.append(f'{loc0}.{side}.points: {len(pts)}, esperado {plo}-{phi}')
        for p in pts: over(f'{loc0}.{side}.points', p, plim)

def _v_cards(val, d, m, loc0, over, errs):
    _v_sided_cards(val, d, m, loc0, over, errs, ('left_card', 'right_card'))

def _v_debate(val, d, m, loc0, over, errs):
    _v_sided_cards(val, d, m, loc0, over, errs, ('pro_card', 'con_card'))

def _v_highlight(val, d, m, loc0, over, errs):
    key, lo, hi = val
    n = sum(1 for s_ in d.get(key, []) if s_.get('highlight'))
    if not lo <= n <= hi:
        errs.append(f'{loc0}: {n} {key} destacados, esperado {lo}-{hi}')

def _v_quads(val, d, m, loc0, over, errs):
    tlim, plo, phi, plim = val
    quads = d.get('quadrants', [])
    if len(quads) != 4:
        errs.append(f'{loc0}.quadrants: {len(quads)} cuadrantes, esperado 4')
    for j, q in enumerate(quads):
        over(f'{loc0}.quadrants[{j}].title', q.get('title', ''), tlim)
        pts = q.get('points', [])
        if not plo <= len(pts) <= phi:
            errs.append(f'{loc0}.quadrants[{j}].points: {len(pts)}, esperado {plo}-{phi}')
        for p in pts: over(f'{loc0}.quadrants[{j}].points', p, plim)

def _v_decision_flow(val, d, m, loc0, over, errs):
    max_dec, dlim = val
    steps_l = d.get('steps', [])
    ndec = sum(1 for s_ in steps_l if s_.get('decision'))
    if ndec > max_dec:
        errs.append(f'{loc0}: {ndec} decisiones, máximo {max_dec}')
    if ndec and d.get('explanation'):
        errs.append(f'{loc0}: steps.decision no es compatible con explanation')
    for j, s_ in enumerate(steps_l):
        if s_.get('decision'):
            over(f'{loc0}.steps[{j}].desc (ramificación NO)', s_.get('desc', ''), dlim)

def _v_acronym(val, d, m, loc0, over, errs):
    key, lim = val
    acr = str(d.get('acronym', ''))
    exp = d.get(key, [])
    if len(exp) != len(acr):
        errs.append(f'{loc0}.{key}: {len(exp)} términos para {len(acr)} letras')
    for j, e in enumerate(exp):
        over(f'{loc0}.{key}[{j}]', e, lim)

def _v_venn(val, d, m, loc0, over, errs):
    flab, slo, shi, ilim, hlo, hhi, hlim = val
    sets_l = d.get('sets', [])
    if not 2 <= len(sets_l) <= 3:
        errs.append(f'{loc0}.sets: {len(sets_l)} conjuntos, esperado 2-3')
    for j, st in enumerate(sets_l):
        over(f'{loc0}.sets[{j}].label', st.get('label', ''), flab)
        its = st.get('items', [])
        if not slo <= len(its) <= shi:
            errs.append(f'{loc0}.sets[{j}].items: {len(its)}, esperado {slo}-{shi}')
        for e in its: over(f'{loc0}.sets[{j}].items', e, ilim)
    sh = d.get('shared', [])
    if not hlo <= len(sh) <= hhi:
        errs.append(f'{loc0}.shared: {len(sh)}, esperado {hlo}-{hhi}')
    for e in sh: over(f'{loc0}.shared', e, hlim)

def _v_chart(val, d, m, loc0, over, errs):
    clo, chi, snlo, snhi, snlim, inlo, inhi, inlim, catlim = val
    cats_l = d.get('categories', [])
    series_l = d.get('series', [])
    ins = d.get('insights', [])
    if d.get('chart_type', 'bar') not in ('bar', 'line'):
        errs.append(f'{loc0}.chart_type: usar "bar" o "line"')
    if not clo <= len(cats_l) <= chi:
        errs.append(f'{loc0}.categories: {len(cats_l)}, esperado {clo}-{chi}')
    for j, cv in enumerate(cats_l):
        over(f'{loc0}.categories[{j}]', cv, catlim)
    if not snlo <= len(series_l) <= snhi:
        errs.append(f'{loc0}.series: {len(series_l)}, esperado {snlo}-{snhi}')
    for j, sr in enumerate(series_l):
        over(f'{loc0}.series[{j}].name', sr.get('name', ''), snlim)
        vals = sr.get('values', [])
        if len(vals) != len(cats_l):
            errs.append(f'{loc0}.series[{j}].values: {len(vals)} vs {len(cats_l)} categorías')
        for k_, v in enumerate(vals):
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errs.append(f'{loc0}.series[{j}].values[{k_}]: valor no numérico ({v!r})')
    if not inlo <= len(ins) <= inhi:
        errs.append(f'{loc0}.insights: {len(ins)}, esperado {inlo}-{inhi}')
    for e in ins: over(f'{loc0}.insights', e, inlim)

def _v_objectives(val, d, m, loc0, over, errs):
    lo, hi, vlim, tlim = val
    objs = d.get('objectives', [])
    if not lo <= len(objs) <= hi:
        errs.append(f'{loc0}.objectives: {len(objs)} objetivos, esperado {lo}-{hi}')
    for j, o in enumerate(objs):
        over(f'{loc0}.objectives[{j}].verb', o.get('verb', ''), vlim)
        over(f'{loc0}.objectives[{j}].text', o.get('text', ''), tlim)
        bl = str(o.get('bloom', '')).strip().lower()
        if bl and bl not in _BLOOM_VERBS:
            errs.append(f'{loc0}.objectives[{j}].bloom: {bl!r} no válido '
                        f'({"|".join(_BLOOM_VERBS)})')

def _v_colloquy(val, d, m, loc0, over, errs):
    lo, hi, tlim = val
    turns = d.get('turns', [])
    if not lo <= len(turns) <= hi:
        errs.append(f'{loc0}.turns: {len(turns)} turnos, esperado {lo}-{hi}')
    for j, t in enumerate(turns):
        sp = str(t.get('speaker', '')).strip().lower()
        if sp not in _COLLOQUY_SPEAKERS:
            errs.append(f'{loc0}.turns[{j}].speaker: {sp!r} no válido (tutor|student)')
        over(f'{loc0}.turns[{j}].text', t.get('text', ''), tlim)

def _v_table(val, d, m, loc0, over, errs):
    key, rlo, rhi, clo, chi, lim = val
    rows = d.get(key, [])
    hdrs = d.get('headers', [])
    cw = d.get('col_widths')
    if not rlo <= len(rows) <= rhi:
        errs.append(f'{loc0}.{key}: {len(rows)} filas, esperado {rlo}-{rhi}')
    if not clo <= len(hdrs) <= chi:
        errs.append(f'{loc0}.headers: {len(hdrs)} columnas, esperado {clo}-{chi}')
    if cw and len(cw) != len(hdrs):
        errs.append(f'{loc0}.col_widths: {len(cw)} pesos vs {len(hdrs)} encabezados '
                    f'— un peso por encabezado, ni uno más (ver: schema {m})')
    if cw:
        if not isinstance(cw, (list, tuple)):
            errs.append(f'{loc0}.col_widths: usar lista de pesos numéricos')
        else:
            for j, w in enumerate(cw):
                if isinstance(w, bool) or not isinstance(w, (int, float)):
                    errs.append(f'{loc0}.col_widths[{j}]: peso no numérico ({w!r})')
                elif w <= 0:
                    errs.append(f'{loc0}.col_widths[{j}]: peso debe ser > 0')
    for r, row in enumerate(rows):
        if len(row) != len(hdrs):
            errs.append(f'{loc0}.{key}[{r}]: {len(row)} celdas vs {len(hdrs)} encabezados '
                        f'— no existe columna de etiqueta implícita: la 1.ª celda ES la 1.ª '
                        f'columna de headers (ver: schema {m})')
        for j, cell in enumerate(row):
            over(f'{loc0}.{key}[{r}][{j}]', cell, lim)

SPEC_VALIDATORS = {
    '_list': _v_list,       # recibe spec para aplicar _desc_by_count
    '_strlist': _v_strlist,
    '_table': _v_table,
    '_examples': _v_examples,
    '_cards': _v_cards,
    '_debate': _v_debate,
    '_highlight': _v_highlight,
    '_quads': _v_quads,
    '_decision_flow': _v_decision_flow,
    '_acronym': _v_acronym,
    '_venn': _v_venn,
    '_chart': _v_chart,
    '_objectives': _v_objectives,
    '_colloquy': _v_colloquy,
}

MODULE_VALIDATORS = {
    'etymology': lambda d, m, loc0, over, errs: (
        (lambda frags_l: (
            errs.append(f'{loc0}.fragments: debe concatenar exactamente en term y '
                        f'tener len(roots) elementos (tiene {len(frags_l)})')
            if frags_l and (len(frags_l) != len(d.get('roots', []))
                            or ''.join(frags_l) != str(d.get('term', ''))) else None
        ))(d.get('fragments') or [])
    ),
    'annotated_passage': lambda d, m, loc0, over, errs: (
        (lambda marks, have: (
            errs.append(f'{loc0}: marcadores {sorted(marks - have, key=int)} del passage '
                        f'sin nota en annotations')
            if marks - have else None
        ))(
            set(_re.findall(r'\[(\d+)\]', str(d.get('passage', '')))),
            {str(a.get('ref', '')).strip() for a in d.get('annotations', [])}
        )
    ),
}

def _check_image_fields(d, m, loc0, errs):
    if m not in IMG_MODS:
        errs.append(f'{loc0}: módulo {m} no soporta imágenes (permitidos: {", ".join(IMG_MODS)})')
    for k in ('caption', 'credit'):
        if not str(d.get(k, '')).strip():
            errs.append(f'{loc0}.{k}: campo obligatorio cuando hay imagen')
    # v8.4 (idea del v8.0.0 paralelo): el pie de una figura debe ser ANALÍTICO,
    # no decorativo — longitud mínima sustantiva.
    if m == 'figure':
        cap_len = len(str(d.get('caption', '')).strip())
        if cap_len < _FIGURE_CAPTION_MIN:
            errs.append(f'{loc0}.caption: {cap_len} caracteres < {_FIGURE_CAPTION_MIN}'
                        f' — la figura debe tener un pie analítico sustantivo, '
                        f'no decorativo')
    pth = str(d.get('image', '')).strip()
    if not os.path.exists(pth):
        errs.append(f'{loc0}: archivo de imagen no encontrado: {pth}')
        return
    if pth.lower().rsplit('.', 1)[-1] not in ('jpg', 'jpeg', 'png'):
        errs.append(f'{loc0}: extensión no soportada (usar jpg/jpeg/png)')
    sz = os.path.getsize(pth)
    if not _IMG_MIN_B <= sz <= _IMG_MAX_B:
        errs.append(f'{loc0}: tamaño de imagen ({sz} B) fuera del rango 20 KB - 4 MB')
    try:
        if min(_image_size(pth)) < _IMG_MIN_PX:
            errs.append(f'{loc0}: dimensión mínima < 300 px')
    except Exception:
        errs.append(f'{loc0}: imagen no legible por Pillow')




# ===================== REGISTRO ÚNICO DE MÓDULOS =====================
# Una sola estructura de verdad por módulo: añadir módulo nuevo = renderer arriba
# + un bloque aquí. `when` guía la elección CONTEXT-AWARE (la imprime schema/new):
# el autor matchea la forma del contenido, no recetas de scaffold cerradas.

_RENDERERS = {
    'title': m_title, 'section_divider': m_section_divider, 'definition': m_definition,
    'figure': m_figure, 'flow_diagram': m_flow_diagram,
    'comparison_table': m_comparison_table, 'synthesis_grid': m_synthesis_grid,
    'stat_card': m_stat_card, 'checklist': m_checklist,
    'fixed_schema_card': m_fixed_schema_card, 'side_by_side': m_side_by_side,
    'taxonomy_tree': m_taxonomy_tree, 'algorithm': m_algorithm,
    'case_block': m_case_block, 'quote_block': m_quote_block,
    'timeline': m_timeline, 'cycle_diagram': m_cycle_diagram,
    'quadrant_matrix': m_quadrant_matrix, 'pyramid': m_pyramid,
    'socratic_question': m_socratic_question, 'oxford_union': m_oxford_union,
    'evidence_card': m_evidence_card, 'viva_question': m_viva_question,
    'mnemonic_card': m_mnemonic_card, 'etymology': m_etymology,
    'venn_diagram': m_venn_diagram, 'chart_data': m_chart_data,
    'references': m_references, 'authority_card': m_authority_card,
    'learning_objectives': m_learning_objectives, 'colloquy': m_colloquy,
    'annotated_passage': m_annotated_passage, 'concept_map': m_concept_map,
    'glossary': m_glossary, 'further_reading': m_further_reading,
}

_MODULE_TIERS = {
    'title': 'core', 'definition': 'core', 'section_divider': 'core', 'figure': 'core',
    'flow_diagram': 'classic', 'comparison_table': 'classic', 'synthesis_grid': 'classic',
    'stat_card': 'classic', 'checklist': 'classic', 'fixed_schema_card': 'classic',
    'side_by_side': 'classic', 'taxonomy_tree': 'classic', 'algorithm': 'classic',
    'case_block': 'classic',
    'timeline': 'diagram', 'cycle_diagram': 'diagram', 'quadrant_matrix': 'diagram',
    'pyramid': 'diagram', 'venn_diagram': 'diagram', 'concept_map': 'diagram',
    'chart_data': 'diagram',
    'quote_block': 'scholarly', 'socratic_question': 'scholarly',
    'oxford_union': 'scholarly', 'evidence_card': 'scholarly',
    'viva_question': 'scholarly', 'mnemonic_card': 'scholarly',
    'etymology': 'scholarly', 'references': 'scholarly', 'authority_card': 'scholarly',
    'learning_objectives': 'pedagogy', 'colloquy': 'pedagogy',
    'annotated_passage': 'pedagogy', 'glossary': 'pedagogy',
    'further_reading': 'pedagogy',
}

_MODULE_WHEN = {
    'title': 'toda presentación: portada con curso, título y subtítulo',
    'section_divider': 'transición entre bloques temáticos del source; da ritmo en decks largos',
    'definition': 'el enunciado central que el deck desarrolla + puntos clave; va temprano',
    'figure': 'hay una imagen REAL que desarrolla contenido (histología, esquema del source, imagen clínica)',
    'flow_diagram': 'proceso lineal de 3-4 pasos; pasos con decision=True ramifican (sí/no)',
    'comparison_table': 'comparar opciones/criterios: 3-4 columnas x 3-4 filas',
    'synthesis_grid': 'malla densa 3x3 de relaciones (matriz resumen de una sección)',
    'stat_card': 'UNA cifra del source merece protagonismo + bloques narrativos de apoyo',
    'checklist': 'protocolo o lista de verificación accionable (pasos a seguir en la práctica)',
    'fixed_schema_card': 'entidad con campos fijos label->valor (criterios diagnósticos, ficha)',
    'side_by_side': 'dicotomía A vs B con puntos por lado',
    'taxonomy_tree': 'clasificación jerárquica: raíz + 2-3 categorías con ejemplos',
    'algorithm': 'cascada numerada de decisiones o procedimientos',
    'case_block': 'caso/viñeta con hallazgos, razonamiento, diagnóstico y perla — cierra bien un tema',
    'quote_block': 'cita textual relevante con autor y contexto',
    'timeline': 'evolución temporal, fases o hitos (3-5): historia natural, etapas, cronología',
    'cycle_diagram': 'proceso cíclico cerrado de 3-6 nodos (retroalimentación)',
    'quadrant_matrix': 'matriz 2x2 con ejes (decisión bidimensional, clasificación)',
    'pyramid': 'jerarquía de niveles (3-5) donde la base sostiene la cima',
    'socratic_question': 'pregunta tutorial con andamiaje de razonamiento numerado — autoestudio',
    'oxford_union': 'debate pro/contra sobre una moción con veredicto (temas controvertidos)',
    'evidence_card': 'un estudio/paper clave: PICO + efecto principal + limitación',
    'viva_question': 'pregunta tipo examen con respuesta modelo y nota del examinador — repaso activo',
    'mnemonic_card': 'regla mnemotécnica tipo acrónimo (un término por letra)',
    'etymology': 'deconstrucción de un término en sus raíces (griego/latín)',
    'venn_diagram': 'solapamiento de 2-3 conjuntos con zona compartida',
    'chart_data': 'datos numéricos comparables (gráfico nativo editable) + panel de lectura',
    'references': 'bibliografía numerada en dos columnas',
    'authority_card': 'autor/figura con retrato real + biografía + legado',
    'learning_objectives': 'objetivos de aprendizaje con verbo Bloom — abre decks de clase',
    'colloquy': 'diálogo tutor/estudiante alternado (tutorial socrático)',
    'annotated_passage': 'texto fuente primario con notas marginales numeradas [1] [2]',
    'concept_map': 'concepto central con 4-6 satélites radiales',
    'glossary': 'terminología clave con definiciones breves (4-10 términos)',
    'further_reading': 'lecturas graduadas por dificultad para profundizar',
}

# Módulos que aceptan imagen (contrato: caption+credit obligatorios con imagen).
IMG_MODS = ('figure', 'definition', 'case_block', 'stat_card', 'checklist',
            'authority_card')

MODULES = {}
for _m, _fn in _RENDERERS.items():
    MODULES[_m] = {
        'render': _fn,
        'tier': _MODULE_TIERS[_m],
        'schema': B.get(_m, {}),
        'required': tuple(REQUIRED_NONEMPTY.get(_m, ())),
        'fit': FIT_RULES.get(_m),
        'when': _MODULE_WHEN[_m],
        'gotcha': MODULE_GOTCHAS.get(_m),
    }
del _m, _fn

dispatch_map = {name: spec['render'] for name, spec in MODULES.items()}  # compat interna

# Integridad del registro en import (lección v9: que las vistas no puedan derivar).
assert set(MODULES) == set(B) == set(REQUIRED_NONEMPTY) == set(_MODULE_WHEN) \
    == set(_MODULE_TIERS), 'registro desincronizado'
assert len(MODULES) == 35, f'espeoraba 35 módulos, hay {len(MODULES)}'
assert all(callable(s['render']) for s in MODULES.values())
assert all(s['when'].strip() for s in MODULES.values()), 'todo módulo necesita `when`'



# ===================== LINT (cordura por slide; sin burocracia) =====================

def check(slides, lang='es-ES'):
    """Contrato de contenido por slide. Fuera (vs kit viejo): floors de variedad,
    core obligatorio, presupuesto de figuras, perfiles coercitivos, ledger/ATU.
    Queda lo que evita decks rotos: requeridos vacíos, presupuestos de caracteres,
    fit tipográfico, imágenes válidas, deriva pt->es cuando el idioma es español."""
    errs = []
    def over(loc, s, lim):
        if isinstance(s, str) and len(s) > lim:
            errs.append(f'{loc}: {len(s)} > {lim} carácteres (sobran {len(s) - lim}; '
                        f'recorte al menos {len(s) - lim} y apunte a <= {int(lim * 0.9)} '
                        f'para dejar margen): "{s[:45]}..."')
    def walk_lang(v, loc):
        if isinstance(v, str):
            for w, fix in _drift_hits(v, lang):
                errs.append(f'{loc}: drift {w!r} -> {fix} (reescribir en el idioma objetivo)')
        elif isinstance(v, dict):
            for k, vv in v.items():
                if k != 'image':
                    walk_lang(vv, f'{loc}.{k}')
        elif isinstance(v, (list, tuple)):
            for j, vv in enumerate(v):
                walk_lang(vv, f'{loc}[{j}]')
    def walk_markers(v, loc):
        """Un scaffold sin editar no puede llegar a render: los marcadores
        '<= N car.>' generados por schema/new deben sustituirse."""
        if isinstance(v, str):
            if _re.fullmatch(r'<=\s*\d+\s*car\.\s*>', v.strip()):
                errs.append(f'{loc}: marcador sin reemplazar "{v.strip()}" — '
                            f'escriba contenido real (schema <módulo> muestra el contrato)')
        elif isinstance(v, dict):
            for k, vv in v.items():
                if k != 'image':
                    walk_markers(vv, f'{loc}.{k}')
        elif isinstance(v, (list, tuple)):
            for j, vv in enumerate(v):
                walk_markers(vv, f'{loc}[{j}]')

    for i, d in enumerate(slides, 1):
        m = d.get('module')
        if m not in MODULES:
            errs.append(f'slide {i}: módulo desconocido {m!r}')
            continue
        loc0 = f'slide {i} [{m}]'
        spec = MODULES[m]['schema']
        if m not in _NO_HEADER_MODULES:
            for k, lim in COMMON.items():
                over(f'{loc0}.{k}', d.get(k, ''), lim)
        for k, lim in spec.items():
            if k.startswith('_'):
                continue
            over(f'{loc0}.{k}', d.get(k, ''), lim)
        for k in MODULES[m]['required']:
            if not str(d.get(k, '')).strip():
                errs.append(f'{loc0}.{k}: campo obligatorio ausente o vacío')
        if d.get('image'):
            _check_image_fields(d, m, loc0, errs)
        for sk_, sv in spec.items():
            if not sk_.startswith('_') or sk_ == '_desc_by_count':
                continue
            fn_ = SPEC_VALIDATORS.get(sk_)
            if fn_ is None:
                continue
            if sk_ == '_list':
                fn_(sv, d, m, loc0, over, errs, spec=spec)
            else:
                fn_(sv, d, m, loc0, over, errs)
        mv = MODULE_VALIDATORS.get(m)
        if mv:
            mv(d, m, loc0, over, errs)
        fit_fn = MODULES[m]['fit']
        if fit_fn:
            for fld, bw, bh, fsz in fit_fn(d):
                need = est_height(d.get(fld, ''), bw, fsz)
                if need > bh * 1.06:
                    errs.append(f'{loc0}.{fld}: desborde estimado ({need:.2f}in > {bh}in) — acortar texto')
        walk_markers(d, loc0)
        walk_lang(d, loc0)
    return errs


def _apply_fonts(pal_key):
    """Tipografía por tema; idempotente. Se aplica ANTES del lint (est_height) y en render."""
    global FONT_TITLE, FONT_BODY
    if pal_key == 'ucp':
        FONT_TITLE = FONT_BODY = "Montserrat"
    else:
        FONT_TITLE, FONT_BODY = "Georgia", "Calibri"




# ===================== PIPELINE DE RENDER =====================

import hashlib as _hashlib
import importlib.util


def _self_hash():
    return _hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()


def _load_slides(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f'manifest no encontrado: {path}')
    spec_ = importlib.util.spec_from_file_location('sd_manifest', os.path.abspath(path))
    mod = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(mod)
    slides = getattr(mod, 'SLIDES', None)
    if not isinstance(slides, list) or not slides:
        raise ValueError('SLIDES vacío o ausente en el manifest')
    return mod, slides


def _get_lang(mod):
    return str((getattr(mod, 'CONFIG', {}) or {}).get('LANG', 'es-ES'))


def _get_pal_key(mod):
    return str((getattr(mod, 'CONFIG', {}) or {}).get('PALETTE', 'ucp')).lower()


def _render(mod, out):
    """Renderiza y devuelve (n_slides, fallos_de_contraste). El CALLER decide si
    el archivo sobrevive: con violaciones de contraste NO se entrega el deck."""
    info = getattr(mod, 'COURSE_INFO', {})
    config = getattr(mod, 'CONFIG', {})
    slides = getattr(mod, 'SLIDES', [])
    set_lang(config.get('LANG', 'es-ES'))
    pal_key = str(config.get('PALETTE', 'ucp')).lower()
    pal = PALETTES.get(pal_key, PALETTES['ucp'])
    _apply_fonts(pal_key)   # Montserrat 100% bajo ucp; Georgia/Calibri si no
    _set_tokens(pal_key)

    prs = Presentation()
    prs.slide_width = Inches(CANVAS_W)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    for i, d in enumerate(slides, start=1):
        mname = d.get('module')
        if mname not in MODULES:
            raise KeyError(f"módulo desconocido {mname!r} (slide {i}) — "
                           f"ejecute `schema` para el listado válido")
        _CTX["slide"], _CTX["module"] = i, mname
        s = prs.slides.add_slide(blank)
        _SURFACE_STACK.clear()
        bg(s, pal)
        if mname not in _NO_HEADER_MODULES:
            header(s, pal, d, i)
            footer(s, pal, i, info.get('course', ''), config)
        MODULES[mname]['render'](s, d, pal, info)
    fails = _contrast_failures()
    prs.save(out)
    return len(slides), fails


def _fixture_image():
    """Imagen determinista para el fixture (cumple el contrato: jpg, >=20 KB,
    >=300 px). Se genera una vez por proceso en temp."""
    from PIL import Image as _PILImage
    p = os.path.join(_tf.gettempdir(), 'omc_fixture_img.jpg')
    if os.path.exists(p):
        return p
    im = _PILImage.new('RGB', (800, 600))
    px = im.load()
    for y in range(0, 600, 4):
        for x in range(0, 800, 4):
            c = ((x * 7 + y * 13) % 256)
            for dy in range(4):
                for dx in range(4):
                    px[min(x + dx, 799), min(y + dy, 599)] = (c, (c * 3) % 256, (c * 7) % 256)
    im.save(p, 'JPEG', quality=88, optimize=True)
    return p

def _self_test_slides():
    """Manifest sintético compartido por self-test y matriz de contraste.
    v9.A: cubre LOS 35 MÓDULOS — la matriz de contraste debe ejercitar toda
    combinación token/superficie real (pills, medallones, paneles de acento),
    no solo 5 módulos. Lección del bug on_success bajo ucp (3.1:1 invisible)."""
    img = None
    try:
        img = _fixture_image()
    except Exception:
        img = None  # sin Pillow el fixture cae a módulos sin imagen
    S = [
        {'module': 'title', 'course': 'check', 'title': 'dry-run',
         'subtitle': '', 'institution': ''},
        {'module': 'section_divider', 'section_title': 'Sección uno'},
        {'module': 'definition', 'kicker': 'k', 'title': 't',
         'main_statement': 'Enunciado central de prueba del motor.',
         'key_points': [{'title': 'a', 'desc': 'desc a'}, {'title': 'b', 'desc': 'desc b'}]},
        {'module': 'flow_diagram', 'kicker': 'k', 'title': 't',
         'steps': [{'label': '1', 'title': 'fase 1', 'desc': 'desc a'},
                   {'label': '2', 'title': 'fase 2', 'desc': 'desc b', 'highlight': True},
                   {'label': '3', 'title': 'fase 3', 'desc': 'desc c'}]},
        {'module': 'comparison_table', 'kicker': 'k', 'title': 't',
         'headers': ['a', 'b', 'c'],
         'rows': [['1', '2', '3'], ['1', '2', '3'], ['1', '2', '3']],
         'col_widths': [1, 2, 3]},
        {'module': 'synthesis_grid', 'kicker': 'k', 'title': 't',
         'headers': ['a', 'b', 'c'],
         'matrix_data': [['1', '2', '3'], ['4', '5', '6'], ['7', '8', '9']]},
        {'module': 'stat_card', 'kicker': 'k', 'title': 't',
         'stat_num': '42%', 'stat_title': 'Resultado principal del estudio de prueba',
         'narrative_blocks': [{'title': 'b1', 'desc': 'd1'}, {'title': 'b2', 'desc': 'd2'}]},
        {'module': 'checklist', 'kicker': 'k', 'title': 't',
         'items': [{'label': 'paso uno'}, {'label': 'paso dos', 'checked': False},
                   {'label': 'paso tres'}]},
        {'module': 'fixed_schema_card', 'kicker': 'k', 'title': 't',
         'fields': [{'label': 'campo', 'value': 'valor'}, {'label': 'otro', 'value': 'dato'}]},
        {'module': 'side_by_side', 'kicker': 'k', 'title': 't',
         'left_card': {'header': 'A', 'title': 'lado A',
                       'points': ['p1', 'p2', 'p3']},
         'right_card': {'header': 'B', 'title': 'lado B',
                        'points': ['q1', 'q2', 'q3']}},
        {'module': 'taxonomy_tree', 'kicker': 'k', 'title': 't', 'root': 'raiz',
         'categories': [{'name': 'cat1', 'property': 'prop', 'examples': ['e1']},
                        {'name': 'cat2', 'property': 'prop', 'examples': ['e2']}]},
        {'module': 'algorithm', 'kicker': 'k', 'title': 't',
         'steps': [{'title': 'paso 1'}, {'title': 'paso 2', 'highlight': True},
                   {'title': 'paso 3'}]},
        {'module': 'case_block', 'kicker': 'k', 'title': 't',
         'case_stem': 'Paciente de prueba con datos suficientes para el caso.',
         'findings': ['hallazgo uno', 'hallazgo dos'],
         'reasoning': 'Razonamiento diagnóstico de prueba del módulo.',
         'diagnosis': 'Diagnóstico', 'clinical_pearl': 'Perla de prueba del módulo.'},
        {'module': 'timeline', 'kicker': 'k', 'title': 't',
         'milestones': [{'label': str(i), 'title': 'Hito ' + str(i), 'desc': 'desc'}
                        for i in range(1, 6)]},
        {'module': 'cycle_diagram', 'kicker': 'k', 'title': 't', 'center_label': 'ciclo',
         'nodes': [{'title': 'n' + str(i)} for i in range(1, 5)]},
        {'module': 'quadrant_matrix', 'kicker': 'k', 'title': 't',
         'x_label': 'eje x', 'y_label': 'eje y',
         'quadrants': [{'title': 'q' + str(i), 'points': ['p1', 'p2']} for i in range(1, 5)]},
        {'module': 'pyramid', 'kicker': 'k', 'title': 't',
         'levels': [{'title': 'nivel ' + str(i)} for i in range(1, 4)]},
        {'module': 'quote_block', 'kicker': 'k', 'title': 't',
         'quote': 'Cita de prueba del motor.', 'author': 'Autor'},
        {'module': 'socratic_question', 'kicker': 'k', 'title': 't',
         'question': 'Pregunta tutorial de prueba?',
         'scaffold': ['razonamiento uno', 'razonamiento dos']},
        {'module': 'oxford_union', 'kicker': 'k', 'title': 't',
         'motion': 'motion de prueba',
         'pro_card': {'title': 'pro', 'points': ['p1', 'p2']},
         'con_card': {'title': 'con', 'points': ['c1', 'c2']},
         'verdict': 'veredicto de prueba'},
        {'module': 'evidence_card', 'kicker': 'k', 'title': 't',
         'study_name': 'Estudio Prueba', 'design': 'rct',
         'population': 'pacientes adultos', 'intervention': 'fármaco X',
         'comparison': 'placebo', 'outcome': 'evento Y',
         'effect': 'HR 0.75', 'credit': 'Revista 2024'},
        {'module': 'viva_question', 'kicker': 'k', 'title': 't',
         'prompt': 'Pregunta de viva voce de prueba.',
         'model_answer': 'Respuesta modelo de prueba.',
         'examiner_note': 'Nota del examinador de prueba.'},
        {'module': 'mnemonic_card', 'kicker': 'k', 'title': 't',
         'acronym': 'ABC', 'expansion': ['alfa', 'beta', 'gamma'],
         'usage': 'Uso clínico de la regla mnemotécnica de prueba.'},
        {'module': 'etymology', 'kicker': 'k', 'title': 't', 'term': 'Apendicitis',
         'fragments': ['Apendic', 'itis'],
         'roots': [{'part': 'Apendic', 'origin': 'latin', 'meaning': 'apéndice'},
                   {'part': 'itis', 'origin': 'greek', 'meaning': 'inflamación'}],
         'modern': 'Inflamación del apéndice.'},
        {'module': 'venn_diagram', 'kicker': 'k', 'title': 't',
         'sets': [{'label': 'A', 'items': ['a1', 'a2']},
                  {'label': 'B', 'items': ['b1', 'b2']},
                  {'label': 'C', 'items': ['c1', 'c2']}],
         'shared': ['común']},
        {'module': 'chart_data', 'kicker': 'k', 'title': 't', 'chart_type': 'bar',
         'categories': ['c1', 'c2'],
         'series': [{'name': 's1', 'values': [1.0, 2.0]}],
         'insights': ['lectura de prueba uno', 'lectura de prueba dos']},
        {'module': 'references', 'kicker': 'k', 'title': 't',
         'refs': ['Autor A. Título de prueba. 2024.', 'Autor B. Otro título. 2023.'] +
                 ['Autor C. Referencia extra. 2022.']},
        {'module': 'learning_objectives', 'kicker': 'k', 'title': 't',
         'objectives': [
             {'verb': 'Explicar', 'text': 'la fisiopatología de la fase aguda y su manejo',
              'bloom': 'understand'},
             {'verb': 'Aplicar', 'text': 'el algoritmo de decisión en cada caso',
              'bloom': 'apply'},
             {'verb': 'Analizar', 'text': 'los hallazgos de los estudios citados',
              'bloom': 'analyze'}]},
        {'module': 'colloquy', 'kicker': 'k', 'title': 't',
         'turns': [{'speaker': 'tutor', 'text': 'turno del tutor de prueba'},
                   {'speaker': 'student', 'text': 'respuesta del estudiante'},
                   {'speaker': 'tutor', 'text': 'replica del tutor'},
                   {'speaker': 'student', 'text': 'contrarespuesta'}]},
        {'module': 'annotated_passage', 'kicker': 'k', 'title': 't',
         'passage': 'Fragmento de fuente primaria [1] con nota al margen [2].',
         'source': 'Fuente, 1900',
         'annotations': [{'ref': '1', 'note': 'nota uno'},
                         {'ref': '2', 'note': 'nota dos'}]},
        {'module': 'concept_map', 'kicker': 'k', 'title': 't', 'hub': 'concepto',
         'nodes': [{'title': 'satelite ' + str(i)} for i in range(1, 5)]},
        {'module': 'glossary', 'kicker': 'k', 'title': 't',
         'terms': [{'term': 'Fase aguda', 'def': 'Periodo inicial de mayor riesgo y demanda'},
                   {'term': 'Algoritmo', 'def': 'Secuencia de pasos con decisión'},
                   {'term': 'Caso índice', 'def': 'Primer caso que motiva el estudio'},
                   {'term': 'Perla clínica', 'def': 'Consejo de alto rendimiento'}]},
        # further_reading con tags success Y alert: ejercita on_success/on_alert
        # sobre fills de color medio (el par exacto del bug ucp 3.1:1).
        {'module': 'further_reading', 'kicker': 'k', 'title': 't',
         'entries': [{'tag': 'esencial', 'title': 'Lectura básica', 'note': 'nota'},
                     {'tag': 'avanzado', 'title': 'Lectura avanzada', 'note': 'nota'},
                     {'tag': 'complementario', 'title': 'Lectura media', 'note': 'nota'}]},
    ]
    if img:
        S.append({'module': 'figure', 'kicker': 'k', 'title': 't', 'image': img,
                  'caption': 'Microfotografía de prueba del fixture del motor.',
                  'credit': 'Motor 2026'})
        S.append({'module': 'authority_card', 'kicker': 'k', 'title': 't', 'image': img,
                  'caption': 'Retrato institucional de prueba del fixture.',
                  'credit': 'Motor 2026',
                  'name': 'Autor de Prueba', 'bio': 'Biografía breve de prueba del fixture.',
                  'legacy': 'Legado de prueba'})
    present = {s['module'] for s in S}
    missing = set(MODULES) - present
    if missing:
        # Nunca debe pasar: si un módulo nuevo no tiene fixture, fallar ruidoso.
        raise AssertionError(f'fixture self-test incompleto, faltan: {sorted(missing)}')
    return S



_ERR_RE = _re.compile(r'^slide (\d+) \[(\w+)\](?:\.([^:]+))?: (.*)$', _re.S)

def errs_to_json(errs, slides=None, profile=None, lang='es-ES'):
    """Machine-readable lint report for self-correcting agents."""
    items = []
    for e in errs:
        m = _ERR_RE.match(e)
        if m:
            items.append({'scope': 'slide', 'slide': int(m.group(1)), 'module': m.group(2),
                          'field': (m.group(3) or '').strip() or None, 'message': m.group(4).strip(),
                          'raw': e})
        else:
            head = e.split(':', 1)[0].strip()
            items.append({'scope': 'ledger' if head.startswith('ledger') else 'deck',
                          'slide': None, 'module': None, 'field': None,
                          'message': e.split(':', 1)[-1].strip(), 'raw': e})
    by_slide = {}
    for it in items:
        if it['slide']:
            by_slide[it['slide']] = by_slide.get(it['slide'], 0) + 1
    return {'kit': KIT_VERSION, 'status': 'PASS' if not errs else 'FAIL',
            'lang': lang, 'profile': profile,
            'slides': len(slides) if slides is not None else None,
            'error_count': len(errs), 'errors': items,
            'slides_with_errors': sorted(by_slide),
            'hint': 'Corrija sólo los campos listados; ejecute `schema <module>` para el contrato.'}



_PLACE = '<= {} car.>'

def _skel_field(lim):
    return _PLACE.format(lim)

def _module_skeleton(m):
    """Paste-ready minimal dict that satisfies the contract for module m.
    v9.6/C3: consume MODULES (no B directo) — el registro es la única vía."""
    spec = MODULES[m]['schema']
    d = {'module': m}
    if m not in _NO_HEADER_MODULES:
        d['kicker'] = _skel_field(COMMON['kicker'])
        d['title'] = _skel_field(COMMON['title'])
    for k, v in spec.items():
        if k.startswith('_'):
            continue
        d[k] = _skel_field(v) if isinstance(v, int) else v
    if m in ('figure', 'authority_card') or 'image' in MODULES[m]['required']:
        d['image'] = 'work/imgs/nombre_snake_case.jpg'
    if '_list' in spec:
        key, lo, hi, fl = spec['_list']
        d[key] = [{fk: _skel_field(fv) for fk, fv in fl.items()} for _ in range(lo)]
        if '_examples' in spec:
            mx, lim = spec['_examples']
            for it in d[key]:
                it['examples'] = [_skel_field(lim)] * min(mx, 2)
    if '_strlist' in spec:
        key, lo, hi, lim = spec['_strlist']
        d[key] = [_skel_field(lim)] * lo
    if '_table' in spec:
        key, rlo, rhi, clo, chi, lim = spec['_table']
        d['headers'] = [_skel_field(lim)] * clo
        d['col_widths'] = [2.0] * clo
        d[key] = [[_skel_field(lim)] * clo for _ in range(rlo)]
    # v9.B/F7: _cards y _debate comparten forma
    for spec_key, sides in (('_cards', ('left_card', 'right_card')),
                            ('_debate', ('pro_card', 'con_card'))):
        if spec_key in spec:
            fl, plo, phi, plim = spec[spec_key]
            for side in sides:
                d[side] = {fk: _skel_field(fv) for fk, fv in fl.items()}
                d[side]['points'] = [_skel_field(plim)] * plo
    if '_quads' in spec:
        tlim, plo, phi, plim = spec['_quads']
        d['quadrants'] = [{'title': _skel_field(tlim),
                           'points': [_skel_field(plim)] * plo} for _ in range(4)]
    if '_venn' in spec:
        flab, slo, shi, ilim, hlo, hhi, hlim = spec['_venn']
        d['sets'] = [{'label': _skel_field(flab), 'items': [_skel_field(ilim)] * slo}
                     for _ in range(2)]
        d['shared'] = [_skel_field(hlim)] * hlo
    if '_chart' in spec:
        clo, chi, snlo, snhi, snlim, inlo, inhi, inlim, catlim = spec['_chart']
        d['chart_type'] = 'bar'
        d['categories'] = [_skel_field(catlim)] * clo
        d['series'] = [{'name': _skel_field(snlim), 'values': [0.0] * clo} for _ in range(snlo)]
        d['insights'] = [_skel_field(inlim)] * inlo
    if '_acronym' in spec:
        key, lim = spec['_acronym']
        d['acronym'] = 'ABC'
        d[key] = [_skel_field(lim)] * 3
    if '_objectives' in spec:
        lo, hi, vlim, tlim = spec['_objectives']
        d['objectives'] = [{'verb': _skel_field(vlim), 'text': _skel_field(tlim),
                            'bloom': 'understand'} for _ in range(lo)]
    if '_colloquy' in spec:
        lo, hi, tlim = spec['_colloquy']
        d['turns'] = [{'speaker': 'tutor' if i % 2 == 0 else 'student',
                       'text': _skel_field(tlim)} for i in range(lo)]
    if '_highlight' in spec:
        key, lo, hi = spec['_highlight']
        if lo >= 1 and isinstance(d.get(key), list) and d[key]:
            d[key][0]['highlight'] = True
    if m == 'etymology':
        d['term'] = 'Apendicitis'
        d['fragments'] = ['Apendic', 'itis']
    if m not in _NO_HEADER_MODULES:
        d.setdefault('footnote', _skel_field(COMMON['footnote']))
    return d

def _fmt_constraints(m):
    spec = MODULES[m]['schema']  # v9.6/C3: vía única de acceso
    out = []
    spec_m = MODULES[m]
    req = spec_m['required']
    if req:
        out.append(f'  obligatorios (no vacíos): {", ".join(req)}')
    for k, v in spec.items():
        if not k.startswith('_'):
            out.append(f'  {k}: máx {v} car.')
    if m not in _NO_HEADER_MODULES:
        out.append(f'  kicker: máx {COMMON["kicker"]} car. · title: máx {COMMON["title"]} car. '
                   f'· footnote: máx {COMMON["footnote"]} car. (opcional)')
    if '_list' in spec:
        key, lo, hi, fl = spec['_list']
        flds = ' · '.join(f'{a}: máx {b}' for a, b in fl.items())
        out.append(f'  {key}: lista de {lo}-{hi} dicts [{flds}]')
    if '_desc_by_count' in spec:
        key, table = spec['_desc_by_count']
        out.append(f'  {key}.desc: el límite varía con el número de ítems -> ' +
                   ', '.join(f'{n} ítems = {lim} car.' for n, lim in table.items()))
    if '_strlist' in spec:
        key, lo, hi, lim = spec['_strlist']
        out.append(f'  {key}: lista de {lo}-{hi} strings, máx {lim} car. c/u')
    if '_table' in spec:
        key, rlo, rhi, clo, chi, lim = spec['_table']
        out.append(f'  headers: {clo}-{chi} columnas · {key}: {rlo}-{rhi} filas x '
                   f'len(headers) celdas, máx {lim} car. c/u · col_widths: '
                   f'un peso numérico > 0 por encabezado')
    # v9.B/F7: _cards y _debate comparten forma
    for spec_key, sides in (('_cards', ('left_card', 'right_card')),
                            ('_debate', ('pro_card', 'con_card'))):
        if spec_key in spec:
            fl, plo, phi, plim = spec[spec_key]
            out.append(f'  {" / ".join(sides)}: {" · ".join(f"{a}: máx {b}" for a, b in fl.items())}'
                       f' + points: {plo}-{phi} strings de máx {plim} car.')
    if '_quads' in spec:
        tlim, plo, phi, plim = spec['_quads']
        out.append(f'  quadrants: EXACTAMENTE 4 dicts [title: máx {tlim}] + points: '
                   f'{plo}-{phi} strings de máx {plim} car.')
    if '_venn' in spec:
        flab, slo, shi, ilim, hlo, hhi, hlim = spec['_venn']
        out.append(f'  sets: 2-3 dicts [label: máx {flab}, items: {slo}-{shi} de máx {ilim}] · '
                   f'shared: {hlo}-{hhi} strings de máx {hlim}')
    if '_chart' in spec:
        clo, chi, snlo, snhi, snlim, inlo, inhi, inlim, catlim = spec['_chart']
        out.append(f'  categories: {clo}-{chi} (máx {catlim} car.) · series: {snlo}-{snhi} '
                   f'[name máx {snlim}, values numéricos = len(categories)] · '
                   f'insights: {inlo}-{inhi} de máx {inlim}')
    if '_acronym' in spec:
        key, lim = spec['_acronym']
        out.append(f'  {key}: un término (máx {lim} car.) POR CADA letra de acronym')
    if '_examples' in spec:
        mx, lim = spec['_examples']
        out.append(f'  categories[].examples: máx {mx} strings de máx {lim} car.')
    if '_highlight' in spec:
        key, lo, hi = spec['_highlight']
        out.append(f'  {key}[].highlight: entre {lo} y {hi} ítems con highlight=True')
    if '_decision_flow' in spec:
        mx, dlim = spec['_decision_flow']
        out.append(f'  steps[].decision: máx {mx} decisiones; desc de un paso decision = '
                   f'etiqueta de rama NO (máx {dlim} car.); incompatible con explanation')
    if '_objectives' in spec:
        lo, hi, vlim, tlim = spec['_objectives']
        out.append(f'  objectives: {lo}-{hi} dicts [verb: máx {vlim}, text: máx {tlim}, '
                   f'bloom: {"|".join(_BLOOM_VERBS)}]')
    if '_colloquy' in spec:
        lo, hi, tlim = spec['_colloquy']
        out.append(f'  turns: {lo}-{hi} dicts [speaker: tutor|student, text: máx {tlim}]')
    fit = spec_m['fit']
    if fit:
        try:
            flds = fit({})
            out.append('  ajuste tipográfico verificado (desborde bloquea el build): ' +
                       ', '.join(f'{f} en caja {w}x{h} in @ {p} pt' for f, w, h, p in flds))
        except Exception:
            pass
    if MODULES[m]['gotcha']:
        out.append(f'  AVISO: {spec_m["gotcha"]}')
    return '\n'.join(out)

def cmd_schema(module=None):
    """Publish the authoring contract: fields, cardinalities, budgets, skeleton, tokens."""
    if module in (None, 'all', '--all'):
        print(f'{KIT_VERSION} — contrato de autoría')
        print(f'\nMódulos núcleo (obligatorios en todo deck): {", ".join(CORE_MODULES)}')
        print(f'Variedad mínima: {MIN_DISTINCT} módulos distintos '
              f'({MIN_DISTINCT_FULL} si el deck tiene >= {FULL_DECK_THRESHOLD} diapositivas)')
        print('Perfiles (CONFIG["PROFILE"]): ' + ' · '.join(
            f'{k}: {v["slides"][0]}-{v["slides"][1]} slides, >={v["distinct"]} módulos, '
            f'{v["figures"][0]}-{v["figures"][1]} figuras' for k, v in PROFILES.items()))
        print(f'Figuras: máx 10 diapositivas con imagen · jpg/jpeg/png · 20 KB-4 MB · >= 300 px')
        print(f'Comunes a todo módulo: kicker <= {COMMON["kicker"]} · title <= {COMMON["title"]} '
              f'· footnote <= {COMMON["footnote"]}')
        print('\nTokens de contraste por tema (texto; los hex de marca quedan para gráfica):')
        hdr = f'  {"tema":<10}{"on_primary":<12}{"on_prm_soft":<12}{"on_accent":<11}{"ink_accent":<11}{"ink_success":<12}{"subtitle":<9}'
        print(hdr)
        for key, P in PALETTES.items():
            t = derive_tokens(key, P)
            print(f'  {key:<10}{t["on_primary"]:<12}{t["on_primary_soft"]:<12}'
                  f'{t["on_accent"]:<11}{t["ink_accent"]:<11}{t["ink_success"]:<12}'
                  f'{t["subtitle_on_primary"]:<9}')
        print('  Override fino: PALETTE_OVERRIDES = {<tema>: {<token>: "RRGGBB"}} en el kit.')
        print('\nREGLAS DE ESTRUCTURA DEL LEDGER (work/atu_ledger.md):')
        print('  · UNA sección `##` por cada section_divider del manifest, en el mismo orden.')
        print('  · refs por #ancla (columna Slide); cada ATU debe ser desarrollado por >=1')
        print('    slide con "atu": N; source_quote verbatim en columna 4 (recomendado).')
        print('\nMódulos disponibles ({}):'.format(len(dispatch_map)))
        for name in sorted(dispatch_map):
            tag = 'núcleo   ' if name in CORE_MODULES else ('opcional ' if name in OPTIONAL_MODULES else 'clásico  ')
            print(f'  [{tag}] {name}')
        print('\nUso: python3 uploads/omc_kit.py schema <módulo>   # contrato + esqueleto pegable')
        return 0
    if module not in dispatch_map:
        import difflib
        near = difflib.get_close_matches(module, list(dispatch_map), n=3)
        print(f"Módulo desconocido: {module!r}" + (f' — ¿quiso decir {", ".join(near)}?' if near else ''))
        print('Ejecute: python3 uploads/omc_kit.py schema   (para el listado completo)')
        return 2
    print(f'{KIT_VERSION} — módulo: {module}')
    print('\nCONTRATO:')
    print(_fmt_constraints(module))
    print('\nESQUELETO (copiar al manifest y sustituir los marcadores):')
    import pprint as _pp
    print(_pp.pformat(_module_skeleton(module), width=98, sort_dicts=False))
    print('\nRecordatorio: los límites son de CARACTERES (con espacios y tildes). '
          'Redacte al 90% del límite para absorber correcciones.')
    return 0




# ===================== SELF-TEST =====================

def _synthetic_manifest(pal_key):
    return _types.SimpleNamespace(
        COURSE_INFO={'course': 'STUDYDECK CHECK'},
        CONFIG={'PALETTE': pal_key},
        SLIDES=_self_test_slides())


def _contrast_scan(modlike):
    """Renderiza un manifest y devuelve las violaciones de contraste."""
    out = os.path.join(_tf.gettempdir(), f'sd_scan_{os.getpid()}.pptx')
    try:
        _CONTRAST_LOG.clear()
        _n, fails = _render(modlike, out)
        return fails
    except Exception as e:
        return [{'error': f'scan falló: {e}'}]
    finally:
        try:
            if os.path.exists(out):
                os.remove(out)
        except OSError:
            pass


def _self_test():
    """Fixture de LOS 35 módulos x 5 paletas + suite FP de drift + lint del fixture.
    Lección central del ciclo v9: el gate solo protege lo que el fixture ejercita."""
    ok = True
    total = 0
    print('[StudyDeck Self-test] Matriz de contraste (35 módulos x 5 paletas):')
    for key in PALETTES:
        fails = _contrast_scan(_synthetic_manifest(key))
        total += len(fails)
        print(f'  [{key:<9}] ' + ('PASS' if not fails else f'FAIL ({len(fails)})'))
        for cf in fails[:4]:
            if 'error' in cf:
                print(f'      ERROR: {cf["error"]}')
                ok = False
            else:
                print(f"      slide {cf.get('slide')} [{cf.get('module')}]: "
                      f"#{cf.get('fg')} sobre #{cf.get('bg')} = {cf.get('ratio')} "
                      f"< {cf.get('required')}")
    cases = [
        # (idioma declarado, texto, esperado-bloquea)
        ('es-ES', 'las modalidades y velocidades del tratamiento', False),  # FP conocido
        ('es-ES', 'ciudades y oportunidades de formación', False),          # FP conocido
        ('es-ES', 'a nacionalidade e cidadania brasileira', True),          # pt real (-dade)
        ('es-ES', 'coração e feijões', True),                               # chars pt
        ('es-ES', 'el exame y la necrose fueron registradas', True),        # léxico pt
        ('es-ES', 'la necrosis en el examen muestra apoptosis', False),     # español legítimo
        ('pt-BR', 'la inflamación y sus complicaciones', False),            # pt declarado: sin guard
        ('en-US', 'der Straßenverkehr und die Überwachung', False),         # en declarado: sin guard
    ]
    bad = [f'[{lg}] {tx!r} -> {"bloquea" if got else "pasa"} (esperado {"bloquea" if exp else "pasa"})'
           for lg, tx, exp in cases
           for got in [bool(_drift_hits(tx, lg))] if got != exp]
    if bad:
        ok = False
        print('  [SELF-TEST] Regresión de drift:')
        for b in bad:
            print('    X ' + b)
    else:
        print(f'  drift: {len(cases)} casos OK (FP + infiltración + sin-guard)')
    errs = check(_self_test_slides(), 'es-ES')
    if errs:
        ok = False
        print('  [SELF-TEST] lint del fixture sintético:')
        for e in errs[:10]:
            print('    X ' + e)
    else:
        print('  lint fixture: PASS (0 errores)')
    if ok and total == 0:
        print('[StudyDeck Self-test] PASS — motor validado.')
        return 0
    print(f'[StudyDeck Self-test] FAIL ({total} violaciones de contraste).')
    return 1


def cmd_check():
    print(f'{VERSION}')
    print(f'sha256: {_self_hash()}')
    return _self_test()




# ===================== COMANDOS =====================

# Guías ADVISORY (sustituyen a los perfiles coercitivos del kit viejo).
GUIDES = {
    'lecture': {'length': '18-30 slides', 'hint':
        'abre con learning_objectives si el source enumera metas; un section_divider '
        'por bloque temático; proceso->flow_diagram/cycle_diagram; comparación->'
        'comparison_table/side_by_side; evolución->timeline; cierra con case_block o '
        'viva_question + further_reading'},
    'short': {'length': '8-14 slides', 'hint':
        'definition+figure temprano; un bloque central según la forma del source '
        '(flow|table|timeline|case); cierra con checklist o further_reading'},
    'custom': {'length': 'libre', 'hint':
        'elige cada módulo por su `when`; title + section_divider bastan de base'},
}


def cmd_schema(module=None):
    """Contrato de autoría: menú context-aware (`when`), contrato por módulo,
    esqueleto pegable y tokens de contraste."""
    if module in (None, 'all', '--all'):
        print(f'{VERSION} — contrato de autoría')
        print('\nElección CONTEXT-AWARE: cada módulo dice CUÁNDO usarlo. Matchea la '
              'forma del contenido del source; no sigas recetas cerradas.\n')
        for name in sorted(MODULES):
            print(f'  [{MODULES[name]["tier"]:<9}] {name}: {MODULES[name]["when"]}')
        print('\nGuías (advisory, no coercitivas):')
        for g, v in GUIDES.items():
            print(f'  {g} ({v["length"]}):\n    {v["hint"]}')
        print('\nPor módulo: schema <módulo>   ·   Tokens WCAG: schema tokens')
        return 0
    if module == 'tokens':
        hdr = (f'  {"tema":<10}{"on_primary":<12}{"on_prm_soft":<12}{"on_accent":<11}'
               f'{"ink_accent":<11}{"ink_success":<12}{"subtitle":<9}')
        print(hdr)
        for key, P in PALETTES.items():
            t = derive_tokens(key, P)
            print(f'  {key:<10}{t["on_primary"]:<12}{t["on_primary_soft"]:<12}'
                  f'{t["on_accent"]:<11}{t["ink_accent"]:<11}{t["ink_success"]:<12}'
                  f'{t["subtitle_on_primary"]:<9}')
        print('\n  Override fino: PALETTE_OVERRIDES = {<tema>: {<token>: "RRGGBB"}}')
        return 0
    if module not in MODULES:
        import difflib
        near = difflib.get_close_matches(module, list(MODULES), n=3)
        print(f'Módulo desconocido: {module!r}'
              + (f' — ¿quiso decir {", ".join(near)}?' if near else ''))
        print('Ejecute: studydeck.py schema   (listado completo)')
        return 2
    spec = MODULES[module]
    print(f'{VERSION} — módulo: {module}')
    print(f'\nCUÁNDO USARLO: {spec["when"]}')
    print('\nCONTRATO:')
    print(_fmt_constraints(module))
    print('\nESQUELETO (pegar al manifest y sustituir los marcadores):')
    import pprint as _pp
    print(_pp.pformat(_module_skeleton(module), width=98, sort_dicts=False))
    print('\nLos límites son de CARACTERES (con espacios y tildes). Redacte al 90% '
          'del límite para absorber correcciones.')
    return 0


def cmd_new(profile='short', out='manifest.py', lang='es-ES', pal_key=None):
    """Scaffold MÍNIMO válido + guía advisory. No dicta estructura: compone el autor
    matcheando el `when` de cada módulo con su source."""
    import pprint as _pp
    pk = pal_key if pal_key in PALETTES else 'ucp'
    if os.path.exists(out):
        print(f'[StudyDeck New] FAIL — {out} ya existe (no se sobrescribe).')
        return 1
    guide = GUIDES.get(profile, GUIDES['custom'])
    examples = [_module_skeleton(m) for m in ('title', 'section_divider',
                                              'definition', 'checklist')]
    menu = '\n'.join(f'  {n}: {MODULES[n]["when"]}' for n in sorted(MODULES))
    L = [
        '# -*- coding: utf-8 -*-',
        f'"""Scaffold mínimo generado por {VERSION} — guía "{profile}" ({guide["length"]}).',
        '',
        'GUÍA (advisory): ' + guide['hint'],
        '',
        'MÓDULOS DISPONIBLES — elija por su CUÁNDO (context-aware):',
        menu,
        '',
        'Contrato por módulo: studydeck.py schema <módulo>.',
        'Redacte al 90% de cada límite de caracteres. Reemplace TODO marcador '
        '"<= N car.>". Los 4 slides iniciales son ejemplos válidos: edítelos, '
        'duplíquelos o borre según su deck."""',
        '',
        "COURSE_INFO = {'course': '<asignatura>', 'institution': '<institución>', 'author': ''}",
        f"CONFIG = {{'PALETTE': '{pk}', 'LANG': '{lang}', 'PROFILE': '{profile}', "
        f"'SHOW_FOOTER': True, 'SHOW_SLIDE_NUMBER': True}}",
        '',
        'SLIDES = [',
    ]
    for ex in examples:
        L.append(_pp.pformat(ex, width=96, sort_dicts=False) + ',')
    L.append(']')
    open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print(f'[StudyDeck New] Scaffold escrito: {out} (guía "{profile}": {guide["length"]})')
    print('[StudyDeck New] Siguiente: componga SLIDES matcheando `when` con su source · '
          'lint · all')
    return 0


def cmd_lint(path, as_json=False):
    try:
        mod, slides = _load_slides(path)
    except Exception as e:
        if as_json:
            print(_json.dumps({'kit': VERSION, 'status': 'FAIL', 'error_count': 1,
                               'errors': [{'scope': 'manifest', 'message': str(e),
                                           'raw': str(e)}]},
                              ensure_ascii=False, indent=2))
        else:
            print(f'[StudyDeck Lint] FAIL — {e}')
        return 1
    _apply_fonts(_get_pal_key(mod))   # est_height consciente de fuente (Montserrat)
    lang = _get_lang(mod)
    errs = check(slides, lang)
    if as_json:
        print(_json.dumps(errs_to_json(errs, slides, lang=lang),
                          ensure_ascii=False, indent=2))
        return 1 if errs else 0
    if errs:
        print(f'[StudyDeck Lint] FAIL — {len(errs)} violación(es):')
        for e in errs:
            print('  X ' + e)
        return 1
    print(f'[StudyDeck Lint] PASS — {len(slides)} diapositivas cumplen el contrato '
          f'(idioma {lang}).')
    return 0


def cmd_build(path, out='deck.pptx'):
    try:
        mod, slides = _load_slides(path)
    except Exception as e:
        print(f'[StudyDeck Build] FAIL — {e}')
        return 1
    _apply_fonts(_get_pal_key(mod))
    errs = check(slides, _get_lang(mod))
    if errs:
        print(f'[StudyDeck Build] Cancelado (fail-fast): {len(errs)} violación(es):')
        for e in errs[:25]:
            print('  X ' + e)
        if len(errs) > 25:
            print(f'  ... y {len(errs) - 25} más (ejecute: lint {path})')
        return 1
    try:
        n, fails = _render(mod, out)
    except KeyError as e:
        print(f'[StudyDeck Build] FAIL — {e}')
        return 1
    if fails:
        try:
            os.remove(out)   # nunca entregar un deck que viola contraste
        except OSError:
            pass
        print(f'[StudyDeck Build] FAIL — {len(fails)} par(es) texto/superficie bajo '
              f'umbral WCAG (deck NO guardado):')
        for cf in fails[:20]:
            print(f"  X slide {cf.get('slide')} [{cf.get('module')}]: "
                  f"#{cf.get('fg')} sobre #{cf.get('bg')} = {cf.get('ratio')} "
                  f"(requiere {cf.get('required')})")
        return 1
    print(f'[StudyDeck Build] OK: {out} ({n} diapositivas · contraste 0 violaciones)')
    return 0


def cmd_all(path, out='deck.pptx'):
    print(f'[StudyDeck All] 1/2 — Lint: {path}')
    rc = cmd_lint(path)
    if rc != 0:
        print('[StudyDeck All] Lint FAIL — no se renderiza.')
        return rc
    print('[StudyDeck All] 2/2 — Build...')
    return cmd_build(path, out)


def cmd_contrast(manifest_path=None, as_json=False):
    """Sin manifest: matriz del fixture x 5 paletas. Con manifest: escaneo del deck."""
    if manifest_path:
        try:
            mod, slides = _load_slides(manifest_path)
        except Exception as e:
            print(f'[StudyDeck Contrast] FAIL — {e}')
            return 1
        fails = _contrast_scan(mod)
        if as_json:
            print(_json.dumps({'kit': VERSION, 'mode': 'manifest',
                               'status': 'PASS' if not fails else 'FAIL',
                               'error_count': len(fails), 'errors': fails},
                              ensure_ascii=False, indent=2))
            return 0 if not fails else 1
        if fails:
            print(f'[StudyDeck Contrast] FAIL — {len(fails)} par(es) bajo umbral:')
            for cf in fails:
                print(f"  X slide {cf.get('slide')} [{cf.get('module')}]: "
                      f"#{cf.get('fg')} sobre #{cf.get('bg')} = {cf.get('ratio')} "
                      f"< {cf.get('required')}")
            return 1
        print(f'[StudyDeck Contrast] PASS — 0 violaciones ({len(slides)} diapositivas).')
        return 0
    total = 0
    print('[StudyDeck Contrast] Matriz (fixture x 5 paletas):')
    for key in PALETTES:
        fails = _contrast_scan(_synthetic_manifest(key))
        total += len(fails)
        print(f'  [{"PASS" if not fails else "FAIL (" + str(len(fails)) + ")"}] {key}')
    print('[StudyDeck Contrast] ' + ('PASS — 0 violaciones en las 5 paletas.'
                                     if total == 0 else f'FAIL — {total} violación(es).'))
    return 0 if total == 0 else 1


# ---------------------------------------------------------------- ingest-lite
def _extract_source_text(path):
    """Texto plano del source (.pdf vía pypdf; .txt/.md directo)."""
    ext = str(path).lower().rsplit('.', 1)[-1]
    if ext in ('txt', 'md'):
        return open(path, encoding='utf-8', errors='replace').read()
    if ext == 'pdf':
        try:
            from pypdf import PdfReader
        except ImportError:
            raise SystemExit('[StudyDeck Ingest] Falta pypdf: uv pip install pypdf')
        reader = PdfReader(path)
        return '\n'.join((pg.extract_text() or '') for pg in reader.pages)
    raise SystemExit(f'[StudyDeck Ingest] Formato .{ext} no soportado (pdf/txt/md)')


def _is_heading(line):
    """Línea-título numerada corta sin punto final (lección H1: excluye miles
    '2.345 pacientes'). Title Case se descartó por falsos positivos (H5)."""
    numbered = _re.match(r'^\d{1,2}(\.\d{1,3})*[\.)]?\s+\S', line) is not None \
        and not _re.match(r'^\d{1,2}\.\d{3}\s', line)
    return numbered and len(line) <= 80 and not line.rstrip().endswith('.')


def cmd_ingest(source_path, out_dir='work'):
    """Conveniencia, no contrato: outline del source para autorar. La autoría
    matchea cada sección con el `when` de los módulos."""
    if not os.path.exists(source_path):
        print(f'[StudyDeck Ingest] FAIL — source no encontrado: {source_path}')
        return 1
    text = _extract_source_text(source_path)
    os.makedirs(out_dir, exist_ok=True)
    L = [f'# OUTLINE — {source_path}', '']
    n_para = 0
    for raw in text.splitlines():
        line_ = raw.strip()
        if not line_:
            continue
        if _is_heading(line_):
            L.append(f'\n## {line_}')
        else:
            L.append(f'- {line_}')
            n_para += 1
    out_md = os.path.join(out_dir, 'outline.md')
    open(out_md, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print(f'[StudyDeck Ingest] OK — outline en {out_md} ({n_para} bloques de texto).')
    print('[StudyDeck Ingest] Autoría: matchee la forma de cada sección con el `when` '
          'de los módulos (schema all) y escriba el manifest.')
    return 0




# ===================== CLI =====================

def cli():
    argv = sys.argv[1:]
    as_json = '--json' in argv
    argv = [x for x in argv if x != '--json']
    if '--help' in argv or '-h' in argv or not argv:
        print(f"{VERSION}\n"
              f"Uso:\n"
              f"  check                            deps + self-test (35 módulos x 5 paletas)\n"
              f"  schema [módulo|all|tokens]       contrato + cuándo usarlo + esqueleto\n"
              f"  new [guia] [out.py]              scaffold mínimo + guía advisory\n"
              f"  ingest <source.pdf|txt|md>       outline del source para autorar\n"
              f"  lint <manifest.py> [--json]      contrato por slide\n"
              f"  build <manifest.py> [out.pptx]   lint fail-fast + render (contraste incluido)\n"
              f"  all <manifest.py> [out.pptx]     lint -> build\n"
              f"  contrast [manifest.py] [--json]  matriz 5 paletas o escaneo de un deck\n")
        return 0
    c = argv[0]
    if c == 'check':
        return cmd_check()
    if c == 'schema':
        return cmd_schema(argv[1] if len(argv) > 1 else None)
    if c == 'new':
        return cmd_new(argv[1] if len(argv) > 1 else 'short',
                       argv[2] if len(argv) > 2 else 'manifest.py')
    if c == 'ingest':
        if len(argv) < 2:
            print("[StudyDeck CLI] FAIL — 'ingest' requiere la ruta del source.")
            return 2
        return cmd_ingest(argv[1], argv[2] if len(argv) > 2 else 'work')
    if c == 'lint':
        if len(argv) < 2:
            print("[StudyDeck CLI] FAIL — 'lint' requiere la ruta del manifest.")
            return 2
        return cmd_lint(argv[1], as_json=as_json)
    if c == 'build':
        if len(argv) < 2:
            print("[StudyDeck CLI] FAIL — 'build' requiere la ruta del manifest.")
            return 2
        return cmd_build(argv[1], argv[2] if len(argv) > 2 else 'deck.pptx')
    if c == 'all':
        if len(argv) < 2:
            print("[StudyDeck CLI] FAIL — 'all' requiere la ruta del manifest.")
            return 2
        return cmd_all(argv[1], argv[2] if len(argv) > 2 else 'deck.pptx')
    if c == 'contrast':
        return cmd_contrast(argv[1] if len(argv) > 1 else None, as_json=as_json)
    print(f'[StudyDeck CLI] Comando desconocido: {c}')
    return 2


if __name__ == '__main__':
    sys.exit(cli() or 0)
