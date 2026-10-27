# -*- coding: utf-8 -*-
"""Superficie de autoria: `when` por modulo, contrato legible y esqueleto
pegable. Es lo que lee el agente que escreve ou edita um manifest.
"""

from .contracts import COMMON, COLLOQUY_SPEAKERS, TIMELINE_MAX, _NO_HEADER_MODULES
from .registry import CORE_MODULES, MODULES

BLOOM_VERBS = ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')

PLACEHOLDER = '<= {} car.>'

def _skel_field(lim):
    return PLACEHOLDER.format(lim)

def skeleton(m):
    """Paste-ready minimal dict that satisfies the contract for module m.
    El registro es la unica via: nadie consume los presupuestos directo."""
    spec = MODULES[m]['schema']
    d = {'module': m}
    if m not in _NO_HEADER_MODULES:
        d['kicker'] = _skel_field(COMMON['kicker'])
        d['title'] = _skel_field(COMMON['title'])
    for k, v in spec.items():
        if k.startswith('_'):
            continue
        d[k] = _skel_field(v) if isinstance(v, int) else v
    if m in ('figure', 'authority_card') or 'image' in MODULES[m]['required']:
        d['image'] = 'work/imgs/nombre_snake_case.jpg'
    if '_list' in spec:
        key, lo, hi, fl = spec['_list']
        d[key] = [{fk: _skel_field(fv) for fk, fv in fl.items()} for _ in range(lo)]
        if '_examples' in spec:
            mx, lim = spec['_examples']
            for it in d[key]:
                it['examples'] = [_skel_field(lim)] * min(mx, 2)
    if '_strlist' in spec:
        key, lo, hi, lim = spec['_strlist']
        d[key] = [_skel_field(lim)] * lo
    if '_table' in spec:
        key, rlo, rhi, clo, chi, lim = spec['_table']
        d['headers'] = [_skel_field(lim)] * clo
        d['col_widths'] = [2.0] * clo
        d[key] = [[_skel_field(lim)] * clo for _ in range(rlo)]
    # _cards y _debate comparten la misma forma de contrato
    for spec_key, sides in (('_cards', ('left_card', 'right_card')),
                            ('_debate', ('pro_card', 'con_card'))):
        if spec_key in spec:
            fl, plo, phi, plim = spec[spec_key]
            for side in sides:
                d[side] = {fk: _skel_field(fv) for fk, fv in fl.items()}
                d[side]['points'] = [_skel_field(plim)] * plo
    if '_quads' in spec:
        tlim, plo, phi, plim = spec['_quads']
        d['quadrants'] = [{'title': _skel_field(tlim),
                           'points': [_skel_field(plim)] * plo} for _ in range(4)]
    if '_venn' in spec:
        flab, slo, shi, ilim, hlo, hhi, hlim = spec['_venn']
        d['sets'] = [{'label': _skel_field(flab), 'items': [_skel_field(ilim)] * slo}
                     for _ in range(2)]
        d['shared'] = [_skel_field(hlim)] * hlo
    if '_chart' in spec:
        clo, chi, snlo, snhi, snlim, inlo, inhi, inlim, catlim = spec['_chart']
        d['chart_type'] = 'bar'
        d['categories'] = [_skel_field(catlim)] * clo
        d['series'] = [{'name': _skel_field(snlim), 'values': [0.0] * clo} for _ in range(snlo)]
        d['insights'] = [_skel_field(inlim)] * inlo
    if '_acronym' in spec:
        key, lim = spec['_acronym']
        d['acronym'] = 'ABC'
        d[key] = [_skel_field(lim)] * 3
    if '_objectives' in spec:
        lo, hi, vlim, tlim = spec['_objectives']
        d['objectives'] = [{'verb': _skel_field(vlim), 'text': _skel_field(tlim),
                            'bloom': 'understand'} for _ in range(lo)]
    if '_colloquy' in spec:
        lo, hi, tlim = spec['_colloquy']
        d['turns'] = [{'speaker': 'tutor' if i % 2 == 0 else 'student',
                       'text': _skel_field(tlim)} for i in range(lo)]
    if '_highlight' in spec:
        key, lo, hi = spec['_highlight']
        if lo >= 1 and isinstance(d.get(key), list) and d[key]:
            d[key][0]['highlight'] = True
    if m == 'etymology':
        d['term'] = 'Apendicitis'
        d['fragments'] = ['Apendic', 'itis']
    if m not in _NO_HEADER_MODULES:
        d.setdefault('footnote', _skel_field(COMMON['footnote']))
    return d

def _fit_preview(fit):
    """Linea informativa del ajuste tipografico; [] si la regla exige slide real.

    Una regla que necesita campos del slide no se puede evaluar con `{}`: esa
    linea es informativa, no un veredicto — y la ausencia se representa como
    lista vacia, no como silencio.
    """
    if not fit:
        return []
    try:
        flds = fit({})
        return ['  ajuste tipográfico verificado (desborde bloquea el build): '
                + ', '.join(f'{f} en caja {w}x{h} in @ {p} pt' for f, w, h, p in flds)]
    except (TypeError, KeyError, ValueError):
        return []


def constraints(m):
    """Contrato legible del modulo: requeridos, presupuestos y trampas."""
    spec = MODULES[m]['schema']  # via unica: el registro
    out = []
    spec_m = MODULES[m]
    req = spec_m['required']
    if req:
        out.append(f'  obligatorios (no vacíos): {", ".join(req)}')
    for k, v in spec.items():
        if not k.startswith('_'):
            out.append(f'  {k}: máx {v} car.')
    if m not in _NO_HEADER_MODULES:
        out.append(f'  kicker: máx {COMMON["kicker"]} car. · title: máx {COMMON["title"]} car. '
                   f'· footnote: máx {COMMON["footnote"]} car. (opcional)')
    if '_list' in spec:
        key, lo, hi, fl = spec['_list']
        flds = ' · '.join(f'{a}: máx {b}' for a, b in fl.items())
        out.append(f'  {key}: lista de {lo}-{hi} dicts [{flds}]')
    if '_desc_by_count' in spec:
        key, table = spec['_desc_by_count']
        out.append(f'  {key}.desc: el límite varía con el número de ítems -> ' +
                   ', '.join(f'{n} ítems = {lim} car.' for n, lim in table.items()))
    if '_strlist' in spec:
        key, lo, hi, lim = spec['_strlist']
        out.append(f'  {key}: lista de {lo}-{hi} strings, máx {lim} car. c/u')
    if '_table' in spec:
        key, rlo, rhi, clo, chi, lim = spec['_table']
        out.append(f'  headers: {clo}-{chi} columnas · {key}: {rlo}-{rhi} filas x '
                   f'len(headers) celdas, máx {lim} car. c/u · col_widths: '
                   f'un peso numérico > 0 por encabezado')
    # _cards y _debate comparten la misma forma de contrato
    for spec_key, sides in (('_cards', ('left_card', 'right_card')),
                            ('_debate', ('pro_card', 'con_card'))):
        if spec_key in spec:
            fl, plo, phi, plim = spec[spec_key]
            out.append(f'  {" / ".join(sides)}: {" · ".join(f"{a}: máx {b}" for a, b in fl.items())}'
                       f' + points: {plo}-{phi} strings de máx {plim} car.')
    if '_quads' in spec:
        tlim, plo, phi, plim = spec['_quads']
        out.append(f'  quadrants: EXACTAMENTE 4 dicts [title: máx {tlim}] + points: '
                   f'{plo}-{phi} strings de máx {plim} car.')
    if '_venn' in spec:
        flab, slo, shi, ilim, hlo, hhi, hlim = spec['_venn']
        out.append(f'  sets: 2-3 dicts [label: máx {flab}, items: {slo}-{shi} de máx {ilim}] · '
                   f'shared: {hlo}-{hhi} strings de máx {hlim}')
    if '_chart' in spec:
        clo, chi, snlo, snhi, snlim, inlo, inhi, inlim, catlim = spec['_chart']
        out.append(f'  categories: {clo}-{chi} (máx {catlim} car.) · series: {snlo}-{snhi} '
                   f'[name máx {snlim}, values numéricos = len(categories)] · '
                   f'insights: {inlo}-{inhi} de máx {inlim}')
    if '_acronym' in spec:
        key, lim = spec['_acronym']
        out.append(f'  {key}: un término (máx {lim} car.) POR CADA letra de acronym')
    if '_examples' in spec:
        mx, lim = spec['_examples']
        out.append(f'  categories[].examples: máx {mx} strings de máx {lim} car.')
    if '_highlight' in spec:
        key, lo, hi = spec['_highlight']
        out.append(f'  {key}[].highlight: entre {lo} y {hi} ítems con highlight=True')
    if '_decision_flow' in spec:
        mx, dlim = spec['_decision_flow']
        out.append(f'  steps[].decision: máx {mx} decisiones; desc de un paso decision = '
                   f'etiqueta de rama NO (máx {dlim} car.); incompatible con explanation')
    if '_objectives' in spec:
        lo, hi, vlim, tlim = spec['_objectives']
        out.append(f'  objectives: {lo}-{hi} dicts [verb: máx {vlim}, text: máx {tlim}, '
                   f'bloom: {"|".join(BLOOM_VERBS)}]')
    if '_colloquy' in spec:
        lo, hi, tlim = spec['_colloquy']
        out.append(f'  turns: {lo}-{hi} dicts [speaker: tutor|student, text: máx {tlim}]')
    out.extend(_fit_preview(spec_m['fit']))
    if MODULES[m]['gotcha']:
        out.append(f'  AVISO: {spec_m["gotcha"]}')
    return '\n'.join(out)
