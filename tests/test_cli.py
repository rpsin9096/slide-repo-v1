# -*- coding: utf-8 -*-
"""CLI: la unica superficie que o autor toca. Cada comando devuelve codigo de
salida; `--json` existe para los agentes que se autocorrijan."""

import contextlib
import io
import pathlib
import tempfile
import textwrap
import unittest

from studydeck import cli


def run(*argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli.main(list(argv))
    return rc, buf.getvalue()


MANIFEST = textwrap.dedent('''
    COURSE_INFO = {'course': 'Fisiopatologia', 'institution': 'UCP'}
    CONFIG = {'LANG': 'pt-BR', 'PROFILE': 'short'}
    SLIDES = [
        {'module': 'title', 'title': 'Inflamação aguda',
         'subtitle': 'Do estímulo à resolução', 'course': 'Fisiopatologia',
         'institution': 'UCP'},
        {'module': 'definition', 'kicker': 'Conceito', 'title': 'Definição',
         'main_statement': 'Resposta vascular estereotipada do tecido vivo diante da lesao.',
         'key_points': [{'title': 'Vascular', 'desc': 'Vasodilatacao e permeabilidade.'},
                        {'title': 'Celular', 'desc': 'Neutrofilos e monocitos.'}]},
    ]
''')

BROKEN = textwrap.dedent('''
    SLIDES = [{'module': 'title', 'title': 'x' * 400}]
''')


class TestHelp(unittest.TestCase):
    def test_help_lists_every_command(self):
        rc, out = run('--help')
        self.assertEqual(rc, 0)
        for cmd in ('check', 'schema', 'new', 'ingest', 'lint', 'build',
                    'all', 'contrast', 'imgprep'):
            with self.subTest(command=cmd):
                self.assertIn(cmd, out)

    def test_no_arguments_prints_help(self):
        rc, out = run()
        self.assertEqual(rc, 0)
        self.assertIn('Uso', out)

    def test_unknown_command_fails(self):
        rc, _out = run('nao_existe')
        self.assertEqual(rc, 2)


class TestCheck(unittest.TestCase):
    def test_check_covers_every_module(self):
        rc, out = run('check')
        self.assertEqual(rc, 0)
        self.assertIn('35/35', out)

    def test_check_reports_contrast_clean(self):
        rc, out = run('check')
        self.assertIn('0 violaciones', out)


class TestSchema(unittest.TestCase):
    def test_menu_lists_when_for_every_module(self):
        rc, out = run('schema')
        self.assertEqual(rc, 0)
        self.assertIn('flow_diagram', out)
        self.assertIn('QUANDO USAR', out.upper())

    def test_module_contract_shows_budgets(self):
        rc, out = run('schema', 'flow_diagram')
        self.assertEqual(rc, 0)
        self.assertIn('340 car.', out)

    def test_tokens_table_is_ucp_only(self):
        rc, out = run('schema', 'tokens')
        self.assertEqual(rc, 0)
        self.assertIn('ucp', out)
        for gone in ('oxford', 'harvard', 'yale', 'cambridge'):
            with self.subTest(palette=gone):
                self.assertNotIn(gone, out)

    def test_unknown_module_suggests_alternatives(self):
        rc, out = run('schema', 'flow_diagran')
        self.assertEqual(rc, 2)
        self.assertIn('flow_diagram', out)


class TestNew(unittest.TestCase):
    def test_scaffold_is_written_and_lints_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_py = f'{tmp}/manifest.py'
            rc, _ = run('new', 'short', out_py)
            self.assertEqual(rc, 0)
            self.assertTrue(pathlib.Path(out_py).exists())
            rc2, _ = run('lint', out_py)
            self.assertEqual(rc2, 0)

    def test_scaffold_has_real_content_not_markers(self):
        import importlib.util
        with tempfile.TemporaryDirectory() as tmp:
            out_py = f'{tmp}/m2.py'
            run('new', 'short', out_py)
            spec = importlib.util.spec_from_file_location('sc', out_py)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            values = []
            for slide in mod.SLIDES:
                values.extend(str(v) for v in slide.values() if isinstance(v, str))
            self.assertFalse([v for v in values if v.startswith('<=')])

    def test_scaffold_defaults_to_ucp_and_pt_br(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_py = f'{tmp}/m.py'
            run('new', 'short', out_py)
            body = pathlib.Path(out_py).read_text(encoding='utf-8')
            self.assertIn("'PALETTE': 'ucp'", body)
            self.assertIn("'LANG': 'pt-BR'", body)

    def test_scaffold_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_py = f'{tmp}/m.py'
            run('new', 'short', out_py)
            rc, _ = run('new', 'short', out_py)
            self.assertEqual(rc, 1)


class TestLintAndBuild(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.ok = f'{self.tmp}/ok.py'
        pathlib.Path(self.ok).write_text(MANIFEST, encoding='utf-8')
        self.broken = f'{self.tmp}/broken.py'
        pathlib.Path(self.broken).write_text(BROKEN, encoding='utf-8')

    def tearDown(self):
        self._tmp.cleanup()

    def test_lint_passes_for_a_valid_deck(self):
        rc, out = run('lint', self.ok)
        self.assertEqual(rc, 0)
        self.assertIn('PASS', out)

    def test_lint_fails_with_the_offending_field(self):
        rc, out = run('lint', self.broken)
        self.assertEqual(rc, 1)
        self.assertIn('title', out)

    def test_lint_json_is_machine_readable(self):
        import json
        rc, out = run('lint', self.broken, '--json')
        payload = json.loads(out)
        self.assertEqual(payload['status'], 'FAIL')
        self.assertTrue(payload['errors'])

    def test_build_is_fail_fast_on_lint(self):
        out_pptx = f'{self.tmp}/x.pptx'
        rc, out = run('build', self.broken, out_pptx)
        self.assertEqual(rc, 1)
        self.assertIn('fail-fast', out.lower())
        self.assertFalse(pathlib.Path(out_pptx).exists())

    def test_build_writes_the_deck(self):
        out_pptx = f'{self.tmp}/ok.pptx'
        rc, out = run('build', self.ok, out_pptx)
        self.assertEqual(rc, 0)
        self.assertTrue(pathlib.Path(out_pptx).exists())
        self.assertIn('0 violaciones', out)

    def test_all_runs_lint_then_build(self):
        out_pptx = f'{self.tmp}/all.pptx'
        rc, out = run('all', self.ok, out_pptx)
        self.assertEqual(rc, 0)
        self.assertIn('2/2', out)
        self.assertTrue(pathlib.Path(out_pptx).exists())

    def test_missing_manifest_exits_two(self):
        rc, _out = run('lint', f'{self.tmp}/nao_existe.py')
        self.assertEqual(rc, 2)

    def test_palette_warning_is_printed(self):
        src = MANIFEST.replace("'LANG'", "'PALETTE': 'oxford', 'LANG'")
        p = f'{self.tmp}/warn.py'
        pathlib.Path(p).write_text(src, encoding='utf-8')
        rc, out = run('lint', p)
        self.assertIn('UCP-only', out)


class TestContrast(unittest.TestCase):
    def test_matrix_is_ucp_only(self):
        rc, out = run('contrast')
        self.assertEqual(rc, 0)
        self.assertIn('ucp', out)
        for gone in ('oxford', 'harvard', 'yale', 'cambridge'):
            with self.subTest(palette=gone):
                self.assertNotIn(gone, out)

    def test_scan_of_a_manifest_reports_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = f'{tmp}/ok.py'
            pathlib.Path(p).write_text(MANIFEST, encoding='utf-8')
            rc, out = run('contrast', p)
            self.assertEqual(rc, 0)
            self.assertIn('0 violaciones', out)


class TestIngestAndImgprep(unittest.TestCase):
    def test_ingest_builds_an_outline(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = f'{tmp}/notas.md'
            pathlib.Path(src).write_text('1. Vascular\n- texto um\n2. Celular\n- texto dois\n',
                                         encoding='utf-8')
            rc, out = run('ingest', src, f'{tmp}/work')
            self.assertEqual(rc, 0)
            self.assertTrue(pathlib.Path(f'{tmp}/work/outline.md').exists())

    def test_ingest_requires_a_source(self):
        rc, _out = run('ingest')
        self.assertEqual(rc, 2)

    def test_imgprep_reports_the_image_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, out = run('imgprep', tmp)
            self.assertEqual(rc, 0)
            self.assertIn('20 KB', out)


if __name__ == "__main__":
    unittest.main()