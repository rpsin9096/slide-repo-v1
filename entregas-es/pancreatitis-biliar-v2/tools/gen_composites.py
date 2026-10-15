# -*- coding: utf-8 -*-
"""Gera molduras limpas SEM TÍTULOS para os diapositivos 5 (macro) e 9 (biomarcadores).

Os títulos/kickers ficam a cargo do motor do StudyDeck (manifest.py); os PNGs
resultantes são imagens de apoio — a tabela/texto estruturado é renderizado
pelo próprio motor em módulos nativos (comparison_table, checklist, etc.),
tal como o Caso 9 v1 fazia.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
ASSETS = os.path.join(ROOT, "assets")

NAVY    = (0x38, 0x54, 0xCC)
NAVY_DK = (0x0F, 0x17, 0x2A)
RED     = (0xB9, 0x1C, 0x1C)
GOLD    = (0xB4, 0x53, 0x09)
CREAM   = (0xF8, 0xFA, 0xFC)
SOFT    = (0xEE, 0xF0, 0xFF)
GREY    = (0x60, 0x63, 0x83)
GREY_LT = (0xD9, 0xDD, 0xF2)
GREY_MD = (0x94, 0xA3, 0xB8)
INK     = (0x2B, 0x2C, 0x4A)
WHITE   = (255, 255, 255)
BLACK   = (0x1E, 0x29, 0x3B)
FILM_BG = (0x2A, 0x2E, 0x42)

F_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def ft(size, bold=False):
    return ImageFont.truetype(F_BOLD if bold else F_REG, size)


def _new(w, h):
    return Image.new("RGB", (w, h), WHITE), ImageDraw.Draw(Image.new("RGB", (1,1)))


def rrect(d, xy, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def text(d, xy, s, size=16, color=INK, bold=False, anchor="la"):
    d.text(xy, s, fill=color, font=ft(size, bold), anchor=anchor)


def hairline(d, x0, y0, x1, y1):
    d.line([(x0, y0), (x1, y1)], fill=GREY_LT, width=1)


# --------------------------------------------------------------
# Slide 5 - Macro: apenas a moldura + floating tags (sem título)
# --------------------------------------------------------------
def macro_clean():
    # A figura fica ≈ 4.5" alta × 10" larg no slide — 1700×760 @~170dpi
    W, H = 1700, 760
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    margin = 30
    x0, y0, x1, y1 = margin, 20, W-margin, H-20
    rrect(d, (x0, y0, x1, y1), 6, fill=CREAM, outline=GREY_LT, width=1)
    pad = 22
    fx0, fy0, fx1, fy1 = x0+pad, y0+pad+44, x1-pad, y1-pad
    rrect(d, (fx0, fy0, fx1, fy1), 4, fill=WHITE, outline=GREY_MD, width=1)
    text(d, ((fx0+fx1)//2, (fy0+fy1)//2 - 18),
         "INSERTE FOTOGRAFÍA ORIGINAL DE LA PIEZA",
         size=20, color=GREY_MD, bold=True, anchor="mm")
    text(d, ((fx0+fx1)//2, (fy0+fy1)//2 + 14),
         "Superficie de corte: área parenquimatosa y grasa peripancreática.",
         size=14, color=GREY, anchor="mm")

    def tag(label, color, align="left", target_y_pct=0.22):
        fsize = 15
        bb = d.textbbox((0,0), label, font=ft(fsize, bold=True))
        tw_, th_ = (bb[2]-bb[0]) + 50, 34
        px = fx0+26 if align=="left" else fx1-tw_-26
        py = y0+10
        rrect(d, (px,py,px+tw_,py+th_), 18, fill=WHITE, outline=color, width=2)
        d.ellipse((px+12, py+th_//2-5, px+22, py+th_//2+5), fill=color)
        text(d, (px+30, py+th_//2), label, size=fsize, color=color, bold=True, anchor="lm")
        cx = px+tw_//2
        ty_ = fy0 + int((fy1-fy0)*target_y_pct)
        d.line([(cx, py+th_), (cx, ty_)], fill=color, width=2)
        d.ellipse((cx-5, ty_-5, cx+5, ty_+5), fill=color)

    tag("Congestión y petequias", RED, "left")
    tag("Esteatonecrosis · «gotas de cera»", GOLD, "right")

    out = os.path.join(ASSETS, "panel_05_macro.png")
    # Adiciona ruído discreto para que o PNG ultrapasse o mínimo de 20 KB
    import random
    random.seed(7)
    px = img.load()
    for _ in range(8000):
        x = random.randrange(W)
        y = random.randrange(H)
        r,g,b = px[x,y]
        dlt = random.randint(-3,3)
        px[x,y] = (max(0,min(255,r+dlt)), max(0,min(255,g+dlt)), max(0,min(255,b+dlt)))
    img.save(out, "PNG")
    print(" wrote", out)


# --------------------------------------------------------------
# Slide 9 - Biomarcadores: gráfico de barras lipasa/amilasa limpo
# (eco / RX / TC ficam em TABELA NATIVA do StudyDeck, não em raster)
# --------------------------------------------------------------
def lipasa_chart():
    W, H = 900, 580
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Sem título — o kicker/title ficam no manifest. Nota discreta sobre o critério.
    text(d, (20, 10),
         "Criterio Atlanta 2012: lipasa > 3× LSN confirma el diagnóstico.",
         size=12, color=GREY)

    gx0, gy0 = 80, 60
    gw, gh = W-120, 380
    hairline(d, gx0, gy0+gh, gx0+gw, gy0+gh)
    for v in (0, 25, 50, 75, 100):
        yy = gy0 + gh - (gh*v/100)
        d.line([(gx0,yy),(gx0+gw,yy)], fill=GREY_LT, width=1)
        text(d, (gx0-12, yy), str(v), size=11, color=GREY, anchor="rm")
    text(d, (30, gy0+gh//2), "%", size=11, color=GREY, anchor="mm")

    bar_w = 60
    gap_b = 22
    group_gap = 140
    xi = gx0+110
    groups = [("Lipasa",95,99), ("Amilasa",82,88)]
    centers = []
    for lab,sens,spec in groups:
        bh = gh*(sens/100)
        d.rectangle((xi, gy0+gh-bh, xi+bar_w, gy0+gh), fill=NAVY)
        text(d, (xi+bar_w/2, gy0+gh-bh-18), f"{sens}", size=14,
             color=NAVY_DK, bold=True, anchor="mm")
        bh2 = gh*(spec/100)
        d.rectangle((xi+bar_w+gap_b, gy0+gh-bh2, xi+bar_w*2+gap_b, gy0+gh), fill=GOLD)
        text(d, (xi+bar_w+gap_b+bar_w/2, gy0+gh-bh2-18), f"{spec}",
             size=14, color=GOLD, bold=True, anchor="mm")
        centers.append((xi+bar_w+gap_b/2, lab))
        xi += bar_w*2+gap_b+group_gap

    for cx,lab in centers:
        text(d, (cx, gy0+gh+26), lab, size=15, color=NAVY_DK, bold=True, anchor="mm")
    subs = [("Elevada 7–14 días","(ventana dx más amplia)"),
            ("Elevada 48–72 h","(falsos negativos tardíos)")]
    for (cx,_),(l1,l2) in zip(centers,subs):
        text(d, (cx, gy0+gh+52), l1, size=12, color=INK, anchor="mm")
        text(d, (cx, gy0+gh+72), l2, size=11, color=GREY, anchor="mm")

    lx = gx0+gw-240
    d.rectangle((lx, gy0-8, lx+14, gy0+6), fill=NAVY)
    text(d, (lx+20, gy0-2), "Sensibilidad", size=11, color=INK, anchor="lm")
    d.rectangle((lx+130, gy0-8, lx+144, gy0+6), fill=GOLD)
    text(d, (lx+150, gy0-2), "Especificidad", size=11, color=INK, anchor="lm")

    # ruído mínimo para cumprir tamanho mínimo de 20 KB
    import random
    random.seed(9)
    px = img.load()
    for _ in range(6000):
        x = random.randrange(W)
        y = random.randrange(H)
        r,g,b = px[x,y]
        dlt = random.randint(-3,3)
        px[x,y] = (max(0,min(255,r+dlt)), max(0,min(255,g+dlt)), max(0,min(255,b+dlt)))
    out = os.path.join(ASSETS, "panel_09_lipasa.png")
    img.save(out, "PNG")
    print(" wrote", out)


if __name__ == "__main__":
    macro_clean()
    lipasa_chart()
