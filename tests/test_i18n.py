# -*- coding: utf-8 -*-
"""i18n: pt-BR por defecto, tres idiomas soportados, sin fuga Oxbridge y
guard de deriva por idioma objetivo."""

import unittest

from studydeck import i18n


class TestLanguageSet(unittest.TestCase):
    def setUp(self):
        i18n.set_ui(i18n.DEFAULT_LANG)

    def tearDown(self):
        i18n.set_ui(i18n.DEFAULT_LANG)

    def test_default_language_is_brazilian_portuguese(self):
        self.assertEqual(i18n.DEFAULT_LANG, 'pt-BR')

    def test_supported_languages_are_exactly_three(self):
        self.assertEqual(list(i18n.LANGS), ['pt-BR', 'es-ES', 'en-US'])

    def test_every_language_translates_every_label(self):
        for lang in i18n.LANGS:
            pack = i18n.lang_pack(lang)
            with self.subTest(lang=lang):
                self.assertEqual(set(pack['labels']), set(i18n.lang_pack('pt-BR')['labels']))

    def test_every_language_translates_every_bloom_term(self):
        for lang in i18n.LANGS:
            with self.subTest(lang=lang):
                self.assertEqual(sorted(i18n.lang_pack(lang)['bloom']),
                                 sorted(i18n.lang_pack('pt-BR')['bloom']))

    def test_pearl_label_is_neutral_not_university_bound(self):
        for lang in i18n.LANGS:
            with self.subTest(lang=lang):
                self.assertNotIn('Cambridge', i18n.lang_pack(lang)['labels']['pearl'])

    def test_unknown_language_falls_back_to_default(self):
        self.assertEqual(i18n.lang_pack('kl-KL')['labels'], i18n.lang_pack('pt-BR')['labels'])

    def test_set_ui_ignores_unsupported_language(self):
        i18n.set_ui('de-DE')
        self.assertEqual(i18n.current(), 'pt-BR')

    def test_label_lookup_differs_across_languages(self):
        pt = i18n.lang_pack('pt-BR')['labels']['glossary']
        en = i18n.lang_pack('en-US')['labels']['glossary']
        self.assertNotEqual(pt, en)

    def test_bloom_labels_are_localised(self):
        self.assertEqual(i18n.lang_pack('pt-BR')['bloom']['remember'], 'lembrar')
        self.assertEqual(i18n.lang_pack('en-US')['bloom']['remember'], 'remember')


class TestEditorialLabels(unittest.TestCase):
    """Las etiquetas del motor hablan el idioma del deck, no una tradicion
    ajena: la mocion es un DEBATE y la pregunta oral es una prueba oral.
    El latin "viva voce" y la formula de la Oxford Union son florituras
    portadas que no significan nada para el estudiante de la UCP."""

    def test_house_label_is_debate_in_every_language(self):
        for lang in i18n.LANGS:
            with self.subTest(lang=lang):
                self.assertTrue(i18n.lang_pack(lang)['labels']['house']
                                .upper().startswith('DEBATE'))

    def test_viva_label_is_oral_exam_in_every_language(self):
        expected = {'pt-BR': 'PROVA ORAL', 'es-ES': 'EXAMEN ORAL',
                   'en-US': 'ORAL EXAM'}
        for lang in i18n.LANGS:
            with self.subTest(lang=lang):
                self.assertEqual(i18n.lang_pack(lang)['labels']['viva'],
                                 expected[lang])

    def test_no_latin_or_union_formula_survives(self):
        for lang in i18n.LANGS:
            labels = i18n.lang_pack(lang)['labels']
            with self.subTest(lang=lang):
                self.assertNotIn('VOCE', labels['viva'].upper())
                self.assertNotIn('CASA', labels['house'].upper())
                self.assertNotIn('CAMARA', labels['house'].upper()
                                 .replace('CÁMARA', 'CAMARA')
                                 .replace('CÂMARA', 'CAMARA'))


class TestDriftGuard(unittest.TestCase):
    def test_portuguese_loanword_is_blocked_for_spanish(self):
        hits = i18n.drift_hits('O desenvolvimento do projeto', 'es-ES')
        self.assertTrue(any(w == 'desenvolvimento' for w, _ in hits))

    def test_portuguese_is_allowed_for_portuguese(self):
        self.assertEqual(i18n.drift_hits('O desenvolvimento do projeto', 'pt-BR'), [])

    def test_spanish_loanword_is_blocked_for_portuguese(self):
        hits = i18n.drift_hits('El desarrollo del proyecto', 'pt-BR')
        self.assertTrue(any(w == 'desarrollo' for w, _ in hits))

    def test_english_loanword_is_blocked_for_portuguese(self):
        hits = i18n.drift_hits('The development of the project', 'pt-BR')
        self.assertTrue(hits)

    def test_target_language_text_is_never_flagged(self):
        text = 'Inflamação aguda: mediadores, cascada vascular e resolução'
        self.assertEqual(i18n.drift_hits(text, 'pt-BR'), [])

    def test_substring_match_does_not_trigger(self):
        self.assertEqual(i18n.drift_hits('desenvolvimentos aritméticos', 'es-ES'), [])

    def test_hit_carries_the_replacement(self):
        hits = i18n.drift_hits('desenvolvimento', 'es-ES')
        self.assertEqual(hits[0][1], 'desarrollo')

    def test_no_hits_for_empty_text(self):
        self.assertEqual(i18n.drift_hits('', 'pt-BR'), [])


if __name__ == "__main__":
    unittest.main()