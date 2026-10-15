# -*- coding: utf-8 -*-
"""Regenera os anexos didácticos (PNG) com TODO o texto por extenso, sem siglas
nem abreviaturas:
  • assets/anexo_acino_colocalizacion.png
  • assets/anexo_via_dolor.png
  • assets/panel_09_lipasa.png (gráfico barras; sem S/E/dx)
  • assets/ecografia_vesicular_esquema.png
  • assets/anexo_ringer_vs_salina.png
  • assets/anexo_histologia_comparativa.png

Também corrige o esquema ampolar: este já era ilustrativo sem texto; não se
altera (não tem abreviatura embutida).
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
ASSETS = os.path.join(ROOT, "assets")

NAVY    = (0x0F, 0x17, 0x2A)
NAVY_2  = (0x38, 0x54, 0xCC)
RED     = (0xB9, 0x1C, 0x1C)
GOLD    = (0xB4, 0x53, 0x09)
GREEN   = (0x16, 0x65, 0x34)
CREAM   = (0xF8, 0xFA, 0xFC)
SOFT    = (0xEE, 0xF0, 0xFF)
GREY    = (0x60, 0x63, 0x83)
GREY_LT = (0xD9, 0xDD, 0xF2)
GREY_MD = (0x94, 0xA3, 0xB8)
GREY_DK = (0x4A, 0x4E, 0x6A)
WHITE   = (255, 255, 255)
BLACK   = (0x1E, 0x29, 0x3B)
GOLD_SOFT = (0xFD, 0xF4, 0xE3)
RED_SOFT = (0xFE, 0xE7, 0xE7)
GREEN_SOFT = (0xDC, 0xFC, 0xE7)
BLUE_SOFT = (0xE0, 0xE7, 0xFF)

F_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def ft(size, bold=False): return ImageFont.truetype(F_BOLD if bold else F_REG, size)

def text(d, xy, s, size=16, color=NAVY, bold=False, anchor="la"):
    d.text(xy, s, fill=color, font=ft(size,bold), anchor=anchor)
def rrect(d, xy, r, **kw): d.rounded_rectangle(xy, radius=r, **kw)
def wrap(d, s, size, max_w, font=None):
    """Quebra a cadeia em várias linhas para caber em max_w. Devolve lista de linhas."""
    if font is None: font = ft(size)
    words = s.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        bb = d.textbbox((0,0), trial, font=font)
        if bb[2]-bb[0] <= max_w:
            cur = trial
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def header_canvas(W, H, title):
    img = Image.new("RGB", (W,H), CREAM)
    d = ImageDraw.Draw(img)
    # Moldura externa hairline
    d.rectangle((10, 10, W-10, H-10), outline=GREY_LT, width=2)
    # Título
    text(d, (W//2, 34), title, size=22, color=NAVY, bold=True, anchor="ma")
    # Faixa inferior com aviso
    d.rectangle((12, H-40, W-12, H-12), fill=WHITE)
    return img, d

def footer(d, W, H, msg):
    text(d, (W//2, H-24), msg, size=12, color=GREY, anchor="mm")


# ------------------------------------------------------------
# 1. Anexo · Colocalização acinar
# ------------------------------------------------------------
def acino():
    W, H = 1900, 880
    img, d = header_canvas(W, H, "Colocalización acinar y activación del tripsinógeno")

    # Três cartões A, B, C
    card_w, card_h = 570, 680
    gap = 40
    total = card_w*3 + gap*2
    x0 = (W - total)//2
    y0 = 80

    cards = [
        ("A · Estado normal", NAVY, BLUE_SOFT),
        ("B · Colocalización patológica", RED, RED_SOFT),
        ("C · Cascada intracelular", NAVY, CREAM),
    ]
    for i,(ttl,col,bg) in enumerate(cards):
        x = x0 + i*(card_w+gap)
        rrect(d, (x, y0, x+card_w, y0+card_h), 22, fill=WHITE, outline=GREY_LT, width=2)
        # Faixa de cor no topo do cartão
        rrect(d, (x, y0, x+card_w, y0+54), 22, fill=col)
        d.rectangle((x, y0+28, x+card_w, y0+54), fill=col)
        text(d, (x+card_w//2, y0+28), ttl, size=18, color=WHITE, bold=True, anchor="mm")

        # Círculo grande representando o acino
        cx, cy, r = x+card_w//2, y0+280, 130
        if i == 0:
            d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=bg, outline=GREY_DK, width=3)
            # Luz do ácino (pequena elipse no topo)
            d.ellipse((cx-40, cy-r+20, cx+40, cy-r+58), outline=GREY_DK, width=2, fill=WHITE)
            text(d, (cx, cy-r+38), "luz", size=12, color=GREY_DK, anchor="mm")
            # Grânulos de cimógeno (azul) na zona apical
            for px,py in [(cx-55,cy-30),(cx-30,cy-50),(cx-5,cy-40),(cx+20,cy-55),(cx+50,cy-35),(cx+70,cy-10)]:
                d.ellipse((px-14,py-14,px+14,py+14), fill=NAVY_2)
            # Lisossomas (verde) mais abaixo/basal
            for px,py in [(cx-80,cy+50),(cx-40,cy+75),(cx-10,cy+40),(cx+30,cy+80),(cx+80,cy+30)]:
                d.ellipse((px-12,py-12,px+12,py+12), fill=GREEN)
            # Legendas abaixo
            text(d, (cx, cy+r+50), "Gránulos de cimógeno (azul)", size=15, color=NAVY, anchor="mm")
            text(d, (cx, cy+r+80), "en la zona apical", size=15, color=NAVY, anchor="mm")
            text(d, (cx, cy+r+120), "Lisosomas (verde), separados", size=15, color=GREEN, bold=True, anchor="mm")

        elif i == 1:
            d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=bg, outline=GREY_DK, width=3)
            # Vacúola ácida oval no centro
            vx, vy, vw, vh = cx-80, cy-80, 160, 130
            d.ellipse((vx, vy, vx+vw, vy+vh), fill=(0xFE,0xF0,0xD0), outline=RED, width=3)
            text(d, (cx, vy-14), "vacuola ácida", size=14, color=RED, bold=True, anchor="mb")
            # Dentro: grânulo azul (zimógeno) + lisossoma verde + pontinho cinza (tripsinógeno) + seta
            for px,py in [(cx-30,cy-30),(cx+10,cy-50)]:
                d.ellipse((px-14,py-14,px+14,py+14), fill=NAVY_2)
            for px,py in [(cx-5,cy-15),(cx+35,cy+5)]:
                d.ellipse((px-12,py-12,px+12,py+12), fill=GREEN)
            d.ellipse((cx+15, cy-10-8, cx+15+16, cy-10+8), fill=GREY_MD)
            # Seta preta do cinza para o lado (catepsina a actuar)
            d.line([(cx+35, cy-10), (cx+60, cy-10)], fill=GREEN, width=2)
            d.polygon([(cx+60,cy-10),(cx+52,cy-4),(cx+52,cy-16)], fill=GREEN)
            text(d, (cx+110, cy-30), "catepsina B", size=13, color=GREEN, bold=True, anchor="lm")
            # Losango vermelho da tripsina activa saindo da vacuola
            d.polygon([(cx-40, cy+vh-30),(cx-20, cy+vh-5),(cx-40, cy+vh+20),(cx-60, cy+vh-5)], fill=RED)
            text(d, (cx+5, cy+vh+20), "tripsina activa", size=15, color=RED, bold=True, anchor="lm")
            # Legendas abaixo
            text(d, (cx, cy+r+50), "Gránulo (azul) y lisosoma (verde)", size=14, color=NAVY, anchor="mm")
            text(d, (cx, cy+r+74), "dentro de la misma vacuola", size=14, color=NAVY, anchor="mm")
            text(d, (cx, cy+r+110), "Gris: tripsinógeno · Rojo: tripsina activa", size=14, color=RED, bold=True, anchor="mm")

        else:  # C
            # Contorno vermelho da célula lesada
            d.ellipse((cx-r-10, cy-r-10, cx+r+10, cy+r+10), fill=RED_SOFT, outline=RED, width=4)
            # Núcleo escuro central
            d.ellipse((cx-22,cy-22,cx+22,cy+22), fill=RED)
            # Pequenos círculos rosa ao redor (lesão)
            for px,py in [(cx-60,cy-60),(cx-70,cy+20),(cx+60,cy-50),(cx+50,cy+60)]:
                d.ellipse((px-24,py-24,px+24,py+24), fill=(0xFC,0xCB,0xCB), outline=RED, width=2)
            # 4 setas de entrada/saída com labels
            labels_top = [
                (cx-90, cy-r-40, "Fosfolipasa A2", "lisis de membranas", RED),
                (cx+90, cy-r-40, "Elastasa",        "lesión vascular",   RED),
            ]
            labels_bot = [
                (cx-90, cy+r+40, "Lipasa",          "esteatonecrosis",   RED),
                (cx+90, cy+r+40, "Citocinas proinflamatorias", "aumento de permeabilidad", NAVY),
            ]
            for (lx, ly, ttl, sub, col) in labels_top:
                d.line([(lx, ly+18),(lx, cy-50)], fill=col, width=2)
                d.polygon([(lx,cy-50),(lx-6,cy-62),(lx+6,cy-62)], fill=col)
                text(d, (lx, ly), ttl, size=14, color=col, bold=True, anchor="ma")
                text(d, (lx, ly+20), sub, size=13, color=NAVY, anchor="ma")
            # Labels de baixo são ajustados mais abaixo
            for (lx, ly, ttl, sub, col) in labels_bot:
                d.line([(lx, ly-18),(lx, cy+50)], fill=col, width=2)
                d.polygon([(lx,cy+50),(lx-6,cy+62),(lx+6,cy+62)], fill=col)
                text(d, (lx, ly+16), ttl, size=14, color=col, bold=True, anchor="ma")
                text(d, (lx, ly+36), sub, size=13, color=NAVY, anchor="ma")
            # Banner no fundo do cartão
            rrect(d, (x+20, y0+card_h-80, x+card_w-20, y0+card_h-30), 12, fill=RED, outline=RED)
            text(d, (x+card_w//2, y0+card_h-55),
                 "Necrosis, tercer espacio y choque distributivo",
                 size=15, color=WHITE, bold=True, anchor="mm")

    footer(d, W, H,
           "Esquema didáctico, no es imagen clínica. Según la revisión «Trypsin in pancreatitis» "
           "(World Journal of Gastroenterology, 2024): la activación ocurre en organelas ácidas.")
    out = os.path.join(ASSETS, "anexo_acino_colocalizacion.png")
    img.save(out, "PNG")
    print(" wrote", out)


# ------------------------------------------------------------
# 2. Anexo · Vía del dolor
# ------------------------------------------------------------
def via_dolor():
    W, H = 1900, 820
    img, d = header_canvas(W, H, "Vía del dolor pancreático: aferencias viscerales y proyección")

    # 4 caixas no fluxo
    boxes = [
        ("Páncreas inflamado", ["edema, necrosis y", "distensión de la", "cápsula"]),
        ("Fibras aferentes viscerales", ["fibras A delta y C", "nervios esplácnicos"]),
        ("Plexo celíaco y médula", ["segmentos T5 a T9", "asta dorsal, vía", "espinotalámica"]),
        ("Tálamo y corteza", ["percepción del dolor", "localización difusa"]),
    ]
    n = len(boxes)
    margin_x = 70
    bw = (W - 2*margin_x - 60*(n-1))//n
    bh = 170
    y0 = 110
    box_xs = []
    for i,(ttl,subs) in enumerate(boxes):
        x = margin_x + i*(bw+60)
        box_xs.append(x)
        rrect(d, (x, y0, x+bw, y0+bh), 22, fill=BLUE_SOFT, outline=NAVY_2, width=3)
        text(d, (x+bw//2, y0+38), ttl, size=18, color=NAVY, bold=True, anchor="mm")
        for j,s in enumerate(subs):
            text(d, (x+bw//2, y0+80+j*24), s, size=14, color=GREY_DK, anchor="mm")
    # Setas entre caixas
    for i in range(n-1):
        xa = box_xs[i]+bw
        xb = box_xs[i+1]
        ya = y0 + bh//2
        d.line([(xa+8, ya),(xb-8, ya)], fill=NAVY, width=4)
        d.polygon([(xb-8,ya),(xb-22,ya-8),(xb-22,ya+8)], fill=NAVY)

    # Duas caixas inferiores: Dolor epigástrico / Irradiación posterior
    y1 = 390
    card_w = (W - 2*margin_x - 50)//2
    # Esquerda
    rrect(d, (margin_x, y1, margin_x+card_w, y1+200), 22, fill=GOLD_SOFT, outline=GOLD, width=3)
    text(d, (margin_x+card_w//2, y1+42), "Dolor epigástrico", size=20, color=NAVY, bold=True, anchor="mm")
    txt1 = ("Proyección anterior de las aferencias pancreáticas en el hemiabdomen "
            "superior, referida a la línea media.")
    for j,line in enumerate(wrap(d, txt1, 15, card_w-50)):
        text(d, (margin_x+card_w//2, y1+90+j*28), line, size=15, color=NAVY, anchor="mm")

    # Direita
    x2 = margin_x + card_w + 50
    rrect(d, (x2, y1, x2+card_w, y1+200), 22, fill=RED_SOFT, outline=RED, width=3)
    text(d, (x2+card_w//2, y1+42), "Irradiación posterior", size=20, color=NAVY, bold=True, anchor="mm")
    txt2 = ("Se proyecta hacia la espalda, en el mismo territorio metamérico de "
            "los segmentos T5 a T9, en cinturón.")
    for j,line in enumerate(wrap(d, txt2, 15, card_w-50)):
        text(d, (x2+card_w//2, y1+90+j*28), line, size=15, color=NAVY, anchor="mm")

    footer(d, W, H,
           "Esquema didáctico, no es imagen clínica. La vía se simplifica para orientar la anamnesis.")
    out = os.path.join(ASSETS, "anexo_via_dolor.png")
    img.save(out, "PNG")
    print(" wrote", out)


# ------------------------------------------------------------
# 3. Gráfico · Lipasa / Amilasa (sem S nem dx)
# ------------------------------------------------------------
def lipasa():
    W, H = 1400, 860
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    d.rectangle((10,10,W-10,H-10), outline=GREY_LT, width=2)

    # Título
    text(d, (W//2, 50),
         "Criterio Atlanta 2012: lipasa por encima de tres veces lo normal "
         "confirma el diagnóstico.",
         size=18, color=GREY_DK, anchor="mm")

    # Área do gráfico (margem esquerda generosa; o rótulo "por ciento" vai
    # horizontal à esquerda, fora da área de plotagem)
    plot_x0, plot_y0, plot_x1, plot_y1 = 220, 170, W-120, H-200
    pw, ph = plot_x1-plot_x0, plot_y1-plot_y0

    # Eixos
    d.line([(plot_x0, plot_y1),(plot_x1, plot_y1)], fill=GREY_MD, width=2)
    d.line([(plot_x0, plot_y0),(plot_x0, plot_y1)], fill=GREY_MD, width=2)

    # Grid horizontal (0/25/50/75/100)
    for pct, lbl in [(0,"0"),(25,"25"),(50,"50"),(75,"75"),(100,"100")]:
        y = plot_y1 - int(ph*pct/100)
        d.line([(plot_x0, y),(plot_x1, y)], fill=GREY_LT, width=1)
        text(d, (plot_x0-20, y), lbl, size=14, color=GREY_DK, anchor="rm")
    text(d, (plot_x0-110, (plot_y0+plot_y1)//2), "por ciento",
         size=14, color=GREY_DK, anchor="mm")

    # Barras: Lipasa S95/E99; Amilasa S82/E88
    groups = [("Lipasa", 95, 99, "elevada entre 7 y 14 días", "(ventana amplia)"),
              ("Amilasa",82, 88, "elevada entre 48 y 72 horas", "(falsos negativos tardíos)")]
    group_w = pw//2
    bar_w = 80
    gap = 40
    for i,(name,s,e,sub1,sub2) in enumerate(groups):
        gx = plot_x0 + i*group_w
        cx = gx + group_w//2
        # Sensibilidade (azul)
        bh_s = int(ph*s/100)
        x1 = cx - bar_w - gap//2
        rrect(d, (x1, plot_y1-bh_s, x1+bar_w, plot_y1), 6, fill=NAVY_2)
        text(d, (x1+bar_w//2, plot_y1-bh_s-14), str(s), size=22, color=NAVY, bold=True, anchor="mm")
        # Especificidade (dourado/laranja escuro para boa leitura)
        bh_e = int(ph*e/100)
        x2 = cx + gap//2
        rrect(d, (x2, plot_y1-bh_e, x2+bar_w, plot_y1), 6, fill=RED)
        text(d, (x2+bar_w//2, plot_y1-bh_e-14), str(e), size=22, color=RED, bold=True, anchor="mm")
        # Rótulo do grupo
        text(d, (cx, plot_y1+30), name, size=24, color=NAVY, bold=True, anchor="mm")
        text(d, (cx, plot_y1+66), sub1, size=16, color=GREY_DK, anchor="mm")
        text(d, (cx, plot_y1+94), sub2, size=14, color=GREY, anchor="mm")

    # Legenda
    ly = plot_y0 - 20
    d.rectangle((W-360, ly-18, W-330, ly+12), fill=NAVY_2)
    text(d, (W-320, ly-3), "Sensibilidad", size=15, color=NAVY, bold=True, anchor="lm")
    d.rectangle((W-180, ly-18, W-150, ly+12), fill=RED)
    text(d, (W-140, ly-3), "Especificidad", size=15, color=NAVY, bold=True, anchor="lm")

    footer(d, W, H,
           "Valores expresados en porcentaje; la lipasa tiene mayor ventana diagnóstica que la amilasa.")
    out = os.path.join(ASSETS, "panel_09_lipasa.png")
    img.save(out, "PNG")
    print(" wrote", out)


# ------------------------------------------------------------
# 4. Ecografía esquema
# ------------------------------------------------------------
def eco():
    W, H = 2200, 720
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    d.rectangle((10,10,W-10,H-10), outline=GREY_LT, width=2)
    text(d, (W//2, 44), "Ecografía vesicular: vesícula normal, cálculo, barro biliar y pólipo",
         size=22, color=NAVY, bold=True, anchor="mm")

    # Quatro painéis A/B/C/D
    panels = [
        ("A · Bilis normal",     "Anecoica: sin ecos internos",                         "Sin sombra posterior"),
        ("B · Cálculo",         "Hiperecogénico y móvil con el decúbito",              "Sombra acústica posterior limpia"),
        ("C · Barro biliar",    "Ecos bajos que se estratifican por gravedad",         "Sin sombra acústica limpia"),
        ("D · Pólipo",          "Fijo a la pared; eco intermedio",                     "No cambia con el decúbito, sin sombra"),
    ]
    margin = 60
    top = 90
    p_bottom = H-140
    pw = (W - 2*margin - 40*3)//4
    ph = p_bottom - top
    FILM = (0x0B,0x16,0x28)
    DARK = (0x33,0x36,0x44)
    for i,(ttl,l1,l2) in enumerate(panels):
        x = margin + i*(pw+40)
        # Faixa
        text(d, (x+20, top-40), ttl, size=20, color=NAVY if i in (0,3) else (RED if i==1 else GREEN), bold=True)
        # Painel escuro
        d.rectangle((x, top, x+pw, p_bottom), fill=FILM)
        # Vesícula (elipse grande)
        ves_w, ves_h = int(pw*0.72), int(ph*0.45)
        vx0 = x + (pw-ves_w)//2
        vy0 = top + 80
        d.ellipse((vx0, vy0, vx0+ves_w, vy0+ves_h), outline=GREY_LT, width=4, fill=BLACK)
        # Cunha do transdutor no topo (triângulo cinza)
        tx = x + pw//2
        d.polygon([(tx-30, top),(tx+30, top),(tx, top+90)], fill=DARK)
        d.rectangle((tx-40, top-10, tx+40, top+10), fill=GREY_MD)

        if i == 0:  # normal
            pass
        elif i == 1:  # cálculo brilhante + sombra
            cx, cy = vx0 + ves_w//2, vy0 + int(ves_h*0.35)
            d.ellipse((cx-24,cy-18,cx+24,cy+18), fill=WHITE)
            # Sombra acústica — cone triangular escuro até o fundo
            sh_top = cy+20
            sw = 180
            d.polygon([(cx-sw//2, sh_top),(cx+sw//2, sh_top),(cx+sw//2+40, p_bottom),(cx-sw//2-40, p_bottom)], fill=BLACK)
            # labels
            text(d, (cx, cy-40), "eco intenso", size=14, color=WHITE, bold=True, anchor="mb")
            text(d, (x+pw-30, p_bottom-30), "sombra acústica", size=14, color=WHITE, anchor="rm")
        elif i == 2:  # barro biliar — camada cinza embaixo com "nível"
            layer_h = 60
            # Camada granulada
            for k in range(220):
                import random
                rx = random.randint(vx0+8, vx0+ves_w-8)
                ry = random.randint(vy0+ves_h-layer_h, vy0+ves_h-8)
                d.point((rx,ry), fill=GREY_LT)
            # Linha do nível
            d.line([(vx0+10, vy0+ves_h-layer_h),(vx0+ves_w-10, vy0+ves_h-layer_h)], fill=WHITE, width=2)
            text(d, (vx0+ves_w-20, vy0+ves_h-layer_h-20), "nivel", size=14, color=WHITE, anchor="rb")
        else:  # pólipo — aderido à parede superior
            cx, cy = vx0 + int(ves_w*0.75), vy0 + 18
            d.ellipse((cx-22,cy-16,cx+22,cy+16), fill=GREY_LT)
            d.line([(cx, cy+16),(cx, vy0+4)], fill=WHITE, width=2)
            text(d, (vx0+ves_w-20, vy0-6), "adherido a la pared", size=14, color=WHITE, anchor="rb")

        # Legenda sob o painel
        text(d, (x+pw//2, p_bottom+28), l1, size=15, color=NAVY, anchor="mt")
        col = RED if i in (1,) else (GREEN if i in (0,3) else GOLD)
        text(d, (x+pw//2, p_bottom+60), l2, size=16, color=col, bold=True, anchor="mt")

    footer(d, W, H,
           "Esquema didáctico de ultrasonido sagital: sonda arriba, luz anecoica en negro. "
           "Ilustración, no es imagen clínica.")
    out = os.path.join(ASSETS, "ecografia_vesicular_esquema.png")
    img.save(out, "PNG")
    print(" wrote", out)


# ------------------------------------------------------------
# 5. Ringer lactato vs solución fisiológica
# ------------------------------------------------------------
def ringer():
    W, H = 1800, 880
    img, d = header_canvas(W, H, "Ringer lactato frente a solución fisiológica al 0,9 por ciento")

    # Cartões esquerdo/direito
    margin = 60
    gap = 60
    cw = (W - 2*margin - gap)//2
    ch = 680
    y0 = 90
    # Esquerdo — Solução fisiológica (vermelho: RISCO)
    x = margin
    rrect(d, (x, y0, x+cw, y0+ch), 22, fill=WHITE, outline=GREY_LT, width=2)
    text(d, (x+cw//2, y0+40), "A · Solución fisiológica 0,9 %", size=22, color=RED, bold=True, anchor="mm")
    # Placa composição
    rrect(d, (x+80, y0+100, x+cw-80, y0+210), 20, fill=BLUE_SOFT, outline=NAVY_2, width=2)
    text(d, (x+cw//2, y0+140), "Solución fisiológica 0,9 %", size=18, color=NAVY, bold=True, anchor="mm")
    text(d, (x+cw//2, y0+180), "Sodio 154 · Cloruro 154 miliequivalentes por litro",
         size=14, color=NAVY, anchor="mm")
    # Seta apontando para baixo
    d.polygon([(x+cw//2-18,y0+240),(x+cw//2+18,y0+240),(x+cw//2,y0+270)], fill=GREY_DK)
    d.rectangle((x+cw//2-6, y0+210, x+cw//2+6, y0+240), fill=GREY_DK)
    # Itens
    items = [
        ("carga elevada de cloruro", GREY_DK, False),
        ("menor pH: acidosis hiperclorémica (hipótesis)", RED, True),
        ("En el acino: posible activación del tripsinógeno", NAVY, False),
        ("en estudios de laboratorio: a menor pH, mayor autoactivación", GREY, False),
        ("Riesgo a considerar: acidosis y activación enzimática", RED, True),
    ]
    yy = y0+290
    for t,col,bold in items:
        text(d, (x+cw//2, yy), t, size=15, color=col, bold=bold, anchor="mm")
        yy += 42
    # Caixa rosa final (flecha)
    rrect(d, (x+40, y0+ch-100, x+cw-40, y0+ch-40), 24, fill=RED_SOFT, outline=RED, width=3)
    text(d, (x+cw//2, y0+ch-70), "vía periférica → circulación → páncreas",
         size=16, color=RED, bold=True, anchor="mm")

    # Direito — Ringer lactato (verde)
    x = margin + cw + gap
    rrect(d, (x, y0, x+cw, y0+ch), 22, fill=WHITE, outline=GREY_LT, width=2)
    text(d, (x+cw//2, y0+40), "B · Ringer lactato", size=22, color=GREEN, bold=True, anchor="mm")
    rrect(d, (x+80, y0+100, x+cw-80, y0+210), 20, fill=GREEN_SOFT, outline=GREEN, width=2)
    text(d, (x+cw//2, y0+140), "Ringer lactato", size=18, color=NAVY, bold=True, anchor="mm")
    text(d, (x+cw//2, y0+180),
         "Sodio 130 · Potasio 4 · Calcio 2,7 · Cloruro 109 · Lactato 28",
         size=12, color=NAVY, anchor="mm")
    text(d, (x+cw//2, y0+198),
         "(concentraciones en miliequivalentes por litro)",
         size=11, color=GREY, anchor="mm")
    d.polygon([(x+cw//2-18,y0+240),(x+cw//2+18,y0+240),(x+cw//2,y0+270)], fill=GREY_DK)
    d.rectangle((x+cw//2-6, y0+210, x+cw//2+6, y0+240), fill=GREY_DK)
    items2 = [
        ("menor carga de cloruro", GREY_DK, False),
        ("el lactato se transforma en bicarbonato en el hígado", GREEN, True),
        ("cercano al pH fisiológico: levemente ácido, no neutro", NAVY, False),
        ("menor riesgo de acidosis hiperclorémica", GREEN, False),
        ("Preferido en la fase inicial de la reanimación", GREEN, True),
    ]
    yy = y0+290
    for t,col,bold in items2:
        text(d, (x+cw//2, yy), t, size=15, color=col, bold=bold, anchor="mm")
        yy += 42
    rrect(d, (x+40, y0+ch-100, x+cw-40, y0+ch-40), 24, fill=RED_SOFT, outline=RED, width=3)
    text(d, (x+cw//2, y0+ch-70), "vía periférica → circulación → páncreas",
         size=16, color=RED, bold=True, anchor="mm")

    footer(d, W, H,
           "Esquema didáctico, no es imagen clínica. Composiciones de referencia; el efecto sobre la "
           "pancreatitis se basa en datos limitados y en inferencia fisiológica.")
    out = os.path.join(ASSETS, "anexo_ringer_vs_salina.png")
    img.save(out, "PNG")
    print(" wrote", out)


# ------------------------------------------------------------
# 6. Histologia comparativa
# ------------------------------------------------------------
def histo_comp():
    W, H = 1800, 880
    img, d = header_canvas(W, H, "Pancreatitis edematosa intersticial frente a necrohemorrágica")

    margin = 60
    gap = 60
    cw = (W - 2*margin - gap)//2
    ch = 680
    y0 = 90

    # A — Edematosa
    x = margin
    rrect(d, (x, y0, x+cw, y0+ch), 22, fill=WHITE, outline=GREY_LT, width=2)
    text(d, (x+cw//2, y0+40), "A · Pancreatitis edematosa intersticial",
         size=20, color=NAVY, bold=True, anchor="mm")
    # Área de desenho
    ax, ay, aw, ah = x+20, y0+80, cw-40, ch-180
    d.rectangle((ax, ay, ax+aw, ay+ah), fill=CREAM)
    # Linhas de septos
    d.line([(ax+aw//3, ay),(ax+aw//3, ay+ah)], fill=(0xFC,0xD7,0xD7), width=8)
    d.line([(ax+2*aw//3, ay),(ax+2*aw//3, ay+ah)], fill=(0xFC,0xD7,0xD7), width=8)
    d.line([(ax, ay+ah//2),(ax+aw, ay+ah//2)], fill=(0xFC,0xD7,0xD7), width=8)
    # Acinos (círculos rosados com pontinhos roxos = núcleos)
    import random
    random.seed(1)
    for _ in range(7):
        cx_ = random.randint(ax+30, ax+aw-30)
        cy_ = random.randint(ay+30, ay+ah-30)
        rr = random.randint(48, 78)
        d.ellipse((cx_-rr, cy_-rr, cx_+rr, cy_+rr), fill=(0xEC,0xB6,0xBC), outline=GOLD, width=2)
        for _n in range(random.randint(2,4)):
            nx = cx_ + random.randint(-rr+10, rr-10)
            ny = cy_ + random.randint(-rr+10, rr-10)
            d.ellipse((nx-5,ny-5,nx+5,ny+5), fill=(0x4E,0x2C,0x82))
    # Adipócito fantasma (círculo claro com halo azul-pálido)
    acx, acy, acr = ax+int(aw*0.72), ay+int(ah*0.62), 38
    d.ellipse((acx-acr, acy-acr, acx+acr, acy+acr), fill=WHITE, outline=GREY_MD, width=2)
    for _n in range(3):
        nx = acx + random.randint(-10,10)
        ny = acy + random.randint(-10,10)
        d.ellipse((nx-4,ny-4,nx+4,ny+4), fill=(0x8C,0x6A,0xC2))
    # Seta + rótulo
    d.line([(acx+acr+10, acy-40),(acx+acr+10, acy-acr)], fill=NAVY, width=2)
    text(d, (acx+acr+20, acy-50), "adipocitos fantasma", size=13, color=NAVY, anchor="lm")
    text(d, (acx+acr+20, acy-32), "(saponificación)",  size=12, color=NAVY, anchor="lm")
    # Pequeno conjunto de neutrófilos (pontinhos azuis)
    bx, by = ax+int(aw*0.15), ay+int(ah*0.85)
    for dx in range(-12,13,8):
        for dy in range(-12,13,8):
            if dx*dx+dy*dy < 160:
                d.ellipse((bx+dx-4, by+dy-4, bx+dx+4, by+dy+4), fill=NAVY_2)
    # Legenda
    text(d, (x+cw//2, y0+ch-55),
         "Septos con edema · acinos viables · vasos conservados",
         size=15, color=NAVY, anchor="mm")

    # B — Necrohemorrágica
    x = margin + cw + gap
    rrect(d, (x, y0, x+cw, y0+ch), 22, fill=WHITE, outline=GREY_LT, width=2)
    text(d, (x+cw//2, y0+40), "B · Pancreatitis necrohemorrágica",
         size=20, color=RED, bold=True, anchor="mm")
    ax, ay, aw, ah = x+20, y0+80, cw-40, ch-180
    d.rectangle((ax, ay, ax+aw, ay+ah), fill=CREAM)
    # Áreas cinza-rosadas de necrose amorfa (blocos irregulares)
    necrose = [
        (0.10,0.18,0.28,0.42),
        (0.46,0.25,0.72,0.56),
        (0.72,0.10,0.93,0.32),
    ]
    for (fx,fy,fxf,fyf) in necrose:
        x0_ = ax + int(aw*fx); y0_ = ay + int(ah*fy)
        x1_ = ax + int(aw*fxf); y1_ = ay + int(ah*fyf)
        d.rectangle((x0_, y0_, x1_, y1_), fill=(0xCB,0xCB,0xCB), outline=GREY_DK, width=2)
        # Resto de acino com núcleos fragmentados
        for _n in range(4):
            nx = random.randint(x0_+10, x1_-10)
            ny = random.randint(y0_+10, y1_-10)
            d.ellipse((nx-6,ny-6,nx+6,ny+6), fill=WHITE, outline=GOLD, width=1)
            for _k in range(3):
                d.ellipse((nx-3+random.randint(-3,3),ny-3+random.randint(-3,3),
                           nx+3+random.randint(-3,3),ny+3+random.randint(-3,3)),
                          fill=(0x4E,0x2C,0x82))
    # Hemorragia: pontinhos vermelhos e coágulos
    for _ in range(260):
        rx = random.randint(ax+5, ax+aw-5)
        ry = random.randint(ay+5, ay+ah-5)
        d.point((rx,ry), fill=RED)
    # Coágulos grandes
    for (cx_,cy_,rr) in [(ax+int(aw*0.22), ay+int(ah*0.05), 30),
                         (ax+int(aw*0.82), ay+int(ah*0.72), 32)]:
        d.ellipse((cx_-rr,cy_-rr,cx_+rr,cy_+rr), fill=(0x7A,0x12,0x12))
    # Vaso trombosado (linha + coágulo)
    vx = ax+int(aw*0.68); vy = ay+int(ah*0.62)
    d.line([(vx, vy),(vx, vy+70)], fill=GREY_DK, width=3)
    d.ellipse((vx-24, vy+70, vx+24, vy+110), fill=(0x7A,0x12,0x12))
    d.polygon([(vx,vy+70),(vx-5,vy+62),(vx+5,vy+62)], fill=RED)
    text(d, (vx+14, vy+55), "vaso trombosado", size=13, color=RED, anchor="lm")
    text(d, (ax+int(aw*0.88), ay+int(ah*0.18)), "hemorragia", size=14, color=RED, anchor="lm")

    text(d, (x+cw//2, y0+ch-55),
         "Acinos destruidos · necrosis amorfa · eritrocitos extravasados",
         size=15, color=NAVY, anchor="mm")

    footer(d, W, H,
           "Esquema didáctico de dos patrones; no es la lámina del Caso Clínico 09. "
           "Trazos simplificados para comparar arquitectura, no para diagnóstico.")
    out = os.path.join(ASSETS, "anexo_histologia_comparativa.png")
    img.save(out, "PNG")
    print(" wrote", out)


if __name__ == "__main__":
    acino()
    via_dolor()
    lipasa()
    eco()
    ringer()
    histo_comp()
