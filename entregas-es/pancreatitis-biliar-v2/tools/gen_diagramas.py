# -*- coding: utf-8 -*-
"""Diagramas estilo «textbook médico» para el Caso 09 v2.

Genera cada figura como SVG vectorial Y como PNG a 300 DPI (el motor StudyDeck
sólo acepta .jpg/.png, pero mantenemos el SVG como fuente editable). Las
figuras se rediseñan con estilo limpio de atlas médico (paleta sobria, línea
fina, tipografía serif/sans elegante), sustituyendo los esquemas de bloques
anteriores.

Figuras producidas:
  1. cascada_etiopato.svg/png         – 4 etapas fisiopatológicas (ductal).
  2. rx_abdomen.svg/png               – RX simple con borramiento del psoas.
  3. tc_axial_pancreas.svg/png        – Corte axial TC con contraste.
  4. lab_imagen_panel.svg/png         – Panel lipasa + RX + TC (slide 9+10).
  5. macro_placeholder.svg/png        – Esquema didáctico de la pieza macro
                                        (sustituye temporalmente a la foto
                                        original sin pretender serla; el
                                        placeholder real se mantiene en la
                                        slide 5 y 6).
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import (Circle, Ellipse, FancyArrowPatch,
                                FancyBboxPatch, Polygon, Wedge)
import numpy as np

import textwrap

# ---------- estilo ---------------------------------------------------------
mpl.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.serif": ["DejaVu Serif", "Liberation Serif"],
    "font.size": 11,
    "axes.linewidth": 0.8,
    "axes.edgecolor": "#2A2A2A",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
})

NAVY = "#1F3A5F"
NAVY_DK = "#12273F"
RED = "#9B2C2C"
GOLD = "#B08D2A"
TEAL = "#2C6E7A"
INK = "#1A1A1A"
GREY = "#5C5C5C"
SOFT = "#F4F1EA"
PANEL = "#FBF8F2"
ARROW = "#B03A2E"

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
SVG = HERE.parent / "assets-svg"
ASSETS.mkdir(exist_ok=True)
SVG.mkdir(exist_ok=True)


def _save(fig: plt.Figure, stem: str) -> None:
    png = ASSETS / f"{stem}.png"
    svg = SVG / f"{stem}.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, format="svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {png.name}  +  {svg.name}")


# ---------------------------------------------------------------------------
# 1) Cascada etiopatogénica — ductus pancreaticus longitudinal
# ---------------------------------------------------------------------------
def cascada() -> None:
    fig, ax = plt.subplots(figsize=(13.5, 7.2))
    ax.set_xlim(0, 27); ax.set_ylim(0, 14); ax.set_aspect('equal'); ax.axis('off')

    ax.text(13.5, 13.2,
            "Cascada etiopatogénica de la pancreatitis aguda biliar",
            ha='center', fontsize=15, fontweight='bold', color=NAVY_DK)
    ax.text(13.5, 12.55,
            "De la migración litiásica a la autodigestión enzimática del parénquima",
            ha='center', fontsize=10.5, color=GREY, style='italic')

    # conducto de Wirsung como conducto anastomosado que cruza la diapositiva
    duct_y = 8.0
    # cuerpo del conducto
    ax.add_patch(FancyBboxPatch((0.5, duct_y - 0.45), 26.0, 0.9,
                                 boxstyle="round,pad=0.02",
                                 facecolor="#FFF6E0", edgecolor=NAVY, lw=1.6))
    # ampolla de Vater
    ax.add_patch(patches.Wedge((26.0, duct_y), 1.2, -65, 65,
                                facecolor="#FCE1B5", edgecolor=NAVY, lw=1.6))
    # esfínter de Oddi (anillo)
    for r in (1.35, 1.55):
        ax.add_patch(patches.Arc((26.0, duct_y), 2*r, 2*r, angle=0,
                                 theta1=-70, theta2=70, color=NAVY_DK, lw=1.0))
    ax.text(26.4, duct_y - 1.85, "Ampolla de Vater / esfínter de Oddi",
            ha='center', fontsize=9, color=NAVY_DK, style='italic')

    # vesícula + colédoco (esquina superior izq)
    ax.add_patch(Ellipse((1.5, 10.6), 1.6, 2.3, facecolor="#9DB7C9",
                          edgecolor=NAVY, lw=1.2))
    ax.plot([1.5, 3.6], [9.4, duct_y + 0.4], color=NAVY, lw=2.0)  # cístico
    ax.plot([3.6, 6.0], [duct_y + 0.4, duct_y + 0.4], color=NAVY, lw=2.4)  # colédoco desciende
    ax.text(1.5, 12.0, "Vesícula biliar", ha='center', fontsize=9, color=NAVY_DK)

    # cálculo que migra (piedra) cerca de la ampolla
    stone_x = 23.6
    ax.add_patch(patches.Polygon(
        [(stone_x-0.35, duct_y), (stone_x-0.15, duct_y+0.35),
         (stone_x+0.25, duct_y+0.3), (stone_x+0.4, duct_y-0.1),
         (stone_x+0.15, duct_y-0.4), (stone_x-0.25, duct_y-0.25)],
        closed=True, facecolor="#6B5A3E", edgecolor="#2C2414", lw=1.2))
    ax.annotate("Microcálculo impactado\nen tránsito",
                xy=(stone_x, duct_y + 0.3), xytext=(20.3, 11.2),
                fontsize=9, ha='center', color=ARROW, fontweight='bold',
                arrowprops=dict(arrowstyle="->", color=ARROW, lw=1.3,
                                connectionstyle="arc3,rad=-0.18"))

    # 4 cuadros numerados bajo el conducto
    boxes = [
        ("1", "Tríptico obstructor",
         "Migración del cálculo → impactación transitoria en la ampolla; "
         "hipertensión retrógrada en Wirsung y reflujo biliar.", NAVY_DK),
        ("2", "Disfunción secretora",
         "Bloqueo de la exocitosis apical; co-localización de zimógenos "
         "con hidrolasas lisosomales.", "#284E72"),
        ("3", "Conversión prematura de tripsina",
         "Catepsina B cliva el tripsinógeno a tripsina activa; se sobrepasa la "
         "capacidad del inhibidor SPINK1.", "#7A2A1F"),
        ("4", "Autodigestión glandular",
         "Elastasa → hemorragia vascular; Fosfolipasa A2 → lisis membranal; "
         "Lipasa → esteatonecrosis con saponificación cálcica.", "#5B2020"),
    ]
    bw = 5.9
    gap = 0.35
    total_w = len(boxes) * bw + (len(boxes) - 1) * gap
    x0 = (27 - total_w) / 2
    bx_x = [x0 + i * (bw + gap) for i in range(len(boxes))]
    box_top_y = 5.5
    box_h = 3.8
    for x, (num, title, body, col) in zip(bx_x, boxes):
        box = FancyBboxPatch((x, 1.0), bw, box_h,
                              boxstyle="round,pad=0.15",
                              facecolor="white", edgecolor=col, lw=1.6)
        ax.add_patch(box)
        # franja de color superior
        ax.add_patch(patches.Rectangle((x + 0.15, box_top_y - 0.1), bw - 0.3, 0.8,
                                        facecolor=col, edgecolor='none', alpha=0.12))
        # número en círculo (fuera, encima de la franja)
        ax.add_patch(Circle((x + 0.7, box_top_y + 0.3), 0.42, facecolor=col,
                             edgecolor=col, zorder=3))
        ax.text(x + 0.7, box_top_y + 0.3, num, ha='center', va='center',
                fontsize=12, color='white', fontweight='bold', zorder=4)
        # título del cuadro: se anida y se envuelve si hace falta
        title_wrapped = "\n".join(textwrap.wrap(title, width=30))
        ax.text(x + 1.5, box_top_y + 0.3, title_wrapped, ha='left', va='center',
                fontsize=10.5, color=col, fontweight='bold')
        # cuerpo (3 líneas aprox.)
        body_wrapped = "\n".join(textwrap.wrap(body, width=42))
        ax.text(x + 0.3, box_top_y - 0.25, body_wrapped, ha='left', va='top',
                fontsize=8.7, color=INK, linespacing=1.3)
        # flecha vertical desde el conducto
        cx = x + bw / 2
        ax.annotate("", xy=(cx, box_top_y + 0.25), xytext=(cx, duct_y - 0.45),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=1.4,
                                    mutation_scale=12))

    # flechas de secuencia entre cajas (sencillas)
    seq_y = 2.9
    for i in range(3):
        x_start = bx_x[i] + bw - 0.15
        x_end = bx_x[i+1] + 0.15
        ax.annotate("", xy=(x_end, seq_y), xytext=(x_start, seq_y),
                    arrowprops=dict(arrowstyle="-|>", color=GOLD, lw=1.6,
                                    mutation_scale=14))

    # pie
    ax.text(13.5, 0.05,
            "Esquema didáctico — basado en Robbins Patología (cap. 19) y Harrison (cap. 347).",
            ha='center', fontsize=8.5, color=GREY, style='italic')

    _save(fig, "cascada_etiopato")


# ---------------------------------------------------------------------------
# 2) Rx abdomen simple — borramiento del psoas, sin aire libre
# ---------------------------------------------------------------------------
def rx_abdomen() -> None:
    fig, ax = plt.subplots(figsize=(10, 11))
    ax.set_xlim(0, 10); ax.set_ylim(0, 11); ax.set_aspect('equal'); ax.axis('off')
    # tono placa
    ax.add_patch(patches.Rectangle((0, 0), 10, 11, facecolor="#FAF8F3"))
    ax.add_patch(patches.Rectangle((0.3, 0.3), 9.4, 10.4, fill=False,
                                    ec=GREY, lw=1))

    # diafragmas
    ax.plot([0.4, 5, 9.6], [8.7, 9.2, 8.7], color=INK, lw=2.2)
    # leyenda «sin aire libre» debajo de la cúpula (una sola flecha central)
    ax.annotate("Cúpulas diafragmáticas: sin aire libre subdiafragmático",
                xy=(5, 9.2), xytext=(5, 9.8), fontsize=9, ha='center',
                color=GOLD, fontweight='bold',
                arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.4))

    # columna (centrada)
    for i, y in enumerate(np.linspace(8.4, 1.6, 14)):
        ax.add_patch(patches.FancyBboxPatch((4.72, y-0.2), 0.56, 0.36,
                                             boxstyle="round,pad=0.02",
                                             facecolor="#E2E6EC", ec=INK, lw=0.7))
    # apófisis transversas
    for y in np.linspace(8.0, 1.9, 13):
        ax.plot([4.72, 4.4], [y, y-0.1], color=INK, lw=0.6)
        ax.plot([5.28, 5.6], [y, y-0.1], color=INK, lw=0.6)

    # psoas izquierdo (lado derecho de la imagen = x>5) nítido
    psoas_izq = Polygon([[5.35, 8.0], [5.0, 4.0], [5.7, 1.8], [6.0, 4.0], [5.95, 8.0]],
                        closed=True, facecolor="#E8EDF3", edgecolor=INK, lw=1.6)
    ax.add_patch(psoas_izq)
    ax.annotate("Psoas izquierdo:\ncontorno nítido",
                xy=(6.0, 5.0), xytext=(7.1, 5.0), fontsize=9, color="#1F6E3A",
                arrowprops=dict(arrowstyle="->", color="#1F6E3A", lw=1.4))

    # psoas derecho BORRADO (lado izquierdo de la imagen)
    psoas_der = Polygon([[4.65, 8.0], [5.0, 4.0], [4.3, 1.8], [4.0, 4.0], [4.05, 8.0]],
                        closed=True, facecolor="#F4F5F7", edgecolor=INK, lw=0.4, ls=':')
    ax.add_patch(psoas_der)
    edema = Ellipse((4.2, 4.3), 3.3, 3.1, facecolor=RED, alpha=0.10,
                    edgecolor=RED, lw=1.2, ls='--')
    ax.add_patch(edema)
    ax.annotate("Edema retroperitoneal:\nborramiento del contorno\ndel psoas derecho",
                xy=(3.4, 4.3), xytext=(0.5, 2.0), fontsize=9.5, color=RED,
                fontweight='bold',
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.8))

    # gases intestinales (burbujas irregulares)
    rng = np.random.default_rng(3)
    for (cx, cy, r) in [(2.0, 7.0, .6), (3.0, 6.0, .5), (2.3, 3.0, .65),
                        (7.5, 6.5, .7), (8.2, 3.8, .55), (7.2, 2.6, .5),
                        (1.5, 4.6, .4), (8.8, 5.6, .35)]:
        ax.add_patch(Circle((cx, cy), r, facecolor="#202020", alpha=0.7))
    ax.text(1.2, 8.1, "Gases intestinales", fontsize=8.5, color=GREY)

    # asa centinela (una asa de ID dilatada)
    ax.add_patch(Ellipse((6.5, 7.4), 1.5, 0.55, facecolor="#202020", alpha=0.8))
    ax.annotate("Asa centinela", xy=(6.5, 7.0), xytext=(8.0, 7.8),
                fontsize=8.5, color=GREY, style='italic',
                arrowprops=dict(arrowstyle="->", color=GREY, lw=0.9))

    ax.text(5, 10.6, "Radiografía simple de abdomen",
            ha='center', fontsize=13, fontweight='bold', color=NAVY_DK)
    ax.text(5, 10.25, "Esquema didáctico · sin neumoperitoneo · edema retroperitoneal",
            ha='center', fontsize=9, color=GREY, style='italic')

    _save(fig, "rx_abdomen")


# ---------------------------------------------------------------------------
# 3) TC axial — páncreas hipoatenuado + colecciones peripancreáticas
# ---------------------------------------------------------------------------
def tc_axial() -> None:
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(-6, 6); ax.set_ylim(-6, 6); ax.set_aspect('equal'); ax.axis('off')

    # capas de la pared abdominal
    ax.add_patch(Ellipse((0, 0), 11.2, 8.8, facecolor="#F2E6D2", ec=INK, lw=1.6))   # piel
    ax.add_patch(Ellipse((0, 0), 10.7, 8.4, facecolor="#E8D1AD", ec=None))          # panículo adiposo
    ax.add_patch(Ellipse((0, 0), 9.9, 7.5, facecolor="#4A4A4A", ec=None))           # músculo/fascia
    ax.add_patch(Ellipse((0, 0), 9.3, 7.0, facecolor="#2F2F2F", ec=None))           # cavidad peritoneal
    ax.add_patch(Ellipse((0, 0), 8.8, 6.6, facecolor="#3C3C3C", ec=None))           # grasa retroperitoneal/omental

    # columna vertebral
    ax.add_patch(Wedge((0, -3.5), 1.0, 30, 150, facecolor="#EFE6D2", ec=INK, lw=1.2))
    ax.add_patch(patches.Rectangle((-0.15, -3.2), 0.3, 0.6, facecolor="#D6CBB0", ec=INK, lw=0.6))

    # Aorta (anterior a la vértebra)
    ax.add_patch(Circle((0, -2.45), 0.55, facecolor="#D6D6D6", ec=INK, lw=1))
    ax.text(0.05, -3.15, "Ao", fontsize=8, ha='center', color=INK)
    # VCI
    ax.add_patch(Circle((1.25, -2.6), 0.45, facecolor="#C9C9C9", ec=INK, lw=1))
    ax.text(1.25, -3.15, "VCI", fontsize=8, ha='center', color=INK)
    # tronco celiaco / MS (pequeñas ramas)
    ax.plot([0, -0.8], [-2.0, -1.4], color="#B8B8B8", lw=0.9)
    ax.plot([0, 0.8], [-2.0, -1.4], color="#B8B8B8", lw=0.9)

    # Hígado (lado DERECHO del paciente → lado izquierdo de la imagen? ATENCIÓN:
    # convención radiológica: el lado derecho del PACIENTE queda a la IZQUIERDA
    # del visor. En la consigna se representa con flechas; usamos esa convención.)
    liver = Ellipse((-3.2, 1.0), 4.6, 4.2, facecolor="#7C4F39", ec=INK, lw=1.2, hatch='....')
    ax.add_patch(liver)
    ax.text(-3.4, 2.9, "Hígado", color="white", fontsize=11, fontweight='bold')
    # Vena porta
    ax.plot([-1.7, -2.6], [-0.5, 0.6], color="#4A2C1E", lw=1.5)

    # Bazo (lado izquierdo del paciente → derecho del visor)
    spleen = Ellipse((3.5, 1.4), 2.2, 3.4, facecolor="#6E3F4F", ec=INK, lw=1.2, hatch='....')
    ax.add_patch(spleen)
    ax.text(4.0, 1.6, "Bazo", color="white", fontsize=11, fontweight='bold')

    # Riñones
    ax.add_patch(Ellipse((-2.5, -1.3), 1.6, 2.4, facecolor="#8C5E48", ec=INK, lw=1))
    ax.add_patch(Ellipse((2.5, -1.3), 1.6, 2.4, facecolor="#8C5E48", ec=INK, lw=1))
    ax.text(-3.4, -1.3, "Riñón\nder.", color="white", fontsize=8, ha='center')
    ax.text(3.4, -1.3, "Riñón\nizq.", color="white", fontsize=8, ha='center')

    # Estómago (cámara gástrica con aire)
    ax.add_patch(Ellipse((1.2, 1.6), 2.0, 1.2, facecolor="#1B1B1B", ec=INK, lw=1))
    ax.text(1.2, 1.6, "Estómago", color="white", fontsize=8, ha='center')
    # Duodeno en C alrededor de la cabeza del páncreas
    ax.plot([1.8, 2.5, 2.2, 1.4], [0.9, 0.2, -0.8, -1.0], color="#5E3C2C", lw=2)

    # Vías biliares: colédoco del hilio hepático a la cabeza pancreática
    ax.plot([-1.6, -0.2], [0.6, -0.3], color="#F5E6C2", lw=1.8)

    # PÁNCREAS (orientado oblicuamente: cabeza en C duodenal, cuerpo sobre aorta, cola al bazo)
    pan = patches.FancyBboxPatch((-2.2, -0.55), 4.8, 1.1,
                                  boxstyle="round,pad=0.15",
                                  facecolor="#7A8998", edgecolor=NAVY_DK, lw=2.2)
    # rotamos un poquito para dar naturalidad anatómica
    from matplotlib.transforms import Affine2D
    t = Affine2D().rotate_deg_around(0.1, 0.0, -6) + ax.transData
    pan.set_transform(t)
    ax.add_patch(pan)
    ax.text(0.0, 0.0, "Páncreas edematoso", ha='center', va='center',
            fontsize=10, color='white', fontweight='bold', transform=t)

    # COLECCIONES LÍQUIDAS agudas peripancreáticas (hipodensas, azul petróleo)
    fluid_col = "#0D1F3D"
    ax.add_patch(Ellipse((-1.6, -1.5), 3.0, 0.9, facecolor=fluid_col,
                          edgecolor=GOLD, lw=2, ls='--'))
    ax.add_patch(Ellipse((1.5, -1.3), 2.2, 0.8, facecolor=fluid_col,
                          edgecolor=GOLD, lw=2, ls='--'))
    ax.add_patch(Ellipse((0.0, -2.0), 1.0, 0.45, facecolor=fluid_col,
                          edgecolor=GOLD, lw=2, ls='--'))
    # grasa peripancreática «estranded» (rayas sutiles)
    for ang in np.linspace(-60, 240, 28):
        x0 = 0.0 + 2.0*np.cos(np.radians(ang))
        y0 = 0.0 + 1.0*np.sin(np.radians(ang))
        x1 = 0.0 + 2.5*np.cos(np.radians(ang))
        y1 = 0.0 + 1.4*np.sin(np.radians(ang))
        ax.plot([x0, x1], [y0, y1], color="#8A8A8A", lw=0.4, alpha=0.6)

    # Flechas de leyenda
    ax.add_patch(FancyArrowPatch((-4.7, -4.8), (-1.5, -1.4),
                                  arrowstyle='-|>,head_width=6,head_length=10',
                                  color=GOLD, lw=2.2))
    ax.text(-5.8, -5.2, "Colecciones líquidas\nperipancreáticas agudas",
            color=GOLD, fontsize=10, fontweight='bold', ha='left')

    ax.add_patch(FancyArrowPatch((4.3, -4.8), (1.0, -0.2),
                                  arrowstyle='-|>,head_width=6,head_length=10',
                                  color=RED, lw=2.2))
    ax.text(3.2, -5.4, "Parénquima hipoatenuado\n(edema intersticial)",
            color=RED, fontsize=10, fontweight='bold', ha='center')

    # marcadores A-P-D-I
    ax.text(-5.7, 5.4, "D", fontsize=15, fontweight='bold', color=GOLD)
    ax.text(5.2, 5.4, "I", fontsize=15, fontweight='bold', color=GOLD)
    ax.text(0, 5.5, "A", fontsize=15, fontweight='bold', color=GOLD)
    ax.text(0, -5.7, "P", fontsize=15, fontweight='bold', color=GOLD)

    ax.text(0, 5.9, "TC axial con contraste (fase portal) — esquema didáctico",
            ha='center', fontsize=13, fontweight='bold', color=NAVY_DK)
    ax.text(0, 5.4, "Páncreas edematoso hipoatenuado con colecciones líquidas peripancreáticas",
            ha='center', fontsize=9.5, color="#DDD", style='italic')

    _save(fig, "tc_axial_pancreas")


# ---------------------------------------------------------------------------
# 4) Panel bioquímica + RX + TC (slide 9/10)
# ---------------------------------------------------------------------------
def panel() -> None:
    rx = plt.imread(ASSETS / "rx_abdomen.png")
    tc = plt.imread(ASSETS / "tc_axial_pancreas.png")

    fig = plt.figure(figsize=(14, 8))
    fig.patch.set_facecolor('white')

    # Título
    fig.text(0.5, 0.96, "Patrón bioquímico e imagenológico",
             ha='center', fontsize=15, fontweight='bold', color=NAVY_DK)
    fig.text(0.5, 0.92, "Lipasa sérica como estándar · RX simple · TC axial con contraste",
             ha='center', fontsize=10, color=GREY, style='italic')

    # Panel IZQ: lipasa vs amilasa
    ax = fig.add_axes([0.03, 0.08, 0.26, 0.78])
    ax.set_facecolor(PANEL)
    labels = ["Lipasa", "Amilasa"]
    sens = [95, 82]
    spec = [99, 88]
    thalf = [11, 2.5]  # días
    x = np.arange(2); w = 0.34
    ax.bar(x - w/2, sens, w, color=NAVY, label="Sensibilidad (%)", edgecolor='white')
    ax.bar(x + w/2, spec, w, color=GOLD, label="Especificidad (%)", edgecolor='white')
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylim(0, 115); ax.set_ylabel("%", fontsize=9)
    ax.set_title("Lipasa vs Amilasa sérica", fontsize=12, fontweight='bold',
                 color=NAVY_DK, pad=8)
    for i, v in enumerate(sens):
        ax.text(i - w/2, v + 2, f"{v}%", ha='center', fontsize=9, color=INK)
    for i, v in enumerate(spec):
        ax.text(i + w/2, v + 2, f"{v}%", ha='center', fontsize=9, color=INK)
    for i, h in enumerate(thalf):
        ax.text(i, 8, f"t½ ≈ {h} d", ha='center', fontsize=10, color=RED,
                fontweight='bold')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2,
              fontsize=8, frameon=False)
    fig.text(0.03, 0.02,
             "Lipasa > 3× LSN (Atlanta 2012).\nElevación más prolongada: evita\nfalsos negativos tardíos.",
             fontsize=9, color=INK)

    # Centro: RX
    axr = fig.add_axes([0.32, 0.20, 0.30, 0.66])
    axr.imshow(rx); axr.axis('off')
    axr.set_title("Radiografía simple", fontsize=12, fontweight='bold',
                   color=NAVY_DK, pad=6)
    fig.text(0.47, 0.16,
             "Negativo para neumoperitoneo   ● Borramiento del psoas (edema retroperitoneal)",
             ha='center', fontsize=9, color=INK,
             bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=NAVY, lw=0.8))

    # Der: TC
    axt = fig.add_axes([0.65, 0.20, 0.30, 0.66])
    axt.imshow(tc); axt.axis('off')
    axt.set_title("Tomografía axial contrastada", fontsize=12, fontweight='bold',
                   color=NAVY_DK, pad=6)
    fig.text(0.80, 0.16,
             "↓ Páncreas hipoatenuado   ● Colecciones peripancreáticas (Balthazar)",
             ha='center', fontsize=9, color=INK,
             bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=NAVY, lw=0.8))

    fig.text(0.5, 0.005,
             "Esquemas didácticos señalizados · las figuras macro y H&E originales del caso se preservan en su plaza marcada.",
             ha='center', fontsize=8, color=GREY, style='italic')

    _save(fig, "lab_imagen_panel")


# ---------------------------------------------------------------------------
# 5) Esquema sustitutivo de la pieza macro (NO reemplaza la foto real; se usa
#    sólo si el placeholder de studydeck no se ve bien). Esta NO se inserta
#    en el manifest final; se genera como referencia visual para el equipo.
# ---------------------------------------------------------------------------
def macro_esquema() -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 22); ax.set_ylim(0, 14); ax.set_aspect('equal'); ax.axis('off')

    ax.text(11, 13.3, "Pieza pancreática: morfología macroscópica",
            ha='center', fontsize=14, fontweight='bold', color=NAVY_DK)
    ax.text(11, 12.7, "Esquema didáctico — NO sustituye la fotografía original del Caso 09",
            ha='center', fontsize=9.5, color=GREY, style='italic')

    # Páncreas como forma alargada con cabeza/cuerpo/cola
    # contorno
    body = patches.FancyBboxPatch((4, 6), 14, 3.0,
                                   boxstyle="round,pad=0.4,rounding_size=1.5",
                                   facecolor="#C99A7B", edgecolor=NAVY_DK, lw=1.8)
    ax.add_patch(body)
    # cabeza (ensanchada)
    head = Ellipse((5.2, 7.5), 3.6, 4.0, facecolor="#B87E61", edgecolor=NAVY_DK, lw=1.8)
    ax.add_patch(head)
    # cola afilada
    tail = Polygon([[17, 6.2], [19.5, 6.8], [19.5, 8.2], [17, 8.8]],
                   closed=True, facecolor="#B87E61", edgecolor=NAVY_DK, lw=1.8)
    ax.add_patch(tail)

    # conducto de Wirsung
    ax.plot([5.8, 18.8], [7.5, 7.5], color="#5C3018", lw=2.0, ls='-')
    ax.text(12.5, 7.9, "Conducto de Wirsung", fontsize=8.5, ha='center',
            color="#5C3018", style='italic')

    # zonas hemorrágicas (parches rojo-vinoso)
    for (cx, cy, r) in [(8, 8.6, 0.9), (11, 8.4, 1.0), (14, 6.6, 0.8),
                        (16.5, 8.3, 0.7), (9.5, 6.5, 0.7)]:
        ax.add_patch(Ellipse((cx, cy), r*1.2, r*0.7, facecolor="#5B1F1F",
                              edgecolor="#320F0F", lw=0.8, alpha=0.85))
    ax.annotate("Necrosis hemorrágica:\nzonas pardo-rojizas/negruzcas\n(digestión vascular por elastasa)",
                xy=(11, 8.4), xytext=(1.2, 11.2), fontsize=9.5, color=RED,
                fontweight='bold',
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.6))

    # esteatonecrosis: gotas blanco-amarillentas en la grasa peripancreática
    rng = np.random.default_rng(11)
    for _ in range(35):
        cx = rng.uniform(3.0, 19.5)
        cy = rng.choice([rng.uniform(4.3, 5.6), rng.uniform(9.3, 10.4)])
        r = rng.uniform(0.15, 0.35)
        ax.add_patch(Ellipse((cx, cy), r*1.1, r*0.8, facecolor="#F0E2C0",
                              edgecolor="#8F7A3D", lw=0.7))
    ax.annotate("Esteatonecrosis en «gotas de cera»:\nplacas blanco-amarillentas en la\ngrasa peripancreática (lipasa → saponificación)",
                xy=(13, 9.8), xytext=(13.5, 11.4), fontsize=9.5, color=GOLD,
                fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.6))

    # etiquetas cabeza/cuerpo/cola
    for (x, lbl) in [(5.2, "Cabeza"), (11.0, "Cuerpo"), (18.0, "Cola")]:
        ax.text(x, 5.0, lbl, ha='center', fontsize=9.5, color=NAVY_DK,
                fontweight='bold')

    _save(fig, "macro_esquema")


if __name__ == "__main__":
    print("[diagramas] generando figuras en estilo textbook…")
    cascada()
    rx_abdomen()
    tc_axial()
    panel()
    macro_esquema()
    print("[diagramas] listo.")
