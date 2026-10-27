# -*- coding: utf-8 -*-
"""ORACULO VISUAL del deck UCP: disciplina de tokens, piso tipografico,
limites del lienzo, banda de contenido y composicion sin colisiones.

Adaptacion honesta de las facetas de diseno de FocusGate al dominio .pptx:
- design-tokens ALLOWLIST_AUDIT -> ningun hex crudo en los renderers; el
  color de texto pasa SIEMPRE por pal[...] o pal.tokens[...].
- focus-design ORACLE_VERIFICATION -> cada afirmacion visual se prueba
  recorriendo el .pptx renderizado, nunca "a ojo".
- banner-safe-zone 70PCT_ENVELOPE -> el contenido vive en la banda canonica;
  el chrome (cabecera, pie, sangrado) es excepcion documentada.
"""

import ast
import pathlib
import re
import tempfile
import unittest

from pptx import Presentation
from pptx.util import Emu

from studydeck import manifest as MF
from studydeck import render as RD
from studydeck.contrast import ratio
from studydeck.fixtures import fixture_slides
from studydeck.palette import load_palette

PKG = pathlib.Path(__file__).resolve().parent.parent / 'studydeck'
RENDERER_FILES = sorted((PKG / 'modules').glob('*.py')) + [PKG / 'primitives.py']

CANVAS_W, CANVAS_H = 13.333, 7.5
BAND_X0, BAND_X1 = 0.63, 12.703      # SAFE_X0/X1 con 0.02 de tolerancia
BAND_TOP, BAND_BOTTOM = 1.45, 6.65   # banda de contenido; header/pie = chrome
EPS = 0.011                          # ruido de coma flotante en EMU
MIN_FONT_PT = 9.0                    # piso editorial: etiquetas bold legibles
OVERLAP_AREA_IN2 = 0.02              # colision de texto que ya se ve
IN = 914400                          # EMU por pulgada

HEX_RE = re.compile(r'^[0-9A-Fa-f]{6}$')


def _render_fixture():
    deck = MF.Deck('<fixture>', fixture_slides(),
                  {'course': 'STUDYDECK CHECK'}, {'LANG': 'pt-BR'})
    tmp = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False)
    tmp.close()
    n, fails = RD.render(deck, tmp.name)
    assert not fails, f'fixture com violacao de contraste: {fails[:3]}'
    return tmp.name, n


def _slides(path):
    return Presentation(path).slides


def _inches(emu):
    return (emu or 0) / IN


def _box(shape):
    try:
        return (_inches(shape.left), _inches(shape.top),
                _inches(shape.width), _inches(shape.height))
    except (TypeError, ValueError):
        return None


def _texts(shape):
    if not getattr(shape, 'has_text_frame', False):
        return None
    runs = [r for p in shape.text_frame.paragraphs for r in p.runs
            if r.text and r.text.strip()]
    return runs or None


def _intersect(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    w = min(ax + aw, bx + bw) - max(ax, bx)
    h = min(ay + ah, by + bh) - max(ay, by)
    return (w > EPS and h > EPS), max(w, 0) * max(h, 0)


def _hex_constants(path):
    """Literales hex de 6 digitos usados como VALOR en codigo (no docstrings)."""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if HEX_RE.match(node.value.strip()):
                # docstrings/expr soltos no son valores de color
                if not (isinstance(node, ast.Expr)):
                    found.append((node.lineno, node.value))
    return found


class TestTokenDiscipline(unittest.TestCase):
    """design-tokens: el color de texto viene del pal; hex crudo = violacion.

    Los hex de marca viven UNA vez en palette.py (capa primitiva); la capa
    semantica son los tokens derivados; los renderers referencian una u otra.
    Un 'FFFFFF' crudo en un renderer hoy pasa WCAG por suerte: el dia que el
    fill debajo cambie (verde success: blanco crudo = 4.34, AA-fail), nadie
    lo derivaria y el deck entregaria texto invisible.
    """

    def test_no_raw_hex_in_any_renderer(self):
        for path in RENDERER_FILES:
            hits = _hex_constants(path)
            with self.subTest(file=path.name):
                self.assertEqual(hits, [],
                                 f'{path.name} tiene hex crudos (use pal[...] / '
                                 f'pal.tokens[...]): {hits}')

    def test_tx_default_color_is_routed_through_the_palette(self):
        src = (PKG / 'primitives.py').read_text(encoding='utf-8')
        self.assertNotIn("color='2B2C4A'", src,
                         'el default crudo de tx() debe resolver via paleta')

    def test_every_renderer_text_color_is_a_palette_reference(self):
        """color= solo acepta pal[...], pal.tokens[...] o variables derivadas."""
        pattern = re.compile(r'color\s*=\s*["\'][0-9A-Fa-f]{6}["\']')
        for path in RENDERER_FILES:
            with self.subTest(file=path.name):
                self.assertEqual(pattern.findall(path.read_text(encoding='utf-8')), [])


class TestTypographyFloor(unittest.TestCase):
    def setUp(self):
        self.path, self.n = _render_fixture()

    def tearDown(self):
        pathlib.Path(self.path).unlink(missing_ok=True)

    def test_no_text_below_the_editorial_floor(self):
        small = []
        for i, slide in enumerate(_slides(self.path), 1):
            for shape in slide.shapes:
                for run in _texts(shape) or []:
                    size = run.font.size
                    if size is not None and size.pt < MIN_FONT_PT:
                        small.append((i, run.text[:24], round(size.pt, 1)))
        self.assertEqual(small, [], f'texto bajo {MIN_FONT_PT}pt: {small}')

    def test_body_text_stays_at_reading_size(self):
        """El cuerpo de un slide de contenido no baja de 10.5pt (no-pill)."""
        thin = []
        for i, slide in enumerate(_slides(self.path), 1):
            for shape in slide.shapes:
                runs = _texts(shape)
                if not runs:
                    continue
                for run in runs:
                    size = run.font.size
                    long_text = len(run.text) > 40
                    if size is not None and long_text and size.pt < 10.5:
                        thin.append((i, run.text[:24], round(size.pt, 1)))
        self.assertEqual(thin, [], f'parrafos largos bajo 10.5pt: {thin}')


class TestCanvasBounds(unittest.TestCase):
    def setUp(self):
        self.path, self.n = _render_fixture()

    def tearDown(self):
        pathlib.Path(self.path).unlink(missing_ok=True)

    def test_no_shape_escapes_the_canvas(self):
        escapes = []
        for i, slide in enumerate(_slides(self.path), 1):
            for shape in slide.shapes:
                box = _box(shape)
                if box is None:
                    continue
                x, y, w, h = box
                if x < -EPS or y < -EPS or x + w > CANVAS_W + EPS or y + h > CANVAS_H + EPS:
                    escapes.append((i, shape.shape_type, round(x, 2), round(y, 2),
                                    round(x + w, 2), round(y + h, 2)))
        self.assertEqual(escapes, [], f'formas fuera del lienzo: {escapes}')

    def test_band_local_content_stays_in_the_band(self):
        """Lo que vive dentro de la banda de contenido respeta la zona segura.

        Excepcion documentada (chrome): la cabecera (kicker/titulo, y<1.45),
        el pie (y>6.65) y los sangrados full-bleed (bg, barras de acento),
        que por diseno cruzan la banda.
        """
        stray = []
        for i, slide in enumerate(_slides(self.path), 1):
            for shape in slide.shapes:
                box = _box(shape)
                if box is None:
                    continue
                x, y, w, h = box
                band_local = y >= BAND_TOP - EPS and y + h <= BAND_BOTTOM + EPS
                if not band_local:
                    continue
                if x < BAND_X0 - EPS or x + w > BAND_X1 + EPS:
                    stray.append((i, shape.shape_type, round(x, 2), round(x + w, 2)))
        self.assertEqual(stray, [], f'contenido fuera de la banda: {stray}')


class TestComposition(unittest.TestCase):
    def setUp(self):
        self.path, self.n = _render_fixture()

    def tearDown(self):
        pathlib.Path(self.path).unlink(missing_ok=True)

    def test_text_boxes_do_not_collide(self):
        """Dos cajas de texto con contenido no se pisan (tolerancia sub-pixel).

        La tolerancia absorbe el redondeo de EMU; 0.02 in^2 ya se ve en
        pantalla como texto montado sobre texto.
        """
        clashes = []
        for i, slide in enumerate(_slides(self.path), 1):
            boxes = []
            for shape in slide.shapes:
                runs = _texts(shape)
                if not runs or getattr(shape, 'has_chart', False) \
                        or getattr(shape, 'has_table', False):
                    continue
                box = _box(shape)
                if box:
                    boxes.append((box, runs[0].text[:18]))
            for a in range(len(boxes)):
                for b in range(a + 1, len(boxes)):
                    hit, area = _intersect(boxes[a][0], boxes[b][0])
                    if hit and area > OVERLAP_AREA_IN2:
                        clashes.append((i, boxes[a][1], boxes[b][1], round(area, 3)))
        self.assertEqual(clashes, [], f'colisiones de texto: {clashes}')


class TestNoPortedNonsense(unittest.TestCase):
    """Lo que el deck RENDERIZA no lleva florituras ni inventa contenido.

    Cada caso nace de una floritura o bug portado del kit viejo: la formula
    de la Oxford Union, el latin "viva voce", defaults fabricados y un
    IndexError latente con 3 raices etimologicas.
    """

    FABRICATED = ('PROGRAMA DE FORMA', 'FACULDADE DE MEDICINA',
                  'SÉRIE DE MONOGRAFIAS', 'SERIE DE MONOGRAFIAS')

    def _render_to_texts(self, slides, course_info=None):
        deck = MF.Deck('<nonsense>', slides, course_info or {},
                       {'LANG': 'pt-BR'})
        tmp = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False)
        tmp.close()
        try:
            _n, fails = RD.render(deck, tmp.name)
            self.assertEqual(fails, [])
            texts = [r.text for sl in _slides(tmp.name) for sh in sl.shapes
                     for r in (_texts(sh) or [])]
            return ' | '.join(texts)
        finally:
            pathlib.Path(tmp.name).unlink(missing_ok=True)

    def test_debate_banner_replaces_the_union_formula(self):
        body = self._render_to_texts([next(s for s in fixture_slides()
                                           if s['module'] == 'oxford_union')])
        self.assertIn('DEBATE', body.upper())
        self.assertNotIn('CASA', body.upper())

    def test_oral_exam_label_is_rendered(self):
        body = self._render_to_texts([next(s for s in fixture_slides()
                                           if s['module'] == 'viva_question')])
        self.assertIn('PROVA ORAL', body)

    def test_etymology_with_three_roots_renders(self):
        slide = {'module': 'etymology', 'kicker': 'Termino', 'title': 'Apendicite',
                 'term': 'Apendicite',
                 'fragments': ['Apendic', 'i', 'te'],
                 'roots': [{'part': 'Apendic', 'origin': 'latim',
                            'meaning': 'apendice'},
                           {'part': 'i', 'origin': 'conector',
                            'meaning': 'letra de ligacao'},
                           {'part': 'te', 'origin': 'sufixo',
                            'meaning': 'inflamacao de'}],
                 'modern': 'Inflamacao do apendice vermiforme.'}
        body = self._render_to_texts([slide])
        self.assertIn('Apendicite', body)

    def test_empty_course_info_invents_nothing(self):
        slides = [
            {'module': 'title', 'title': 'Fisiopatologia da inflamacao'},
            {'module': 'definition', 'kicker': 'Conceito', 'title': 'Definicao',
             'main_statement': 'Resposta vascular do tecido vivo diante da lesao.',
             'key_points': [{'title': 'Vascular', 'desc': 'Vasodilatacao.'},
                            {'title': 'Celular', 'desc': 'Neutrofilos.'}]},
        ]
        body = self._render_to_texts(slides, course_info={})
        for invented in self.FABRICATED:
            self.assertNotIn(invented, body.upper())

    def test_footer_without_course_prints_no_series_title(self):
        slides = [{'module': 'definition', 'kicker': 'Conceito', 'title': 'Definicao',
                   'main_statement': 'Resposta vascular do tecido vivo diante da lesao.',
                   'key_points': [{'title': 'Vascular', 'desc': 'Vasodilatacao.'},
                                  {'title': 'Celular', 'desc': 'Neutrofilos.'}]}]
        body = self._render_to_texts(slides, course_info={'course': ''})
        self.assertNotIn('MONOGRAFIAS', body.upper())


class TestNativeContentContrast(unittest.TestCase):
    """El texto que el gate NO mide en runtime (tablas/graficos nativos) se
    verifica aqui por pares exactos: las celdas las pinta PowerPoint."""

    def test_table_pairs_meet_aa(self):
        pal = load_palette()
        b = pal.brand
        pairs = [
            ('FFFFFF', b['primary']),      # cabecera de tabla
            (b['primary'], b['card']),    # fila lead sobre card
            (b['text'], b['card']),       # celda sobre card
            (b['primary'], b['soft']),     # fila lead sobre soft (zebra)
            (b['text'], b['soft']),        # celda sobre soft (zebra)
        ]
        for fg, bg in pairs:
            with self.subTest(fg=fg, bg=bg):
                self.assertGreaterEqual(ratio(fg, bg), 4.5)

    def test_chart_axis_labels_have_explicit_color(self):
        """Sin color explicito el eje hereda el tema de PowerPoint: fuera de
        control del motor = fuera de la disciplina de tokens."""
        path, _n = _render_fixture()
        try:
            charts = []
            for slide in _slides(path):
                for shape in slide.shapes:
                    if getattr(shape, 'has_chart', False):
                        charts.append(shape.chart)
            self.assertTrue(charts, 'o fixture nao tem grafico')
            for chart in charts:
                for axis in (chart.category_axis, chart.value_axis):
                    with self.subTest(axis=type(axis).__name__):
                        self.assertIsNotNone(axis.tick_labels.font.color.rgb)
        finally:
            pathlib.Path(path).unlink(missing_ok=True)

    def test_success_fill_never_receives_raw_white_text(self):
        """Verde UCP #1E8A5A con blanco crudo = 4.34 (AA-fail). El token
        derivado on_success es la UNICA via para texto sobre ese fill."""
        pal = load_palette()
        self.assertLess(ratio('FFFFFF', pal.brand['success']), 4.5)
        self.assertGreaterEqual(ratio(pal.tokens['on_success'],
                                      pal.brand['success']), 4.5)


if __name__ == "__main__":
    unittest.main()