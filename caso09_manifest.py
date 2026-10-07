# -*- coding: utf-8 -*-
"""StudyDeck v2: seminario del Caso Clínico 09, UCP.

El usuario aportó la transcripción de la historia clínica. El archivo con las
imágenes macro/H&E y la lista exacta de referencias no están accesibles; se
conservan marcadores claros y no se atribuyen hallazgos a imágenes no revisadas.
"""

COURSE_INFO = {
    'course': 'Seminario · Caso Clínico · 5.º Semestre · Sección E',
    'institution': 'Universidad Central del Paraguay · Centro Tecnológico I',
    'author': '',
}

CONFIG = {
    'PALETTE': 'ucp',
    'LANG': 'es-ES',
    'PROFILE': 'custom',
    'IMAGES': {
        'mode': 'mixed',
        'max_n': 2,
        'allow_ai': False,
        'allow_placeholder': True,
    },
    'SHOW_FOOTER': True,
    'SHOW_SLIDE_NUMBER': True,
    'ALLOW_TERMS': [
        'Opie', 'Atlanta', 'Balthazar', 'Cullen', 'Grey Turner', 'PONCHO',
        'H&E', 'Na+/K+-ATPasa', 'Ca²+', 'TNF-α', 'IL-1', 'IL-6', 'NF-κB',
        'DAMP', 'CPRE', 'LSN', 'CTSI', 'SNG', 'functio laesa',
    ],
}

SLIDES = [
    # 1. Portada con datos transcritos; los campos académicos no informados quedan editables.
    {
        'module': 'title',
        'course': 'Seminario · Caso Clínico',
        'title': 'Caso Clínico 09: pancreatitis aguda',
        'subtitle': 'Centro Tecnológico I · 5.º Semestre · Sección E',
        'institution': 'Universidad Central del Paraguay',
        'author': 'Docente: [Nombre] · Cátedra: [Nombre] · Unidad: [Nombre]',
    },

    # 2. Integrantes y campos académicos que la transcripción dejó en blanco.
    {
        'module': 'fixed_schema_card',
        'kicker': 'Equipo y datos académicos',
        'title': 'Integrantes y distribución de la exposición',
        'fields': [
            {'label': 'Docente', 'value': '[Nombre completo]'},
            {'label': 'Cátedra y unidad', 'value': '[Cátedra] · [Unidad]'},
            {'label': 'Integrantes', 'value': '[Nombre 1] · [Nombre 2] · [Nombre 3] · [Nombre 4]'},
            {'label': 'Relatoría', 'value': 'R1: apertura, caso y diagnóstico (1–4); R2: mecanismo y clínica (5–6); R3: patología e imagen (7–11); R4: tratamiento, APS y fuentes (12–14).'},
            {'label': 'Sustentación', 'value': 'Todos responden el banco común; confirmar nombres, vocería y cronómetro.'},
        ],
        'footnote': 'Tiempo sugerido: hasta 2:30 min por relator; ajustar el reparto al equipo real.',
    },

    # 3. Historia clínica: secuencia temporal con datos literales del relato.
    {
        'module': 'timeline',
        'kicker': 'Historia clínica',
        'title': 'Historia clínica: mujer de 38 años con dolor abdominal agudo',
        'milestones': [
            {'label': 'Antecedente', 'title': 'Enfermedad vesicular',
             'desc': 'Mujer de 38 años; enfermedad vesicular de larga evolución.'},
            {'label': 'Inicio', 'title': 'Dolor abdominal',
             'desc': 'Súbito, intenso y en abdomen medio.'},
            {'label': 'Examen', 'title': 'Hipersensibilidad',
             'desc': 'Marcada en abdomen superior; ruidos intestinales reducidos.'},
            {'label': 'Rx / TC', 'title': 'Edema marcado de tejidos blandos',
             'desc': 'Rx sin aire libre; TC: menor atenuación, densidad líquida pancreática.'},
            {'label': 'Manejo', 'title': 'Lipasa elevada; recuperación gradual',
             'desc': 'Recibió líquidos IV y sonda nasogástrica.'},
        ],
        'footnote': 'Lipasa sin valor/LSN; informe completo de TC no disponible. No inferir otros datos.',
    },

    # 4. Diagnóstico probable, presentado como pregunta de defensa oral.
    {
        'module': 'viva_question',
        'kicker': 'Diagnóstico probable',
        'title': 'El cuadro es compatible; la causa biliar no está confirmada',
        'prompt': '¿Qué datos permiten plantear el diagnóstico y cuáles siguen pendientes?',
        'model_answer': 'Atlanta exige 2 de 3 criterios: dolor compatible, enzimas ≥3 veces el límite superior normal o imagen característica. Aquí constan dolor y alteración pancreática descrita en TC; falta informe. Lipasa elevada, sin valor. Origen biliar posible, no confirmado.',
        'examiner_note': 'Verificar si la TC cumple criterio de imagen característica. No asignar gravedad sin datos de fallo orgánico persistente ni duración.',
        'difficulty': 'Intermedia',
        'footnote': 'Atlanta revisada [1]; el valor de lipasa y el informe radiológico completo no están disponibles.',
    },

    # 5. Etiología biliar y mecanismos celulares, sin atribuir cálculo confirmado al caso.
    {
        'module': 'flow_diagram',
        'kicker': 'Mecanismo etiológico propuesto',
        'title': 'Una posible obstrucción biliar puede iniciar la lesión pancreática',
        'steps': [
            {'label': 'ANTECEDENTE', 'title': 'Enfermedad vesicular',
             'desc': 'La historia prolongada del caso hace plausible, pero no confirma, origen biliar.'},
            {'label': 'OBSTRUCCIÓN', 'title': 'Impactación distal',
             'desc': 'Un cálculo ampular puede elevar presión ductal e impedir el drenaje.',
             'highlight': True},
            {'label': 'ACINO', 'title': 'Activación enzimática',
             'desc': 'Ca²⁺ sostenido y colocalización lisosoma-zimógeno favorecen activación de tripsinógeno.'},
            {'label': 'INFLAMACIÓN', 'title': 'Daño local y sistémico',
             'desc': 'Tripsina, lipasa y elastasa lesionan tejido; histamina y citocinas amplifican la respuesta.'},
        ],
        'explanation': 'La hipótesis de Opie propone obstrucción ampular y posible reflujo biliar en ciertas anatomías; el reflujo no es un requisito universal. En este caso no se aporta ecografía que documente un cálculo.',
        'footnote': 'TNF-α e IL-1/IL-6 son citocinas; la elastasa puede dañar vasos y la lipasa favorece necrosis grasa.',
    },

    # 6. Manifestaciones como mapa radial; diferencia hallazgos descritos de signos no informados.
    {
        'module': 'concept_map',
        'kicker': 'Manifestaciones y examen físico',
        'title': 'Los hallazgos orientan; los signos clásicos no descartan el cuadro',
        'hub': 'Manifestaciones clínicas',
        'nodes': [
            {'title': 'Dolor visceral', 'desc': 'Plexo celíaco/esplácnicos; posible referencia dorsal (T5–T9).'},
            {'title': 'Hallazgos del caso', 'desc': 'Hipersensibilidad superior y ruidos intestinales reducidos.'},
            {'title': 'Celso / Galeno', 'desc': 'Rubor, calor, tumor y dolor; Galeno añade pérdida de función.'},
            {'title': 'Signo de Cullen', 'desc': 'Equimosis periumbilical tardía e infrecuente; no informada.'},
            {'title': 'Signo de Grey Turner', 'desc': 'Equimosis de flancos, tardía e infrecuente; no informada.'},
        ],
        'footnote': 'Cullen y Grey Turner tienen baja sensibilidad; su ausencia no descarta pancreatitis [9].',
    },

    # 7. Imagen macro oficial exigida; no disponible para inspección en esta sesión.
    {
        'module': 'figure',
        'kicker': 'Correlación macroscópica',
        'title': 'Saponificación y necrosis grasa en la pieza pancreática',
        'image': 'placeholder:Fotografía macroscópica oficial del Caso 09 | páncreas y focos cerosos',
        'caption': 'La lipasa libera ácidos grasos que se unen al calcio (Ca²⁺) y forman jabones insolubles blancos.',
        'credit': 'Fotografía macro oficial del Caso 09; archivo visual no accesible.',
        'footnote': 'Insertar la foto original; rotular solo páncreas, grasa y focos visibles. No usar imagen generada.',
    },

    # 8. Imagen H&E oficial y diagnóstico anatomopatológico por verificar.
    {
        'module': 'figure',
        'kicker': 'Correlación microscópica',
        'title': 'Diagnóstico anatomopatológico: pendiente de revisar la imagen oficial',
        'image': 'placeholder:Microfotografía H&E oficial del Caso 09 | necrosis grasa/saponificación',
        'caption': 'H&E (hematoxilina-eosina): buscar adipocitos necróticos y depósitos basófilos solo si son visibles.',
        'credit': 'Microfotografía oficial H&E del Caso 09; archivo visual no accesible.',
        'footnote': 'No afirmar un diagnóstico histológico final sin revisar la microfotografía original.',
    },

    # 9. Patrones de pancreatitis: la morfología no sustituye gravedad clínica.
    {
        'module': 'side_by_side',
        'kicker': 'Patrones morfológicos',
        'title': 'La pancreatitis edematosa y la necrotizante tienen patrones distintos',
        'left_card': {
            'header': 'INTERSTICIAL EDEMATOSA',
            'title': 'Parénquima con realce conservado',
            'points': [
                'Edema intersticial con arquitectura pancreática conservada.',
                'No hay necrosis parenquimatosa en este patrón.',
                'La gravedad clínica requiere evaluar fallo orgánico y complicaciones.',
            ],
        },
        'right_card': {
            'header': 'NECROTIZANTE',
            'title': 'Daño parenquimatoso o peripancreático',
            'points': [
                'En TC contrastada oportuna puede verse tejido sin realce.',
                'La elastasa puede degradar la pared vascular y favorecer hemorragia.',
                'Puede coexistir necrosis grasa con saponificación.',
            ],
        },
        'footnote': 'Atlanta separa morfología (intersticial/necrotizante) de gravedad clínica (fallo orgánico/complicaciones).',
    },

    # 10. Algoritmo de selección de imagen por pregunta clínica.
    {
        'module': 'algorithm',
        'kicker': 'Selección de estudios de imagen',
        'title': 'Elegir el estudio de imagen según la pregunta clínica',
        'steps': [
            {'title': 'Radiografía simple',
             'desc': 'Ante sospecha de aire libre; en el caso no se observó, aunque se describió edema de tejidos blandos.'},
            {'title': 'Ecografía biliar',
             'desc': 'Buscar cálculos y dilatación de la vía biliar; no consta resultado en la transcripción.'},
            {'title': 'TC con contraste',
             'desc': 'Valorar parénquima y complicaciones ante incertidumbre o deterioro; no es rutinaria al ingreso. Falta el informe del caso.',
             'highlight': True},
            {'title': 'CTSI de Balthazar',
             'desc': 'CTSI: grado A–E (0–4) + necrosis (0 % = 0; <30 % = 2; 30–50 % = 4; >50 % = 6) = 0–10; complementa Atlanta.'},
        ],
        'footnote': 'No TC de rutina si asintomático. Necrosis más visible 48–72 h; >4 sem: pseudoquiste sin detritos; necrosis encapsulada con detritos [1,2].',
    },

    # 11. Hallazgos ecográficos para etiología biliar; el estudio no consta en el caso.
    {
        'module': 'comparison_table',
        'kicker': 'Ecografía de la vesícula biliar',
        'title': 'Cálculo, barro y pólipo se diferencian por movilidad y sombra',
        'headers': ['Hallazgo', 'Ecogenicidad y movilidad', 'Sombra posterior / clave'],
        'col_widths': [1.2, 2.3, 1.8],
        'rows': [
            ['Bilis normal', 'Anecoica; vesícula distendida.', 'Luz sin ecos internos.'],
            ['Cálculo', 'Hiperecogénico; suele moverse con el decúbito.', 'Sombra acústica posterior.'],
            ['Barro biliar', 'Ecos bajos dependientes; se desplaza o estratifica.', 'Habitualmente sin sombra limpia.'],
            ['Pólipo', 'Lesión mural fija; no cambia de posición.', 'Habitualmente sin sombra posterior.'],
        ],
        'takeaway': 'Ayuno 6–8 h; documentar planos longitudinal/sagital y transversal/axial, posición y sombra acústica.',
        'footnote': 'La historia menciona enfermedad vesicular; no se aporta ecografía que confirme cálculos.',
    },

    # 12. Manejo recibido y práctica farmacológica actual.
    {
        'module': 'checklist',
        'kicker': 'Tratamiento durante el episodio agudo',
        'title': 'Individualizar hidratación, analgesia, alimentación y antimicrobianos',
        'items': [
            {'label': 'Líquidos intravenosos',
             'desc': 'Caso 09: líquidos IV; solución y volumen no consignados. Preferir cristaloide balanceado y reevaluar perfusión y sobrecarga.'},
            {'label': 'Cloruro y acidosis',
             'desc': 'El exceso de cloruro (Cl⁻) puede causar acidosis hiperclorémica; el efecto del pH bajo sobre zimógenos es experimental.'},
            {'label': 'Analgesia',
             'desc': 'Morfina no está prohibida por una supuesta contraindicación absoluta; titular y vigilar sedación, función renal e íleo.'},
            {'label': 'Antibióticos',
             'desc': 'No indicar profilaxis para pancreatitis o necrosis estéril; tratar infección documentada o clínicamente sospechada.'},
            {'label': 'Sonda y nutrición',
             'desc': 'Caso 09: sonda nasogástrica. No es rutinaria si tolera vía oral; iniciar alimentación temprana según tolerancia.'},
        ],
        'footnote': 'CPRE = colangiopancreatografía retrógrada endoscópica; reservar para colangitis u obstrucción biliar persistente.',
    },

    # 13. Ensayo PONCHO en una tarjeta de evidencia PICO; límites de generalización explícitos.
    {
        'module': 'evidence_card',
        'kicker': 'Prevención secundaria y APS',
        'title': 'PONCHO: colecistectomía en el ingreso para pancreatitis biliar leve',
        'study_name': 'Ensayo PONCHO',
        'design': 'Ensayo multicéntrico aleatorizado',
        'population': 'Pacientes aptos con pancreatitis biliar leve.',
        'intervention': 'Colecistectomía durante la hospitalización inicial.',
        'comparison': 'Colecistectomía diferida tras el alta.',
        'outcome': 'Reingreso por complicaciones biliares o muerte a seis meses.',
        'effect': '17 % / 5 %',
        'effect_desc': 'Cirugía diferida vs durante el mismo ingreso; desenlace compuesto.',
        'limitation': 'No extrapolar a etiología no confirmada ni a necrosis/colecciones; en esos casos, individualizar la cirugía.',
        'year': '2015',
        'credit': 'da Costa DW, et al. Lancet. 2015;386:1261–1268. doi:10.1016/S0140-6736(15)00274-3.',
        'footnote': 'APS: confirmar etiología y derivar. Cirugía en ingreso si cuadro leve; diferir ante necrosis/colecciones. Control clínico a 4–6 semanas.',
    },

    # 14. Bibliografía complementaria seleccionada; debe contrastarse con las páginas originales.
    {
        'module': 'references',
        'kicker': 'Fuentes complementarias seleccionadas',
        'title': 'Fuentes para diagnóstico, mecanismos y manejo',
        'refs': [
            'Banks PA, et al. Gut. 2013;62:102–111. doi:10.1136/gutjnl-2012-302779.',
            'Tenner S, et al. Am J Gastroenterol. 2024;119:419–437. doi:10.14309/ajg.0000000000002645.',
            'Saluja A, et al. Gastroenterology. 2019;156:1979–1993. doi:10.1053/j.gastro.2019.01.268.',
            'da Costa DW, et al. Lancet. 2015;386:1261–1268. doi:10.1016/S0140-6736(15)00274-3.',
            'Moore KL, Dalley AF, Agur AMR. Clinically Oriented Anatomy. 9th ed. Wolters Kluwer; 2023.',
            'Balthazar EJ, et al. Radiology. 1990;174:331–336. doi:10.1148/radiology.174.2.2296641.',
            'Kumar V, Abbas AK, Aster JC. Robbins & Cotran. 10th ed. Elsevier; 2020.',
            'Murphy MC, et al. Insights Imaging. 2020;11:13. doi:10.1186/s13244-019-0825-4.',
            'Wright WF. J Am Osteopath Assoc. 2016;116:398–401. doi:10.7556/jaoa.2016.081.',
            'Thompson DR. Am J Gastroenterol. 2001;96:1266–1272. doi:10.1111/j.1572-0241.2001.03536.x.',
        ],
        'footnote': 'Bibliografía añadida para respaldar contenidos generales; sustituir o reducir según las fuentes verificadas del PDF original.',
    },
]
