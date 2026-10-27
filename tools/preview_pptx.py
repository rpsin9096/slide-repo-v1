# -*- coding: utf-8 -*-
"""Render aproximado de un .pptx a PNG/PDF, para revisar composición sin Office.

No es un visor fiel: dibuja las cajas reales del pptx (posición, tamaño, relleno,
borde, imagen y texto) sobre un lienzo 16:9, con Montserrat (la fuente del
motor) tomada de `tools/fonts`. Sirve para detectar desbordes, choques de cajas
y figuras fuera de encuadre antes de abrir el archivo en PowerPoint.

Uso:
    python3 tools/preview_pptx.py <deck.pptx> <carpeta_salida> [--dpi 110]
    python3 tools/preview_pptx.py <deck.pptx> <salida.pdf> --pdf
"""

import argparse
import io
import os
import sys

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    (False, False): os.path.join(HERE, 'fonts', 'Montserrat-Regular.ttf'),
    (False, True): os.path.join(HERE, 'fonts', 'Montserrat-Italic.ttf'),
    (True, False): os.path.join(HERE, 'fonts', 'Montserrat-Bold.ttf'),
    (True, True): os.path.join(HERE, 'fonts', 'Montserrat-Bold.ttf'),
}
FALLBACK = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
_FONT_CACHE = {}


def _font(size_px, bold, italic=False):
    key = (int(size_px), bool(bold), bool(italic))
    if key not in _FONT_CACHE:
        path = FONTS.get((bool(bold), bool(italic)), FALLBACK)
        if not os.path.exists(path):
            path = FALLBACK
        _FONT_CACHE[key] = ImageFont.truetype(path, max(int(size_px), 1))
    return _FONT_CACHE[key]


def _rgb(color):
    try:
        if color is not None and color.type is not None and color.rgb is not None:
            return '#%s' % str(color.rgb)
    except (AttributeError, ValueError):
        pass
    return None


def _wrap(draw, text, font, width_px):
    """Líneas por ajuste de palabra midiendo con la fuente real."""
    words = text.split(' ')
    lines, cur = [], ''
    for word in words:
        trial = (cur + ' ' + word).strip()
        if draw.textlength(trial, font=font) <= width_px or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _draw_paragraphs(draw, tf, box, scale, anchor):
    """Texto del text frame con ajuste de línea, alineación y espaciado."""
    x, y, w, h = box
    blocks = []
    for para in tf.paragraphs:
        runs = [r for r in para.runs if r.text]
        if not runs:
            blocks.append(([], 0, 0, None, 0, None))
            continue
        size = (runs[0].font.size.pt if runs[0].font.size else 14.0) * scale
        bold = bool(runs[0].font.bold)
        italic = bool(runs[0].font.italic)
        color = _rgb(runs[0].font.color) or '#222222'
        text = ''.join(r.text for r in runs)
        spacing = para.line_spacing if isinstance(para.line_spacing, float) else 1.0
        after = para.space_after.pt * scale if para.space_after is not None else 0
        font = _font(size, bold, italic)
        blocks.append((_wrap(draw, text, font, w), size, spacing, color, after,
                       para.alignment, font))
    heights = [len(b[0]) * b[1] * 1.22 * (b[2] or 1.0) + b[4] for b in blocks]
    total = sum(heights)
    cur_y = y + (h - total) / 2.0 if anchor == MSO_ANCHOR.MIDDLE else y
    for (lines, size, sp, color, _after, align, font), lh in zip(blocks, heights):
        for line in lines:
            fw = draw.textlength(line, font=font)
            lx = x if align != PP_ALIGN.CENTER else x + (w - fw) / 2.0
            if align == PP_ALIGN.RIGHT:
                lx = x + w - fw
            draw.text((lx, cur_y), line, font=font, fill=color)
            cur_y += size * 1.22 * (sp or 1.0)
    return total


def _draw_table(draw, table, box, scale):
    """Rejilla con las celdas reales: fila a fila, alto uniforme."""
    rows, cols = len(table.rows), len(table.columns)
    x, y, w, h = box
    widths = [Emu(col.width).inches for col in table.columns]
    total = sum(widths) or 1.0
    widths = [ww / total for ww in widths]
    heights = [Emu(row.height).inches for row in table.rows]
    hmax = sum(heights) or 1.0
    heights = [hh / hmax for hh in heights]
    row_y = y
    for r in range(rows):
        row_h = h * heights[r]
        col_x = x
        for c in range(cols):
            cell_w = w * widths[c]
            cell = table.cell(r, c)
            fill = _rgb(cell.fill.fore_color) if cell.fill.type == 1 else None
            draw.rectangle([col_x, row_y, col_x + cell_w, row_y + row_h],
                           fill=fill, outline='#CCCCCC', width=1)
            _draw_paragraphs(draw, cell.text_frame,
                             (col_x + 6, row_y + 4, cell_w - 12, row_h - 8), scale,
                             cell.text_frame.vertical_anchor)
            col_x += cell_w
        row_y += row_h


def _shape_box(shape, scale_x, scale_y):
    return (Emu(shape.left).inches * scale_x, Emu(shape.top).inches * scale_y,
            Emu(shape.width).inches * scale_x, Emu(shape.height).inches * scale_y)


def render(pptx_path, outdir=None, dpi=110):
    """[rutas PNG] del deck, una por diapositiva."""
    prs = Presentation(pptx_path)
    width_in = prs.slide_width / 914400.0
    height_in = prs.slide_height / 914400.0
    sx, sy = width_in * dpi, height_in * dpi
    scale = dpi / 72.0
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    paths = []
    for index, slide in enumerate(prs.slides, 1):
        canvas = Image.new('RGB', (int(sx), int(sy)), 'white')
        draw = ImageDraw.Draw(canvas)
        for shape in slide.shapes:
            box = _shape_box(shape, sx / width_in, sy / height_in)
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                img = Image.open(io.BytesIO(shape.image.blob)).convert('RGB')
                target = (max(int(box[2]), 1), max(int(box[3]), 1))
                canvas.paste(img.resize(target, Image.LANCZOS),
                             (int(box[0]), int(box[1])))
                continue
            if getattr(shape, 'has_table', False) and shape.has_table:
                _draw_table(draw, shape.table, box, scale)
                continue
            fill = None
            if getattr(shape, 'fill', None) is not None and shape.fill.type == 1:
                fill = _rgb(shape.fill.fore_color)
            line = None
            try:
                if shape.line.color and shape.line.color.type is not None:
                    line = _rgb(shape.line.color)
            except (AttributeError, ValueError):
                line = None
            rounded = (shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
                       and getattr(shape, 'adjustments', None) is not None)
            if fill or line:
                rect_box = [box[0], box[1], box[0] + box[2], box[1] + box[3]]
                if rounded:
                    draw.rounded_rectangle(rect_box, radius=min(box[2], box[3]) * 0.10,
                                           fill=fill, outline=line, width=2)
                else:
                    draw.rectangle(rect_box, fill=fill, outline=line, width=2)
            if shape.has_text_frame and shape.text_frame.text.strip():
                _draw_paragraphs(draw, shape.text_frame, box, scale,
                                 shape.text_frame.vertical_anchor)
        path = os.path.join(outdir or '.', f'slide_{index:02d}.png')
        canvas.save(path)
        paths.append(path)
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('pptx')
    ap.add_argument('out')
    ap.add_argument('--dpi', type=int, default=110)
    args = ap.parse_args(argv)
    if args.out.lower().endswith('.pdf'):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            paths = render(args.pptx, tmp, dpi=args.dpi)
            pages = [Image.open(p).convert('RGB') for p in paths]
            pages[0].save(args.out, save_all=True, append_images=pages[1:],
                          resolution=args.dpi)
        print(f'{len(paths)} página(s) -> {args.out}')
        return 0
    paths = render(args.pptx, args.out, dpi=args.dpi)
    print(f'{len(paths)} slide(s) -> {args.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
