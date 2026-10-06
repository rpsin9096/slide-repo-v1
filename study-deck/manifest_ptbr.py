# -*- coding: utf-8 -*-
"""Deck customizado pt-BR — Caso Clínico 09: pancreatite aguda biliar.

Os dois marcadores ``placeholder:`` reservam os espaços das imagens oficiais
(macroscopia e H&E) que ainda precisam ser extraídas do PPTX original. A
ilustração local é um apoio visual gerado por IA para a etiopatogenia; ela não
substitui as imagens do caso.
"""

COURSE_INFO = {
    'course': 'Seminário Integrador · S5 · Turma E',
    'institution': 'Universidad Central del Paraguay (UCP)',
    'author': 'Equipe de 10 integrantes',
}

CONFIG = {
    'PALETTE': 'ucp',
    'LANG': 'pt-BR',
    'PROFILE': 'custom',
    'IMAGES': {
        'mode': 'mixed',
        'max_n': 'auto',
        'allow_ai': True,
        'allow_placeholder': True,
    },
    'SHOW_FOOTER': True,
    'SHOW_SLIDE_NUMBER': True,
    # "del" é parte do nome institucional oficial; não é um calco editorial.
    'ALLOW_TERMS': ['del'],
}

SLIDES = [
    {
        'module': 'title',
        'course': 'Seminário Integrador · S5 · Turma E',
        'title': 'Caso clínico 09: pancreatite aguda biliar',
        'subtitle': 'Abdome agudo inflamatório · apresentação integrada do grupo',
        'institution': 'Universidad Central del Paraguay (UCP) · Curso de Medicina',
        'author': 'Equipe de 10 integrantes',
    },
    {
        'module': 'side_by_side',
        'kicker': 'Organização do grupo',
        'title': 'Uma defesa, dez frentes de preparo',
        'left_card': {
            'header': 'Relatoria · 4 integrantes',
            'title': 'A exposição em 10 minutos',
            'points': [
                '01 · Abertura: história clínica e hipóteses',
                '02 · Mecanismo: obstrução biliar e tripsina',
                '03 · Morfologia e imagem: macro, H&E e TC',
                '04 · Manejo: fase aguda, prevenção e referências',
            ],
        },
        'right_card': {
            'header': 'Sustentação · 6 integrantes',
            'title': 'A banca encontra seis respostas-chave',
            'points': [
                '05–06 · fármacos, dor, íleo e sinais semiológicos',
                '07–08 · zimógenos, citocinas, TC e ultrassom',
                '09–10 · APS, prevenção e lesões histopatológicas',
            ],
        },
        'footnote': 'Os rótulos 01–10 seguem o plano de trabalho; substituir pelos nomes e matrículas oficiais antes do upload.',
    },
    {
        'module': 'case_block',
        'kicker': 'Quadro clínico',
        'title': 'A história orienta o primeiro diagnóstico',
        'case_stem': 'Mulher, 38 anos, com litíase vesicular sintomática recorrente, evolui com dor abdominal súbita e intensa no abdome superior.',
        'findings': [
            'Hipersensibilidade marcada no hemiabdome superior',
            'Ruídos hidroaéreos intensamente diminuídos',
            'Evolução rápida do quadro doloroso',
        ],
        'reasoning': 'Dor alta, íleo reflexo e antecedente biliar colocam pancreatite aguda litiásica no centro da hipótese — sem transformar um achado isolado em diagnóstico.',
        'diagnosis': 'Pancreatite biliar intersticial edematosa',
        'clinical_pearl': 'Cullen e Grey-Turner ausentes: a forma intersticial leve não sugere hemorragia retroperitoneal extensa.',
        'footnote': 'Caso clínico 09 · dados clínicos imutáveis do material de origem.',
    },
    {
        'module': 'fixed_schema_card',
        'kicker': 'Avaliação inicial',
        'title': 'Quatro dados fecham a orientação diagnóstica',
        'fields': [
            {'label': 'Radiografia', 'value': 'Sem pneumoperitônio; edema reflexo e distensão de alças contíguas.'},
            {'label': 'Tomografia', 'value': 'Hipodensidade pancreática difusa e coleções líquidas peripancreáticas.'},
            {'label': 'Bioquímica', 'value': 'Lipase sérica acima de três vezes o limite superior da normalidade.'},
            {'label': 'Síntese', 'value': 'Principal: pancreatite biliar. Diferenciais: úlcera perfurada, colecistite, isquemia mesentérica e obstrução alta.'},
        ],
        'footnote': 'A combinação de quadro típico, lipase elevada e imagem compatível sustenta a hipótese principal.',
    },
    {
        'module': 'definition',
        'kicker': 'Mecanismo',
        'title': 'O cálculo migra; o pâncreas responde',
        'main_statement': 'A obstrução transitória na ampola de Vater aumenta a pressão ductal e aproxima os zimógenos do gatilho da autodigestão.',
        'elaboration': 'Microcálculos chegam ao colédoco e podem impactar a ampola de Vater, retendo o suco pancreático rico em zimógenos.',
        'key_points': [
            {'title': 'Canal comum', 'desc': 'A teoria de Opie conecta o cálculo biliar à obstrução transitória do fluxo pancreático.'},
            {'title': 'Imagem de apoio', 'desc': 'A anatomia abaixo visualiza o ponto de impacto; o diagnóstico continua dependente do quadro clínico e da bioquímica.'},
        ],
        'image': 'study-deck/assets/ai_obstrucao_biliar.png',
        'caption': 'O ponto de impacto biliar explica a hipertensão ductal que antecede a ativação enzimática.',
        'credit': 'Apoio visual gerado por IA; revisão anatômica pela equipe.',
    },
    {
        'module': 'flow_diagram',
        'kicker': 'Cascata inflamatória',
        'title': 'Da célula acinar ao terceiro espaço',
        'steps': [
            {'label': '01', 'title': 'Colocalização', 'desc': 'Grânulos de zimógeno se fundem a vesículas lisossomais na célula acinar.'},
            {'label': '02', 'title': 'Tripsina ativa', 'desc': 'A catepsina B converte tripsinogênio em tripsina antes do momento correto.', 'highlight': True},
            {'label': '03', 'title': 'Autodigestão', 'desc': 'Elastase lesa vasos; fosfolipase A2 rompe membranas; lipase promove esteatonecrose.'},
            {'label': '04', 'title': 'SIRS e edema', 'desc': 'TNF-alfa, IL-1, IL-6 e histamina elevam a permeabilidade e sequestram volume.'},
        ],
        'explanation': 'A sobrecarga sustentada de cálcio citosólico reduz ATP, favorece a necrose acinar e mantém a ativação patológica de tripsina.',
        'footnote': 'A lesão local pode se tornar sistêmica quando a permeabilidade capilar e o terceiro espaço superam a reserva circulatória.',
    },
    {
        'module': 'figure',
        'kicker': 'Morfologia macroscópica',
        'title': 'A peça traduz a forma edematosa',
        'image': 'placeholder:macroscopia oficial do Caso 09 · inserir imagem do PPTX original',
        'caption': 'Tumefação glandular e focos de saponificação mostram a ação enzimática sobre a gordura peripancreática.',
        'credit': 'Fonte reservada: fotografia macroscópica oficial do Caso 09, PPTX original.',
    },
    {
        'module': 'figure',
        'kicker': 'Microscopia · H&E',
        'title': 'A lâmina confirma a inflamação intersticial',
        'image': 'placeholder:microfotografia H&E oficial do Caso 09 · inserir imagem do PPTX original',
        'caption': 'Adipócitos anucleados, sabões de cálcio, neutrófilos e edema interacinar conectam a lâmina à fisiopatologia.',
        'credit': 'Fonte reservada: microfotografia H&E oficial do Caso 09, PPTX original.',
    },
    {
        'module': 'comparison_table',
        'kicker': 'Correlação por imagem',
        'title': 'A imagem qualifica a inflamação e a causa',
        'headers': ['Método', 'Achado-chave', 'Leitura clínica'],
        'col_widths': [1.0, 1.35, 1.15],
        'rows': [
            ['Radiografia', 'Sem ar livre; edema reflexo e alça sentinela.', 'Reduz a probabilidade de perfuração.'],
            ['TC', 'Pâncreas aumentado, bordas imprecisas e líquido peripancreático.', 'Balthazar C/D, sem necrose: processo leve a moderado.'],
            ['Ultrassom', 'Cálculos e sinais de litíase vesicular.', 'Sustenta a etiologia biliar e orienta prevenção.'],
        ],
        'takeaway': 'A TC entre 72 e 96 horas é mais útil para mapear necrose; a gravidade clínica deve ser reavaliada continuamente.',
    },
    {
        'module': 'checklist',
        'kicker': 'Fase aguda',
        'title': 'Manejo inicial: metas antes de excessos',
        'items': [
            {'label': 'Hidratar com meta', 'desc': 'Ringer Lactato IV, inicialmente 250–500 mL/h; acompanhar hematócrito e diurese acima de 0,5 mL/kg/h.'},
            {'label': 'Descomprimir se necessário', 'desc': 'Sonda nasogástrica em vômitos incoercíveis, íleo paralítico ou gastroparesia.'},
            {'label': 'Tratar a dor', 'desc': 'Dipirona ou AINE em fase inicial; tramadol como resgate conforme resposta e segurança.'},
            {'label': 'Não prescrever profilaxia', 'desc': 'Antibiótico não é rotina na forma edematosa nem na necrose estéril; investigar colangite ou infecção.'},
            {'label': 'Realimentar cedo', 'desc': 'Após melhora da dor e do trânsito, iniciar tolerância oral com dieta hipograxa.'},
        ],
        'footnote': 'A conduta é guiada por resposta clínica; evitar jejum prolongado e intervenções sem indicação.',
    },
    {
        'module': 'timeline',
        'kicker': 'Depois da alta',
        'title': 'Prevenir a recidiva é parte do tratamento',
        'milestones': [
            {'label': 'Fase aguda', 'title': 'Estabilizar e reavaliar', 'desc': 'Dor, perfusão, diurese, hematócrito e sinais de complicação orientam a evolução.'},
            {'label': 'Mesmo internamento', 'title': 'Resolver a causa', 'desc': 'Colecistectomia laparoscópica precoce, após a resolução do processo inflamatório, reduz recorrência.'},
            {'label': 'APS e seguimento', 'title': 'Vigiar e educar', 'desc': 'Controlar peso e dieta; conferir cirurgia e investigar dor recorrente ou pseudoquisto.'},
        ],
        'footnote': 'A APS também identifica cólica biliar e litíase sintomática antes de um novo episódio grave.',
    },
    {
        'module': 'references',
        'kicker': 'Base bibliográfica',
        'title': 'Referências essenciais',
        'refs': [
            '1. Brunicardi FC et al. Schwartz: Princípios de Cirurgia. 11. ed. McGraw-Hill; 2020.',
            '2. Kumar V, Abbas AK, Aster JC. Robbins e Cotran: Patologia — Bases Patológicas das Doenças. 10. ed. Elsevier; 2021.',
            '3. Brunton LL, Hilal-Dandan R, Knollmann BC. Goodman e Gilman: As Bases Farmacológicas da Terapêutica. 13. ed. McGraw-Hill; 2019.',
            '4. Argente HA, Álvarez ME. Semiologia Médica: Fisiopatologia, Semiotecnia e Propedêutica. 3. ed. Médica Panamericana; 2021.',
            '5. Tenner S et al. American College of Gastroenterology Guideline: Management of Acute Pancreatitis. Am J Gastroenterol. 2024;119(3):419–437.',
        ],
        'footnote': 'Versão de trabalho para apresentação integrada · revisar a paginação conforme a edição consultada.',
    },
]
