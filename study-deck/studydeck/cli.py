# -*- coding: utf-8 -*-
"""CLI — a unica superficie que el autor toca.

Convenio: cada comando imprime su veredicto y devuelve codigo de salida (0 ok,
1 veredicto negativo, 2 uso incorrecto). `--json` existe para los agentes que
se autocorrijan.
"""

import json
import pprint
import sys

from . import ingest as ING
from . import lint as L
from . import manifest as MF
from . import render as RD
from .authoring import PLACEHOLDER, constraints, skeleton
from .i18n import DEFAULT_LANG, LANGS
from .imagedata import imgprep, inspect_sources
from .palette import PALETTES, derive_tokens_for_display
from .registry import MODULES
from .scaffold import GUIDES, write_scaffold
from .version import VERSION

USAGE = f"""  check                              deps + self-test (35/35 modulos, contraste UCP)
  schema [modulo|all|tokens]         contrato + quando usar + esqueleto
  new [guia] [out.py]                scaffold minimo + guia advisory
  ingest <fonte.pdf|txt|md>          outline do source para autorar
  imgprep [pasta]                    contrato de imagens (20 KB-4 MB, >=300 px)
  lint <manifest.py> [--json]        contrato por slide
  build <manifest.py> [out.pptx]     lint fail-fast + render (contraste incluido)
  all <manifest.py> [out.pptx]       lint -> build
  contrast [manifest.py] [--json]    matriz UCP ou escaneo de um deck"""


def _fail(message):
    print(message)
    return 1


def cmd_check():
    """Self-test: renderiza os 35 modulos e fecha o veredicto de contraste."""
    print(VERSION)
    rows = RD.self_test()
    ok = sum(1 for _n, passed, _d in rows if passed)
    for name, passed, detail in rows:
        if not passed:
            print(f'  FAIL {name}: {detail}')
    total_fails = 0
    for name, _passed, _detail in rows:
        from .fixtures import fixture_slides
        break
    print(f'[StudyDeck Check] modulos {ok}/{len(rows)} renderizados sem violacao de contraste')
    # matriz de contraste sobre el fixture completo (los 35 modulos en un deck)
    fixture = [s for s in fixture_slides()]
    deck = MF.Deck('<fixture>', fixture, {'course': 'STUDYDECK CHECK'},
                   {'LANG': DEFAULT_LANG})
    _errs, fails = RD.contrast_scan(deck)
    total_fails += len(fails)
    for cf in fails[:8]:
        print(f"  X slide {cf.get('slide')} [{cf.get('module')}]: #{cf.get('fg')} "
              f"sobre #{cf.get('bg')} = {cf.get('ratio')} (requer {cf.get('required')})")
    print(f'[StudyDeck Check] contraste fixture: '
          f'{"PASS — 0 violaciones" if not fails else f"FAIL — {len(fails)}"}')
    return 0 if (ok == len(rows) and not fails) else 1


def cmd_schema(module=None):
    """Menú context-aware (`when`), contrato por módulo y esqueleto pegable."""
    if module in (None, 'all', '--all'):
        print(f'{VERSION} — contrato de autoria')
        print('\nEscolha CONTEXT-AWARE: cada modulo diz QUANDO usar. Case a forma do '
              'conteudo do source; nao siga receitas fechadas.\n')
        for name in sorted(MODULES):
            print(f'  [{MODULES[name]["tier"]:<9}] {name}: {MODULES[name]["when"]}')
        print('\nGuias (advisory, nao coercitivas):')
        for guide, data in GUIDES.items():
            print(f'  {guide} ({data["length"]}):\n    {data["hint"]}')
        print(f'\nPor modulo: schema <modulo>   ·   Tokens WCAG: schema tokens')
        return 0
    if module == 'tokens':
        print(f'  {"tema":<10}{"on_primary":<12}{"on_prm_soft":<13}{"on_accent":<11}'
              f'{"ink_accent":<11}{"ink_success":<12}{"subtitle":<9}')
        for key in PALETTES:
            tokens = derive_tokens_for_display(key)
            print(f'  {key:<10}{tokens["on_primary"]:<12}{tokens["on_primary_soft"]:<13}'
                  f'{tokens["on_accent"]:<11}{tokens["ink_accent"]:<11}'
                  f'{tokens["ink_success"]:<12}{tokens["subtitle_on_primary"]:<9}')
        print('\n  Override fino: PALETTE_OVERRIDES = {<tema>: {<token>: "RRGGBB"}}')
        return 0
    if module not in MODULES:
        import difflib
        near = difflib.get_close_matches(module, list(MODULES), n=3)
        print(f'Modulo desconhecido: {module!r}'
              + (f' — quis dizer {", ".join(near)}?' if near else ''))
        print('Execute: studydeck schema   (listado completo)')
        return 2
    spec = MODULES[module]
    print(f'{VERSION} — modulo: {module}')
    print(f'\nQUANDO USAR: {spec["when"]}')
    print('\nCONTRATO:')
    print(constraints(module))
    print('\nESQUELETO (colar no manifest e substituir os marcadores):')
    print(pprint.pformat(skeleton(module), width=98, sort_dicts=False))
    print('\nOs limites sao de CARACTERES (com espacos e acentos). Redija a 90% do '
          'limite para absorver correcoes.')
    return 0


USAGE_ERROR = 2
VERIFY_ERROR = 1


def _load_or_report(path):
    """(deck, rc) — rc=2 se a rota nao existe (uso), rc=1 se o conteudo esta ruim."""
    import os
    if not os.path.exists(path):
        print(f'[StudyDeck] FAIL — manifest nao encontrado: {path}')
        return None, USAGE_ERROR
    try:
        deck = MF.load(path)
    except Exception as exc:                        # noqa: BLE001 - erro de autor
        print(f'[StudyDeck] FAIL — {exc}')
        return None, VERIFY_ERROR
    for warning in deck.warnings:
        print(f'[StudyDeck] AVISO — {warning}')
    return deck, 0


def cmd_lint(path, as_json=False):
    """Veredicto de contrato por slide; `--json` para agentes."""
    deck, rc = _load_or_report(path)
    if deck is None:
        if as_json:
            print(json.dumps({'kit': VERSION, 'status': 'FAIL', 'error_count': 1,
                              'errors': [{'scope': 'manifest',
                                          'message': f'manifest ilegivel: {path}',
                                          'raw': str(path)}]},
                             ensure_ascii=False, indent=2))
        return rc
    errs = L.check(deck.slides, deck.lang, deck.images, deck.allow_terms)
    errs.extend(inspect_sources(deck.slides))
    if as_json:
        print(json.dumps(L.errs_to_json(errs, deck.slides, deck.lang, deck.profile),
                         ensure_ascii=False, indent=2))
        return 1 if errs else 0
    if errs:
        print(f'[StudyDeck Lint] FAIL — {len(errs)} violacao(oes):')
        for err in errs:
            print('  X ' + err)
        return 1
    print(f'[StudyDeck Lint] PASS — {len(deck.slides)} slides cumprem o contrato '
          f'(idioma {deck.lang}, imagens {deck.images.mode}).')
    return 0


def cmd_build(path, out='deck.pptx'):
    """Lint fail-fast y render; no entrega deck con contraste insuficiente."""
    deck, rc = _load_or_report(path)
    if deck is None:
        return rc
    rc = cmd_lint(path)
    if rc != 0:
        print(f'[StudyDeck Build] Cancelado (fail-fast): rode `studydeck lint {path}`.')
        return rc
    try:
        n, fails = RD.render(deck, out)
    except KeyError as exc:
        print(f'[StudyDeck Build] FAIL — {exc}')
        return 1
    except FileNotFoundError as exc:
        print(f'[StudyDeck Build] FAIL — {exc}')
        return 1
    if fails:
        print(f'[StudyDeck Build] FAIL — {len(fails)} par(es) texto/superficie abaixo '
              f'do limiar WCAG (deck NAO salvo):')
        for cf in fails[:20]:
            print(f"  X slide {cf.get('slide')} [{cf.get('module')}]: "
                  f"#{cf.get('fg')} sobre #{cf.get('bg')} = {cf.get('ratio')} "
                  f"(requer {cf.get('required')})")
        return 1
    print(f'[StudyDeck Build] OK: {out} ({n} slides · contraste 0 violaciones)')
    return 0


def cmd_all(path, out='deck.pptx'):
    """Pipeline lint -> build."""
    print(f'[StudyDeck All] 1/2 — Lint: {path}')
    rc = cmd_lint(path)
    if rc != 0:
        print('[StudyDeck All] Lint FAIL — nao renderiza.')
        return rc
    print('[StudyDeck All] 2/2 — Build...')
    return cmd_build(path, out)


def cmd_contrast(path=None, as_json=False):
    """Matriz UCP del fixture o escaneo de un deck concreto."""
    if path:
        deck, rc = _load_or_report(path)
        if deck is None:
            return rc
        _errs, fails = RD.contrast_scan(deck)
        if as_json:
            print(json.dumps({'kit': VERSION, 'mode': 'manifest',
                              'status': 'PASS' if not fails else 'FAIL',
                              'error_count': len(fails), 'errors': fails},
                             ensure_ascii=False, indent=2))
            return 0 if not fails else 1
        if fails:
            print(f'[StudyDeck Contrast] FAIL — {len(fails)} par(es) abaixo do limiar:')
            for cf in fails:
                print(f"  X slide {cf.get('slide')} [{cf.get('module')}]: "
                      f"#{cf.get('fg')} sobre #{cf.get('bg')} = {cf.get('ratio')} "
                      f"< {cf.get('required')}")
            return 1
        print(f'[StudyDeck Contrast] PASS — 0 violaciones ({len(deck.slides)} slides).')
        return 0
    from .fixtures import fixture_slides
    deck = MF.Deck('<fixture>', fixture_slides(), {'course': 'STUDYDECK CHECK'},
                   {'LANG': DEFAULT_LANG})
    _errs, fails = RD.contrast_scan(deck)
    print('[StudyDeck Contrast] Matriz (fixture x paletas):')
    for key in PALETTES:
        print(f'  [{"PASS" if not fails else f"FAIL ({len(fails)})"}] {key}')
    for cf in fails[:8]:
        print(f"  X slide {cf.get('slide')} [{cf.get('module')}]: #{cf.get('fg')} "
              f"sobre #{cf.get('bg')} = {cf.get('ratio')}")
    print('[StudyDeck Contrast] '
          + ('PASS — 0 violaciones.' if not fails else f'FAIL — {len(fails)} violacao(oes).'))
    return 0 if not fails else 1


def cmd_ingest(source_path, out_dir='work'):
    """Outline del source para que el autor case cada sección con un `when`."""
    if not source_path:
        print("[StudyDeck CLI] FAIL — 'ingest' exige a rota do source.")
        return 2
    try:
        out_md, blocks = ING.ingest(source_path, out_dir)
    except FileNotFoundError as exc:
        return _fail(f'[StudyDeck Ingest] FAIL — {exc}')
    print(f'[StudyDeck Ingest] OK — outline em {out_md} ({blocks} blocos de texto).')
    print('[StudyDeck Ingest] Autoria: case cada secao com o `when` dos modulos '
          '(studydeck schema) e escreva o manifest.')
    return 0


def main(argv=None):
    """Punto de entrada de la CLI: devuelve código de salida, no imprime el final."""
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = '--json' in argv
    argv = [a for a in argv if a != '--json']
    if not argv or '--help' in argv or '-h' in argv:
        print(f'{VERSION}\nUso:\n{USAGE}')
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == 'check':
        return cmd_check()
    if cmd == 'schema':
        return cmd_schema(rest[0] if rest else None)
    if cmd == 'new':
        return write_scaffold(rest[0] if rest else 'short',
                               rest[1] if len(rest) > 1 else 'manifest.py')
    if cmd == 'ingest':
        if not rest:
            print("[StudyDeck CLI] FAIL — 'ingest' exige a rota do source.")
            return 2
        return cmd_ingest(rest[0], rest[1] if len(rest) > 1 else 'work')
    if cmd == 'imgprep':
        return imgprep(rest[0] if rest else 'work/imgs')
    if cmd == 'lint':
        if not rest:
            print("[StudyDeck CLI] FAIL — 'lint' exige a rota do manifest.")
            return 2
        return cmd_lint(rest[0], as_json=as_json)
    if cmd == 'build':
        if not rest:
            print("[StudyDeck CLI] FAIL — 'build' exige a rota do manifest.")
            return 2
        return cmd_build(rest[0], rest[1] if len(rest) > 1 else 'deck.pptx')
    if cmd == 'all':
        if not rest:
            print("[StudyDeck CLI] FAIL — 'all' exige a rota do manifest.")
            return 2
        return cmd_all(rest[0], rest[1] if len(rest) > 1 else 'deck.pptx')
    if cmd == 'contrast':
        return cmd_contrast(rest[0] if rest else None, as_json=as_json)
    print(f'[StudyDeck CLI] Comando desconhecido: {cmd}')
    return 2


if __name__ == '__main__':
    sys.exit(main() or 0)