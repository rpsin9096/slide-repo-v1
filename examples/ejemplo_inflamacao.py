# -*- coding: utf-8 -*-
"""Deck de exemplo StudyDeck v2 — perfil curto, pt-BR, paleta UCP.

Módulos escolhidos pelo `when` de cada um, não por receita. Sem imagens: o
orçamento segue `auto` (lê o source) e o modo é `web-only` — para incluir uma
figura, aponte um arquivo local ou `https://` com `caption` analítico + `credit`.
"""

COURSE_INFO = {'course': 'Fisiopatologia', 'institution': 'UCP',
               'author': 'Cátedra de Fisiopatologia'}

CONFIG = {
    'PALETTE': 'ucp',
    'LANG': 'pt-BR',
    'PROFILE': 'short',
    'IMAGES': {'mode': 'web-only', 'max_n': 'auto',
               'allow_ai': False, 'allow_placeholder': False},
    'SHOW_FOOTER': True,
    'SHOW_SLIDE_NUMBER': True,
    'ALLOW_TERMS': [],
}

SLIDES = [
    {'module': 'title',
     'title': 'Fisiopatologia da inflamação aguda',
     'subtitle': 'Do estímulo lesivo à resolução',
     'course': 'Fisiopatologia', 'institution': 'UCP'},

    {'module': 'learning_objectives', 'kicker': 'Abertura', 'title': 'Objetivos',
     'objectives': [
         {'verb': 'Explicar', 'text': 'a cascada vascular e celular da inflamação aguda',
          'bloom': 'understand'},
         {'verb': 'Diferenciar', 'text': 'inflamação aguda de crônica por células e mediadores',
          'bloom': 'analyze'},
         {'verb': 'Aplicar', 'text': 'os sinais cardinais ao reconhecimento clínico precoce',
          'bloom': 'apply'}]},

    {'module': 'section_divider',
     'section_title': 'A resposta inflamatória',
     'section_subtitle': 'Vasodilatação, aumento da permeabilidade e migração leucocitária '
                         'formam uma sequência coordenada e autolimitada.'},

    {'module': 'definition', 'kicker': 'Conceito', 'title': 'Definição operacional',
     'main_statement': 'A inflamação aguda é a resposta vascular estereotipada do '
                       'tecido vivo diante da lesão, orientada a neutralizar o agente '
                       'e reparar o dano.',
     'key_points': [
         {'title': 'Fase vascular',
          'desc': 'Vasodilatação e aumento da permeabilidade produzem rubor, calor e edema.'},
         {'title': 'Fase celular',
          'desc': 'Neutrófilos chegam primeiro; monocitos conduzem a fase de reparo.'}]},

    {'module': 'timeline', 'kicker': 'Evolução', 'title': 'Fases temporais',
     'milestones': [
         {'label': '0-6 h', 'title': 'Vascular',
          'desc': 'Vasodilatação arteriolar e exsudato proteico.'},
         {'label': '1-2 d', 'title': 'Neutrófilos',
          'desc': 'Marginação, adesão e diapedese até o foco lesional.'},
         {'label': '3-5 d', 'title': 'Monócitos',
          'desc': 'Fagocitose persistente e sinais de resolução.'}]},

    {'module': 'comparison_table', 'kicker': 'Contraste', 'title': 'Aguda versus crônica',
     'headers': ['Critério', 'Aguda', 'Crônica'],
     'col_widths': [1.0, 1.2, 1.2],
     'rows': [['Duração', 'Minutos a dias', 'Semanas a anos'],
              ['Células', 'Neutrófilos', 'Linfócitos e macrófagos'],
              ['Tecido', 'Resolução ou abscesso', 'Fibrose e destruição']],
     'takeaway': 'A duração muda as células dominantes e o prognóstico do tecido.'},

    {'module': 'flow_diagram', 'kicker': 'Sequência', 'title': 'Cascada de mediadores',
     'steps': [
         {'label': '1', 'title': 'Lesão',
          'desc': 'O estímulo ativa mastócitos residentes.'},
         {'label': '2', 'title': 'Histamina',
          'desc': 'Vasodilatação e permeabilidade imediatas.', 'highlight': True},
         {'label': '3', 'title': 'Prostaglandinas',
          'desc': 'Sensibilização nociceptiva e febre.'},
         {'label': '4', 'title': 'Leucócitos',
          'desc': 'Quimiocinese dirigida ao foco lesional.'}]},

    {'module': 'case_block', 'kicker': 'Caso', 'title': 'Caso integrador',
     'case_stem': 'Paciente de 24 anos com ferida perfurante no antebraço: dor, calor, '
                  'eritema e tumefação de 12 horas de evolução, sem febre.',
     'findings': ['Rubor e calor localizados', 'Edema doloroso à pressão'],
     'reasoning': 'Os quatro sinais cardinais surgem nas primeiras horas: correspondem '
                  'à fase vascular, com exsudato já estabelecido.',
     'diagnosis': 'Inflamação aguda localizada',
     'clinical_pearl': 'O calor precede o edema: sua ausência precoce sugere alteração '
                       'vascular periférica e não inflamação.'},

    {'module': 'glossary', 'kicker': 'Termos', 'title': 'Glossário mínimo',
     'terms': [
         {'term': 'Diapedese', 'def': 'Passagem do leucócito entre as células endoteliais '
                                       'em direção ao interstício.'},
         {'term': 'Exsudato', 'def': 'Líquido rico em proteínas que se filtra na fase vascular.'},
         {'term': 'Quimiocinese', 'def': 'Migração celular orientada por gradientes químicos.'},
         {'term': 'Resolução', 'def': 'Retorno programado do tecido ao estado basal.'}]},

    {'module': 'further_reading', 'kicker': 'Aprofundar', 'title': 'Leituras graduadas',
     'entries': [
         {'tag': 'Essencial', 'title': 'Robbins: capítulo de inflamação aguda',
          'note': 'Base mínima para a prova.'},
         {'tag': 'Complementar', 'title': 'Mediadores lipídicos e resolução',
          'note': 'Resolvinas e lipoxinas em profundidade.'},
         {'tag': 'Avançado', 'title': 'Inflamação estéril e DAMPs',
          'note': 'Literatura primária recente.'}]},
]