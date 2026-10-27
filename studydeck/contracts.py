# -*- coding: utf-8 -*-
"""CONTRATOS DE AUTORIA: presupuestos de caracteres, requeridos, cardinalidades,
reglas de ajuste tipografico y trampas documentadas por modulo.

Este es el UNICO escritor de los presupuestos (`B`) y de `REQUIRED_NONEMPTY`:
el registro y el linter los importan; nadie redefine un segundo bloque.
"""

import re

from .geometry import CONTENT_W, SAFE_X0
from .typography import est_height

MARKER = re.compile(r'<=\s*\d+\s*car\.\s*>')
TIMELINE_MAX = 5
COLLOQUY_SPEAKERS = ('tutor', 'student')

FIT_RULES = {  # module -> callable(d) -> [(field, box_w_in, box_h_in, font_pt)]
 'title':          lambda d: [('title', 10.933, 2.1, 38.0)],
 'section_divider':lambda d: [('section_title', 11.0, 1.8, 36.0), ('section_subtitle', 10.5, 1.5, 15.0)],
 'definition':     lambda d: [('main_statement', (7.1 if d.get('image') else 11.5), 0.95, 15.5),
                              ('elaboration', (7.2 if d.get('image') else 11.6), SAFE_X0, CONTENT_W)],
 'stat_card':      lambda d: [('stat_title', 3.9, 1.8, 13.5)],
 'case_block':     lambda d: [('case_stem', (4.2 if d.get('image') else 5.45), 1.6, 11.5),
                              ('reasoning', (4.1 if d.get('image') else 5.4), 1.9, 10.8),
                              ('clinical_pearl', (4.1 if d.get('image') else 5.4), 1.15, 10.8)],
 'quote_block':    lambda d: [('quote', 9.4, 2.3, 20.0)],
 'socratic_question': lambda d: [('question', 9.9, 1.6, 20.0)],
 'oxford_union':   lambda d: [('motion', 11.4, 0.68, 17.0)],
 'viva_question':  lambda d: [('prompt', 5.1, 3.6, 16.0), ('model_answer', 5.6, 2.0, 11.5)],
 'authority_card': lambda d: [('bio', 7.8, 2.4, 11.5)],
 'evidence_card':  lambda d: [('population', 6.5, 0.85, 11.0), ('intervention', 6.5, 0.85, 11.0),
                              ('comparison', 6.5, 0.85, 11.0), ('outcome', 6.5, 0.85, 11.0)],
 'annotated_passage': lambda d: [('passage', 6.7, 4.15, 13.0)],
}


_BLOOM_VERBS = ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')






_NO_HEADER_MODULES = ('title', 'section_divider')


B = {
 'title':            {'title': 80, 'subtitle': 100, 'course': 70, 'institution': 70, 'author': 70},
 'figure':           {'caption': 110, 'credit': 130},
 'section_divider':  {'section_title': 70, 'section_subtitle': 180, 'divider_style': 40, 'author': 70},
 'definition':       {'main_statement': 240, 'elaboration': 230, 'footnote': 120,
                      'caption': 110, 'credit': 130,
                      '_list': ('key_points', 2, 3, {'title': 45, 'desc': 150})},
 'flow_diagram':     {'explanation': 340,
                      '_list': ('steps', 3, 4, {'label': 12, 'title': 35, 'desc': 170}),
                      '_desc_by_count': ('steps', {3: 220, 4: 170}),
                      '_highlight': ('steps', 1, 1),
                      '_decision_flow': (2, 40)},
 'comparison_table': {'takeaway': 140, '_table': ('rows', 3, 4, 3, 4, 160)},
 'synthesis_grid':   {'takeaway': 140, '_table': ('matrix_data', 3, 3, 3, 3, 220)},
 'stat_card':        {'stat_num': 10, 'stat_title': 120, 'caption': 110, 'credit': 130,
                      '_list': ('narrative_blocks', 1, 3, {'title': 45, 'desc': 180})},
 'checklist':        {'_list': ('items', 2, 5, {'label': 65, 'desc': 150}),
                      'caption': 110, 'credit': 130},
 'fixed_schema_card':{'_list': ('fields', 2, 5, {'label': 30, 'value': 170})},
 'side_by_side':     {'_cards': ({'header': 35, 'title': 50}, 3, 4, 125)},
 'taxonomy_tree':    {'root': 50,
                      '_list': ('categories', 2, 3, {'name': 30, 'property': 65}),
                      '_examples': (3, 90)},
 'algorithm':        {'_list': ('steps', 2, 4, {'title': 70, 'desc': 200}),
                      '_highlight': ('steps', 0, 1)},
 'case_block':       {'case_stem': 240, 'reasoning': 250, 'diagnosis': 50,
                      'clinical_pearl': 160, '_strlist': ('findings', 2, 5, 80),
                      'caption': 110, 'credit': 130},
 'timeline':         {'_list': ('milestones', 3, TIMELINE_MAX, {'label': 20, 'title': 40, 'desc': 110}),
                      '_desc_by_count': ('milestones', {3: 110, 4: 95, 5: 70})},
 'cycle_diagram':    {'center_label': 40,
                      '_list': ('nodes', 3, 6, {'title': 40, 'desc': 90}),
                      '_highlight': ('nodes', 0, 2)},
 'quadrant_matrix':  {'x_label': 45, 'y_label': 45, '_quads': (40, 2, 5, 110)},
 'pyramid':          {'_list': ('levels', 3, 5, {'title': 55, 'desc': 90}),
                      '_highlight': ('levels', 0, 1)},
 'quote_block':      {'quote': 260, 'author': 60, 'source': 90, 'year': 12, 'context': 160},
 'socratic_question':{'question': 220, 'context': 160, 'reading': 130,
                      '_strlist': ('scaffold', 2, 4, 90)},
 'oxford_union':     {'motion': 140, 'verdict': 160,
                      '_debate': ({'title': 30}, 2, 4, 110)},
 'evidence_card':    {'study_name': 60, 'design': 60, 'population': 140, 'intervention': 140,
                      'comparison': 140, 'outcome': 140, 'effect': 14, 'effect_desc': 120,
                      'limitation': 160, 'year': 10, 'credit': 130},
 'viva_question':    {'prompt': 220, 'model_answer': 260, 'examiner_note': 180, 'difficulty': 12},
 'mnemonic_card':    {'acronym': 8, 'usage': 200, 'domain': 30,
                      '_acronym': ('expansion', 30)},
 'etymology':        {'term': 30, 'modern': 160,
                      '_list': ('roots', 2, 3, {'part': 20, 'origin': 20, 'meaning': 70})},
 'venn_diagram':     {'_venn': (30, 2, 4, 45, 1, 3, 45)},
 'chart_data':       {'chart_type': 6, 'credit': 130,
                      '_chart': (2, 8, 1, 2, 30, 2, 3, 120, 25)},
 'references':       {'_strlist': ('refs', 3, 10, 160)},
 'authority_card':   {'name': 60, 'dates': 30, 'epithet': 80, 'bio': 300,
                      'legacy': 120, 'caption': 110, 'credit': 130},
 'learning_objectives': {'_objectives': (3, 6, 25, 130)},
 'colloquy':         {'_colloquy': (4, 8, 160)},
 'annotated_passage':{'passage': 520, 'source': 90,
                      '_list': ('annotations', 2, 5, {'ref': 6, 'note': 110})},
 'concept_map':      {'hub': 40,
                      '_list': ('nodes', 4, 6, {'title': 35, 'desc': 80}),
                      '_highlight': ('nodes', 0, 2)},
 'glossary':         {'_list': ('terms', 4, 10, {'term': 30, 'def': 130})},
 'further_reading':  {'_list': ('entries', 3, 6, {'title': 90, 'tag': 20, 'note': 100})},
}
COMMON = {'kicker': 55, 'title': 75, 'footnote': 140}

REQUIRED_NONEMPTY = {
    'title':            ['title'],
    'figure':           ['image', 'caption', 'credit'],
    'section_divider':  ['section_title'],
    'definition':       ['main_statement'],
    'flow_diagram':     [],
    'comparison_table': ['headers'],
    'synthesis_grid':   ['headers'],
    'stat_card':        ['stat_num', 'stat_title'],
    'checklist':        [],
    'fixed_schema_card':[],
    'side_by_side':     [],
    'taxonomy_tree':    ['root'],
    'algorithm':        [],
    'case_block':       ['case_stem', 'reasoning', 'diagnosis', 'clinical_pearl'],
    'timeline':         [],
    'cycle_diagram':    [],
    'quadrant_matrix':  [],
    'pyramid':          [],
    'quote_block':      ['quote', 'author'],
    'socratic_question':['question'],
    'oxford_union':     ['motion', 'verdict'],
    'evidence_card':    ['study_name', 'design', 'population', 'intervention', 'outcome', 'effect', 'credit'],
    'viva_question':    ['prompt', 'model_answer', 'examiner_note'],
    'mnemonic_card':    ['acronym', 'usage'],
    'etymology':        ['term', 'modern'],
    'venn_diagram':     [],
    'chart_data':       [],
    'references':       [],
    'authority_card':   ['image', 'name', 'bio'],
    'learning_objectives': [],
    'colloquy':         [],
    'annotated_passage':['passage'],
    'concept_map':      ['hub'],
    'glossary':         [],
    'further_reading':  [],
}



def _v_list(val, d, m, loc0, over, errs, spec=None):
    key, lo, hi, fl = val
    items = d.get(key, [])
    if spec and '_desc_by_count' in spec and spec['_desc_by_count'][0] == key:
        dl = spec['_desc_by_count'][1].get(len(items))
        if dl: fl = dict(fl, desc=dl)
    if not lo <= len(items) <= hi:
        errs.append(f'{loc0}.{key}: {len(items)} ítems, esperado {lo}-{hi}')
    for j, it in enumerate(items):
        for fk, flim in fl.items():
            over(f'{loc0}.{key}[{j}].{fk}', it.get(fk, ''), flim)

def _v_strlist(val, d, m, loc0, over, errs):
    key, lo, hi, lim = val
    items = d.get(key, [])
    if not lo <= len(items) <= hi:
        errs.append(f'{loc0}.{key}: {len(items)} ítems, esperado {lo}-{hi}')
    for s_ in items: over(f'{loc0}.{key}', s_, lim)

def _v_examples(val, d, m, loc0, over, errs):
    mx, lim = val
    for j, c in enumerate(d.get('categories', [])):
        exs = c.get('examples', [])
        if len(exs) > mx:
            errs.append(f'{loc0}.categories[{j}].examples: {len(exs)} > {mx}')
        for e in exs: over(f'{loc0}.categories[{j}].examples', e, lim)

def _v_sided_cards(val, d, m, loc0, over, errs, sides):
    fl, plo, phi, plim = val
    for side in sides:
        c = d.get(side, {})
        for fk, flim in fl.items():
            over(f'{loc0}.{side}.{fk}', c.get(fk, ''), flim)
        pts = c.get('points', [])
        if not plo <= len(pts) <= phi:
            errs.append(f'{loc0}.{side}.points: {len(pts)}, esperado {plo}-{phi}')
        for p in pts: over(f'{loc0}.{side}.points', p, plim)

def _v_cards(val, d, m, loc0, over, errs):
    _v_sided_cards(val, d, m, loc0, over, errs, ('left_card', 'right_card'))

def _v_debate(val, d, m, loc0, over, errs):
    _v_sided_cards(val, d, m, loc0, over, errs, ('pro_card', 'con_card'))

def _v_highlight(val, d, m, loc0, over, errs):
    key, lo, hi = val
    n = sum(1 for s_ in d.get(key, []) if s_.get('highlight'))
    if not lo <= n <= hi:
        errs.append(f'{loc0}: {n} {key} destacados, esperado {lo}-{hi}')

def _v_quads(val, d, m, loc0, over, errs):
    tlim, plo, phi, plim = val
    quads = d.get('quadrants', [])
    if len(quads) != 4:
        errs.append(f'{loc0}.quadrants: {len(quads)} cuadrantes, esperado 4')
    for j, q in enumerate(quads):
        over(f'{loc0}.quadrants[{j}].title', q.get('title', ''), tlim)
        pts = q.get('points', [])
        if not plo <= len(pts) <= phi:
            errs.append(f'{loc0}.quadrants[{j}].points: {len(pts)}, esperado {plo}-{phi}')
        for p in pts: over(f'{loc0}.quadrants[{j}].points', p, plim)

def _v_decision_flow(val, d, m, loc0, over, errs):
    max_dec, dlim = val
    steps_l = d.get('steps', [])
    ndec = sum(1 for s_ in steps_l if s_.get('decision'))
    if ndec > max_dec:
        errs.append(f'{loc0}: {ndec} decisiones, máximo {max_dec}')
    if ndec and d.get('explanation'):
        errs.append(f'{loc0}: steps.decision no es compatible con explanation')
    for j, s_ in enumerate(steps_l):
        if s_.get('decision'):
            over(f'{loc0}.steps[{j}].desc (ramificación NO)', s_.get('desc', ''), dlim)

def _v_acronym(val, d, m, loc0, over, errs):
    key, lim = val
    acr = str(d.get('acronym', ''))
    exp = d.get(key, [])
    if len(exp) != len(acr):
        errs.append(f'{loc0}.{key}: {len(exp)} términos para {len(acr)} letras')
    for j, e in enumerate(exp):
        over(f'{loc0}.{key}[{j}]', e, lim)

def _v_venn(val, d, m, loc0, over, errs):
    flab, slo, shi, ilim, hlo, hhi, hlim = val
    sets_l = d.get('sets', [])
    if not 2 <= len(sets_l) <= 3:
        errs.append(f'{loc0}.sets: {len(sets_l)} conjuntos, esperado 2-3')
    for j, st in enumerate(sets_l):
        over(f'{loc0}.sets[{j}].label', st.get('label', ''), flab)
        its = st.get('items', [])
        if not slo <= len(its) <= shi:
            errs.append(f'{loc0}.sets[{j}].items: {len(its)}, esperado {slo}-{shi}')
        for e in its: over(f'{loc0}.sets[{j}].items', e, ilim)
    sh = d.get('shared', [])
    if not hlo <= len(sh) <= hhi:
        errs.append(f'{loc0}.shared: {len(sh)}, esperado {hlo}-{hhi}')
    for e in sh: over(f'{loc0}.shared', e, hlim)

def _v_chart(val, d, m, loc0, over, errs):
    clo, chi, snlo, snhi, snlim, inlo, inhi, inlim, catlim = val
    cats_l = d.get('categories', [])
    series_l = d.get('series', [])
    ins = d.get('insights', [])
    if d.get('chart_type', 'bar') not in ('bar', 'line'):
        errs.append(f'{loc0}.chart_type: usar "bar" o "line"')
    if not clo <= len(cats_l) <= chi:
        errs.append(f'{loc0}.categories: {len(cats_l)}, esperado {clo}-{chi}')
    for j, cv in enumerate(cats_l):
        over(f'{loc0}.categories[{j}]', cv, catlim)
    if not snlo <= len(series_l) <= snhi:
        errs.append(f'{loc0}.series: {len(series_l)}, esperado {snlo}-{snhi}')
    for j, sr in enumerate(series_l):
        over(f'{loc0}.series[{j}].name', sr.get('name', ''), snlim)
        vals = sr.get('values', [])
        if len(vals) != len(cats_l):
            errs.append(f'{loc0}.series[{j}].values: {len(vals)} vs {len(cats_l)} categorías')
        for k_, v in enumerate(vals):
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errs.append(f'{loc0}.series[{j}].values[{k_}]: valor no numérico ({v!r})')
    if not inlo <= len(ins) <= inhi:
        errs.append(f'{loc0}.insights: {len(ins)}, esperado {inlo}-{inhi}')
    for e in ins: over(f'{loc0}.insights', e, inlim)

def _v_objectives(val, d, m, loc0, over, errs):
    lo, hi, vlim, tlim = val
    objs = d.get('objectives', [])
    if not lo <= len(objs) <= hi:
        errs.append(f'{loc0}.objectives: {len(objs)} objetivos, esperado {lo}-{hi}')
    for j, o in enumerate(objs):
        over(f'{loc0}.objectives[{j}].verb', o.get('verb', ''), vlim)
        over(f'{loc0}.objectives[{j}].text', o.get('text', ''), tlim)
        bl = str(o.get('bloom', '')).strip().lower()
        if bl and bl not in _BLOOM_VERBS:
            errs.append(f'{loc0}.objectives[{j}].bloom: {bl!r} no válido '
                        f'({"|".join(_BLOOM_VERBS)})')

def _v_colloquy(val, d, m, loc0, over, errs):
    lo, hi, tlim = val
    turns = d.get('turns', [])
    if not lo <= len(turns) <= hi:
        errs.append(f'{loc0}.turns: {len(turns)} turnos, esperado {lo}-{hi}')
    for j, t in enumerate(turns):
        sp = str(t.get('speaker', '')).strip().lower()
        if sp not in COLLOQUY_SPEAKERS:
            errs.append(f'{loc0}.turns[{j}].speaker: {sp!r} no válido (tutor|student)')
        over(f'{loc0}.turns[{j}].text', t.get('text', ''), tlim)

def _v_table(val, d, m, loc0, over, errs):
    key, rlo, rhi, clo, chi, lim = val
    rows = d.get(key, [])
    hdrs = d.get('headers', [])
    cw = d.get('col_widths')
    if not rlo <= len(rows) <= rhi:
        errs.append(f'{loc0}.{key}: {len(rows)} filas, esperado {rlo}-{rhi}')
    if not clo <= len(hdrs) <= chi:
        errs.append(f'{loc0}.headers: {len(hdrs)} columnas, esperado {clo}-{chi}')
    if cw and len(cw) != len(hdrs):
        errs.append(f'{loc0}.col_widths: {len(cw)} pesos vs {len(hdrs)} encabezados '
                    f'— un peso por encabezado, ni uno más (ver: schema {m})')
    if cw:
        if not isinstance(cw, (list, tuple)):
            errs.append(f'{loc0}.col_widths: usar lista de pesos numéricos')
        else:
            for j, w in enumerate(cw):
                if isinstance(w, bool) or not isinstance(w, (int, float)):
                    errs.append(f'{loc0}.col_widths[{j}]: peso no numérico ({w!r})')
                elif w <= 0:
                    errs.append(f'{loc0}.col_widths[{j}]: peso debe ser > 0')
    for r, row in enumerate(rows):
        if len(row) != len(hdrs):
            errs.append(f'{loc0}.{key}[{r}]: {len(row)} celdas vs {len(hdrs)} encabezados '
                        f'— no existe columna de etiqueta implícita: la 1.ª celda ES la 1.ª '
                        f'columna de headers (ver: schema {m})')
        for j, cell in enumerate(row):
            over(f'{loc0}.{key}[{r}][{j}]', cell, lim)

MODULE_GOTCHAS = {
 'comparison_table': 'La 1.ª columna de headers ES la columna de criterio: cada fila '
                     'debe tener exactamente len(headers) celdas.',
 'synthesis_grid':   'NO tiene columna de etiqueta implícita. matrix_data es una malla '
                     'de 3 filas x len(headers) celdas; la 1.ª celda ya es la 1.ª columna.',
 'flow_diagram':     'Exactamente 1 paso con highlight=True. Si algún paso lleva '
                     'decision=True, NO puede existir la clave explanation, y desc pasa '
                     'a ser la etiqueta de la rama NO (máx. 40 car.).',
 'etymology':        'fragments debe concatenarse EXACTAMENTE en term y tener el mismo '
                     'número de elementos que roots.',
 'mnemonic_card':    'len(expansion) debe ser igual a len(acronym): un término por letra.',
 'chart_data':       'chart_type solo admite "bar" o "line"; cada series.values debe tener '
                     'la misma longitud que categories y ser numérico.',
 'venn_diagram':     'shared representa SOLO la intersección; 2-3 conjuntos.',
 'learning_objectives': 'bloom debe ser remember|understand|apply|analyze|evaluate|create.',
 'colloquy':         'speaker debe ser exactamente "tutor" o "student".',
 'figure':           'image debe ser .jpg/.jpeg/.png existente, 20 KB-4 MB y >= 300 px de '
                     'lado menor. Ejecute `imgprep work/imgs` antes del lint. '
                     'caption ANALÍTICO (15-110 car.): describa qué muestra la figura, '
                     'no la decore.',
 'authority_card':   'Requiere retrato: mismas reglas de imagen que figure.',
 'case_block':       'findings es una lista de STRINGS cortas (no dicts).',
 'annotated_passage':'Los marcadores [1], [2]... del passage deben existir en annotations.ref.',
}


OPTIONAL_MODULES = ['timeline', 'cycle_diagram', 'quadrant_matrix', 'pyramid',
    'quote_block', 'socratic_question', 'oxford_union', 'evidence_card',
    'viva_question', 'mnemonic_card', 'etymology', 'venn_diagram',
    'chart_data', 'references', 'authority_card',
    'learning_objectives', 'colloquy', 'annotated_passage', 'concept_map',
    'glossary', 'further_reading']


SPEC_VALIDATORS = {
    '_list': _v_list,       # recibe spec para aplicar _desc_by_count
    '_strlist': _v_strlist,
    '_table': _v_table,
    '_examples': _v_examples,
    '_cards': _v_cards,
    '_debate': _v_debate,
    '_highlight': _v_highlight,
    '_quads': _v_quads,
    '_decision_flow': _v_decision_flow,
    '_acronym': _v_acronym,
    '_venn': _v_venn,
    '_chart': _v_chart,
    '_objectives': _v_objectives,
    '_colloquy': _v_colloquy,
}

MODULE_VALIDATORS = {
    'etymology': lambda d, m, loc0, over, errs: (
        (lambda frags_l: (
            errs.append(f'{loc0}.fragments: debe concatenar exactamente en term y '
                        f'tener len(roots) elementos (tiene {len(frags_l)})')
            if frags_l and (len(frags_l) != len(d.get('roots', []))
                            or ''.join(frags_l) != str(d.get('term', ''))) else None
        ))(d.get('fragments') or [])
    ),
    'annotated_passage': lambda d, m, loc0, over, errs: (
        (lambda marks, have: (
            errs.append(f'{loc0}: marcadores {sorted(marks - have, key=int)} del passage '
                        f'sin nota en annotations')
            if marks - have else None
        ))(
            set(re.findall(r'\[(\d+)\]', str(d.get('passage', '')))),
            {str(a.get('ref', '')).strip() for a in d.get('annotations', [])}
        )
    ),
}

