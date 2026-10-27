# -*- coding: utf-8 -*-
"""SCAFFOLD: guias advisory e o deck-minimo que `studydeck new` escreve.

Vive fora da CLI porque e DADO DE AUTORIA, nao comportamento de linha de
comando: as guias descrevem ritmo de leitura; os exemplos descrevem como se
escreve um campo que passa o lint.
"""

import os
import pprint

from .authoring import PLACEHOLDER
from .images import HARD_CAP, ImagePolicy
from .i18n import DEFAULT_LANG
from .registry import MODULES
from .version import VERSION

GUIDES = {
    'lecture': {
        'length': '18-30 slides',
        'hint': ('abre con learning_objectives si o source enumera metas; un '
                 'section_divider por bloco tematico; processo->flow_diagram/'
                 'cycle_diagram; comparacao->comparison_table/side_by_side; '
                 'evolucao->timeline; fecha com case_block o viva_question + '
                 'further_reading'),
    },
    'short': {
        'length': '8-14 slides',
        'hint': ('definition+figure cedo; um bloco central conforme a forma do '
                 'source (flow|table|timeline|case); fecha com checklist ou '
                 'further_reading'),
    },
    'custom': {
        'length': 'livre',
        'hint': 'escolha cada modulo pelo seu `when`; title + section_divider bastam de base',
    },
}


EXAMPLES = {
    'title': {
        'module': 'title',
        'title': 'Exemplo: inflamacao aguda',
        'subtitle': 'Do estimulo lesivo a resolucao do tecido',
        'course': 'Nome da disciplina',
        'institution': 'Nome da instituicao',
    },
    'section_divider': {
        'module': 'section_divider',
        'section_title': 'Exemplo: a resposta inflamatoria',
        'section_subtitle': ('Vasodilatacao, aumento da permeabilidade e migracao '
                             'leucocitaria formam uma sequencia coordenada.'),
    },
    'definition': {
        'module': 'definition',
        'kicker': 'Conceito',
        'title': 'Exemplo: inflamacao aguda',
        'main_statement': ('Resposta vascular estereotipada do tecido vivo diante '
                           'da lesao, orientada a neutralizar o agente e reparar '
                           'o dano.'),
        'key_points': [
            {'title': 'Fase vascular',
             'desc': 'Vasodilatacao e aumento da permeabilidade produzem rubor, '
                     'calor e edema.'},
            {'title': 'Fase celular',
             'desc': 'Neutrofilos chegam primeiro; monocitos conduzem a reparacao.'},
        ],
    },
    'checklist': {
        'module': 'checklist',
        'kicker': 'Pratica',
        'title': 'Exemplo: verificacao do primeiro atendimento',
        'items': [
            {'label': 'Confirmar sinal vital alterado',
             'desc': 'Registrar hora do primeiro registro e tendencia.'},
            {'label': 'Solicitar exames guiados',
             'desc': 'Pedir apenas o que muda a conduta imediata.'},
        ],
    },
}


def write_scaffold(profile='short', out='manifest.py', lang=DEFAULT_LANG):
    """write_scaffold: documented behavior of the module."""
    if profile not in GUIDES:
        print(f'[StudyDeck New] Guia desconhecida: {profile!r}; use '
              f'{", ".join(GUIDES)}')
        return 1
    guide = GUIDES[profile]
    import os
    if os.path.exists(out):
        print(f'[StudyDeck New] FAIL — {out} ja existe (nao sobrescreve).')
        return 1
    examples = [EXAMPLES[m] for m in ('title', 'section_divider', 'definition',
                                       'checklist')]
    menu = '\n'.join(f'  {n}: {MODULES[n]["when"]}' for n in sorted(MODULES))
    policy = ImagePolicy()
    lines = [
        '# -*- coding: utf-8 -*-',
        f'"""Scaffold gerado por {VERSION} — guia "{profile}" ({guide["length"]}).',
        '',
        'GUIA (advisory): ' + guide['hint'],
        '',
        'IMAGENS: por defecto web-only, presupuesto auto pelo source '
        f'(tope {HARD_CAP}). A imagem APOIA a mensagem: pie analitico '
        'que diga o que se ensina, nunca preenchimento.',
        '',
        'MODULOS DISPONIVEIS — escolha pelo QUANDO (context-aware):',
        menu,
        '',
        'Contrato por modulo: studydeck schema <modulo>.',
        'Os 4 slides iniciais sao EXEMPLOS completos que passam o lint: edite-os, '
        'duplique o bloco que precisar ou apague o que nao usar. Ao escrever '
        f'conteudo novo, respeite os limites de `studydeck schema <modulo>` e '
        f'rediga a 90% deles. Nenhum marcador "{PLACEHOLDER.format("N")}" sobrevive '
        'ao lint."""',
        '',
        "COURSE_INFO = {'course': '<disciplina>', 'institution': '<instituicao>', 'author': ''}",
        "CONFIG = {'PALETTE': 'ucp', 'LANG': '%s', 'PROFILE': '%s'," % (lang, profile),
        "          'IMAGES': {'mode': 'web-only', 'max_n': 'auto',",
        "                     'allow_ai': False, 'allow_placeholder': False},",
        "          'SHOW_FOOTER': True, 'SHOW_SLIDE_NUMBER': True,",
        "          'ALLOW_TERMS': []}",
        '',
        'SLIDES = [',
    ]
    for ex in examples:
        lines.append(pprint.pformat(ex, width=96, sort_dicts=False) + ',')
    lines.append(']')
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f'[StudyDeck New] Scaffold escrito: {out} (guia "{profile}": {guide["length"]})')
    print('[StudyDeck New] Proximo: componha SLIDES casando `when` com o source · '
          'lint · all')
    return 0
