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

    # 3. Historia clínica con datos literales de la transcripción aportada por el usuario.
    {
        'module': 'fixed_schema_card',
        'kicker': 'Historia clínica',
        'title': 'Historia clínica: mujer de 38 años con dolor abdominal agudo',
        'fields': [
            {'label': 'Antecedente', 'value': 'Enfermedad vesicular de larga evolución.'},
            {'label': 'Dolor y examen', 'value': 'Dolor medio, súbito e intenso; hipersensibilidad superior y ruidos intestinales reducidos.'},
            {'label': 'Radiografía', 'value': 'Sin aire libre; edema marcado de tejidos blandos.'},
            {'label': 'TC y lipasa', 'value': 'Menor atenuación y densidad líquida pancreática; lipasa elevada, sin valor informado.'},
            {'label': 'Manejo y evolución', 'value': 'Líquidos IV y sonda nasogástrica; recuperación gradual.'},
        ],
        'footnote': 'Relato transcrito; lipasa sin valor/LSN y TC sin informe completo. No añadir datos no consignados.',
    },

    # 4. Diagnóstico probable: distinguir criterios aportados de datos no cuantificados.
    {
        'module': 'fixed_schema_card',
        'kicker': 'Diagnóstico probable',
        'title': 'El cuadro es compatible con pancreatitis aguda de posible origen biliar',
        'fields': [
            {'label': 'Criterios de Atlanta', 'value': 'Dolor compatible + TC con alteración pancreática descrita; la imagen debe confirmarse como característica. Lipasa elevada, sin cuantificación.'},
            {'label': 'Diagnóstico', 'value': 'Pancreatitis aguda probable; dolor e imagen pueden aportar 2 de los 3 criterios diagnósticos.'},
            {'label': 'Etiología', 'value': 'Origen biliar posible por enfermedad vesicular de larga evolución; no confirmado sin ecografía o datos bioquímicos.'},
            {'label': 'Gravedad', 'value': 'Recuperación gradual; faltan datos para clasificar fallo orgánico y gravedad según Atlanta.'},
            {'label': 'Diagnósticos diferenciales', 'value': 'Perforación, obstrucción, colecistitis/colangitis y otras causas de abdomen agudo; Rx sin aire libre no excluye por sí sola perforación.'},
        ],
        'footnote': 'La lipasa no está expresada como múltiplo del límite superior normal (LSN).',
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

    # 6. Hallazgos clínicos y examen: consignar solo lo que consta en el caso.
    {
        'module': 'fixed_schema_card',
        'kicker': 'Manifestaciones y examen físico',
        'title': 'El examen muestra dolor superior y ruidos intestinales reducidos',
        'fields': [
            {'label': 'Dolor referido', 'value': 'Aferencias esplácnicas y plexo celíaco; la convergencia torácica T5–T9 puede referir dolor al dorso.'},
            {'label': 'Celso y Galeno', 'value': 'Tétrada de Celso: rubor, calor, tumor y dolor. Galeno añade functio laesa (pérdida de función).'},
            {'label': 'Ruidos intestinales', 'value': 'En el caso están reducidos; pueden acompañar íleo, pero este dato aislado no lo confirma.'},
            {'label': 'Cullen', 'value': 'Equimosis periumbilical tardía e infrecuente; el texto no informa si estaba presente.'},
            {'label': 'Grey Turner', 'value': 'Equimosis en flancos tardía e infrecuente; el texto no informa si estaba presente.'},
        ],
        'footnote': 'No se describen equimosis; dato no informado no equivale a examen negativo.',
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

    # 10. Radiografía, ecografía, TC y CTSI.
    {
        'module': 'flow_diagram',
        'kicker': 'Selección de estudios de imagen',
        'title': 'Cada modalidad responde una pregunta clínica diferente',
        'steps': [
            {'label': 'AIRE LIBRE', 'title': 'Radiografía simple',
             'desc': 'Caso 09: no se observó aire libre; se describió edema de tejidos blandos.'},
            {'label': 'LITIASIS', 'title': 'Ecografía',
             'desc': 'Busca cálculos y dilatación biliar; no se informa ecografía en el caso.'},
            {'label': 'PÁNCREAS', 'title': 'TC con contraste',
             'desc': 'Caso 09: menor atenuación y densidad líquida; falta el informe radiológico completo.',
             'highlight': True},
            {'label': 'CTSI', 'title': 'Índice de Balthazar',
             'desc': 'Puntaje morfológico 0–10; complementa y no reemplaza la gravedad de Atlanta.'},
        ],
        'explanation': 'La TC no se usa de rutina al ingreso para graduar gravedad. Si hay incertidumbre, deterioro o falta de mejoría, puede evaluar complicaciones; para necrosis suele ser más útil tras 48–72 h, según evolución.',
        'footnote': 'CTSI (índice de gravedad por TC): grado A–E (0–4) + necrosis (0; <30%=2; 30–50%=4; >50%=6) = 0–10.',
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

    # 13. APS, prevención secundaria y seguimiento dirigido.
    {
        'module': 'stat_card',
        'kicker': 'Prevención secundaria y APS',
        'title': 'La evaluación biliar y la cirugía oportuna reducen recurrencias',
        'stat_num': '17 % / 5 %',
        'stat_title': 'PONCHO: reingreso por complicación biliar o muerte; cirugía diferida vs mismo ingreso (6 meses).',
        'narrative_blocks': [
            {'title': 'Atención primaria',
             'desc': 'Investigar cólico biliar, litiasis y episodios previos; solicitar ecografía según sospecha y coordinar derivación.'},
            {'title': 'Colecistectomía',
             'desc': 'En pancreatitis biliar leve y paciente apto, realizar durante el mismo ingreso; necrosis/colecciones requieren individualizar y diferir.'},
            {'title': 'Control a 4–6 semanas',
             'desc': 'Revisar síntomas persistentes. Tras 4 semanas: pseudoquiste sin detritos; necrosis encapsulada si contiene detritos.'},
        ],
        'footnote': 'PONCHO: 17 % con cirugía diferida vs 5 % en el mismo ingreso. No afirmar «30 % en 3 meses» sin fuente.',
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
