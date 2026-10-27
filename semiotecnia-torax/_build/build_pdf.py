#!/usr/bin/env python3
"""Construye el PDF (misma fuente de contenido que el DOCX) con ReportLab."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from content import TITLE, SUBTITLE, INTRO, BLOCKS, FIGCAP, PERCUSSION_TABLE, APPENDIX_NOTES
from extract_figures import FIGURES

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent.parent
FIGDIR = ROOT / "figures"
OUT = ROOT / "Semiotecnia-del-Torax-y-Aparato-Respiratorio.pdf"

NAVY = colors.HexColor("#143C50")
teal = colors.HexColor("#0E7C7B")
GREY = colors.HexColor("#5A6B76")
LIGHT = colors.HexColor("#EAF3F3")
BORDER = colors.HexColor("#B9C6CC")

PROV = {fid: (pdfp, bookp) for fid, pdfp, bookp, _box, _t in FIGURES}
FIGREF = re.compile(r"(\(Fig\.[^)]*\))")
FRAME_W = A4[0] - 3.6 * cm


def fig_label(fid: str) -> str:
    if fid == "3-08a":
        return "Fig. 3-8A"
    if fid == "3-08b":
        return "Fig. 3-8B"
    return f"Fig. 3-{int(fid.split('-')[1])}"


def esc(text: str) -> str:
    text = text.replace("&", "&amp;")
    parts = FIGREF.split(text)
    return "".join(
        f'<b><font color="#0E7C7B">{p}</font></b>' if p.startswith("(Fig.") else p for p in parts
    )


SS = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", parent=SS["Title"], fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=NAVY, alignment=TA_CENTER, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", parent=SS["Normal"], fontName="Helvetica-Oblique", fontSize=11, leading=14, textColor=GREY, alignment=TA_CENTER, spaceAfter=10),
    "kicker": ParagraphStyle("kicker", parent=SS["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=teal, alignment=TA_CENTER, spaceAfter=8),
    "h1": ParagraphStyle("h1", parent=SS["Heading1"], fontName="Helvetica-Bold", fontSize=15.5, leading=18, textColor=NAVY, spaceBefore=16, spaceAfter=6, keepWithNext=1),
    "h2": ParagraphStyle("h2", parent=SS["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=14.5, textColor=teal, spaceBefore=11, spaceAfter=4, keepWithNext=1),
    "body": ParagraphStyle("body", parent=SS["Normal"], fontName="Helvetica", fontSize=10, leading=13.6, alignment=TA_JUSTIFY, spaceAfter=5),
    "bullet": ParagraphStyle("bullet", parent=SS["Normal"], fontName="Helvetica", fontSize=10, leading=13.6, alignment=TA_JUSTIFY, leftIndent=14, bulletIndent=4, spaceAfter=3),
    "cap": ParagraphStyle("cap", parent=SS["Normal"], fontName="Helvetica", fontSize=7.8, leading=9.8, alignment=TA_CENTER, spaceBefore=4),
    "src": ParagraphStyle("src", parent=SS["Normal"], fontName="Helvetica-Oblique", fontSize=6.6, leading=8, textColor=GREY, alignment=TA_CENTER),
    "note": ParagraphStyle("note", parent=SS["Normal"], fontName="Helvetica-Oblique", fontSize=8.3, leading=11, textColor=GREY, alignment=TA_JUSTIFY, spaceAfter=6),
    "cell": ParagraphStyle("cell", parent=SS["Normal"], fontName="Helvetica", fontSize=7.8, leading=9.6),
    "cellH": ParagraphStyle("cellH", parent=SS["Normal"], fontName="Helvetica-Bold", fontSize=7.8, leading=9.6, textColor=colors.white),
    "h1x": ParagraphStyle("h1x", parent=SS["Heading1"], fontName="Helvetica-Bold", fontSize=15.5, leading=18, textColor=NAVY, spaceBefore=16, spaceAfter=6, keepWithNext=1),
    "toc1": ParagraphStyle("toc1", parent=SS["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=15, textColor=NAVY, leftIndent=2),
    "toc2": ParagraphStyle("toc2", parent=SS["Normal"], fontName="Helvetica", fontSize=9.3, leading=12.5, textColor=GREY, leftIndent=14),
}


def img_flowable(fid: str, max_w: float, max_h: float = 10.0 * cm) -> Image:
    path = FIGDIR / f"fig-{fid}.jpg"
    with PILImage.open(path) as im:
        iw, ih = im.size
    scale = min(max_w / iw, max_h / ih)
    img = Image(str(path), width=iw * scale, height=ih * scale)
    img.hAlign = "CENTER"
    return img


def plate(fids):
    n = len(fids)
    col_w = FRAME_W / n
    max_h = {1: 11.0 * cm, 2: 9.8 * cm, 3: 8.4 * cm}[n]
    if n == 1:
        col_w = min(FRAME_W, 10.6 * cm)
    cells, caps, srcs = [], [], []
    for fid in fids:
        cells.append(img_flowable(fid, col_w - 10, max_h))
        title, note = FIGCAP[fid]
        pdfp, bookp = PROV[fid]
        cap_txt = f'<b><font color="#143C50">{fig_label(fid)}. {title}.</font></b>'
        if note:
            cap_txt += f" {note}"
        caps.append(Paragraph(cap_txt, S["cap"]))
        srcs.append(Paragraph(f"Recorte del PDF fuente · p. {pdfp} del PDF (p. {bookp} del libro) · fig-{fid}.jpg", S["src"]))
    t = Table([cells, caps, srcs], colWidths=[col_w] * n)
    t.hAlign = "CENTER"
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 6), ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return KeepTogether([t, Spacer(1, 6)])


def bullet(term, tag, body):
    label = f'<b><font color="#143C50">{term}</font></b>'
    if tag:
        label += f' <font size=7.5 color="#0E7C7B"><b>[{tag.upper()}]</b></font>'
    return Paragraph(f"{label} — {esc(body)}", S["bullet"], bulletText="•")


def percussion_table():
    col_w = [FRAME_W * f for f in (0.16, 0.29, 0.31, 0.24)]
    rows = []
    for ri, row in enumerate(PERCUSSION_TABLE):
        rows.append([Paragraph(f"<b>{c}</b>" if ri == 0 or ci == 0 else c, S["cellH"] if ri == 0 else S["cell"]) for ci, c in enumerate(row)])
    t = Table(rows, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F8F8")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    cap = Paragraph("Tabla 3-1. Timbres percutorios: sustrato, topografía fisiológica y valor patológico. EIC: espacio intercostal.", S["src"])
    return [t, Spacer(1, 3), cap, Spacer(1, 6)]


class Doc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            if style == "h1":
                self.notify("TOCEntry", (0, flowable.getPlainText(), self.page))
            elif style == "h2":
                self.notify("TOCEntry", (1, flowable.getPlainText(), self.page))

    def on_page(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Oblique", 7.2)
        canvas.setFillColor(GREY)
        canvas.drawRightString(A4[0] - 1.8 * cm, A4[1] - 1.15 * cm, "Semiotecnia del tórax: aparato respiratorio · Figuras 3-1 a 3-35")
        canvas.drawCentredString(A4[0] / 2, 1.05 * cm, f"Semiotecnia del tórax y aparato respiratorio  ·  {doc.page}")
        canvas.restoreState()


def main():
    doc = Doc(str(OUT), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
              topMargin=1.7 * cm, bottomMargin=1.7 * cm,
              title=TITLE, subject="Documento ilustrado con figuras 3-1 a 3-35 recortadas del PDF fuente")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=doc.on_page)])

    story = []
    story.append(Paragraph("CAPÍTULO 3 · SEMIOTECNIA — MANIOBRAS DE EXPLORACIÓN", S["kicker"]))
    story.append(Paragraph(TITLE, S["title"]))
    story.append(Paragraph(SUBTITLE, S["subtitle"]))
    cover_img = img_flowable("3-34", 6.8 * cm)
    cover_img.hAlign = "CENTER"
    story.append(cover_img)
    story.append(Paragraph("Portada: Fig. 3-34 — distribución anterior de los ruidos respiratorios normales (detalle en cap. 4).", S["src"]))
    story.append(Spacer(1, 10))
    chips = Table([[Paragraph(f'<font size=15 color="#0E7C7B"><b>{n}</b></font><br/><font size=9 color="#143C50"><b>{name}</b></font>',
                              ParagraphStyle("chip", parent=SS["Normal"], alignment=TA_CENTER, leading=17))
                    for n, name in [("1", "Inspección"), ("2", "Palpación"), ("3", "Percusión"), ("4", "Auscultación")]]],
                  colWidths=[FRAME_W / 4] * 4)
    chips.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                               ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER), ("TOPPADDING", (0, 0), (-1, -1), 7),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.append(chips)
    story.append(Spacer(1, 10))
    story.append(Paragraph(INTRO, S["body"]))
    story.append(Paragraph(
        "Nota de edición: el texto reproduce el material provisto; las 36 imágenes (Figs. 3-1 a 3-35, con 3-8 "
        "separada en A y B) son recortes de renders a 300 dpi del PDF adjunto, sin redibujo. Cada epígrafe indica "
        "la página del PDF y la página impresa del libro. La Fig. 3-23, presente en la fuente pero no citada en "
        "el texto base, se incluye en el Apéndice B. Detalle completo: Apéndice A y figuras-manifiesto.csv.", S["note"]))

    story.append(PageBreak())
    story.append(Paragraph("Índice", S["h1x"]))
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"], S["toc2"]]
    story.append(toc)

    for block in BLOCKS:
        kind = block[0]
        if kind == "h1":
            story.append(Paragraph(block[1], S["h1"]))
        elif kind == "h2":
            story.append(Paragraph(block[1], S["h2"]))
        elif kind == "p":
            story.append(Paragraph(esc(block[1]), S["body"]))
        elif kind == "bullets":
            for term, tag, body, _level in block[1]:
                story.append(bullet(term, tag, body))
        elif kind == "plate":
            story.append(plate(block[1]))
        elif kind == "perc_table":
            story.extend(percussion_table())

    story.append(PageBreak())
    story.append(Paragraph("Apéndice A. Índice de figuras y procedencia de los recortes", S["h1"]))
    story.append(Paragraph(
        "Cada imagen es un recorte directo de un render a 300 dpi de la página indicada del PDF adjunto "
        "(«semiotecnia del torax.pdf», 14 páginas). La columna «Libro» da la página impresa del capítulo 3.", S["body"]))
    col_w = [FRAME_W * f for f in (0.11, 0.52, 0.09, 0.09, 0.19)]
    rows = [[Paragraph(h, S["cellH"]) for h in ["Figura", "Título (epígrafe original, resumido)", "PDF", "Libro", "Archivo"]]]
    for fid, pdfp, bookp, _box, orig_title in FIGURES:
        rows.append([
            Paragraph(f'<b><font color="#143C50">{fig_label(fid)}</font></b>', S["cell"]),
            Paragraph(orig_title, S["cell"]),
            Paragraph(f"p. {pdfp}", S["cell"]),
            Paragraph(f"p. {bookp}", S["cell"]),
            Paragraph(f"fig-{fid}.jpg", S["cell"]),
        ])
    t = Table(rows, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F8F8")]),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                           ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    story.append(t)
    story.append(Spacer(1, 8))
    for note in APPENDIX_NOTES:
        story.append(Paragraph(note, S["bullet"], bulletText="•"))

    story.append(Paragraph("Apéndice B. Figura complementaria no citada en el texto base", S["h1"]))
    story.append(Paragraph(
        "La Fig. 3-23 aparece en la fuente (p. 18 del libro) entre las maniobras de expansión y las vibraciones "
        "vocales, pero no es citada en el texto provisto. Se adjunta aquí para completar la serie 3-1 a 3-35 y "
        "como referencia topográfica previa al frémito táctil y la percusión anterior (2.º espacio intercostal).", S["body"]))
    story.append(plate(["3-23"]))

    doc.multiBuild(story)
    print(f"OK -> {OUT} ({OUT.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
