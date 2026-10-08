# -*- coding: utf-8 -*-
"""Genera cuatro esquemas didácticos de anexo para la sabatina (diapositivas 14-17).

Salidas en assets/:
  anexo_acino_colocalizacion.png   colocalización intra-acinar y activación del tripsinógeno
  anexo_ringer_vs_salina.png       cloruro y lactato: solución fisiológica frente a Ringer lactato
  anexo_histologia_comparativa.png  pancreatitis edematosa frente a necrohemorrágica
  anexo_via_dolor.png              vía del dolor pancreático (aferencias T5–T9)

Son esquemas ilustrativos hechos por código: no son imágenes clínicas del Caso Clínico 09.
Ejecutar desde la carpeta de la entrega: python tools/diagramas_anexo.py
"""
import math
import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle, Polygon, FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
NAVY = "#2B2C4A"
RED = "#D92A2B"
TXT = "#1f2937"
plt.rcParams["font.family"] = "DejaVu Sans"


def arrow(ax, p, q, color="#374151", lw=1.4, style="-|>"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=12, color=color, lw=lw, zorder=6))


def label(ax, x, y, s, size=9.5, color=TXT, weight="normal", ha="center", va="center"):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha, va=va, zorder=7)


def panel_frame(ax, title, color=NAVY):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0,rounding_size=0.03",
                                fc="#fbfaf7", ec="#cbd5e1", lw=1.2, zorder=0))
    label(ax, 0.5, 0.93, title, size=12, color=color, weight="bold")


def save(fig, name):
    os.makedirs(ASSETS, exist_ok=True)
    out = os.path.join(ASSETS, name)
    fig.savefig(out, dpi=200, facecolor="white")
    plt.close(fig)
    print("OK:", os.path.normpath(out))


# ---------------------------------------------------------------- 1. acino
def diagram_acino():
    random.seed(11)
    fig, axes = plt.subplots(1, 3, figsize=(13, 5.2))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.10, wspace=0.04)
    GRAN, LYSO, TRYP, TRYPOGEN = "#2563eb", "#16a34a", "#dc2626", "#9ca3af"

    # A · normal
    ax = axes[0]
    panel_frame(ax, "A · Estado normal")
    ax.add_patch(Ellipse((0.5, 0.56), 0.62, 0.50, fc="#eef4fb", ec="#64748b", lw=1.6, zorder=1))
    ax.add_patch(Ellipse((0.5, 0.75), 0.18, 0.05, fc="#f8fafc", ec="#64748b", lw=1.0, zorder=2))
    label(ax, 0.5, 0.75, "luz", size=7.5, color="#64748b")
    for _ in range(8):
        x, y = random.uniform(0.38, 0.62), random.uniform(0.62, 0.70)
        ax.add_patch(Circle((x, y), 0.02, fc=GRAN, ec="none", zorder=3))
    for _ in range(5):
        x, y = random.uniform(0.38, 0.62), random.uniform(0.40, 0.48)
        ax.add_patch(Circle((x, y), 0.018, fc=LYSO, ec="none", zorder=3))
    label(ax, 0.5, 0.20, "Gránulos de cimógeno (azul), en la zona apical", size=9)
    label(ax, 0.5, 0.12, "Lisosomas (verde), separados", size=9)

    # B · colocalización patológica (dentro de la vacuola ácida)
    ax = axes[1]
    panel_frame(ax, "B · Colocalización patológica", color=RED)
    ax.add_patch(Ellipse((0.5, 0.56), 0.62, 0.50, fc="#eef4fb", ec="#64748b", lw=1.6, zorder=1))
    ax.add_patch(Ellipse((0.5, 0.58), 0.38, 0.24, fc="#fed7aa", ec="#ea580c", lw=1.4, alpha=0.9, zorder=2))
    label(ax, 0.5, 0.735, "vacuola ácida", size=8, color="#9a3412", weight="bold")
    for x, y in [(0.42, 0.58), (0.52, 0.55)]:
        ax.add_patch(Circle((x, y), 0.025, fc=GRAN, ec="none", zorder=3))
    for x, y in [(0.57, 0.60), (0.46, 0.51)]:
        ax.add_patch(Circle((x, y), 0.022, fc=LYSO, ec="none", zorder=3))
    ax.add_patch(Circle((0.55, 0.52), 0.02, fc=TRYPOGEN, ec="none", zorder=4))
    arrow(ax, (0.63, 0.55), (0.57, 0.53), color="#166534", lw=1.2)
    label(ax, 0.73, 0.49, "catepsina B", size=7.5, color="#166534", ha="left")
    ax.add_patch(Polygon([(0.37, 0.42), (0.40, 0.48), (0.43, 0.42), (0.40, 0.36)],
                         closed=True, fc=TRYP, ec="none", zorder=4))
    label(ax, 0.45, 0.42, "tripsina activa", size=8.5, color=RED, weight="bold", ha="left")
    label(ax, 0.5, 0.20, "Gránulo (azul) y lisosoma (verde) en la misma vacuola", size=9)
    label(ax, 0.5, 0.12, "Gris: tripsinógeno · Rojo: tripsina activa, intracelular", size=9, color=RED)

    # C · cascada y lesión de membrana (rótulos fuera de la célula)
    ax = axes[2]
    panel_frame(ax, "C · Cascada intracelular")
    ang = [i * 2 * math.pi / 40 for i in range(40)]
    pts = [(0.5 + 0.25 * (1 + 0.08 * math.sin(3 * a + 1)) * math.cos(a) * 1.25,
            0.52 + 0.22 * (1 + 0.06 * math.cos(5 * a)) * math.sin(a)) for a in ang]
    ax.add_patch(Polygon(pts, closed=True, fc="#fde2e2", ec=RED, lw=1.8, zorder=1))
    for x, y in [(0.42, 0.56), (0.56, 0.48), (0.46, 0.44)]:
        ax.add_patch(Circle((x, y), 0.03, fc="#fca5a5", ec="#b91c1c", lw=0.8, zorder=2))
    ax.add_patch(Circle((0.5, 0.52), 0.035, fc=TRYP, ec="none", zorder=3))
    label(ax, 0.18, 0.80, "Fosfolipasa A2\nlisis de membranas", size=8.5, ha="center")
    label(ax, 0.82, 0.80, "Elastasa\nlesión vascular", size=8.5, ha="center")
    label(ax, 0.18, 0.24, "Lipasa\nesteatonecrosis", size=8.5, ha="center")
    label(ax, 0.82, 0.24, "TNF-α · IL-1 · IL-6\npermeabilidad capilar", size=8.5, ha="center")
    arrow(ax, (0.24, 0.72), (0.38, 0.60), color=RED, lw=1.1)
    arrow(ax, (0.76, 0.72), (0.62, 0.60), color=RED, lw=1.1)
    arrow(ax, (0.24, 0.32), (0.38, 0.44), color=RED, lw=1.1)
    arrow(ax, (0.76, 0.32), (0.62, 0.44), color=RED, lw=1.1)
    label(ax, 0.5, 0.12, "Necrosis, tercer espacio y choque distributivo", size=9, color=RED, weight="bold")

    fig.text(0.01, 0.025, "Esquema didáctico, no imagen clínica. Base: revisión «Trypsin in pancreatitis» (WJG, 2024): "
                          "la activación ocurre en organelas ácidas, no en gránulos de cimógeno.",
             fontsize=8.5, color="#6b7280")
    save(fig, "anexo_acino_colocalizacion.png")


# ---------------------------------------------------------- 2. ringer vs SF
def diagram_ringer():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.10, wspace=0.05)

    def bag(ax, fc):
        ax.add_patch(FancyBboxPatch((0.27, 0.63), 0.46, 0.20, boxstyle="round,pad=0,rounding_size=0.04",
                                    fc=fc, ec="#475569", lw=1.4, zorder=2))
        ax.add_patch(Polygon([(0.47, 0.63), (0.53, 0.63), (0.51, 0.59), (0.49, 0.59)],
                             closed=True, fc="#94a3b8", ec="none", zorder=2))

    def vessel(ax):
        ax.add_patch(FancyBboxPatch((0.06, 0.05), 0.88, 0.10, boxstyle="round,pad=0,rounding_size=0.04",
                                    fc="#fee2e2", ec="#b91c1c", lw=1.2, zorder=1))
        label(ax, 0.5, 0.10, "vena periférica → circulación → páncreas", size=8.5, color="#7f1d1d")

    # A · solución fisiológica
    ax = axes[0]
    panel_frame(ax, "A · Solución fisiológica 0,9 %", color=RED)
    bag(ax, "#dbeafe")
    label(ax, 0.5, 0.79, "SF 0,9 %", size=11, weight="bold")
    label(ax, 0.5, 0.72, "Na⁺ 154 · Cl⁻ 154 mEq/L", size=9.5)
    arrow(ax, (0.5, 0.58), (0.5, 0.56), color="#475569")
    vessel(ax)
    label(ax, 0.5, 0.50, "carga de cloruro elevada", size=9.5)
    label(ax, 0.5, 0.44, "↓ pH: acidosis hiperclorémica (hipótesis)", size=9.5, color=RED, weight="bold")
    label(ax, 0.5, 0.36, "En el acino: posible activación del tripsinógeno", size=9.5)
    label(ax, 0.5, 0.29, "in vitro: a menor pH, mayor autoactivación", size=8.5, color="#6b7280")
    label(ax, 0.5, 0.21, "Riesgo a considerar: acidosis y activación enzimática", size=9.5, color=RED)

    # B · Ringer lactato
    ax = axes[1]
    panel_frame(ax, "B · Ringer lactato", color="#166534")
    bag(ax, "#dcfce7")
    label(ax, 0.5, 0.79, "Ringer lactato", size=11, weight="bold")
    label(ax, 0.5, 0.735, "Na⁺ 130 · K⁺ 4 · Ca²⁺ 2,7 mEq/L", size=8.5)
    label(ax, 0.5, 0.685, "Cl⁻ 109 · lactato 28 mEq/L", size=8.5)
    arrow(ax, (0.5, 0.58), (0.5, 0.56), color="#475569")
    vessel(ax)
    label(ax, 0.5, 0.50, "menor carga de cloruro", size=9.5)
    label(ax, 0.5, 0.44, "lactato → bicarbonato (hígado)", size=9.5, color="#166534", weight="bold")
    label(ax, 0.5, 0.36, "pH cercano a 6,5: levemente ácido, no neutro", size=9.5)
    label(ax, 0.5, 0.29, "menor riesgo de acidosis hiperclorémica", size=9.5)
    label(ax, 0.5, 0.21, "Preferido en la fase inicial (diapositiva 10)", size=9.5, color="#166534", weight="bold")

    fig.text(0.01, 0.025, "Esquema didáctico, no imagen clínica. Composiciones de referencia; el efecto sobre la "
                          "pancreatitis se basa en datos limitados y en inferencia fisiológica.",
             fontsize=8.5, color="#6b7280")
    save(fig, "anexo_ringer_vs_salina.png")


# ---------------------------------------------------------- 3. histología
def diagram_histologia():
    random.seed(5)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.10, wspace=0.05)
    PINK, NUC, FAT = "#e9b8c6", "#4c1d95", "#fdfcfa"

    def acinus(ax, x, y, r, color=PINK):
        ax.add_patch(Circle((x, y), r, fc=color, ec="#a16207", lw=0.6, zorder=2))
        for _ in range(4):
            ax.add_patch(Circle((x + random.uniform(-r * 0.5, r * 0.5), y + random.uniform(-r * 0.5, r * 0.5)),
                                r * 0.10, fc=NUC, ec="none", zorder=3))

    def ghost_fat(ax, x, y, r):
        ax.add_patch(Circle((x, y), r, fc=FAT, ec="#cbd5e1", lw=0.8, zorder=2))
        for _ in range(3):
            ax.add_patch(Circle((x + random.uniform(-r * 0.4, r * 0.4), y + random.uniform(-r * 0.4, r * 0.4)),
                                r * 0.12, fc="#7e22ce", ec="none", zorder=3))

    def tissue(ax):
        ax.add_patch(Polygon([(0.05, 0.14), (0.95, 0.14), (0.95, 0.80), (0.05, 0.80)], closed=True,
                             fc="#fff", ec="none", zorder=0.5))

    # A · edematosa intersticial
    ax = axes[0]
    panel_frame(ax, "A · Pancreatitis edematosa intersticial")
    tissue(ax)
    for x, y in [(0.22, 0.62), (0.45, 0.66), (0.70, 0.60), (0.33, 0.36), (0.62, 0.34)]:
        acinus(ax, x, y, 0.10)
    for x0, y0, x1, y1 in [(0.05, 0.50, 0.95, 0.52), (0.33, 0.20, 0.36, 0.80), (0.58, 0.22, 0.60, 0.80)]:
        ax.add_patch(Polygon([(x0, y0 - 0.03), (x1, y1 - 0.03), (x1, y1 + 0.03), (x0, y0 + 0.03)],
                             closed=True, fc="#f9dfe6", ec="none", zorder=1))
    ghost_fat(ax, 0.84, 0.46, 0.055)
    ghost_fat(ax, 0.15, 0.27, 0.045)
    ax.add_patch(Circle((0.80, 0.22), 0.025, fc="#2563eb", ec="none", zorder=3))
    ax.add_patch(Circle((0.85, 0.24), 0.02, fc="#2563eb", ec="none", zorder=3))
    label(ax, 0.84, 0.66, "adipocitos fantasma\n(saponificación)", size=8.3, ha="center")
    arrow(ax, (0.84, 0.62), (0.84, 0.52), color="#374151", lw=1.1)
    label(ax, 0.5, 0.07, "Septos con edema · acinos viables · vasos conservados", size=8.8)

    # B · necrohemorrágica
    ax = axes[1]
    panel_frame(ax, "B · Pancreatitis necrohemorrágica", color=RED)
    tissue(ax)
    ax.add_patch(Polygon([(0.20, 0.30), (0.46, 0.40), (0.42, 0.66), (0.18, 0.60)], closed=True,
                         fc="#d6d3d1", ec="none", zorder=2))
    ax.add_patch(Polygon([(0.55, 0.50), (0.80, 0.46), (0.82, 0.70), (0.58, 0.72)], closed=True,
                         fc="#d6d3d1", ec="none", zorder=2))
    for _ in range(120):
        x, y = random.uniform(0.18, 0.84), random.uniform(0.22, 0.76)
        ax.add_patch(Circle((x, y), 0.007, fc="#b91c1c", ec="none", zorder=3))
    ax.add_patch(Ellipse((0.66, 0.30), 0.12, 0.07, fc="#7f1d1d", ec="#450a0a", lw=0.8, zorder=3))
    ax.add_patch(Ellipse((0.30, 0.78), 0.10, 0.05, fc="#7f1d1d", ec="#450a0a", lw=0.8, zorder=3))
    acinus(ax, 0.30, 0.52, 0.06, color="#f3e7ea")
    label(ax, 0.66, 0.44, "vaso trombosado", size=8.3, color="#7f1d1d")
    arrow(ax, (0.66, 0.41), (0.66, 0.34), color="#7f1d1d", lw=1.0)
    label(ax, 0.84, 0.62, "hemorragia", size=8.3, color="#b91c1c")
    label(ax, 0.5, 0.07, "Acinos destruidos · necrosis amorfa · eritrocitos extravasados", size=8.8)

    fig.text(0.01, 0.025, "Esquema didáctico de dos patrones, no es la lámina del Caso Clínico 09. Trazos "
                          "simplificados para comparar arquitectura, no para diagnóstico.",
             fontsize=8.5, color="#6b7280")
    save(fig, "anexo_histologia_comparativa.png")



# ---------------------------------------------------------- 4. vía del dolor
def diagram_dolor():
    fig, ax = plt.subplots(1, 1, figsize=(13, 5.2))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.10)
    panel_frame(ax, "Vía del dolor pancreático: aferencias viscerales y proyección")

    stages = [
        ("Páncreas inflamado", "edema, necrosis y", "distensión de la cápsula"),
        ("Fibras aferentes viscerales", "fibras Aδ y C", "nervios esplácnicos"),
        ("Plexo celíaco y médula", "segmentos T5–T9", "asta dorsal, vía espinotalámica"),
        ("Tálamo y corteza", "percepción del dolor", "localización difusa"),
    ]
    x0, w, gap = 0.03, 0.19, 0.06
    for i, (t1, t2, t3) in enumerate(stages):
        x = x0 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 0.53), w, 0.22, boxstyle="round,pad=0,rounding_size=0.03",
                                    fc="#e0e7ff" if i < 3 else "#f1f5f9", ec=NAVY, lw=1.2, zorder=2))
        label(ax, x + w / 2, 0.70, t1, size=9.5, color=NAVY, weight="bold")
        label(ax, x + w / 2, 0.635, t2, size=8.8)
        label(ax, x + w / 2, 0.575, t3, size=8.8, color="#475569")
        if i < len(stages) - 1:
            arrow(ax, (x + w + 0.005, 0.64), (x + w + gap - 0.005, 0.64), color=NAVY, lw=1.6)

    # Dos proyecciones del dolor
    cards = [
        ("Dolor epigástrico", "Proyección anterior de las aferencias pancreáticas en el hemiabdomen superior."),
        ("Irradiación posterior", "Se proyecta hacia la espalda, en el mismo territorio metamérico T5–T9."),
    ]
    cw = 0.45
    for j, (ct, cd) in enumerate(cards):
        cx = 0.03 + j * (cw + 0.04)
        ax.add_patch(FancyBboxPatch((cx, 0.14), cw, 0.26, boxstyle="round,pad=0,rounding_size=0.03",
                                    fc="#fff7ed" if j == 0 else "#fef2f2", ec="#c2410c" if j == 0 else RED,
                                    lw=1.2, zorder=2))
        label(ax, cx + cw / 2, 0.335, ct, size=10.5, color=NAVY, weight="bold")
        label(ax, cx + cw / 2, 0.23, cd, size=9.2)

    label(ax, 0.5, 0.075, "Esquema didáctico, no imagen clínica. Vía simplificada para orientar la anamnesis.",
          size=8.5, color="#6b7280")
    save(fig, "anexo_via_dolor.png")


if __name__ == "__main__":
    diagram_acino()
    diagram_ringer()
    diagram_histologia()
    diagram_dolor()
