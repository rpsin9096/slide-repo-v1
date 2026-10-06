# -*- coding: utf-8 -*-
"""REGISTRO UNICO DE MODULOS.

Indice y nada mas: para anadir un modulo se escribe su renderer y su bloque en
este archivo. Ni el linter ni el render conocen la lista por otra via.
"""

from .contracts import B, FIT_RULES, MODULE_GOTCHAS, REQUIRED_NONEMPTY
from .images import IMAGE_MODULES
from .modules.core import (
    m_algorithm, m_case_block, m_checklist, m_comparison_table, m_definition,
    m_figure, m_fixed_schema_card, m_flow_diagram, m_section_divider,
    m_side_by_side, m_stat_card, m_synthesis_grid, m_taxonomy_tree, m_title,
)
from .modules.diagram import (
    m_chart_data, m_cycle_diagram, m_pyramid, m_quadrant_matrix, m_timeline,
)
from .modules.pedagogy import (
    m_annotated_passage, m_colloquy, m_further_reading, m_glossary,
    m_learning_objectives,
)
from .modules.scholarly import (
    m_authority_card, m_etymology, m_evidence_card,
    m_mnemonic_card, m_oxford_union, m_quote_block, m_references,
    m_socratic_question, m_venn_diagram, m_viva_question,
)
from .modules.pedagogy import m_concept_map

RENDERERS = {
    'title': m_title, 'section_divider': m_section_divider,
    'definition': m_definition, 'figure': m_figure, 'flow_diagram': m_flow_diagram,
    'comparison_table': m_comparison_table, 'synthesis_grid': m_synthesis_grid,
    'stat_card': m_stat_card, 'checklist': m_checklist,
    'fixed_schema_card': m_fixed_schema_card, 'side_by_side': m_side_by_side,
    'taxonomy_tree': m_taxonomy_tree, 'algorithm': m_algorithm,
    'case_block': m_case_block, 'quote_block': m_quote_block,
    'timeline': m_timeline, 'cycle_diagram': m_cycle_diagram,
    'quadrant_matrix': m_quadrant_matrix, 'pyramid': m_pyramid,
    'socratic_question': m_socratic_question, 'oxford_union': m_oxford_union,
    'evidence_card': m_evidence_card, 'viva_question': m_viva_question,
    'mnemonic_card': m_mnemonic_card, 'etymology': m_etymology,
    'venn_diagram': m_venn_diagram, 'chart_data': m_chart_data,
    'references': m_references, 'authority_card': m_authority_card,
    'learning_objectives': m_learning_objectives, 'colloquy': m_colloquy,
    'annotated_passage': m_annotated_passage, 'concept_map': m_concept_map,
    'glossary': m_glossary, 'further_reading': m_further_reading,
}

TIERS = {
    'title': 'core', 'definition': 'core', 'section_divider': 'core',
    'figure': 'core',
    'flow_diagram': 'classic', 'comparison_table': 'classic',
    'synthesis_grid': 'classic', 'stat_card': 'classic', 'checklist': 'classic',
    'fixed_schema_card': 'classic', 'side_by_side': 'classic',
    'taxonomy_tree': 'classic', 'algorithm': 'classic', 'case_block': 'classic',
    'timeline': 'diagram', 'cycle_diagram': 'diagram',
    'quadrant_matrix': 'diagram', 'pyramid': 'diagram',
    'venn_diagram': 'diagram', 'concept_map': 'diagram', 'chart_data': 'diagram',
    'quote_block': 'scholarly', 'socratic_question': 'scholarly',
    'oxford_union': 'scholarly', 'evidence_card': 'scholarly',
    'viva_question': 'scholarly', 'mnemonic_card': 'scholarly',
    'etymology': 'scholarly', 'references': 'scholarly',
    'authority_card': 'scholarly',
    'learning_objectives': 'pedagogy', 'colloquy': 'pedagogy',
    'annotated_passage': 'pedagogy', 'glossary': 'pedagogy',
    'further_reading': 'pedagogy',
}

WHEN = {
    'title': 'toda apresentacao: capa com curso, titulo e subtitulo',
    'section_divider': 'transicao entre blocos tematicos do source; da ritmo em decks longos',
    'definition': 'a tese central que o deck desenvolve + pontos-chave; vai no inicio',
    'figure': 'ha uma imagem REAL que desenvolve conteudo (histologia, esquema do source, imagem clinica)',
    'flow_diagram': 'processo linear de 3-4 passos; passos com decision=True ramificam (sim/nao)',
    'comparison_table': 'comparar opcoes/criterios: 3-4 colunas x 3-4 linhas',
    'synthesis_grid': 'malla densa 3x3 de relacoes (matriz-resumo de uma secao)',
    'stat_card': 'UM numero do source merece protagonismo + blocos narrativos de apoio',
    'checklist': 'protocolo ou lista de verificacao acionavel (passos a seguir na pratica)',
    'fixed_schema_card': 'entidade com campos fixos label->valor (criterios diagnosticos, ficha)',
    'side_by_side': 'dicotomia A vs B com pontos de cada lado',
    'taxonomy_tree': 'classificacao hierarquica: raiz + 2-3 categorias com exemplos',
    'algorithm': 'cascata numerada de decisoes ou procedimentos',
    'case_block': 'caso/vinheta com achados, raciocinio, diagnostico e perola — fecha bem um tema',
    'quote_block': 'citacao textual relevante com autor e contexto',
    'timeline': 'evolucao temporal, fases ou marcos (3-5): historia natural, etapas, cronologia',
    'cycle_diagram': 'processo ciclico fechado de 3-6 nos (retroalimentacao)',
    'quadrant_matrix': 'matriz 2x2 com eixos (decisao bidimensional, classificacao)',
    'pyramid': 'hierarquia de niveis (3-5) onde a base sustenta o topo',
    'socratic_question': 'pergunta tutorial com andaime de raciocinio numerado — autoestudo',
    'oxford_union': 'debate pro/contra sobre uma mocai com veredito (temas controvertidos)',
    'evidence_card': 'um estudo/paper chave: PICO + efeito principal + limitacao',
    'viva_question': 'pergunta de prova oral com resposta-modelo e nota do examinador — revisao ativa',
    'mnemonic_card': 'regra mnemotecnica tipo acronimo (um termo por letra)',
    'etymology': 'deconstrucao de um termo em suas raizes (grego/latino)',
    'venn_diagram': 'sobreposicao de 2-3 conjuntos com zona compartilhada',
    'chart_data': 'dados numericos comparaveis (grafico nativo editavel) + painel de leitura',
    'references': 'bibliografia numerada em duas colunas',
    'authority_card': 'autor/figura com retrato real + biografia + legado',
    'learning_objectives': 'objetivos de aprendizagem com verbo Bloom — abre decks de aula',
    'colloquy': 'dialogo tutor/estudante alternado (tutoria socratica)',
    'annotated_passage': 'texto-fonte primario com notas marginais numeradas [1] [2]',
    'concept_map': 'conceito central com 4-6 satelites radiais',
    'glossary': 'terminologia-chave com definicoes breves (4-10 termos)',
    'further_reading': 'leituras graduadas por dificuldade para aprofundar',
}

CORE_MODULES = ('title', 'definition', 'section_divider', 'figure')

MODULES = {}
for _name, _fn in RENDERERS.items():
    MODULES[_name] = {
        'render': _fn,
        'tier': TIERS[_name],
        'schema': B[_name],
        'required': tuple(REQUIRED_NONEMPTY[_name]),
        'fit': FIT_RULES.get(_name),
        'when': WHEN[_name],
        'gotcha': MODULE_GOTCHAS.get(_name),
        'accepts_image': _name in IMAGE_MODULES,
    }
del _name, _fn

assert set(MODULES) == set(B) == set(REQUIRED_NONEMPTY) == set(TIERS) == set(WHEN) \
    == set(MODULE_GOTCHAS) | set(MODULES), 'registro desincronizado'
assert len(MODULES) == 35, f'esperava 35 modulos, ha {len(MODULES)}'
assert all(callable(s['render']) for s in MODULES.values())
assert all(s['when'].strip() for s in MODULES.values())
assert set(CORE_MODULES) <= set(MODULES)


def modules_of_tier(tier):
    """Nombres de los modulos de una familia editorial (core/classic/diagram/...)."""
    return tuple(n for n in MODULES if MODULES[n]['tier'] == tier)