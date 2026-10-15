# -*- coding: utf-8 -*-
"""Figuras tipográficas limpas (estilo JAMA/NEJM) para o Caso 09 v2.

Produz apenas figuras que NÃO inventam anatomia:

  * cascada_etiopato.png   — fluxograma tipográfico puro (4 etapas).
  * placa_rx.png           — molde radiográfico com lista de achados +
                             indicação de inserção da RX real.
  * placa_tc.png           — molde tomográfico com lista de achados +
                             indicação de inserção da TC real.
  * macro_moldura.png      — moldura elegante para foto macro do caso
                             (placeholder; NÃO simula uma peça).
  * histo_he_panel.png     — micro H&E real (esteatonecrose por
                             saponificação) com etiquetas tipográficas;
                             a micro original do caso segue marcada.

Produz SVG + PNG a 300 DPI.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.patches import Ellipse
import numpy as np

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
SVG = HERE.parent / "assets-svg"
ROOT = HERE.parent.parent.parent   # repo root
SEARCH = ROOT / "image-search"
ASSETS.mkdir(exist_ok=True); SVG.mkdir(exist_ok=True)

mpl.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.serif": ["DejaVu Serif", "Liberation Serif"],
    "font.size": 11,
    "axes.linewidth": 0.8,
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
})

NAVY = "#1F3A5F"; NAVY_DK = "#102540"; RED = "#9B2C2C"; GOLD = "#B08D2A"
INK = "#1A1A1A"; GREY = "#555555"; SOFT = "#F7F5EE"; LINE = "#222"


def _save(fig, stem, tight=True):
    png = ASSETS / f"{stem}.png"; svg = SVG / f"{stem}.svg"
    kw = dict(dpi=300, facecolor="white")
    kwa = dict(format="svg", facecolor="white")
    if tight:
        kw["bbox_inches"] = "tight"
        kwa["bbox_inches"] = "tight"
    fig.savefig(png, **kw)
    fig.savefig(svg, **kwa)
    plt.close(fig)
    print(f"  wrote {png.name} + {svg.name}")


# ---------------------------------------------------------------------------
# Cascada fisiopatológica (4 etapas, fluxograma tipográfico)
# ---------------------------------------------------------------------------
def cascada():
    fig, ax = plt.subplots(figsize=(14, 6.2))
    ax.set_xlim(0, 28); ax.set_ylim(0, 12); ax.axis("off")

    ax.text(14, 11.2,
            "Cascada etiopatogénica: de la impactación litiásica a la autodigestión",
            ha="center", fontsize=15, fontweight="bold", color=NAVY_DK)
    ax.text(14, 10.5,
            "Pancreatitis aguda biliar · cuatro etapas encadenadas",
            ha="center", fontsize=10, color=GREY, style="italic")

    stages = [
        ("I", "Obstrucción",
         ["Migración del microcálculo.",
          "Impactación ampolar.",
          "HT retrógrada + reflujo."], NAVY_DK),
        ("II", "Disfunción acinar",
         ["Bloqueo ductal.",
          "Fusión zimógeno-lisosoma.",
          "Pérdida de compartimentación."], "#224A73"),
        ("III", "Activación",
         ["Catepsina B activa tripsina.",
          "SPINK1 sobrepasado.",
          "Gatillo enzimático."], "#802E24"),
        ("IV", "Autodigestión",
         ["Elastasa → lesión vascular.",
          "Fosfolipasa A2 → lisis.",
          "Lipasa → esteatonecrosis."], "#4C1F1F"),
    ]

    n = len(stages)
    bw = 5.6; gap = 1.5
    total_w = n*bw + (n-1)*gap
    x0 = (28 - total_w)/2
    box_y = 2.0; box_h = 6.0

    for i,(num,title,bullets,col) in enumerate(stages):
        x = x0 + i*(bw+gap)
        ax.add_patch(FancyBboxPatch((x, box_y), bw, box_h,
                                     boxstyle="round,pad=0.18",
                                     facecolor="white", edgecolor=col, lw=1.6))
        ax.add_patch(Rectangle((x+0.15, box_y+box_h-0.9), bw-0.3, 0.75,
                                facecolor=col, edgecolor="none"))
        ax.text(x+0.65, box_y+box_h-0.52, num, ha="center", va="center",
                fontsize=12, color="white", fontweight="bold")
        ax.text(x+1.4, box_y+box_h-0.52, title, ha="left", va="center",
                fontsize=11.0, color="white", fontweight="bold")
        # bullets — margen derecho de 0.5 dentro de la caja para que
        # el texto no toque flechas ni bordes redondeados
        text_w = bw - 1.10
        by = box_y+box_h-1.55
        for b in bullets:
            ax.text(x+0.45, by, "•", ha="left", va="top", color=col,
                    fontsize=12, fontweight="bold")
            tx = ax.text(x+0.85, by, b, ha="left", va="top", fontsize=10,
                         color=INK)
            tx.set_clip_on(False)
            by -= 1.05
        # flecha entre cajas: una única FancyArrowPatch con retraimiento
        # (shrink) para respetar los bordes redondeados y no tocar texto.
        if i < n-1:
            x_start = x + bw + 0.35
            x_end   = x + bw + gap - 0.35
            ymid = box_y + box_h/2
            ax.add_patch(FancyArrowPatch((x_start, ymid), (x_end, ymid),
                                         arrowstyle="-|>,head_width=0.35,head_length=0.45",
                                         color=GOLD, lw=1.8,
                                         shrinkA=2, shrinkB=2,
                                         mutation_scale=12,
                                         linewidth=1.8))

    ax.text(14, 1.15,
            "Basado en Robbins Patología cap. 19 y Harrison cap. 347.",
            ha="center", fontsize=9, color=GREY, style="italic")
    _save(fig, "cascada_etiopato")


# ---------------------------------------------------------------------------
# RX / TC: placa radiológica tipográfica (lado der) + área de inserción da
# imagem real (lado esq, sem desenho de órgãos)
# ---------------------------------------------------------------------------
def _wrap(text, n):
    out=[]; cur=""
    for w in text.split():
        if len(cur)+len(w)+1 > n:
            out.append(cur); cur=w
        else:
            cur=(cur+" "+w).strip()
    if cur: out.append(cur)
    return out


def _placa(titulo, subtitulo, achados, stem, cor_placa="#272727",
           faixa=None, img_real=None, aviso=None, H=18.0):
    W = 26
    fig_h = 13 * (H/26)
    fig, ax = plt.subplots(figsize=(13, fig_h))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    # bloque de títulos (altura holgada)
    ax.text(W/2, H-0.3, titulo, ha="center", va="top",
            fontsize=14.5, fontweight="bold", color=NAVY_DK)
    ax.text(W/2, H-1.3, subtitulo, ha="center", va="top",
            fontsize=10, color=GREY, style="italic")

    fx0, fy0, fw = 0.6, 1.2, 11.0
    fh = H - 3.5   # filme: top en H-2.3, 1.0 de aire bajo subtítulo
    # moldura preta exterior
    ax.add_patch(Rectangle((fx0-0.25, fy0-0.25), fw+0.5, fh+0.5,
                           facecolor="black", edgecolor="none"))
    if img_real is not None:
        from PIL import Image
        im = Image.open(img_real).convert("RGB")
        iw, ih = im.size
        scale = min(fw/iw, fh/ih) * 0.96
        dw, dh = iw*scale, ih*scale
        dx = fx0 + (fw-dw)/2
        dy = fy0 + (fh-dh)/2
        ax.imshow(im, extent=[dx, dx+dw, dy, dy+dh], aspect="auto")
        ax.add_patch(Rectangle((fx0, fy0), fw, fh, facecolor="none",
                               edgecolor="#111", lw=1.5))
        ax.text(fx0+0.3, fy0+fh-0.3, "D", ha="left", va="top",
                fontsize=12, color="white", fontweight="bold", alpha=0.85)
        ax.text(fx0+fw-0.3, fy0+fh-0.3, "I", ha="right", va="top",
                fontsize=12, color="white", fontweight="bold", alpha=0.85)
        ax.text(fx0+fw-0.3, fy0+0.3, "Imagen representativa",
                ha="right", va="bottom", fontsize=7.5, color="white", alpha=0.6)
    else:
        ax.add_patch(Rectangle((fx0, fy0), fw, fh, facecolor=cor_placa,
                               edgecolor="#111", lw=1.5))
        ax.text(fx0+0.3, fy0+fh-0.3, "D", ha="left", va="top",
                fontsize=12, color="white", fontweight="bold", alpha=0.75)
        ax.text(fx0+fw-0.3, fy0+fh-0.3, "I", ha="right", va="top",
                fontsize=12, color="white", fontweight="bold", alpha=0.75)
        ax.text(fx0+fw-0.3, fy0+0.3, "UCP", ha="right", va="bottom",
                fontsize=8, color="white", alpha=0.6)
        if faixa is not None:
            for (cxr, cyr, ww, hh, aa, col) in faixa:
                ax.add_patch(Ellipse((fx0+cxr*fw, fy0+cyr*fh),
                                     ww*fw, hh*fh, facecolor=col,
                                     edgecolor="none", alpha=aa))
        msg = aviso or ("INSERIR AQUÍ LA IMAGEN ORIGINAL DEL CASO\n"
                        "(RX simple / TC axial) con marcaciones:\n"
                        "flechas/círculos sobre los hallazgos listados.")
        ax.text(fx0+fw/2, fy0+fh/2, msg,
                ha="center", va="center", fontsize=10, color="white",
                alpha=0.45, style="italic", linespacing=1.5)

    # caixa de achados (dir): alineada con el filme
    ax0 = 13.0; ay0 = 1.2; aw = 12.4; ah = H - 3.5
    ax.add_patch(FancyBboxPatch((ax0, ay0), aw, ah,
                                 boxstyle="round,pad=0.25",
                                 facecolor="white", edgecolor=LINE, lw=0.8))
    ax.text(ax0+0.4, ay0+ah-0.4, "Hallazgos informados",
            ha="left", va="top", fontsize=13, color=NAVY_DK,
            fontweight="bold")
    ax.plot([ax0+0.4, ax0+aw-0.4], [ay0+ah-1.0, ay0+ah-1.0],
            color=GOLD, lw=1.2)
    y = ay0+ah-1.7
    for head, body in achados:
        ax.text(ax0+0.6, y, "▸ "+head, ha="left", va="top",
                fontsize=11, color=RED, fontweight="bold")
        lines = _wrap(body, 58)   # ancho más estrecho para evitar corte en borde
        ty = y-0.7
        for ln in lines:
            ax.text(ax0+1.1, ty, ln, ha="left", va="top",
                    fontsize=9.5, color=INK)
            ty -= 0.55
        y = ty - 0.25
    ax.text(ax0+0.4, ay0+0.3,
            "Lectura integrada al juicio clínico (Atlanta 2012).",
            ha="left", va="bottom", fontsize=8.5, color=GREY, style="italic")

    _save(fig, stem)


def rx():
    achados = [
        ("Ausencia de neumoperitoneo",
         "Sin aire libre subdiafragmático (signo de Jobert negativo); "
         "descarta perforación de víscera hueca."),
        ("Borramiento del psoas derecho",
         "Edema retroperitoneal que difumina el contorno muscular; "
         "el psoas izquierdo permanece nítido."),
        ("Asa centinela",
         "Asa de intestino delgado localizada y dilatada adyacente "
         "al proceso inflamatorio pancreático."),
        ("Distribución gaseosa",
         "Gas intestinal sin niveles hidroaéreos difusos; patrón de íleo "
         "paralítico reflejo, no de obstrucción mecánica."),
    ]
    _placa("Radiografía simple de abdomen",
           "Proyección en decúbito supino · espacio para RX del caso",
           achados, "placa_rx", cor_placa="#3A3A3A",
           faixa=[(0.38,0.45,0.30,0.50,0.18,"#FFE6E0"),
                  (0.45,0.55,0.08,0.12,0.35,"#666")])


def tc():
    achados = [
        ("Páncreas aumentado de volumen",
         "Tumefacción difusa con realce heterogéneo del parénquima "
         "(edema intersticial)."),
        ("Hipoatenuación líquida peripancreática",
         "Colecciones agudas líquidas en el espacio peripancreático y "
         "raíz del mesocolon transverso."),
        ("Densificación de la grasa peripancreática",
         "Opacificación reticular de la grasa adyacente por edema e "
         "inflamación (fat stranding en inglés)."),
        ("Sin necrosis parenquimatosa extensa",
         "Ausencia de áreas de falta de realce > 30% ni gas "
         "intra o peripancreático."),
        ("Índice Balthazar",
         "Grado C-D (edema intersticial con colecciones peripancreáticas), "
         "sin necrosis."),
    ]
    _placa("Tomografía axial computarizada (TC c/C)",
           "Fase portal · espacio para TC del caso",
           achados, "placa_tc", cor_placa="#2E2E2E",
           faixa=[(0.5,0.5,0.65,0.35,0.22,"#101F3C"),
                  (0.5,0.5,0.30,0.10,0.45,"#7A8998")],
           H=19.0)


# ---------------------------------------------------------------------------
# Macroscopia — moldura de placeholder
# ---------------------------------------------------------------------------
def macro_moldura():
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_xlim(0,22); ax.set_ylim(0,16); ax.axis("off")

    # Títulos
    ax.text(11, 15.5, "Pieza macroscópica — espacio reservado",
            ha="center", fontsize=14, fontweight="bold", color=NAVY_DK)
    ax.text(11, 14.8,
            "Inserte aquí la fotografía original de la pieza del Caso 09.",
            ha="center", fontsize=10, color=GREY, style="italic")

    # Leyenda de marcadores: dos chips en línea (rojo izq, dorado der)
    ax.text(11, 13.9, "Marcadores a superponer a la foto:",
            ha="center", fontsize=10.5, color=NAVY_DK, fontweight="bold")
    leg_y = 13.2
    # chip rojo
    ax.add_patch(FancyBboxPatch((3.2, leg_y-0.32), 7.0, 0.55,
                                 boxstyle="round,pad=0.08",
                                 facecolor="white", edgecolor=RED, lw=1.1))
    ax.text(4.0, leg_y-0.05, "●", ha="left", va="center",
            fontsize=11, color=RED)
    ax.text(6.7, leg_y-0.05, "Congestión y petequias",
            ha="center", va="center", fontsize=10, color=RED, fontweight="bold")
    # chip dorado
    ax.add_patch(FancyBboxPatch((11.8, leg_y-0.32), 7.0, 0.55,
                                 boxstyle="round,pad=0.08",
                                 facecolor="white", edgecolor=GOLD, lw=1.1))
    ax.text(12.6, leg_y-0.05, "●", ha="left", va="center",
            fontsize=11, color=GOLD)
    ax.text(15.3, leg_y-0.05, "Esteatonecrosis «gotas de cera»",
            ha="center", va="center", fontsize=10, color=GOLD, fontweight="bold")

    # Moldura
    frame_top = 12.4
    frame_bot = 2.5
    frame_lft = 2.5
    frame_rgt = 19.5
    ax.add_patch(Rectangle((frame_lft, frame_bot), frame_rgt-frame_lft,
                            frame_top-frame_bot,
                            facecolor=SOFT, edgecolor=NAVY, lw=2.0))
    inner_lft, inner_rgt = 3.3, 18.7
    inner_top, inner_bot = frame_top-0.7, frame_bot+0.8
    ax.add_patch(Rectangle((inner_lft, inner_bot), inner_rgt-inner_lft,
                            inner_top-inner_bot, facecolor="white",
                            edgecolor=GREY, lw=0.8, ls=(0,(6,4))))
    c = 0.5
    for (cx,cy) in [(frame_lft,frame_bot),(frame_rgt,frame_bot),
                    (frame_lft,frame_top),(frame_rgt,frame_top)]:
        ax.plot([cx, cx+(c if cx<11 else -c)], [cy, cy], color=NAVY, lw=3)
        ax.plot([cx, cx], [cy, cy+(c if cy>7 else -c)], color=NAVY, lw=3)

    # flechas que nacen en el borde superior del marco y apuntan a dos
    # zonas indicativas del interior (izq-sup: congestión; der-sup: esteatonecrosis)
    ax.add_patch(FancyArrowPatch((6.2, inner_top), (7.2, 10.2),
                                 arrowstyle="-|>", color=RED, lw=2.2,
                                 mutation_scale=16))
    ax.add_patch(FancyArrowPatch((15.8, inner_top), (14.8, 10.2),
                                 arrowstyle="-|>", color=GOLD, lw=2.2,
                                 mutation_scale=16))

    ax.text(11, 4.5,
            "Leyenda a pie de imagen: glándula tumefacta, friable, con congestión,\n"
            "petequias hemorrágicas y placas blanco-amarillentas\n"
            "de esteatonecrosis por saponificación cálcica.",
            ha="center", fontsize=10, color=INK, style="italic", linespacing=1.5)

    _save(fig, "macro_moldura")


# ---------------------------------------------------------------------------
# Histopatologia — micro real com setas tipográficas
# ---------------------------------------------------------------------------
def histo_he():
    """Faz um painel com a micro H&E real (esteatonecrosis + saponificación)
    encontrada em image-search; não substitui a micro do caso (que continua
    como placeholder), mas serve de referência didáctica.
    """
    src = SEARCH / "wikimedia-commons-histology-acute-pancre-2.jpg"
    if not src.exists():
        print("  [histo_he] imagem H&E de referência não encontrada; pulando.")
        return

    from PIL import Image
    im = Image.open(src).convert("RGB")
    iw, ih = im.size

    fig = plt.figure(figsize=(12, 7.5), facecolor="white")
    # micro ocupa a esq; caixa de achados a der
    ax = fig.add_axes([0.02, 0.10, 0.58, 0.84])
    ax.imshow(im, aspect="auto")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_edgecolor(NAVY); sp.set_linewidth(1.0)
    ax.set_title("Histología H&E · esteatonecrosis con saponificación cálcica",
                 fontsize=12, color=NAVY_DK, fontweight="bold", pad=10)

    # caixa de achados (der)
    ax2 = fig.add_axes([0.63, 0.10, 0.34, 0.84])
    ax2.set_xticks([]); ax2.set_yticks([])
    for sp in ax2.spines.values(): sp.set_visible(False)
    ax2.set_xlim(0,1); ax2.set_ylim(0,1)
    ax2.text(0, 1, "Hallazgos histológicos",
             ha="left", va="top", fontsize=13, color=NAVY_DK, fontweight="bold")
    ax2.plot([0,1],[0.95,0.95], color=GOLD, lw=1.2)
    items = [
        ("Adipocitos «fantasma»",
         "Contornos de células grasas anucleadas por necrosis enzimática "
         "(acción de la lipasa)."),
        ("Saponificación cálcica",
         "Depósitos basófilos amorfos azul-violeta (flechas): sales de Ca "
         "insolubles sobre ácidos grasos libres."),
        ("Infiltrado neutrofílico",
         "Banda densa de neutrófilos en el intersticio y alrededor de los "
         "focos necróticos."),
        ("Necrosis acinar",
         "Pérdida de arquitectura en los acinos adyacentes; cariólisis y "
         "citoplasma eosinófilo homogéneo."),
    ]
    y = 0.88
    line_h = 0.052
    for h,b in items:
        ax2.text(0, y, "▸ "+h, ha="left", va="top", fontsize=10,
                 color=RED, fontweight="bold")
        ty = y - 0.075
        for ln in _wrap(b, 54):
            ax2.text(0.03, ty, ln, ha="left", va="top",
                     fontsize=8.7, color=INK)
            ty -= line_h
        y = ty - 0.04
    ax2.text(0, 0.03,
             "Micrografía de referencia. Sustituir por la H&E del Caso 09.",
             ha="left", va="bottom", fontsize=7.5, color=GREY, style="italic")

    _save(fig, "histo_he_panel", tight=False)


# ---------------------------------------------------------------------------
# Painel 9 — bioquímica + RX + TC (sem desenho de órgãos)
# ---------------------------------------------------------------------------
def lab_panel():
    W, H = 26, 14
    fig, ax = plt.subplots(figsize=(13, 7.0))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    ax.text(W/2, H-0.3, "Patrón bioquímico e imagenológico",
            ha="center", fontsize=15, fontweight="bold", color=NAVY_DK)
    ax.text(W/2, H-1.2,
            "Lipasa sérica · RX simple · TC axial con contraste",
            ha="center", fontsize=10, color=GREY, style="italic")

    # ----- bloco 1: barras lipase vs amilase -----
    bx, by, bw, bh = 0.6, 2.0, 8.5, 10.0
    ax.add_patch(FancyBboxPatch((bx, by), bw, bh,
                                 boxstyle="round,pad=0.2",
                                 facecolor=SOFT, edgecolor=NAVY, lw=1.0))
    ax.text(bx+bw/2, by+bh-0.5, "Lipasa vs amilasa sérica",
            ha="center", va="top", fontsize=12, color=NAVY_DK,
            fontweight="bold")

    gx, gy, gw, gh = bx+1.1, by+2.4, bw-2.0, bh-4.6
    ax.add_patch(Rectangle((gx, gy), gw, gh, facecolor="white",
                            edgecolor="#999", lw=0.6))
    for v in range(0, 101, 20):
        yy = gy + gh*(v/100)
        ax.plot([gx, gx+gw], [yy, yy], color="#ddd", lw=0.6)
        ax.text(gx-0.2, yy, f"{v}", ha="right", va="center", fontsize=8,
                color=GREY)
    ax.text(gx-0.8, gy+gh/2, "%", ha="center", va="center", fontsize=9,
            color=GREY, rotation=90)

    cats = [(95, NAVY_DK), (99, GOLD), (82, NAVY_DK), (88, GOLD)]
    bw_bar = 0.9; gap_b = 0.55; group_gap = 1.2
    total = 4*bw_bar + 3*gap_b + group_gap
    xs = gx + (gw-total)/2
    xi = xs
    centers = []
    for i,(v,col) in enumerate(cats):
        h_bar = gh*(v/100)
        ax.add_patch(Rectangle((xi, gy), bw_bar, h_bar,
                                facecolor=col, edgecolor="none"))
        ax.text(xi+bw_bar/2, gy+h_bar+0.2, f"{v}",
                ha="center", va="bottom", fontsize=9, color=INK,
                fontweight="bold")
        centers.append(xi+bw_bar/2)
        xi += bw_bar + gap_b
        if i == 1:
            xi += group_gap
    # centros dos grupos (meio do par lipasa e meio do par amilasa)
    lip_c = (centers[0]+centers[1])/2
    ami_c = (centers[2]+centers[3])/2
    ax.text(lip_c, gy-0.5, "Lipasa",
            ha="center", fontsize=10, color=NAVY_DK, fontweight="bold")
    ax.text(lip_c, gy-1.1, "Elevada 7–14 días",
            ha="center", fontsize=8, color=INK, style="italic")
    ax.text(lip_c, gy-1.5, "(ventana dx más amplia)",
            ha="center", fontsize=7.5, color=GREY)
    ax.text(ami_c, gy-0.5, "Amilasa",
            ha="center", fontsize=10, color=NAVY_DK, fontweight="bold")
    ax.text(ami_c, gy-1.1, "Elevada 48–72 h",
            ha="center", fontsize=8, color=INK, style="italic")
    ax.text(ami_c, gy-1.5, "(falsos negativos tardíos)",
            ha="center", fontsize=7.5, color=GREY)
    # legenda (acima das barras, à direita)
    ax.add_patch(Rectangle((gx+gw-4.2, gy+gh+0.1), 0.3, 0.22, facecolor=NAVY_DK))
    ax.text(gx+gw-3.8, gy+gh+0.22, "Sensibilidad",
            ha="left", va="center", fontsize=8, color=INK)
    ax.add_patch(Rectangle((gx+gw-2.0, gy+gh+0.1), 0.3, 0.22, facecolor=GOLD))
    ax.text(gx+gw-1.6, gy+gh+0.22, "Especificidad",
            ha="left", va="center", fontsize=8, color=INK)
    ax.text(bx+bw/2, by+0.3,
            "Criterio Atlanta 2012: lipasa > 3× LSN confirma el diagnóstico.",
            ha="center", fontsize=7.8, color=GREY, style="italic")

    # ----- bloco 2: RX/TC miniaturas tipográficas -----
    def mini_plate(px, py, pw, ph, titulo, achados_pairs, dmark):
        ax.add_patch(FancyBboxPatch((px, py), pw, ph,
                                     boxstyle="round,pad=0.18",
                                     facecolor="white", edgecolor=LINE, lw=0.8))
        # título por ENCIMA del mini-filme (holgado)
        title_h = 0.85
        ax.text(px+0.35, py+ph-0.2, titulo,
                ha="left", va="top", fontsize=10.5, color=NAVY_DK,
                fontweight="bold")
        # mini-filme (bajo el título)
        fx, fy, fw_, fh_ = px+0.35, py+0.3, 4.0, ph-title_h-0.6
        ax.add_patch(Rectangle((fx-0.12, fy-0.12), fw_+0.24, fh_+0.24,
                               facecolor="black", edgecolor="none"))
        ax.add_patch(Rectangle((fx, fy), fw_, fh_, facecolor="#3A3A3A",
                               edgecolor="#111", lw=0.8))
        ax.text(fx+0.2, fy+fh_-0.15, "D", ha="left", va="top",
                fontsize=9, color="white", fontweight="bold", alpha=0.7)
        ax.text(fx+fw_-0.2, fy+fh_-0.15, "I", ha="right", va="top",
                fontsize=9, color="white", fontweight="bold", alpha=0.7)
        ax.text(fx+fw_/2, fy+fh_/2,
                "Imagen original\na insertar con\nmarcaciones",
                ha="center", va="center", fontsize=8, color="white",
                alpha=0.5, style="italic", linespacing=1.3)
        tx = fx+fw_+0.4
        ty = py+ph-title_h-0.05
        for head, body in achados_pairs:
            ax.text(tx, ty, "▸ "+head, ha="left", va="top",
                    fontsize=9.2, color=RED, fontweight="bold")
            tty = ty-0.5
            for ln in _wrap(body, 42):
                ax.text(tx+0.15, tty, ln, ha="left", va="top",
                        fontsize=8, color=INK)
                tty -= 0.38
            ty = tty-0.05

    rx_find = [
        ("Sin neumoperitoneo", "Jobert negativo; descarta perforación."),
        ("Borramiento psoas dcho.", "Edema retroperitoneal."),
        ("Asa centinela", "Íleo adinámico focal adyacente."),
    ]
    tc_find = [
        ("Páncreas edematoso", "Tumefacción con realce heterogéneo."),
        ("Líquido y densidad grasa", "Colecciones agudas + borramiento peripancreático."),
        ("Balthazar C–D", "Sin necrosis (>30% áreas sin realce)."),
    ]
    mini_plate(9.6, 7.4, 15.8, 4.6,
               "Radiografía simple de abdomen · decúbito supino",
               rx_find, "D")
    mini_plate(9.6, 2.0, 15.8, 4.8,
               "TC axial c/C (fase portal)",
               tc_find, "D")

    # rodapé
    ax.text(W/2, 0.5,
            "Esquemas del equipo; las figuras macro y H&E originales del caso "
            "se insertan en sus diapositivas marcadas.",
            ha="center", fontsize=8.5, color=GREY, style="italic")
    _save(fig, "lab_imagen_panel")


if __name__ == "__main__":
    print("[figuras] gerando…")
    cascada(); rx(); tc(); macro_moldura(); histo_he(); lab_panel()
    print("[figuras] OK.")
