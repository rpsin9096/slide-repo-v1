# -*- coding: utf-8 -*-
"""Politica de imagenes: la imagen APOYA el mensaje, nunca lo sustituye.

Modos: web-only (por defecto) | mixed | ai-only | none.
Presupuesto `auto` sensible al source (perfil + tamano) con tope duro 10 y
override explicito del autor.
"""

import unittest

from studydeck.images import HARD_CAP, IMAGE_MODULES, ImagePolicy, textbook_prompt


def fig(**kw):
    d = {'module': 'figure', 'title': 'Serología', 'image': 'work/imgs/serologia.jpg',
         'caption': 'Anti-CCP elevado en paciente seronegativo para factor reumatoide.',
         'credit': 'Archivo propio · CC BY 4.0'}
    d.update(kw)
    return d


def support(module='stat_card', **kw):
    d = {'module': module, 'title': 'Prevalencia', 'image': 'work/imgs/prevalencia.jpg',
         'caption': 'Prevalencia de artritis reumatoide por sexo y edad en la cohorte.',
         'credit': 'OMS 2024'}
    d.update(kw)
    return d


class TestDefaults(unittest.TestCase):
    def test_web_only_is_the_default_mode(self):
        self.assertEqual(ImagePolicy().mode, 'web-only')

    def test_ai_is_opt_in(self):
        self.assertFalse(ImagePolicy().allow_ai)

    def test_placeholder_is_opt_in(self):
        self.assertFalse(ImagePolicy().allow_placeholder)

    def test_image_modules_are_explicit(self):
        self.assertEqual(IMAGE_MODULES,
                         ('figure', 'definition', 'case_block', 'stat_card',
                          'checklist', 'authority_card'))

    def test_hard_cap_is_ten(self):
        self.assertEqual(HARD_CAP, 10)

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            ImagePolicy(mode='stock-photo')

    def test_budget_above_hard_cap_is_rejected(self):
        with self.assertRaises(ValueError):
            ImagePolicy(max_n=11)

    def test_policy_from_config_reads_images_block(self):
        p = ImagePolicy.from_config({'IMAGES': {'mode': 'mixed', 'max_n': 2}})
        self.assertEqual((p.mode, p.max_n), ('mixed', 2))


class TestContextAwareBudget(unittest.TestCase):
    def test_short_deck_gets_small_budget(self):
        self.assertLessEqual(ImagePolicy().budget(10, 'short'), 4)

    def test_lecture_deck_gets_larger_budget(self):
        self.assertGreater(ImagePolicy().budget(24, 'lecture'),
                           ImagePolicy().budget(10, 'short'))

    def test_budget_grows_with_slide_count(self):
        self.assertGreater(ImagePolicy().budget(30, 'lecture'),
                           ImagePolicy().budget(14, 'lecture'))

    def test_auto_budget_never_exceeds_hard_cap(self):
        self.assertLessEqual(ImagePolicy().budget(400, 'lecture'), HARD_CAP)

    def test_explicit_max_n_overrides_auto(self):
        self.assertEqual(ImagePolicy(max_n=1).budget(30, 'lecture'), 1)

    def test_zero_disables_images(self):
        self.assertEqual(ImagePolicy(max_n=0).budget(30, 'lecture'), 0)

    def test_unknown_profile_falls_back_to_short(self):
        self.assertEqual(ImagePolicy().budget(10, 'inventado'),
                         ImagePolicy().budget(10, 'short'))

    def test_budget_is_never_negative(self):
        self.assertGreaterEqual(ImagePolicy().budget(1, 'short'), 0)


class TestPurposeContract(unittest.TestCase):
    def test_figure_requires_an_image(self):
        errs = ImagePolicy().validate([{'module': 'figure', 'title': 'X', 'caption': 'a' * 20,
                                        'credit': 'c'}])
        self.assertTrue(any('IMG_REQUIRED' in e for e in errs))

    def test_figure_without_caption_fails(self):
        errs = ImagePolicy().validate([fig(caption='')])
        self.assertTrue(any('caption' in e for e in errs))

    def test_caption_under_fifteen_characters_fails(self):
        errs = ImagePolicy().validate([fig(caption='Serologia')])
        self.assertTrue(any('caption' in e for e in errs))

    def test_generic_caption_fails_as_non_analytical(self):
        errs = ImagePolicy().validate([fig(caption='Imagen de ejemplo del tema')])
        self.assertTrue(any('IMG_CAPTION_GENERIC' in e for e in errs))

    def test_analytical_caption_passes(self):
        self.assertEqual(ImagePolicy().validate([fig()]), [])

    def test_image_requires_credit(self):
        errs = ImagePolicy().validate([fig(credit='')])
        self.assertTrue(any('credit' in e for e in errs))

    def test_support_module_image_is_optional(self):
        slides = [{'module': 'stat_card', 'title': 'Prevalencia', 'stat_num': '1:2000',
                   'stat_title': 'Prevalencia'}]
        self.assertEqual(ImagePolicy().validate(slides), [])

    def test_image_in_module_without_support_fails(self):
        errs = ImagePolicy().validate([{'module': 'pyramid', 'title': 'Niveles',
                                        'image': 'work/imgs/x.jpg', 'caption': 'a' * 20,
                                        'credit': 'c'}])
        self.assertTrue(any('IMG_MODULE_UNSUPPORTED' in e and 'pyramid' in e for e in errs))


class TestModes(unittest.TestCase):
    def test_web_only_accepts_local_file(self):
        self.assertEqual(ImagePolicy().validate([fig(image='work/imgs/a.jpg')]), [])

    def test_web_only_accepts_https_source(self):
        slides = [fig(image='https://commons.wikimedia.org/x.jpg')]
        self.assertEqual(ImagePolicy().validate(slides), [])

    def test_web_only_rejects_plain_http(self):
        errs = ImagePolicy().validate([fig(image='http://example.org/x.jpg')])
        self.assertTrue(errs)

    def test_web_only_rejects_ai_marker(self):
        errs = ImagePolicy().validate([fig(image='ai:serologia textbook diagram')])
        self.assertTrue(any('allow_ai' in e for e in errs))

    def test_web_only_rejects_placeholder_marker(self):
        errs = ImagePolicy().validate([fig(image='placeholder:serologia')])
        self.assertTrue(any('allow_placeholder' in e for e in errs))

    def test_ai_only_requires_opt_in(self):
        errs = ImagePolicy(mode='ai-only').validate(
            [fig(image='ai:diagrama da cascada inflamatoria')])
        self.assertTrue(any('allow_ai' in e for e in errs))

    def test_ai_marker_passes_with_opt_in(self):
        p = ImagePolicy(mode='ai-only', allow_ai=True)
        self.assertEqual(p.validate([fig(image='ai:diagrama da cascada inflamatoria')]), [])

    def test_placeholder_passes_only_with_opt_in(self):
        self.assertTrue(ImagePolicy(mode='mixed', allow_placeholder=True).validate(
            [fig(image='placeholder:serologia')]) == [])

    def test_none_mode_rejects_every_image(self):
        errs = ImagePolicy(mode='none').validate([fig()])
        self.assertTrue(errs)

    def test_none_mode_allows_image_free_deck(self):
        slides = [{'module': 'definition', 'title': 'T', 'main_statement': 'x' * 30}]
        self.assertEqual(ImagePolicy(mode='none').validate(slides), [])

    def test_unknown_scheme_is_rejected(self):
        errs = ImagePolicy().validate([fig(image='ftp://host/x.jpg')])
        self.assertTrue(any('IMG_SOURCE_SCHEME' in e for e in errs))


class TestBudgetEnforcement(unittest.TestCase):
    def test_more_images_than_budget_fails(self):
        slides = [fig(title=f'S{i}', image=f'work/imgs/{i}.jpg') for i in range(6)]
        errs = ImagePolicy(max_n=2).validate(slides)
        self.assertTrue(any('IMG_BUDGET' in e for e in errs))

    def test_within_budget_passes(self):
        slides = [fig(title=f'S{i}', image=f'work/imgs/{i}.jpg') for i in range(2)]
        self.assertEqual(ImagePolicy(max_n=2).validate(slides), [])

    def test_support_images_count_against_budget(self):
        slides = [support(image=f'work/imgs/{i}.jpg') for i in range(4)]
        self.assertTrue(ImagePolicy(max_n=2).validate(slides))

    def test_error_names_the_offending_slide(self):
        slides = [fig(title=f'S{i}', image=f'work/imgs/{i}.jpg') for i in range(4)]
        errs = ImagePolicy(max_n=1).validate(slides)
        self.assertTrue(any('slide 4' in e for e in errs))


class TestTextbookPrompt(unittest.TestCase):
    def test_prompt_carries_ucp_brand_colours(self):
        self.assertIn('3854CC', textbook_prompt('cascada inflamatoria', 'pt-BR'))

    def test_prompt_carries_target_language(self):
        self.assertIn('pt-BR', textbook_prompt('cascada inflamatoria', 'pt-BR'))

    def test_prompt_states_support_not_content(self):
        self.assertIn('suporte', textbook_prompt('cascada inflamatoria', 'pt-BR'))

    def test_prompt_forbids_watermark_and_stock(self):
        out = textbook_prompt('cascada inflamatoria', 'pt-BR').lower()
        self.assertNotIn('watermark', out.replace('sem marca d’água', ''))
        self.assertIn('água', out)


if __name__ == "__main__":
    unittest.main()