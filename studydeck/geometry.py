# -*- coding: utf-8 -*-
"""Lienzo, zona segura y reparto de tarjetas.

La asimetria 0.650 / 0.683 (borde derecho de facto 12.65) es historica y
CANONICA: no se "corrige" en silencio porque cambiaria la composicion de los
35 modulos calibrados contra ella.
"""

CANVAS_W, CANVAS_H = 13.333, 7.500
SAFE_X0, SAFE_Y0 = 0.650, 1.550
SAFE_X1 = CANVAS_W - SAFE_X0      # 12.683 (documental)
CONTENT_W = 12.0                  # de facto: 0.650 + 12.0 = borde 12.65
CONTENT_H = 5.05                  # banda de contenido SAFE_Y0 -> 6.60
FOOTER_Y = 6.98
CAPTION_MIN = 15


def content_top():
    """content_top: documented behavior of the module."""
    return SAFE_Y0


def stack_layout(y0, zone_h, n, gap, cap=None):
    """Alto de fila con tope + desplazamiento vertical para centrar el grupo."""
    n = max(n, 1)
    row_h = (zone_h - gap * (n - 1)) / n
    if cap:
        row_h = min(row_h, cap)
    return row_h, y0 + (zone_h - (row_h * n + gap * (n - 1))) / 2.0


def row_layout(x0, total_w, n, gap, center=False):
    """Hermano horizontal de stack_layout: ancho de item + x de inicio."""
    n = max(n, 1)
    item_w = min((total_w - gap * (n - 1)) / n, total_w)
    if center:
        item_w = min(1.35, item_w)
        x0 = x0 + (total_w - (item_w * n + gap * (n - 1))) / 2.0
    return item_w, x0