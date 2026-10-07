# -*- coding: utf-8 -*-
"""Manifest StudyDeck v2 para el Seminario Integrador UCP, Caso Clínico 09.

Las fuentes clínicas originales y el PPTX con las dos imágenes oficiales no
están presentes en el kit recibido. Los campos del caso y la iconografía quedan
marcados para completar; no se fabrican hallazgos ni nombres.
"""

COURSE_INFO = {
    'course': 'Seminario Integrador · 5.º Semestre · Sección E',
    'institution': 'Universidad Central del Paraguay',
    'author': '',
}

CONFIG = {
    'PALETTE': 'ucp',
    'LANG': 'es-ES',
    'PROFILE': 'lecture',
    'IMAGES': {
        'mode': 'mixed',
        'max_n': 2,
        'allow_ai': False,
        'allow_placeholder': True,
    },
    'SHOW_FOOTER': True,
    'SHOW_SLIDE_NUMBER': True,
    # StudyDeck v2 fija Montserrat en toda la presentación.
    'ALLOW_TERMS': [
        'Opie', 'Atlanta', 'Balthazar', 'Cullen', 'Grey Turner', 'PONCHO',
        'WATERFALL', 'H&E', 'Na+/K+-ATPasa', 'Ca²+', 'TNF-α', 'IL-1', 'IL-6',
        'NF-κB', 'DAMP', 'CPRE', 'functio laesa', 'LSN',
    ],
}

SLIDES = [
    # 1. Carátula institucional común: sin cátedras individuales.
    {
        'module': 'title',
        'course': 'Seminario Integrador · Medicina',
        'title': 'Caso 09: dolor abdominal y lesión pancreática',
        'subtitle': '5.º Semestre · Sección E',
        'institution': 'Universidad Central del Paraguay',
    },

    # 2. Nómina editable; nombres no incluidos en la fuente disponible.
    {
        'module': 'fixed_schema_card',
        'kicker': 'Equipo y responsabilidades',
        'title': 'Una defensa común, cuatro tramos',
        'fields': [
            {'label': 'Relator 1',
             'value': 'Apertura, historia y juicio diagnóstico · diapositivas 1–4 · [Nombre y apellido]'},
            {'label': 'Relator 2',
             'value': 'Etiopatogenia y respuesta celular · diapositivas 5–8 · [Nombre y apellido]'},
            {'label': 'Relator 3',
             'value': 'Morfología e imagen · diapositivas 9–13 · [Nombre y apellido]'},
            {'label': 'Relator 4',
             'value': 'Soporte, prevención, seguimiento y fuentes · diapositivas 14–18 · [Nombre y apellido]'},
            {'label': 'Sustentación',
             'value': 'Equipo completo: banco común de respuestas; confirmar vocería y cronómetro.'},
        ],
        'footnote': 'Completar nombres y validar el reparto con el cronograma docente.',
    },

    # 3. Historia clínica: contenido individualizado pendiente de las fuentes del caso.
    {
        'module': 'case_block',
        'kicker': 'Ingreso y secuencia temporal',
        'title': 'El dolor ordena la anamnesis',
        'case_stem': 'Datos individualizados pendientes: la ficha clínica, la planificación y el PPTX original no venían en el archivo recibido.',
        'findings': [
            'Inicio, sitio, carácter, intensidad y duración del dolor.',
            'Irradiación dorsal, postura, ingesta, náuseas y vómitos.',
            'Antecedentes biliares, fármacos, alcohol y comorbilidad.',
            'Signos vitales, examen abdominal, laboratorio e imagen.',
        ],
        'reasoning': 'Completar edad, sexo, motivo, cronología y antecedentes; registrar hallazgos verificables antes de interpretarlos.',
        'diagnosis': 'Transcripción pendiente',
        'clinical_pearl': 'Dato no consignado no equivale a signo ausente. Anotar valores, unidades, hora y fuente de cada hallazgo.',
        'footnote': 'Sustituir los campos pendientes con el Caso 09 antes de la defensa.',
    },

    # 4. Atlanta, gravedad y diferenciales de urgencia.
    {
        'module': 'fixed_schema_card',
        'kicker': 'Decisión en urgencias',
        'title': 'Dos de tres criterios sostienen el diagnóstico',
        'fields': [
            {'label': 'Atlanta · diagnóstico',
             'value': '≥2/3: dolor típico; lipasa o amilasa ≥3× LSN; imagen característica.'},
            {'label': 'Gravedad clínica',
             'value': 'Leve: sin fallo orgánico ni complicaciones. Moderada: fallo transitorio ≤48 h o complicación; grave: fallo persistente >48 h.'},
            {'label': 'Diferenciales',
             'value': 'Colecistitis/colangitis; perforación péptica; isquemia mesentérica; obstrucción; infarto inferior.'},
            {'label': 'Verificación',
             'value': 'Etiología biliar requiere evidencia. Solicitar ecografía inicial; no usar TC precoz para graduar gravedad.'},
        ],
        'footnote': 'Documentar en la ficha cuáles criterios están presentes y cuáles aún faltan.',
    },

    # 5. Teoría de Opie: mecanismo posible, no afirmación universal.
    {
        'module': 'flow_diagram',
        'kicker': 'Obstrucción y etiología biliar',
        'title': 'La teoría de Opie vincula obstrucción y lesión acinar',
        'steps': [
            {'label': '01', 'title': 'Migración',
             'desc': 'La litiasis vesicular alcanza el colédoco distal.'},
            {'label': '02', 'title': 'Impactación',
             'desc': 'La obstrucción ampular transitoria dificulta el drenaje pancreático.',
             'highlight': True},
            {'label': '03', 'title': 'Estasis o reflujo',
             'desc': 'La presión ductal y el posible reflujo biliar contribuyen al estrés acinar; la anatomía varía.'},
            {'label': '04', 'title': 'Lesión pancreática',
             'desc': 'La lesión activa enzimas e inflamación local; confirmar la etiología con los datos del caso.'},
        ],
        'explanation': 'La migración e impactación transitoria de un cálculo puede obstruir la ampolla y elevar la presión ductal. El reflujo biliar se propone en la anatomía de canal común; no es un mecanismo demostrado en todos los casos.',
        'footnote': 'Opie describe una hipótesis histórica; correlacionar con ecografía, perfil hepático y evolución.',
    },

    # 6. Daño reversible frente a irreversible.
    {
        'module': 'side_by_side',
        'kicker': 'Umbral de daño celular',
        'title': 'La tumefacción puede revertir; la ruptura de membrana no',
        'left_card': {
            'header': 'LESIÓN REVERSIBLE',
            'title': 'Edema hidrópico',
            'points': [
                'Falla Na⁺/K⁺-ATPasa → retención de Na⁺ y agua.',
                'La célula se hincha; la membrana conserva integridad.',
                'Restablecer energía y perfusión puede devolver homeostasis.',
            ],
        },
        'right_card': {
            'header': 'LESIÓN IRREVERSIBLE',
            'title': 'Sobrecarga de Ca²⁺',
            'points': [
                'Ca²⁺ citosólico sostenido abre el poro mitocondrial de transición.',
                'Cae el ATP; aumentan disfunción de membranas y estrés celular.',
                'La ruptura de membranas favorece necrosis y libera señales de daño.',
            ],
        },
        'footnote': 'La progresión integra lesión mitocondrial, activación enzimática y respuesta inflamatoria.',
    },

    # 7. Colocalización acinar y mediadores.
    {
        'module': 'flow_diagram',
        'kicker': 'Lesión acinar y mediadores',
        'title': 'La activación precoz amplifica el daño local y sistémico',
        'steps': [
            {'label': '01', 'title': 'Estímulo',
             'desc': 'Ca²⁺ sostenido, estrés del retículo y tráfico acinar alterado.'},
            {'label': '02', 'title': 'Colocalización',
             'desc': 'Lisosoma y gránulo de zimógeno coinciden; catepsina B contacta tripsinógeno.',
             'highlight': True},
            {'label': '03', 'title': 'Proteasas',
             'desc': 'La tripsina activa otras proenzimas; elastasa y lipasa amplían la lesión.'},
            {'label': '04', 'title': 'Mediadores',
             'desc': 'Histamina actúa rápido; TNF-α, IL-1/IL-6 y eicosanoides amplifican inflamación.'},
        ],
        'explanation': 'La catepsina B puede activar tripsinógeno dentro de compartimentos colocalizados. La señal inflamatoria avanza en paralelo: citocinas, histamina y eicosanoides reclutan células y aumentan permeabilidad; la tripsina no explica por sí sola la respuesta sistémica.',
        'footnote': 'Histamina: vasoactiva · citocinas: respuesta sistémica · prostaglandinas/leucotrienos: eicosanoides.',
    },

    # 8. Semiología: dolor, motilidad y hallazgos negativos.
    {
        'module': 'fixed_schema_card',
        'kicker': 'Traducción al examen clínico',
        'title': 'El plexo explica la irradiación; los signos cutáneos no descartan',
        'fields': [
            {'label': 'Dolor visceral',
             'value': 'Aferencias por plexo celíaco/esplácnicos con entrada torácica T5–T9; la convergencia puede referir dolor al dorso.'},
            {'label': 'Celso / Galeno',
             'value': 'Tétrada: rubor, calor, tumor, dolor. Péntada: añade functio laesa (pérdida de función).'},
            {'label': 'Íleo paralítico',
             'value': 'Inflamación retroperitoneal → reflejo inhibidor; simpático reduce motilidad y parasimpático la facilita. Mecanismo multifactorial.'},
            {'label': 'Cullen',
             'value': 'Equimosis periumbilical, infrecuente y tardía; su ausencia no excluye pancreatitis hemorrágica.'},
            {'label': 'Grey Turner',
             'value': 'Equimosis de flancos, infrecuente y tardía; su ausencia no excluye sangrado retroperitoneal.'},
        ],
        'footnote': 'Estos signos no integran Atlanta ni estiman por sí solos la gravedad; consignar el momento del examen.',
    },

    # 9. Imagen macroscópica oficial obligatoria: marcador que debe sustituirse.
    {
        'module': 'figure',
        'kicker': 'Pieza macroscópica',
        'title': 'La saponificación dibuja gotas cerosas',
        'image': 'placeholder:Pieza MACRO oficial | páncreas con esteatonecrosis en gotas de cera',
        'caption': 'La lipasa libera ácidos grasos; con Ca²⁺ forman jabones insolubles visibles como focos blancos cerosos.',
        'credit': 'PPTX original Caso Clínico 09; imagen oficial ausente en el material recibido.',
        'footnote': 'Reemplazar el marcador por la fotografía macroscópica original; no usar ilustración generada.',
    },

    # 10. Microfotografía oficial H&E obligatoria: marcador que debe sustituirse.
    {
        'module': 'figure',
        'kicker': 'Microfotografía oficial H&E',
        'title': 'El calcio marca los adipocitos lesionados',
        'image': 'placeholder:Microfotografía H&E oficial | saponificación pancreática',
        'caption': 'H&E: adipocitos necróticos y depósitos basófilos de calcio; correlacionar con acinos y vasos.',
        'credit': 'PPTX original Caso Clínico 09; imagen oficial ausente en el material recibido.',
        'footnote': 'Reemplazar por la microfotografía H&E original; conservar aumento, tinción y crédito docente.',
    },

    # 11. Diferencial morfológico y rol vascular de la elastasa.
    {
        'module': 'side_by_side',
        'kicker': 'Correlación morfológica',
        'title': 'Edema intersticial y necrosis no son el mismo patrón',
        'left_card': {
            'header': 'INTERSTICIAL EDEMATOSA',
            'title': 'Realce conservado',
            'points': [
                'Edema intersticial y aumento de tamaño glandular.',
                'Inflamación aguda con parénquima viable y realce conservado.',
                'La morfología no sustituye la evaluación clínica del fallo orgánico.',
            ],
        },
        'right_card': {
            'header': 'NECROHEMORRÁGICA',
            'title': 'Daño parenquimatoso y vascular',
            'points': [
                'Puede haber necrosis acinar, hemorragia y saponificación peripancreática.',
                'Elastasa degrada pared vascular y puede favorecer hemorragia.',
                'La TC contrastada muestra áreas sin realce si se realiza a tiempo.',
            ],
        },
        'footnote': 'La morfología (intersticial o necrotizante) y la gravedad clínica se informan por separado.',
    },

    # 12. Ventanas de imagen y Balthazar.
    {
        'module': 'flow_diagram',
        'kicker': 'Selección de estudio',
        'title': 'Cada ventana responde una pregunta distinta',
        'steps': [
            {'label': 'AIRE', 'title': 'Radiografía simple',
             'desc': 'Considerar ante neumoperitoneo o íleo; no confirma pancreatitis.'},
            {'label': 'LITIASIS', 'title': 'Ecografía',
             'desc': 'Busca cálculos, barro, dilatación biliar y colecciones accesibles.'},
            {'label': 'PARÉNQUIMA', 'title': 'TC contrastada',
             'desc': 'Evalúa perfusión, necrosis y complicaciones; la TC precoz puede subestimarlas.',
             'highlight': True},
            {'label': 'BALTAZAR', 'title': 'Índice tomográfico',
             'desc': 'Grado A–E (0–4) + necrosis (0/2/4/6) = 0–10; no sustituye Atlanta.'},
        ],
        'explanation': 'La TC con contraste no se indica de rutina al ingreso. Reservarla para incertidumbre, deterioro o falta de mejoría; para valorar necrosis, esperar al menos 48–72 h y, a menudo, 72–96 h desde el inicio, según evolución.',
        'footnote': 'CTSI = grado A–E (0–4) + necrosis (0; <30%=2; 30–50%=4; >50%=6) = 0–10. No sustituye Atlanta.',
    },

    # 13. Ecografía biliar: hallazgos y preparación.
    {
        'module': 'comparison_table',
        'kicker': 'Semiótica ecográfica',
        'title': 'La ecografía distingue cálculos de imitadores',
        'headers': ['Hallazgo', 'Ecogenicidad y movilidad', 'Sombra posterior / clave'],
        'col_widths': [1.2, 2.3, 1.8],
        'rows': [
            ['Bilis normal', 'Anecoica; vesícula distendida.', 'Contenido sin ecos internos.'],
            ['Cálculo', 'Hiperecogénico; suele moverse con el decúbito.', 'Sombra acústica posterior: favorece litiasis.'],
            ['Barro biliar', 'Ecos de bajo nivel, dependientes; se desplaza o estratifica.', 'Habitualmente sin sombra; diferenciar de pólipo.'],
            ['Pólipo', 'Lesión mural fija; no cambia de posición.', 'Sin sombra posterior; correlacionar con pared y Doppler.'],
        ],
        'takeaway': 'Ayuno de 6–8 h; registrar cortes longitudinal (sagital) y transversal (axial), posición y sombra acústica.',
        'footnote': 'La nomenclatura de planos varía entre protocolos; documentar orientación y decúbito.',
    },

    # 14. Tratamiento hospitalario: evidencia y correcciones de seguridad.
    {
        'module': 'checklist',
        'kicker': 'Soporte agudo',
        'title': 'Tratar la fisiología, no perseguir profilaxis antibiótica',
        'items': [
            {'label': 'Ringer lactato frente a salina',
             'desc': 'Preferir cristaloide isotónico balanceado; reanimación moderada, guiada por perfusión, diuresis y sobrecarga.'},
            {'label': 'Acidosis y activación enzimática',
             'desc': 'La carga alta de Cl⁻ puede causar acidosis hiperclorémica; el efecto del pH sobre zimógenos es experimental, no causalidad clínica probada.'},
            {'label': 'Analgesia titulada',
             'desc': 'Morfina no está contraindicada por espasmo de Oddi; vigilar sedación, función renal e íleo.'},
            {'label': 'Antimicrobianos',
             'desc': 'No indicar profilaxis en pancreatitis ni necrosis estéril; tratar infección documentada o clínicamente sospechada.'},
            {'label': 'Nutrición y CPRE',
             'desc': 'Alimentación oral temprana si se tolera. CPRE ante colangitis u obstrucción persistente, no de rutina sin colangitis.'},
        ],
        'footnote': 'ACG 2024: hidratación moderada individualizada, analgesia, nutrición temprana y antibióticos solo ante infección.',
    },

    # 15. APS, litogénesis y prevención secundaria.
    {
        'module': 'stat_card',
        'kicker': 'Prevención de nueva lesión biliar',
        'title': 'La colecistectomía oportuna cierra el ciclo causal',
        'stat_num': '17% / 5%',
        'stat_title': 'Evento biliar compuesto: cirugía diferida frente a la misma hospitalización (PONCHO; 6 meses)',
        'narrative_blocks': [
            {'title': 'Atención primaria',
             'desc': 'Investigar cólico biliar recurrente, litiasis o barro; solicitar ecografía ante sospecha y coordinar derivación.'},
            {'title': 'Pancreatitis leve',
             'desc': 'Si es de origen biliar y el paciente es apto, colecistectomía laparoscópica en el mismo ingreso, antes del alta.'},
            {'title': 'Evitar la cifra no validada',
             'desc': 'No afirmar 30% en 3 meses sin fuente primaria. PONCHO informó 17% vs 5% de eventos compuestos con estrategia diferida vs misma admisión.'},
        ],
        'footnote': 'Necrosis, colecciones o gravedad mayor: individualizar y diferir la cirugía hasta estabilidad clínica.',
    },

    # 16. Seguimiento dirigido, no imagen de pesquisa rutinaria.
    {
        'module': 'timeline',
        'kicker': 'Salida y reparación',
        'title': 'El seguimiento busca síntomas persistentes, no una imagen automática',
        'milestones': [
            {'label': 'Alta', 'title': 'Recuperación inicial',
             'desc': 'Confirmar analgesia, tolerancia oral, control clínico y plan biliar.'},
            {'label': '4–6 semanas', 'title': 'Revisión dirigida',
             'desc': 'Valorar dolor, fiebre, saciedad precoz e intolerancia oral persistentes.'},
            {'label': '>4 semanas', 'title': 'Colección encapsulada',
             'desc': 'Pseudoquiste tras pancreatitis intersticial; necrosis encapsulada si hay detritos.'},
            {'label': 'Signos de alarma', 'title': 'Reevaluar',
             'desc': 'Fiebre, ictericia, dolor o vómitos persistentes exigen nueva valoración.'},
        ],
        'footnote': 'Control a 4–6 semanas si hay síntomas o complicaciones; no indicar TC rutinaria en asintomáticos recuperados.',
    },

    # 17. Bibliografía Vancouver numerada 1–6 por el módulo.
    {
        'module': 'references',
        'kicker': 'Fuentes · diagnóstico, mecanismos y manejo',
        'title': 'Fuentes que sustentan el diagnóstico y el manejo',
        'refs': [
            'Banks PA, et al. Gut. 2013;62:102–111. doi:10.1136/gutjnl-2012-302779.',
            'Tenner S, et al. Am J Gastroenterol. 2024;119:419–437. doi:10.14309/ajg.0000000000002645.',
            'Saluja A, et al. Gastroenterology. 2019;156:1979–1993. doi:10.1053/j.gastro.2019.01.268.',
            'de-Madaria E, et al. N Engl J Med. 2022;387:989–1000. doi:10.1056/NEJMoa2202884.',
            'da Costa DW, et al. Lancet. 2015;386:1261–1268. doi:10.1016/S0140-6736(15)00274-3.',
            'Expert Panel GI Imaging, et al. J Am Coll Radiol. 2019;16:S316–S330. doi:10.1016/j.jacr.2019.05.017.',
        ],
        'footnote': 'Citas completas y correspondencia con los contenidos: ver guion maestro.',
    },
    # 18. Continuación de la bibliografía: las etiquetas conservan la secuencia 7–12.
    {
        'module': 'further_reading',
        'kicker': 'Fuentes · anatomía, morfología e imagen',
        'title': 'Fuentes que sostienen la anatomía y la morfología',
        'entries': [
            {'tag': 'REF. 07', 'title': 'Balthazar EJ, et al. Radiology. 1990;174:331–336.', 'note': ''},
            {'tag': 'REF. 08', 'title': 'Kumar V, Abbas AK, Aster JC. Robbins & Cotran. 10.ª ed. Elsevier; 2020.', 'note': ''},
            {'tag': 'REF. 09', 'title': 'Murphy MC, et al. Insights Imaging. 2020;11:13.', 'note': ''},
            {'tag': 'REF. 10', 'title': 'Wright WF. J Am Osteopath Assoc. 2016;116:398–401.', 'note': ''},
            {'tag': 'REF. 11', 'title': 'Thompson DR. Am J Gastroenterol. 2001;96:1266–1272.', 'note': ''},
            {'tag': 'REF. 12', 'title': 'Moore KL, Dalley AF, Agur AMR. Clinically Oriented Anatomy. 9.ª ed. 2023.', 'note': ''},
        ],
        'footnote': 'DOI completos y créditos institucionales: ver guion maestro; añadir la planificación y el PPTX al recibirlos.',
    },
]
