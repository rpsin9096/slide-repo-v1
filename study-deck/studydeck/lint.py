# -*- coding: utf-8 -*-
"""LINTER DE CONTRATO POR SLIDE.

Que evita decks rotos y nada mas: campos obrigatorios no vazios, presupuestos
de caracteres, marcadores de scaffold sin substituir, ajuste tipografico,
deriva de idioma y politica de imagenes. No impone floors de variedad ni
exige la presencia de un modulo: elige cada modulo por su `when`.
"""

import re

from . import i18n
from .contracts import (
    COLLOQUY_SPEAKERS, COMMON, MARKER, MODULE_VALIDATORS, SPEC_VALIDATORS,
    _NO_HEADER_MODULES,
)
from .images import ImagePolicy
from .registry import MODULES
from .typography import est_height

FIT_TOLERANCE = 1.06


def _walk_strings(value, loc, visit):
    """Recorre los strings de un manifest saltando la clave `image`."""
    if isinstance(value, str):
        visit(value, loc)
    elif isinstance(value, dict):
        for k, v in value.items():
            if k == 'image':
                continue
            _walk_strings(v, f'{loc}.{k}', visit)
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            _walk_strings(v, f'{loc}[{i}]', visit)


def check(slides, lang=None, images=None, allow_terms=()):
    """[errores] del deck; lista vacia = contrato cumplido.

    `allow_terms` exime termos deliberadamente en outro idioma (latim medico,
    nome proprio, titulo de fonte) del guard de deriva.
    """
    lang = lang or i18n.DEFAULT_LANG
    allow_terms = tuple(str(t).lower() for t in (allow_terms or ()))
    policy = images if isinstance(images, ImagePolicy) else ImagePolicy()
    errs = []

    def over(loc, value, limit):
        if isinstance(value, str) and len(value) > limit:
            errs.append(f'{loc}: {len(value)} > {limit} caracteres (sobran '
                        f'{len(value) - limit}; recorte a <= {int(limit * 0.9)} '
                        f'para deixar margem)')

    def visit_marker(text, loc):
        if MARKER.fullmatch(text.strip()):
            errs.append(f'{loc}: marcador sin substituir "{text.strip()}" — '
                        f'escreva conteudo real (`schema {mod}` mostra o contrato)')

    def visit_drift(text, loc):
        for word, fix in i18n.drift_hits(text, lang):
            if any(t in text.lower() for t in allow_terms):
                continue
            errs.append(f'{loc}: drift {word!r} -> {fix} (reescreva em {lang})')

    for i, d in enumerate(slides, 1):
        mod = d.get('module')
        if mod not in MODULES:
            errs.append(f'slide {i}: modulo desconhecido {mod!r} '
                        f'(use `schema` para o catalogo)')
            continue
        loc0 = f'slide {i} [{mod}]'
        spec = MODULES[mod]['schema']
        if mod not in _NO_HEADER_MODULES:
            for field, limit in COMMON.items():
                over(f'{loc0}.{field}', d.get(field, ''), limit)
        for field, limit in spec.items():
            if field.startswith('_'):
                continue
            over(f'{loc0}.{field}', d.get(field, ''), limit)
        for field in MODULES[mod]['required']:
            if not str(d.get(field, '')).strip():
                errs.append(f'{loc0}.{field}: campo obrigatorio ausente ou vazio')
        for key, spec_rule in spec.items():
            if not key.startswith('_') or key == '_desc_by_count':
                continue
            fn = SPEC_VALIDATORS.get(key)
            if fn is None:
                continue
            if key == '_list':
                fn(spec_rule, d, mod, loc0, over, errs, spec=spec)
            else:
                fn(spec_rule, d, mod, loc0, over, errs)
        if mod in MODULE_VALIDATORS:
            MODULE_VALIDATORS[mod](d, mod, loc0, over, errs)
        fit = MODULES[mod]['fit']
        if fit:
            for field, box_w, box_h, size in fit(d):
                need = est_height(d.get(field, ''), box_w, size)
                if need > box_h * FIT_TOLERANCE:
                    errs.append(f'{loc0}.{field}: transbordo estimado '
                                f'({need:.2f}in > {box_h:.2f}in) — encurte o texto')
        _walk_strings(d, loc0, visit_marker)
        _walk_strings(d, loc0, visit_drift)
    errs.extend(policy.validate(slides))
    return errs


def errs_to_json(errs, slides=None, lang=None, profile=None):
    """Mismo veredicto en JSON, agrupado por slide: la salida que leen los agentes."""
    items, by_slide = [], {}
    for raw in errs:
        item = {'scope': 'slide', 'message': raw, 'raw': raw}
        match = re.match(r'slide (\d+)', raw)
        if match:
            idx = int(match.group(1))
            by_slide[idx] = by_slide.get(idx, 0) + 1
            item['slide'] = idx
        items.append(item)
    return {'kit': 'StudyDeck v2', 'status': 'PASS' if not errs else 'FAIL',
            'lang': lang or i18n.DEFAULT_LANG, 'profile': profile,
            'slides': len(slides) if slides is not None else None,
            'error_count': len(errs), 'errors': items,
            'slides_with_errors': sorted(by_slide),
            'hint': ('Corrija apenas os campos listados; rode `schema <modulo>` '
                     'para o contrato.')}