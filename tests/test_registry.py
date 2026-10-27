# -*- coding: utf-8 -*-
"""Registro unico de modulos: 35 renderers, cada uno con tier, `when`,
presupuestos, requeridos, ajuste tipografico y gotcha."""

import unittest

from studydeck import registry
from studydeck.images import IMAGE_MODULES
from studydeck.modules import core, diagram, pedagogy, scholarly
from studydeck.registry import CORE_MODULES, MODULES, TIERS


class TestCatalogue(unittest.TestCase):
    def test_thirty_five_modules(self):
        self.assertEqual(len(MODULES), 35)

    def test_every_module_renders(self):
        for name, spec in MODULES.items():
            with self.subTest(module=name):
                self.assertTrue(callable(spec['render']))

    def test_every_module_declares_when_to_use_it(self):
        for name, spec in MODULES.items():
            with self.subTest(module=name):
                self.assertTrue(spec['when'].strip())

    def test_every_module_has_a_tier(self):
        self.assertEqual(set(TIERS), set(MODULES))

    def test_every_module_has_a_schema(self):
        for name, spec in MODULES.items():
            with self.subTest(module=name):
                self.assertTrue(spec['schema'])

    def test_renderers_are_distinct_functions(self):
        seen = {}
        for name, spec in MODULES.items():
            fn = spec['render']
            self.assertNotIn(fn, seen, f'{name} comparte renderer con {seen.get(fn)}')
            seen[fn] = name

    def test_all_renderers_come_from_the_four_tier_modules(self):
        allowed = set()
        for mod in (core, diagram, scholarly, pedagogy):
            allowed.update(getattr(mod, n) for n in dir(mod) if n.startswith('m_'))
        self.assertEqual({spec['render'] for spec in MODULES.values()} - allowed, set())

    def test_unknown_module_lookup_raises(self):
        with self.assertRaises(KeyError):
            MODULES['no_existe']

    def test_core_modules_are_present(self):
        self.assertTrue(set(CORE_MODULES).issubset(set(MODULES)))

    def test_image_modules_are_flagged_on_the_registry(self):
        flagged = {n for n, s in MODULES.items() if s['accepts_image']}
        self.assertEqual(flagged, set(IMAGE_MODULES))

    def test_risky_modules_document_their_gotcha(self):
        for name in ('comparison_table', 'synthesis_grid', 'flow_diagram',
                     'etymology', 'mnemonic_card', 'chart_data'):
            with self.subTest(module=name):
                self.assertTrue(MODULES[name]['gotcha'])

    def test_no_duplicate_budget_blocks(self):
        import studydeck.contracts as c
        self.assertIs(c.B, registry.B)

    def test_registry_exposes_modules_by_tier(self):
        for tier in set(TIERS.values()):
            with self.subTest(tier=tier):
                self.assertTrue(registry.modules_of_tier(tier))


class TestSelfConsistency(unittest.TestCase):
    def test_tiers_cover_the_five_editorial_families(self):
        self.assertEqual(set(TIERS.values()) - {'core', 'classic', 'diagram',
                                                'scholarly', 'pedagogy'}, set())

    def test_required_fields_are_known_contract_fields(self):
        for name, spec in MODULES.items():
            with self.subTest(module=name):
                for field in spec['required']:
                    self.assertNotIn(field, ('module',))

    def test_fit_rules_only_for_text_bearing_modules(self):
        for name, spec in MODULES.items():
            if spec['fit'] is not None:
                with self.subTest(module=name):
                    self.assertTrue(callable(spec['fit']))


if __name__ == "__main__":
    unittest.main()