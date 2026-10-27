# -*- coding: utf-8 -*-
"""Tipografia UCP: Montserrat 100% (titular y cuerpo) + estimador de ajuste.

`est_height` aproxima el alto que ocupara un texto. No es un motor de layout:
es el tripwire que BLOQUEA el build cuando el texto no cabe en su caja. Se
ajusta el TEXTO, nunca el estimador.
"""

FONT_TITLE = 'Montserrat'
FONT_BODY = 'Montserrat'
FONTS = {'title': FONT_TITLE, 'body': FONT_BODY}

CHAR_W = {'Montserrat': 0.57}
CHAR_W_DEFAULT = 0.57


def font(role='body'):
    """font: documented behavior of the module."""
    return FONTS.get(role, FONT_BODY)


def est_height(text, box_w_in, size_pt, line_sp=1.34, sp_after=3, font_role='body'):
    """Alto estimado en pulgadas del texto dentro de una caja."""
    if not text:
        return 0.0
    per_pt = CHAR_W.get(font(font_role), CHAR_W_DEFAULT)
    char_w_in = per_pt * size_pt / 72.0
    usable = max(box_w_in - 0.30, 0.35)
    per_line = max(int(usable / char_w_in), 1)
    lines = 0
    for raw in str(text).split('\n'):
        lines += max(1, -(-len(raw) // per_line))
    return lines * (size_pt * line_sp) / 72.0 + sp_after / 72.0