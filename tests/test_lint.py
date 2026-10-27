# -*- coding: utf-8 -*-
"""Linter de contrato por slide: presupuestos, requeridos, marcadores, deriva
de idioma, ajuste tipografico y politica de imagenes."""

import unittest

from studydeck.authoring import constraints, skeleton
from studydeck.lint import check
from studydeck.registry import MODULES


def base(module='definition', **kw):
    d = {'module': module, 'kicker': 'Conceito', 'title': 'Inflamação aguda',
         'main_statement': 'Resposta vascular estereotipada do tecido vivo diante da lesao.',
         'key_points': [
             {'title': 'Vascular', 'desc': 'Vasodilatacao e aumento de permeabilidade.'},
             {'title': 'Celular', 'desc': 'Neutrofilos primeiro; monocitos na reparacao.'}]}
    d.update(kw)
    return d


class TestHardFailures(unittest.TestCase):
    def test_canonical_slide_passes(self):
        self.assertEqual(check([base()], 'pt-BR'), [])

    def test_intentional_foreign_term_is_exempt(self):
        slide = base(main_statement='Reacao de corpo estranho granulomatosa进展 do tecido.')
        errs = check([slide], 'pt-BR', allow_terms=('granulomatosa',))
        self.assertEqual([e for e in errs if 'drift' in e], [])

    def test_unknown_module_fails(self):
        errs = check([base(module='inventado')], 'pt-BR')
        self.assertTrue(any('inventado' in e for e in errs))

    def test_missing_required_field_fails(self):
        errs = check([base(main_statement='')], 'pt-BR')
        self.assertTrue(any('main_statement' in e for e in errs))

    def test_field_over_budget_fails(self):
        errs = check([base(main_statement='x' * 300)], 'pt-BR')
        self.assertTrue(any('main_statement' in e for e in errs))

    def test_title_over_budget_fails(self):
        errs = check([base(title='y' * 90)], 'pt-BR')
        self.assertTrue(any('title' in e for e in errs))

    def test_unreplaced_scaffold_marker_fails(self):
        errs = check([base(main_statement='<= 240 car.>')], 'pt-BR')
        self.assertTrue(any('marcador' in e for e in errs))

    def test_error_prefixes_the_slide_and_module(self):
        errs = check([base(main_statement='')], 'pt-BR')
        self.assertTrue(errs[0].startswith('slide 1 [definition]'))


class TestLanguageDrift(unittest.TestCase):
    def test_portuguese_loanword_blocks_for_spanish(self):
        errs = check([base(main_statement='O desenvolvimento da resposta vascular.')], 'es-ES')
        self.assertTrue(any('drift' in e for e in errs))

    def test_same_text_passes_for_portuguese(self):
        errs = check([base(main_statement='O desenvolvimento da resposta vascular.')], 'pt-BR')
        self.assertEqual([e for e in errs if 'drift' in e], [])

    def test_english_loanword_blocks_for_portuguese(self):
        errs = check([base(main_statement='The vascular response of the tissue.')], 'pt-BR')
        self.assertTrue(any('drift' in e for e in errs))

    def test_image_path_is_not_language_checked(self):
        slide = base(main_statement='Resposta vascular do tecido vivo ante a lesao.')
        slide['image'] = 'work/imgs/the_development.png'
        errs = check([slide], 'pt-BR')
        self.assertEqual([e for e in errs if 'drift' in e], [])


class TestTypographyFit(unittest.TestCase):
    def test_budget_that_exceeds_the_box_is_reported_as_budget(self):
        # o orcamento de `elaboration` e menor que a caixa: o autor ve o erro de
        # caracteres, nunca um transbordo confuso.
        slide = base(elaboration='a' * 235)
        errs = check([slide], 'pt-BR')
        self.assertTrue(any('elaboration' in e and 'caracteres' in e for e in errs))

    def test_short_statement_fits(self):
        self.assertEqual([e for e in check([base()], 'pt-BR') if 'transbordo' in e], [])


class TestImagePolicyIntegration(unittest.TestCase):
    def fig(self, **kw):
        d = base(module='figure', main_statement='',
                 image='https://exemplo.org/serologia.jpg',
                 caption='Anti-CCP elevado em paciente seronegativo para fator reumatoide.',
                 credit='Arquivo próprio')
        d.pop('main_statement')
        d.update(kw)
        return d

    def test_web_figure_passes_with_analytical_caption(self):
        self.assertEqual(check([self.fig()], 'pt-BR'), [])

    def test_figure_without_credit_fails(self):
        errs = check([self.fig(credit='')], 'pt-BR')
        self.assertTrue(any('credit' in e for e in errs))

    def test_generic_caption_fails(self):
        errs = check([self.fig(caption='Imagem de exemplo do tema')], 'pt-BR')
        self.assertTrue(any('IMG_CAPTION' in e for e in errs))

    def test_image_in_unsupported_module_fails(self):
        pyr = {'module': 'pyramid', 'title': 'Niveis', 'image': 'work/imgs/a.jpg',
               'caption': 'Camadas da barreira hematoencefalica em corte coronal.',
               'credit': 'Arquivo proprio'}
        errs = check([pyr], 'pt-BR')
        self.assertTrue(any('IMG_MODULE_UNSUPPORTED' in e for e in errs))


class TestManifestLevel(unittest.TestCase):
    def test_missing_required_field_is_reported_with_its_name(self):
        errs = check([{'module': 'definition', 'title': 'X'}], 'pt-BR')
        self.assertEqual([e for e in errs if 'main_statement' in e and 'obrigatorio' in e],
                         ['slide 1 [definition].main_statement: campo obrigatorio ausente ou vazio'])


class TestSchemaSurface(unittest.TestCase):
    def test_every_module_exposes_skeleton_for_agents(self):
        for name in MODULES:
            with self.subTest(module=name):
                self.assertIsInstance(skeleton(name), dict)

    def test_skeleton_markers_are_detected_by_lint(self):
        sk = skeleton('definition')
        sk['main_statement'] = '<= 240 car.>'
        errs = check([sk], 'pt-BR')
        self.assertTrue(any('marcador' in e for e in errs))

    def test_constraints_humanise_every_module(self):
        for name in MODULES:
            with self.subTest(module=name):
                self.assertTrue(constraints(name).strip())


if __name__ == "__main__":
    unittest.main()