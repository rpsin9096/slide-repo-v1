# -*- coding: utf-8 -*-
"""Gera assets/ecografia_vesicular_esquema.png: esquema didáctico de ecografía vesicular.

Convención de ultrasonido: lumen anecoico (negro), sombra acústica posterior en negro. El cálculo es
hiperecogénico (blanco); el pólipo, de eco intermedio, similar o algo más ecogénico que la pared,
nunca tan brillante como una litiasis calcificada.

sonda en la parte superior. Es un esquema ilustrativo, no una imagen clínica.
Ejecutar desde la carpeta de la entrega: python tools/diagram_ecografia.py
"""
import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Polygon, Circle, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "ecografia_vesicular_esquema.png")

FAN = "#2e2e2e"
SHADOW = "#000000"
WALL = "#9aa0a6"
TEXT = "#1f2937"
ACCENT = "#D92A2B"
NAVY = "#2B2C4A"

plt.rcParams["font.family"] = "DejaVu Sans"

fig = plt.figure(figsize=(12, 2.05), dpi=250)
fig.patch.set_facecolor("white")

panels = [
    ("A · Bilis normal", "Anecoica: sin ecos internos", "Sin sombra posterior"),
    ("B · Cálculo", "Hiperecogénico y móvil con el decúbito", "Sombra acústica posterior limpia"),
    ("C · Barro biliar", "Ecos bajos que se estratifican", "Sin sombra limpia"),
    ("D · Pólipo", "Fija a la pared; eco intermedio", "No cambia con el decúbito; sin sombra"),
]

random.seed(7)  # speckle reproducible


def fan(ax):
    """Campo de ultrasonido en abanico desde la sonda (parte superior)."""
    ax.add_patch(Polygon([(0.5, 1.0), (0.02, 0.0), (0.98, 0.0)], closed=True,
                         facecolor=FAN, edgecolor="none", zorder=0))
    ax.add_patch(Rectangle((0.44, 0.955), 0.12, 0.045, facecolor="#6b7280",
                           edgecolor="none", zorder=1))  # sonda


def gallbladder(ax):
    """Vesícula en sección sagital: pared y lumen anecoico."""
    lumen = Ellipse((0.5, 0.5), 0.56, 0.52, facecolor="#050505", edgecolor=WALL,
                    linewidth=1.6, zorder=2)
    ax.add_patch(lumen)
    return lumen


for i, (title, line1, line2) in enumerate(panels):
    ax = fig.add_axes([0.012 + i * 0.247, 0.30, 0.23, 0.58])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor="#111827", edgecolor="none", zorder=-1))
    fan(ax)
    lumen = gallbladder(ax)

    if i == 1:  # cálculo: foco hiperecogénico + cono de sombra posterior
        ax.add_patch(Polygon([(0.455, 0.585), (0.545, 0.585), (0.66, 0.0), (0.34, 0.0)],
                             closed=True, facecolor=SHADOW, edgecolor="none", alpha=0.95, zorder=3))
        ax.add_patch(Circle((0.5, 0.63), 0.045, facecolor="#f8f8f8", edgecolor="none", zorder=4))
        ax.annotate("eco intenso", xy=(0.56, 0.63), xytext=(0.16, 0.80),
                    fontsize=6.6, color="white", ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color="white", lw=0.7), zorder=5)
        ax.annotate("sombra", xy=(0.62, 0.22), xytext=(0.70, 0.36),
                    fontsize=6.6, color="white", ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color="white", lw=0.7), zorder=5)

    if i == 2:  # barro: capa de ecos bajos en declive (zona dependiente)
        clip = Ellipse((0.5, 0.5), 0.56, 0.52, transform=ax.transData)
        for _ in range(700):
            x = random.uniform(0.25, 0.75)
            y = random.uniform(0.25, 0.40)
            ax.add_patch(Circle((x, y), random.uniform(0.004, 0.011),
                                facecolor="#9ca3af", edgecolor="none", alpha=0.85, zorder=3))
        level = Rectangle((0.2, 0.25), 0.6, 0.155, facecolor="none", edgecolor="none", zorder=3)
        ax.add_patch(level)
        for p in ax.patches[-700:]:
            p.set_clip_path(clip)
        ax.plot([0.22, 0.78], [0.40, 0.41], color="#cbd5e1", lw=0.7, zorder=4)
        ax.annotate("nivel", xy=(0.74, 0.405), xytext=(0.80, 0.80),
                    fontsize=6.6, color="white", ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color="white", lw=0.7), zorder=5)

    if i == 3:  # pólipo: masa adherida a la pared, sin sombra; eco intermedio (no blanco como el cálculo)
        ax.add_patch(Circle((0.5, 0.735), 0.05, facecolor="#aab1bb", edgecolor="none", zorder=4))
        ax.annotate("adherido", xy=(0.55, 0.735), xytext=(0.74, 0.90),
                    fontsize=6.6, color="white", ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color="white", lw=0.7), zorder=5)

    ax.set_title(title, fontsize=9.5, color=NAVY, fontweight="bold", pad=3, loc="left")
    fig.text(0.012 + i * 0.247, 0.205, line1, fontsize=7.6, color=TEXT, ha="left", va="center")
    fig.text(0.012 + i * 0.247, 0.11, line2, fontsize=7.6, color=ACCENT, ha="left", va="center",
             fontweight="bold")

fig.text(0.012, 0.035, "Esquema didáctico de ultrasonido sagital: sonda arriba, lumen anecoico en negro. "
                      "Ilustración, no imagen clínica.", fontsize=6.8, color="#6b7280", ha="left", va="center")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, dpi=250, facecolor="white")
print("OK:", os.path.normpath(OUT))
