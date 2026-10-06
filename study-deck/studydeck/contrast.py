"""Motor WCAG 2.1: matiz, ratios, umbrales por tamano de texto y la
instrumentacion que registra cada par texto/superficie durante el render.

Invariante del motor: el evaluador corre al final del render, no por texto
(python-pptx no expone el ancho real del glifo). Solo se miden los textos que
el motor pinta con surface conocida; las tablas y graficos nativos quedan
suspendidos por `unmeasured()` porque los pinta PowerPoint.
"""

from contextlib import contextmanager

WCAG_AA_TEXT = 4.5
WCAG_AA_DISPLAY = 3.0


def rel_lum(hexc):
    """rel_lum: documented behavior of the module."""
    hexc = str(hexc).lstrip('#')
    def ch(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(int(hexc[i:i + 2], 16)) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bgc):
    """ratio: documented behavior of the module."""
    l1, l2 = sorted((rel_lum(fg), rel_lum(bgc)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def required_ratio(size, bold):
    """required_ratio: documented behavior of the module."""
    return WCAG_AA_DISPLAY if (size >= 18 or (bold and size >= 14)) else WCAG_AA_TEXT


def pick(candidates, surface, target):
    """pick: documented behavior of the module."""
    for cand in candidates:
        if cand and ratio(cand, surface) >= target:
            return cand
    return None


def shade_until(hexcolor, surface, target, max_steps=12):
    """shade_until: documented behavior of the module."""
    c = str(hexcolor).lstrip('#')
    for step in range(1, max_steps + 1):
        f = 1.0 - step * 0.07
        c = ''.join(f'{max(0, round(int(c[i:i + 2], 16) * f)):02X}' for i in (0, 2, 4))
        if ratio(c, surface) >= target:
            return c
    return c


class ContrastGate:
    """Recoge superficies pintadas y texto medible; evalua al final del render."""

    def __init__(self):
        self.log = []
        self.surfaces = []
        self.slide = 0
        self.module = '?'
        self._unmeasured = False

    def begin_slide(self, idx, module):
        self.new_slide()
        self.slide = idx
        self.module = module

    def new_slide(self):
        """Nueva diapositiva: limpia las superficies (estado de pintado).

        El log NO se limpia: las violaciones son del DECK completo y cada
        entrada lleva su slide/module. Perderlas al empezar la siguiente
        diapositiva entregaria decks ilegibles como si fueran legibles.
        """
        self.surfaces.clear()

    def note_surface(self, fill, x, y, w, h):
        if fill:
            self.surfaces.append((float(x), float(y), float(w), float(h), str(fill)))

    def surface_at(self, px, py):
        if px is None or py is None:
            return None
        for x, y, w, h, fill in reversed(self.surfaces):
            if x <= px <= x + w and y <= py <= y + h:
                return fill
        return None

    def log_text(self, fg, size, bold, deco=False, px=None, py=None):
        if self._unmeasured or not str(fg) or deco:
            return
        surf = self.surface_at(px, py)
        if surf:
            self.log.append({'fg': str(fg), 'bg': surf, 'size': float(size),
                             'bold': bool(bold), 'slide': self.slide,
                             'module': self.module})

    @contextmanager
    def unmeasured(self):
        prev = self._unmeasured
        self._unmeasured = True
        try:
            yield
        finally:
            self._unmeasured = prev

    def failures(self):
        out = []
        for e in self.log:
            need = required_ratio(e['size'], e['bold'])
            r = ratio(e['fg'], e['bg'])
            if r < need:
                out.append({'slide': e['slide'], 'module': e['module'], 'fg': e['fg'],
                            'bg': e['bg'], 'ratio': round(r, 2), 'required': need})
        return out