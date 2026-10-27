# -*- coding: utf-8 -*-
"""Carga de manifests: COURSE_INFO + CONFIG + SLIDES, con valores por defecto."""

import textwrap
import pathlib
import tempfile
import unittest

from studydeck import manifest as M


SRC = textwrap.dedent('''
    # -*- coding: utf-8 -*-
    COURSE_INFO = {'course': 'Fisiopatologia', 'institution': 'UCP'}
    CONFIG = {'LANG': 'es-ES', 'PROFILE': 'short',
              'IMAGES': {'mode': 'mixed', 'max_n': 2, 'allow_ai': True}}
    SLIDES = [{'module': 'title', 'title': 'Inflamacao aguda'}]
''')

MIN_SRC = "SLIDES = [{'module': 'title', 'title': 'X'}]"


def write(tmp, src, name='manifest.py'):
    p = pathlib.Path(tmp) / name
    p.write_text(src, encoding='utf-8')
    return str(p)


class TestLoading(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_reads_slides_course_and_config(self):
        doc = M.load(write(self.tmp, SRC))
        self.assertEqual(len(doc.slides), 1)
        self.assertEqual(doc.course, 'Fisiopatologia')
        self.assertEqual(doc.lang, 'es-ES')

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            M.load(self.tmp + '/nao_existe.py')

    def test_empty_slides_raise(self):
        with self.assertRaises(ValueError):
            M.load(write(self.tmp, "SLIDES = []", 'vazio.py'))

    def test_absent_config_falls_back_to_defaults(self):
        doc = M.load(write(self.tmp, MIN_SRC, 'min.py'))
        self.assertEqual(doc.lang, 'pt-BR')
        self.assertEqual(doc.profile, 'short')
        self.assertEqual(doc.course, '')

    def test_images_policy_comes_from_config(self):
        doc = M.load(write(self.tmp, SRC))
        self.assertEqual(doc.images.mode, 'mixed')
        self.assertEqual(doc.images.max_n, 2)
        self.assertTrue(doc.images.allow_ai)

    def test_default_images_policy_is_web_only(self):
        doc = M.load(write(self.tmp, MIN_SRC, 'min.py'))
        self.assertEqual(doc.images.mode, 'web-only')
        self.assertEqual(doc.images.max_n, 'auto')

    def test_allow_terms_is_read(self):
        src = SRC.replace("'IMAGES':", "'ALLOW_TERMS': ['d KIT'], 'IMAGES':")
        self.assertEqual(M.load(write(self.tmp, src)).allow_terms, ('d KIT',))

    def test_palette_is_always_ucp(self):
        doc = M.load(write(self.tmp, SRC.replace("'LANG'", "'PALETTE': 'oxford', 'LANG'")))
        self.assertEqual(doc.palette_key, 'ucp')

    def test_non_ucp_palette_is_reported_as_a_warning(self):
        src = SRC.replace("'LANG'", "'PALETTE': 'oxford', 'LANG'")
        self.assertTrue(M.load(write(self.tmp, src)).warnings)

    def test_non_python_file_fails_with_clear_message(self):
        bogus = pathlib.Path(self.tmp) / 'deck.pptx'
        bogus.write_bytes(b'PK\x03\x04 not python')
        with self.assertRaises(ValueError) as ctx:
            M.load(str(bogus))
        self.assertIn('manifest', str(ctx.exception))

    def test_version_is_exposed(self):
        self.assertTrue(M.load(write(self.tmp, MIN_SRC, 'v.py')).version)


if __name__ == "__main__":
    unittest.main()