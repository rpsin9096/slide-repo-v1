#!/usr/bin/env python3
"""Extrae y recorta las figuras 3-1 a 3-35 desde renders del PDF fuente.

Uso:
    python3 extract_figures.py "/ruta/semiotecnia del torax.pdf" [carpeta_salida]

Método: cada figura se renderiza directamente desde el PDF con PyMuPDF
(get_pixmap con clip) a 300 dpi —no se recorta un JPEG intermedio— y luego
se limpia con Pillow (escala de grises, nivel de blancos y recorte automático
de márgenes blancos con relleno). Las coordenadas son fracciones de página
(x0, y0, x1, y1) verificadas visualmente contra los renders de página completa.
"""
import csv
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps

DPI = 300
PAD_PX = 28          # relleno blanco tras el recorte automático (a 300 dpi)
WHITE_THRESHOLD = 248

# fig_id, pdf_page (1-based), book_page, (x0,y0,x1,y1), título según epígrafe original
FIGURES = [
    ("3-01",  3, 11, (0.055, 0.605, 0.485, 0.875), "Deformaciones torácicas: tórax enfisematoso (corte transversal)"),
    ("3-02",  3, 11, (0.515, 0.605, 0.915, 0.875), "Deformaciones torácicas: tórax de pollo —en quilla— (corte transversal)"),
    ("3-03",  4, 12, (0.075, 0.095, 0.490, 0.335), "Deformaciones torácicas: tórax excavado (corte transversal)"),
    ("3-04",  4, 12, (0.510, 0.085, 0.940, 0.335), "Deformaciones torácicas: tórax piriforme (corte transversal)"),
    ("3-05",  4, 12, (0.100, 0.545, 0.545, 0.795), "Deformaciones torácicas: tórax paralítico (corte transversal)"),
    ("3-06",  4, 12, (0.585, 0.495, 0.885, 0.800), "Deformaciones torácicas: tórax cifótico senil"),
    ("3-07",  5, 13, (0.330, 0.170, 0.630, 0.475), "Deformidades torácicas: tórax cifótico juvenil"),
    ("3-08a", 5, 13, (0.135, 0.555, 0.470, 0.835), "Deformaciones torácicas: tórax escoliótico — A, escoliosis dorsal sinistroconvexa"),
    ("3-08b", 5, 13, (0.535, 0.555, 0.815, 0.835), "Deformaciones torácicas: tórax escoliótico — B, escoliosis dorsal dextroconvexa"),
    ("3-09",  6, 14, (0.110, 0.095, 0.475, 0.375), "Palpación de tórax: «mano de escultor»"),
    ("3-10",  6, 14, (0.515, 0.080, 0.915, 0.365), "Examen del trofismo del tórax"),
    ("3-11",  6, 14, (0.135, 0.505, 0.450, 0.805), "Examen del tono"),
    ("3-12",  6, 14, (0.545, 0.470, 0.885, 0.815), "Localización de grupos ganglionares axilares (tomado de Bailey)"),
    ("3-13",  7, 15, (0.095, 0.145, 0.470, 0.435), "Palpación de ganglios supraclaviculares"),
    ("3-14",  7, 15, (0.510, 0.165, 0.880, 0.435), "Palpación de grupos ganglionares axilares: parte I (grupo central / vértice axilar)"),
    ("3-15",  7, 15, (0.135, 0.535, 0.470, 0.860), "Palpación de grupos ganglionares axilares: parte II (descenso por pared torácica)"),
    ("3-16",  7, 15, (0.505, 0.565, 0.900, 0.860), "Palpación de grupos ganglionares axilares: parte III (grupo subescapular)"),
    ("3-17",  8, 16, (0.080, 0.105, 0.490, 0.460), "Palpación de grupos ganglionares axilares: parte IV (grupo infraclavicular)"),
    ("3-18",  8, 16, (0.535, 0.105, 0.900, 0.460), "Examen de la elasticidad o resistencia torácica"),
    ("3-19",  8, 16, (0.110, 0.575, 0.500, 0.845), "Expansión torácica: maniobra de Ruault (vértices)"),
    ("3-20",  9, 17, (0.425, 0.175, 0.895, 0.490), "Expansión torácica infraclavicular"),
    ("3-21",  9, 17, (0.090, 0.535, 0.470, 0.840), "Expansión de las bases por delante"),
    ("3-22",  9, 17, (0.540, 0.525, 0.825, 0.825), "Expansión de las bases por detrás"),
    ("3-23", 10, 18, (0.095, 0.105, 0.495, 0.355), "Palpación del ángulo de Louis: reconocimiento de espacios intercostales"),
    ("3-24", 10, 18, (0.525, 0.105, 0.910, 0.360), "Palpación de vibraciones vocales: región anterior"),
    ("3-25", 10, 18, (0.110, 0.510, 0.520, 0.855), "Palpación de las vibraciones vocales: región posterior"),
    ("3-26", 11, 19, (0.085, 0.140, 0.455, 0.460), "Palpación de vibraciones vocales: delimitación de las bases"),
    ("3-27", 11, 19, (0.500, 0.165, 0.875, 0.395), "Percusión del tórax: delimitación de los campos de Krönig"),
    ("3-28", 11, 19, (0.450, 0.572, 0.875, 0.975), "Percusión de las clavículas"),
    ("3-29", 12, 20, (0.085, 0.105, 0.470, 0.325), "Percusión del esternón"),
    ("3-30", 12, 20, (0.515, 0.090, 0.915, 0.265), "Percusión del tórax por delante: delimitación del borde superior hepático (detalle digito-digital)"),
    ("3-31", 12, 20, (0.125, 0.520, 0.475, 0.798), "Percusión del tórax por detrás"),
    ("3-32", 12, 20, (0.530, 0.475, 0.885, 0.745), "Excursión de las bases pulmonares (a: inspiración forzada; b: espiración forzada)"),
    ("3-33", 13, 21, (0.060, 0.170, 0.465, 0.490), "Percusión de la columna"),
    ("3-34", 13, 21, (0.500, 0.165, 0.885, 0.490), "Auscultación pulmonar: distribución anterior de los ruidos normales"),
    ("3-35", 13, 21, (0.545, 0.575, 0.885, 0.975), "Auscultación pulmonar: distribución posterior de los ruidos normales"),
]


def clean(img: Image.Image) -> Image.Image:
    g = img.convert("L")
    # Nivel de blancos suave: lleva el papel escaneado a blanco sin borrar el trazo tenue.
    g = g.point(lambda v: 255 if v >= 250 else int(v * 255 / 250))
    g = ImageOps.autocontrast(g, cutoff=0)
    mask = g.point(lambda v: 255 if v < WHITE_THRESHOLD else 0)
    bbox = mask.getbbox()
    if bbox:
        x0 = max(0, bbox[0] - PAD_PX)
        y0 = max(0, bbox[1] - PAD_PX)
        x1 = min(g.width, bbox[2] + PAD_PX)
        y1 = min(g.height, bbox[3] + PAD_PX)
        g = g.crop((x0, y0, x1, y1))
    return g.convert("RGB")


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/arena-coding-uploads/semiotecnia del torax.pdf")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "figures"
    out.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(src)
    rows = []
    for fig_id, pdf_page, book_page, (fx0, fy0, fx1, fy1), title in FIGURES:
        page = doc[pdf_page - 1]
        r = page.rect
        clip = pymupdf.Rect(r.width * fx0, r.height * fy0, r.width * fx1, r.height * fy1)
        pix = page.get_pixmap(dpi=DPI, clip=clip)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img = clean(img)
        name = f"fig-{fig_id}.jpg"
        img.save(out / name, quality=90)
        rows.append({
            "figura": f"Fig. {fig_id.replace('3-0', '3-').replace('3-08', '3-8')}",
            "archivo": name,
            "titulo_epigrafe_original": title,
            "pagina_pdf": pdf_page,
            "pagina_libro": book_page,
            "recorte_fraccion_pagina": f"{fx0:.3f},{fy0:.3f},{fx1:.3f},{fy1:.3f}",
            "px": f"{img.width}x{img.height}",
        })
        print(f"{name}: PDF p.{pdf_page} (libro p.{book_page}) {img.width}x{img.height} — {title}")
    manifest = Path(__file__).resolve().parent.parent / "figuras-manifiesto.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} recortes -> {out}\nManifiesto -> {manifest}")


if __name__ == "__main__":
    main()
