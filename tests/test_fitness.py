# -*- coding: utf-8 -*-
"""FITNESS RATCHETS: regras estructurales que solo pueden endurecerse.

Cada test falla hoy si alguien reintroduce la deuda que este rebuild elimino:
el doble bloque de presupuestos, el cajon `utils`, los modulos gordos y las
dependencias que apuntan hacia afuera.
"""

import ast
import pathlib
import unittest

PKG = pathlib.Path(__file__).resolve().parent.parent / 'studydeck'
MODULES = PKG / 'modules'
SOURCE_DIRS = ('contracts.py', 'authoring.py', 'registry.py', 'lint.py',
               'render.py', 'cli.py', 'manifest.py', 'images.py', 'imagedata.py',
               'primitives.py', 'palette.py', 'geometry.py', 'i18n.py',
               'typography.py', 'contrast.py', 'fixtures.py', 'ingest.py',
               'version.py', '__init__.py', '__main__.py', 'scaffold.py')

SIZE_CAPS = {
    'core.py': 420, 'diagram.py': 220, 'scholarly.py': 305, 'pedagogy.py': 210,
    'contracts.py': 420, 'primitives.py': 300, 'cli.py': 300, 'lint.py': 200,
    'registry.py': 200, 'images.py': 240, 'render.py': 140,
}

JUNK_DRAWERS = ('utils.py', 'helpers.py', 'common.py', 'misc.py', 'tools.py')

INWARD_OK = {'contrast', 'geometry', 'i18n', 'images', 'primitives', 'typography',
             'contracts', 'version'}

OUTWARD = {'lint', 'render', 'cli', 'registry', 'manifest', 'fixtures'}


def py_files():
    yield PKG / '__init__.py'
    for name in SOURCE_DIRS:
        yield PKG / name
    for path in sorted(MODULES.glob('*.py')):
        yield path


def lines(path):
    return len(path.read_text(encoding='utf-8').splitlines())


def imports_of(path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level and node.module:
                out.add(node.module.split('.')[0])
            elif node.level == 0 and node.module:
                out.add(node.module.split('.')[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name.split('.')[0])
    return out


class TestNoJunkDrawer(unittest.TestCase):
    def test_no_junk_drawer_modules(self):
        found = [p.name for p in PKG.rglob('*.py') if p.name in JUNK_DRAWERS]
        self.assertEqual(found, [], f'cajon de utilidades rejeitado: {found}')

    def test_package_has_the_expected_files_only(self):
        actual = {p.name for p in PKG.rglob('*.py')}
        allowed = set(SOURCE_DIRS) | {p.name for p in MODULES.glob('*.py')}
        self.assertEqual(actual - allowed, set())


LEGACY_PALETTE_WORDS = ('oxford', 'harvard', 'yale', 'cambridge')
LEGACY_PALETTE_HEX = ('002147', 'B08D57', 'A51C30', 'B88B4A',
                      '0F4D92', 'C5A059', '1B365D', '007788')


class TestNoLegacyPalette(unittest.TestCase):
    """UCP-only: ninguna palabra ni hex de las paletas retirementadas sobrevive.
    `oxford_union` es el nombre de un modulo de debate, no una paleta."""

    def _sources(self):
        yield from py_files()
        for name in ('README.md', 'prompt.md', 'SYSTEM_PROMPT.md'):
            path = pathlib.Path(__file__).resolve().parent.parent / name
            if path.exists():
                yield path

    def test_no_legacy_palette_word_outside_the_debate_module(self):
        offenders = []
        for path in self._sources():
            body = path.read_text(encoding='utf-8').lower().replace('oxford_union', '')
            for word in LEGACY_PALETTE_WORDS:
                if word in body:
                    offenders.append(f'{path.name}:{word}')
        self.assertEqual(offenders, [], f'paleta legada ainda citada: {offenders}')

    def test_no_legacy_palette_hex_anywhere(self):
        offenders = [p.name for p in self._sources()
                     if any(hx in p.read_text(encoding='utf-8').upper()
                            for hx in LEGACY_PALETTE_HEX)]
        self.assertEqual(offenders, [])


class TestSingleWriter(unittest.TestCase):
    def _toplevel_assigns(self, path):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        return {t.id for n in tree.body if isinstance(n, ast.Assign)
                for t in n.targets if isinstance(t, ast.Name)}

    def test_character_budgets_are_written_once(self):
        owners = [p.name for p in py_files() if 'B' in self._toplevel_assigns(p)
                  and p.name != 'contracts.py'
                  and 'B' in self._toplevel_assigns(p)]
        self.assertEqual(owners, [], 'presupuestos duplicados fora de contracts.py')

    def test_required_fields_are_written_once(self):
        owners = [p.name for p in py_files()
                  if 'REQUIRED_NONEMPTY' in self._toplevel_assigns(p)
                  and p.name != 'contracts.py']
        self.assertEqual(owners, [])

    def test_no_module_table_is_built_outside_the_registry(self):
        owners = [p.name for p in py_files()
                  if 'MODULES' in self._toplevel_assigns(p) and p.name != 'registry.py']
        self.assertEqual(owners, [])

    def test_contracts_exposes_the_single_budget_object(self):
        import studydeck.contracts as c
        import studydeck.registry as r
        self.assertIs(c.B, r.B)


class TestSizeRatchet(unittest.TestCase):
    def test_every_source_file_is_inside_its_cap(self):
        for path in py_files():
            with self.subTest(file=path.name):
                cap = SIZE_CAPS.get(path.name)
                if cap is not None:
                    self.assertLessEqual(lines(path), cap,
                                         f'{path.name} passo do teto de {cap} linhas')

    def test_no_file_exceeds_the_global_cap(self):
        for path in py_files():
            with self.subTest(file=path.name):
                self.assertLessEqual(lines(path), 460)

    def test_legacy_reference_is_not_inside_the_package(self):
        self.assertFalse((PKG / 'legacy_studydeck_reference.py').exists())


class TestImportDirection(unittest.TestCase):
    def test_renderers_only_import_inward(self):
        for path in sorted(MODULES.glob('*.py')):
            with self.subTest(file=path.name):
                bad = {m for m in imports_of(path)
                       if m.startswith('studydeck') or m in OUTWARD}
                self.assertEqual(bad - INWARD_OK, set(),
                                 f'{path.name} importa hacia afuera: {bad}')

    def test_registry_does_not_import_lint_or_render(self):
        bad = {'lint', 'render', 'cli'} & imports_of(PKG / 'registry.py')
        self.assertEqual(bad, set())

    def test_contracts_does_not_import_registry(self):
        self.assertNotIn('registry', imports_of(PKG / 'contracts.py'))

    def test_primitives_does_not_import_registry(self):
        self.assertNotIn('registry', imports_of(PKG / 'primitives.py'))


class TestDocumentation(unittest.TestCase):
    def test_every_module_has_a_docstring(self):
        for path in py_files():
            with self.subTest(file=path.name):
                tree = ast.parse(path.read_text(encoding='utf-8'))
                self.assertTrue(ast.get_docstring(tree), f'{path.name} sem docstring')

    def test_every_renderer_has_a_docstring(self):
        import studydeck.registry as registry
        for name, spec in registry.MODULES.items():
            with self.subTest(module=name):
                self.assertTrue(spec['render'].__doc__, f'{name} sem docstring')

    def test_public_functions_are_documented(self):
        for path in py_files():
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    with self.subTest(file=path.name, function=node.name):
                        self.assertTrue(ast.get_docstring(node),
                                        f'{path.name}:{node.name} sem docstring')


class TestNoSuppression(unittest.TestCase):
    def test_no_bare_except_pass(self):
        for path in py_files():
            body = path.read_text(encoding='utf-8')
            with self.subTest(file=path.name):
                self.assertNotIn('except: pass', body)
                self.assertNotIn('except Exception: pass', body)

    def test_broad_exceptions_are_annotated(self):
        for path in py_files():
            body = path.read_text(encoding='utf-8').splitlines()
            for i, line in enumerate(body, 1):
                if 'except Exception' in line and 'noqa' not in line and '#' not in line:
                    with self.subTest(file=path.name, line=i):
                        self.fail(f'{path.name}:{i} except Exception sem justificativa')


if __name__ == "__main__":
    unittest.main()