# -*- coding: utf-8 -*-
"""Recorta las figuras del capítulo 3 desde el PDF escaneado.

El PDF trae cada página como una imagen 1-bit de ~397 dpi nativos. En vez de
volver a rasterizar la página (que remuestrea y mete ruido), se extrae el PNG
embebido tal cual y se recorta en coordenadas de píxel.

Las líneas del dibujo y las palabras OCR viven en la misma imagen: para recortar
solo el dibujo se enmascaran las cajas de texto que reporta la capa OCR y se
busca la tinta restante dentro de la región de cada figura.

Uso:
    python3 tools/extract_figures.py <pdf> <carpeta_salida>
"""

import argparse
import io
import os
import sys

import numpy as np
import pymupdf
from PIL import Image, ImageDraw

# figura -> (página 0-based, caja de búsqueda en puntos PDF, máscaras extra)
# Las máscaras extra tapan fragmentos de pies de figura que el OCR devuelve como
# bloques sueltos y que caerían dentro de la caja de búsqueda.
REGIONS = {
    'fig_3_1':  (2, (58, 556, 294, 722), ()),                       # tórax en tonel
    'fig_3_3':  (3, (76, 128, 302, 277), ()),                       # tórax excavado
    'fig_3_8':  (4, (93, 470, 505, 730), ()),                       # escoliosis A/B
    'fig_3_9':  (5, (76, 86, 262, 264), ((50, 392, 300, 404),       # "escultor"."
                                         (98, 566, 136, 640))),     # rayas sueltas
    'fig_3_10': (5, (308, 88, 552, 320), ()),                       # examen del trofismo
    'fig_3_11': (5, (94, 420, 268, 642), ()),                       # examen del tono
    'fig_3_12': (5, (326, 391, 545, 686), ()),                      # ganglios axilares
    'fig_3_13': (6, (52, 145, 280, 402), ()),                       # ganglios supraclaviculares
    'fig_3_18': (7, (320, 90, 528, 396), ()),                       # resistencia torácica
    'fig_3_19': (7, (103, 518, 302, 712), ()),                      # maniobra de Ruault
    'fig_3_20': (8, (262, 145, 500, 412), ()),                      # expansión infraclavicular
    'fig_3_21': (8, (55, 450, 292, 714), ()),                       # expansión de las bases delante
    'fig_3_22': (8, (321, 441, 472, 697), ()),                      # bases posteriores
    'fig_3_27': (10, (305, 143, 477, 366), ((290, 364, 540, 382),)),  # campos de Krönig
    'fig_3_32': (11, (334, 370, 547, 620), ()),                     # excursión basal
    'fig_3_34': (12, (288, 144, 480, 424), ((288, 424, 540, 442),)),  # auscultación frontal
    'fig_3_35': (12, (326, 505, 503, 787), ()),                     # auscultación posterior
}

# Parejas que se publican como una sola lámina: dos dibujos verticales seguidos
# caben a la misma altura que uno solo y llenan el lienzo 16:9.
PAIRS = {
    'fig_3_9_3_10_3_11': ('fig_3_9', 'fig_3_10', 'fig_3_11'),  # escultor, trofismo, tono
    'fig_3_1_3_3':    ('fig_3_1', 'fig_3_3'),       # cortes transversales
    'fig_3_12_3_13':  ('fig_3_12', 'fig_3_13'),     # ganglios axilares + supraclaviculares
    'fig_3_18_3_19':  ('fig_3_18', 'fig_3_19'),     # resistencia + Ruault
    'fig_3_21_3_22':  ('fig_3_21', 'fig_3_22'),     # bases por delante + por detrás
    'fig_3_27_3_32':  ('fig_3_27', 'fig_3_32'),     # Krönig + excursión basal
    'fig_3_34_3_35':  ('fig_3_34', 'fig_3_35'),     # auscultación anterior + posterior
}
# Recortes que el deck usa sueltos: se publican en la carpeta de salida, no en
# `_partes`. El resto de los recortes sueltos queda solo como material de trabajo
# (fig_3_9 se conserva suelto para revisar el recorte, pero el deck usa la lámina).
SINGLES = ('fig_3_8', 'fig_3_9')
GAP_RATIO = 0.045      # separación entre las dos láminas, relativa a la altura
DIVIDER = 208          # gris de la línea divisoria

# figura -> cajas donde el "texto OCR" es en realidad rótulo de la figura y debe
# conservarse (p. ej. las letras A/B de las dos variantes de escoliosis).
KEEP_TEXT = {'fig_3_8': ((190, 708, 412, 730),)}

INK = 128          # umbral de tinta en la imagen 1-bit ya convertida a gris
ROW_MIN_PX = 4     # píxeles oscuros mínimos por fila/columna para contar
PAD_PT = 7         # margen blanco alrededor del recorte, en puntos
MAX_SIDE = 1800    # lado mayor de salida, en píxeles


def _page_bitmap(doc, page_no):
    """(array booleano de tinta, escala px/pt) de la página escaneada."""
    page = doc[page_no]
    big = [i for i in page.get_image_info(xrefs=True) if i['width'] > 500]
    if not big:
        raise SystemExit(f'página {page_no}: sin imagen de página embebida')
    info = big[0]
    raw = doc.extract_image(info['xref'])['image']
    img = Image.open(io.BytesIO(raw)).convert('L')
    arr = np.asarray(img, dtype=np.uint8)
    return arr < INK, arr.shape[1] / page.rect.width


def _text_mask(page, shape, scale, keep=()):
    """Máscara booleana de las cajas de texto OCR (True = texto, no dibujo)."""
    mask = np.zeros(shape, dtype=bool)
    for block in page.get_text('blocks'):
        if block[6] != 0:          # 0 = bloque de texto
            continue
        x0, y0, x1, y1 = block[:4]
        if any(kx0 <= x0 and kx1 >= x1 and ky0 <= y0 and ky1 >= y1
               for kx0, ky0, kx1, ky1 in keep):
            continue               # rótulo de la figura: se conserva
        r0, c0 = int(y0 * scale), int(x0 * scale)
        r1, c1 = int(y1 * scale) + 2, int(x1 * scale) + 2
        mask[max(r0, 0):r1, max(c0, 0):c1] = True
    return mask


def _ink_box(ink, page, region, masks, scale, keep=()):
    """(x0, y0, x1, y1) en píxeles de la tinta dentro de la región."""
    rx0, ry0, rx1, ry1 = region
    c0, r0 = max(int(rx0 * scale), 0), max(int(ry0 * scale), 0)
    c1, r1 = int(rx1 * scale), int(ry1 * scale)
    roi = ink[r0:r1, c0:c1]
    text = _text_mask(page, ink.shape, scale, keep)
    for bx0, by0, bx1, by1 in masks:
        text[int(by0 * scale):int(by1 * scale), int(bx0 * scale):int(bx1 * scale)] = True
    text = text[r0:r1, c0:c1]
    draw = roi & ~text
    rows = np.where(draw.sum(axis=1) >= ROW_MIN_PX)[0]
    cols = np.where(draw.sum(axis=0) >= ROW_MIN_PX)[0]
    if not len(rows) or not len(cols):
        raise SystemExit(f'sin tinta en la región {region} de la página {page.number}')
    return c0 + cols[0], r0 + rows[0], c0 + cols[-1], r0 + rows[-1]


def crop(doc, page_no, region, masks=(), keep=(), max_side=MAX_SIDE, pad_pt=PAD_PT):
    """Imagen PIL en gris del dibujo, recortada y reducida por área (BOX)."""
    ink, scale = _page_bitmap(doc, page_no)
    x0, y0, x1, y1 = _ink_box(ink, doc[page_no], region, masks, scale, keep)
    pad = int(pad_pt * scale)
    x0, y0 = max(x0 - pad, 0), max(y0 - pad, 0)
    x1, y1 = x1 + pad, y1 + pad
    img = Image.fromarray(np.where(ink[y0:y1, x0:x1], 0, 255).astype(np.uint8), 'L')
    factor = max(img.width, img.height) / max_side
    if factor > 1:
        img = img.resize((round(img.width / factor), round(img.height / factor)),
                         Image.BOX)
    return img


def compose_pair(*parts, gap_ratio=GAP_RATIO):
    """Lámina única con dos o tres recortes a la misma altura y sus divisorias."""
    height = max(im.height for im in parts)
    scaled = [im.resize((round(im.width * height / im.height), height), Image.BOX)
              for im in parts]
    gap = max(int(height * gap_ratio), 12)
    width = sum(im.width for im in scaled) + gap * (len(scaled) - 1)
    canvas = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(canvas)
    x = 0
    for index, im in enumerate(scaled):
        canvas.paste(im, (x, 0))
        x += im.width
        if index < len(scaled) - 1:
            draw.line([(x + gap / 2.0, height * 0.06), (x + gap / 2.0, height * 0.94)],
                      fill=DIVIDER, width=3)
            x += gap
    return canvas


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('pdf')
    ap.add_argument('outdir')
    args = ap.parse_args(argv)
    os.makedirs(args.outdir, exist_ok=True)
    parts_dir = os.path.join(args.outdir, '_partes')   # recortes sueltos, no van al deck
    os.makedirs(parts_dir, exist_ok=True)
    doc = pymupdf.open(args.pdf)
    plates = {}
    for name, (page_no, region, masks) in REGIONS.items():
        img = crop(doc, page_no, region, masks, KEEP_TEXT.get(name, ()))
        plates[name] = img
        path = os.path.join(parts_dir, f'{name}.png')
        # PNG sin pérdida: compress_level 1 mantiene el detalle 1-bit intacto y
        # deja el archivo por encima del piso de 20 KB del contrato de imágenes.
        img.save(path, compress_level=1)
        if name in SINGLES:
            img.save(os.path.join(args.outdir, f'{name}.png'), compress_level=1)
    print(f'{len(plates)} recortes sueltos -> {parts_dir}')
    for name, parts in PAIRS.items():
        img = compose_pair(*(plates[part] for part in parts))
        path = os.path.join(args.outdir, f'{name}.png')
        img.save(path, compress_level=1)
        print(f'{name}: {img.width}x{img.height} px · {os.path.getsize(path) // 1024} KB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
