# -*- coding: utf-8 -*-
"""Compõe os painéis 5 (macro) e 6 (H&E) com as imagens REAIS do Caso 09
anexadas pelo usuário, com callouts/marcadores limpos e sem molduras
aninhadas.  Os PNGs resultantes ocupam só a área de figura do StudyDeck
(título/kicker/caption ficam no motor)."""

import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
ASSETS = os.path.join(ROOT, "assets")
REAL = os.path.join(ASSETS, "real")

NAVY    = (0x0F, 0x17, 0x2A)
RED     = (0xB9, 0x1C, 0x1C)
GOLD    = (0xB4, 0x53, 0x09)
CREAM   = (0xF8, 0xFA, 0xFC)
GREY    = (0x60, 0x63, 0x83)
GREY_LT = (0xD9, 0xDD, 0xF2)
GREY_MD = (0x94, 0xA3, 0xB8)
WHITE   = (255,255,255)

F_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def ft(s,b=False): return ImageFont.truetype(F_BOLD if b else F_REG, s)


def cover_crop(img, tw, th):
    """Recorte 'cover': preenche tw×th mantendo AR, centraliza."""
    iw, ih = img.size
    s = max(tw/iw, th/ih)
    nw, nh = int(iw*s), int(ih*s)
    r = img.resize((nw, nh), Image.LANCZOS)
    return r.crop(((nw-tw)//2, (nh-th)//2, (nw-tw)//2+tw, (nh-th)//2+th))


def fit_contain(img, tw, th):
    iw, ih = img.size
    s = min(tw/iw, th/ih)
    return img.resize((int(iw*s), int(ih*s)), Image.LANCZOS)


def rrect(d, xy, r, **kw): d.rounded_rectangle(xy, radius=r, **kw)
def text(d, xy, s, size=16, color=NAVY, bold=False, anchor="la"):
    d.text(xy, s, fill=color, font=ft(size,bold), anchor=anchor)


def pill(d, x, y, label, color, pointer_from="bottom"):
    """Desenha uma pill flutuante branca com contorno colorido.
    pointer_from = 'bottom' indica que a ponta da seta está para baixo."""
    fbbox = d.textbbox((0,0), label, font=ft(16, True))
    tw_, th_ = (fbbox[2]-fbbox[0]) + 40, 38
    rrect(d, (x, y, x+tw_, y+th_), 19, fill=WHITE, outline=color, width=2)
    d.ellipse((x+13, y+th_//2-6, x+25, y+th_//2+6), fill=color)
    text(d, (x+33, y+th_//2), label, size=16, color=color, bold=True, anchor="lm")
    return x+tw_//2, y+th_  # ponto onde sai a seta


# --------------------------------------------------------------
# Slide 5 — Macro: foto real com duas pills flutuantes e setas
# --------------------------------------------------------------
def macro_real():
    W, H = 1700, 760
    canvas = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(canvas)

    # Imagem real em cover para preencher a área com uma margem hairline
    pad = 14
    inner = (pad, pad, W-pad, H-pad)
    ix0, iy0, ix1, iy1 = inner
    iw, ih = ix1-ix0, iy1-iy0
    src = Image.open(os.path.join(REAL, "macro_real.png")).convert("RGB")
    photo = cover_crop(src, iw, ih)
    canvas.paste(photo, (ix0, iy0))
    # Moldura fina
    d.rectangle((ix0, iy0, ix1, iy1), outline=GREY_MD, width=1)

    # Barra inferior semi-transparente com legenda técnica
    bar_h = 64
    overlay = Image.new("RGBA", (W,H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((ix0, iy1-bar_h, ix1, iy1), fill=(15,23,42,200))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(canvas)
    text(d, (ix0+22, iy1-bar_h//2),
         "Superficie de corte: glándula tumefacta con áreas pardo-rojizas "
         "(congestión/petequias) y nódulos blanco-amarillentos de esteatonecrosis.",
         size=14, color=WHITE, anchor="lm")
    text(d, (ix1-22, iy1-bar_h//2),
         "Balthazar C-D · pancreatitis edematosa intersticial",
         size=12, color=(226,232,240), anchor="rm")

    # Faixa clara no topo para as pills não se perderem na imagem
    top_band_h = 64
    overlay2 = Image.new("RGBA",(W,H),(0,0,0,0))
    od2 = ImageDraw.Draw(overlay2)
    od2.rectangle((ix0, iy0, ix1, iy0+top_band_h), fill=(248,250,252,235))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay2).convert("RGB")
    d = ImageDraw.Draw(canvas)

    # Pontos-alvo dentro da foto:
    # • vermelho → parênquima congestivo (peça inferior, área róseo-avermelhada)
    # • dourado  → nódulos branco-amarelos de esteatonecrosis (peça da direita)
    target_red  = (ix0 + int(iw*0.18), iy0 + int(ih*0.78))
    target_gold = (ix0 + int(iw*0.76), iy0 + int(ih*0.42))

    # Pills centralizadas horizontalmente sobre os alvos para setas verticais
    red_lbl  = "Congestión y petequias"
    gold_lbl = "Esteatonecrosis · «gotas de cera»"
    red_w  = (d.textbbox((0,0), red_lbl,  font=ft(16,True))[2]) + 40
    gold_w = (d.textbbox((0,0), gold_lbl, font=ft(16,True))[2]) + 40

    px_r = target_red[0]  - red_w//2
    px_g = target_gold[0] - gold_w//2
    px_r = max(ix0+10, min(px_r, ix1-red_w-10))
    px_g = max(ix0+10, min(px_g, ix1-gold_w-10))
    py_pill = iy0+16

    cx_r, py_r = pill(d, px_r, py_pill, red_lbl, RED)
    cx_g, py_g = pill(d, px_g, py_pill, gold_lbl, GOLD)

    # Setas com sombra preta suave para contraste sobre tons claros/escuros
    # Sombra
    d.line([(cx_r+2, py_r+2), (cx_r+2, target_red[1]+2)], fill=(40,40,40), width=5)
    d.line([(cx_g+2, py_g+2), (cx_g+2, target_gold[1]+2)], fill=(40,40,40), width=5)
    # Linha colorida
    d.line([(cx_r, py_r), (cx_r, target_red[1])], fill=RED, width=4)
    d.line([(cx_g, py_g), (cx_g, target_gold[1])], fill=GOLD, width=4)
    # Alvos com anel branco e preenchimento colorido
    for (tx,ty,col) in [(target_red[0],target_red[1],RED),(target_gold[0],target_gold[1],GOLD)]:
        d.ellipse((tx-11, ty-11, tx+11, ty+11), fill=WHITE, outline=col, width=3)
        d.ellipse((tx-6,  ty-6,  tx+6,  ty+6),  fill=col)

    out = os.path.join(ASSETS, "panel_05_macro.png")
    canvas.save(out, "PNG")
    print(" wrote", out)


# --------------------------------------------------------------
# Slide 6 — H&E: micrografia real com 3 marcadores numerados
# --------------------------------------------------------------
def histo_real():
    W, H = 1700, 760
    canvas = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(canvas)

    pad = 14
    ix0, iy0, ix1, iy1 = pad, pad, W-pad, H-pad-56
    iw, ih = ix1-ix0, iy1-iy0
    src = Image.open(os.path.join(REAL, "histo_real.jpg")).convert("RGB")
    micro = cover_crop(src, iw, ih)
    canvas.paste(micro, (ix0, iy0))
    d.rectangle((ix0, iy0, ix1, iy1), outline=GREY_MD, width=1)

    # Barra inferior com legenda técnica
    overlay = Image.new("RGBA",(W,H),(0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((ix0, iy1, ix1, iy1+56), fill=(15,23,42,220))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(canvas)
    text(d, (ix0+22, iy1+28),
         "H&E · esteatonecrosis con saponificación cálcica. Adipocitos «fantasma» "
         "anucleados con material basófilo amorfo (sales de Ca) e infiltrado neutrofílico.",
         size=13, color=WHITE, anchor="lm")

    # 3 marcadores numerados com chips brancos opacos (legibilidade garantida
    # sobre fundo rosa/violeta da micrografia), setas com sombra e números
    # grandes em cor contrastante.
    # Alvos auditados contra a micrografia real:
    #  1 → grande vacúlio claro anucleado (adipócito fantasma)
    #  2 → placa rosa densa coagulada (necrosis acinar yuxtapuesta)
    #  3 → aglomerado basófilo escuro periférico (neutrófilos + Ca²⁺)
    marks = [
        # (x%, y%, numero, rotulo, cor, lado preferencial)
        (0.28, 0.55, "1", "Adipocitos «fantasma» anucleados",  RED,  "right"),
        (0.55, 0.40, "2", "Necrosis acinar yuxtapuesta",       GOLD, "right"),
        (0.08, 0.30, "3", "Infiltrado neutrofílico + calcio", NAVY, "right"),
    ]
    f_lbl = ft(16, True)
    for (rx_pct, ry_pct, num, lbl, col, side) in marks:
        mx = ix0 + int(iw*rx_pct)
        my = iy0 + int(ih*ry_pct)

        # Chip da legenda: retângulo branco arredondado com contorno colorido
        pad_x, pad_y, radius = 22, 11, 12
        bbox = d.textbbox((0,0), lbl, font=f_lbl)
        # Margem extra para acomodar superíndices (ex: Ca²⁺)
        lw, lh = (bbox[2]-bbox[0]) + pad_x*2 + 8, (bbox[3]-bbox[1]) + pad_y*2 + 6
        # Posição do chip: preferencialmente à direita do marcador; se cair fora, põe à esquerda.
        cx_marker = mx
        desired_right_x = mx + 44
        if desired_right_x + lw > ix1 - 14:
            chip_x1 = mx - 44 - lw
            line_end_x = chip_x1 + lw
            line_from_x = cx_marker - 24
            text_anchor = "lm"
            text_x = chip_x1 + pad_x
        else:
            chip_x1 = desired_right_x
            line_end_x = chip_x1
            line_from_x = cx_marker + 24
            text_anchor = "lm"
            text_x = chip_x1 + pad_x
        chip_y1 = my - lh//2
        chip_x2 = chip_x1 + lw
        chip_y2 = chip_y1 + lh

        # Sombra do chip
        rrect(d, (chip_x1+2, chip_y1+2, chip_x2+2, chip_y2+2), radius, fill=(0,0,0))
        # Chip branco com contorno grosso
        rrect(d, (chip_x1, chip_y1, chip_x2, chip_y2), radius, fill=WHITE, outline=col, width=3)
        # Bolinha colorida antes do texto
        dot_cx = chip_x1 + 18
        dot_cy = my
        d.ellipse((dot_cx-6, dot_cy-6, dot_cx+6, dot_cy+6), fill=col)
        # Texto preto sobre branco → máximo contraste
        d.text((text_x + 14, my), lbl, fill=NAVY, font=f_lbl, anchor="lm")

        # Linha conector com sombra
        # Sombra preta
        d.line([(line_from_x+1, my+1), (line_end_x+1, my+1)], fill=(30,30,30), width=5)
        d.line([(line_from_x, my), (line_end_x, my)], fill=col, width=3)

        # Círculo numerado do marcador (maior, com anel branco e contorno preto)
        r_out, r_in = 24, 20
        # Halo preto
        d.ellipse((mx-r_out-2, my-r_out-2, mx+r_out+2, my+r_out+2), fill=(30,30,30))
        # Anel branco
        d.ellipse((mx-r_out, my-r_out, mx+r_out, my+r_out), fill=WHITE)
        # Círculo colorido interno
        d.ellipse((mx-r_in, my-r_in, mx+r_in, my+r_in), fill=col)
        # Número branco bold sobre cor
        d.text((mx, my), num, fill=WHITE, font=ft(22,True), anchor="mm")

    out = os.path.join(ASSETS, "panel_06_histo.png")
    canvas.save(out, "PNG")
    print(" wrote", out)


if __name__ == "__main__":
    macro_real()
    histo_real()
