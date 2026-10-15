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
    # 1. Carátula institucional: sin docente, cátedra ni unidad individual.
    {
        'module': 'title',
        'course': '',
        'title': 'Caso Clínico 09: pancreatitis aguda',
        'subtitle': '',
        'institution': 'Universidad Central del Paraguay · Centro Tecnológico I',
        'author': '',
    },

    # 2. Grupo 5: competencias en orden de la presentación; la vocería sigue pendiente.
    {
        'module': 'fixed_schema_card',
        'kicker': 'Equipo expositor · Grupo 5',
        'title': 'Grupo 5 · integrantes y competencias para el Caso 09',
        'fields': [
            {'label': '01 · Introducción',
             'value': 'Anielle Santos — Introducción y encuadre. Expositor/a: [por definir].\nRaul de Oliveira — Historia clínica y presentación del caso. Expositor/a: [por definir].'},
            {'label': '02 · Diagnóstico',
             'value': 'Gabrielly Frois — Diagnóstico anatomoclínico. Expositor/a: [por definir].\nCaroline Brunete — Fisiopatología y activación acinar. Expositor/a: [por definir].'},
            {'label': '03 · Clínica y macro',
             'value': 'Douglas do Amaral — Semiología y manifestaciones. Expositor/a: [por definir].\nRobinson dos Santos — Correlación macroscópica. Expositor/a: [por definir].'},
            {'label': '04 · H&E e imagen',
             'value': 'Breno Moura — H&E y patrones morfológicos. Expositor/a: [por definir].\nNathalia Borges — Imagenología y ecografía biliar. Expositor/a: [por definir].'},
            {'label': '05 · Manejo y cierre',
             'value': 'Mikaella Urgniani — Tratamiento inicial y farmacología. Expositor/a: [por definir].\nLiara Fenili — APS, PONCHO, prevención y cierre. Expositor/a: [por definir].'},
        ],
    },

    # 3. Historia clínica: secuencia temporal con datos literales del relato.
    {
        'module': 'timeline',
        'kicker': 'Historia clínica',
        'title': 'Historia clínica: mujer de 38 años con dolor abdominal agudo',
        'milestones': [
            {'label': 'Antecedente', 'title': 'Litiasis biliar',
             'desc': 'Mujer de 38 años; litiasis/enfermedad vesicular de larga evolución.'},
            {'label': 'Inicio', 'title': 'Dolor abdominal',
             'desc': 'Súbito, intenso y en abdomen medio.'},
            {'label': 'Examen', 'title': 'Hipersensibilidad',
             'desc': 'Marcada en abdomen superior; ruidos intestinales reducidos.'},
            {'label': 'Rx / TC', 'title': 'Edema marcado de tejidos blandos',
             'desc': 'Rx sin aire libre; TC: menor atenuación, densidad líquida pancreática.'},
            {'label': 'Manejo', 'title': 'Lipasa elevada; recuperación gradual',
             'desc': 'Recibió líquidos IV y sonda nasogástrica.'},
        ],
    },

    # 4. Diagnóstico anatomoclínico según los hallazgos y la corrección aportada.
    {
        'module': 'definition',
        'kicker': 'Diagnóstico anatomoclínico',
        'title': 'Diagnóstico anatomoclínico del Caso 09',
        'main_statement': 'Pancreatitis aguda edematosa intersticial de origen biliar.',
        'elaboration': 'La historia litiásica prolongada, el dolor agudo, la lipasa elevada, la TC pancreática y la esteatonecrosis macro con adipocitos anucleados en H&E convergen en el diagnóstico.',
        'key_points': [
            {'title': 'Clínica y enzimas',
             'desc': 'Dolor abdominal medio, súbito e intenso, con hipersensibilidad superior y lipasa sérica elevada.'},
            {'title': 'Imagen',
             'desc': 'La TC describe menor atenuación y densidad líquida en el páncreas.'},
            {'title': 'Morfología',
             'desc': 'Pieza: esteatonecrosis en gotas de vela; H&E: adipocitos anucleados.'},
        ],
    },

    # 5. Etiología biliar y mecanismos celulares, sin atribuir cálculo confirmado al caso.
    {
        'module': 'flow_diagram',
        'kicker': 'Mecanismo etiológico propuesto',
        'title': 'La litiasis biliar puede iniciar la lesión acinar pancreática',
        'steps': [
            {'label': 'ANTECEDENTE', 'title': 'Enfermedad vesicular',
             'desc': 'El Caso 09 presenta antecedentes litiásicos de larga data.'},
            {'label': 'OBSTRUCCIÓN', 'title': 'Impactación distal',
             'desc': 'Un cálculo ampular puede elevar presión ductal e impedir el drenaje.',
             'highlight': True},
            {'label': 'ACINO', 'title': 'Activación enzimática',
             'desc': 'Ca²⁺ sostenido y colocalización lisosoma-zimógeno acercan catepsina B y tripsinógeno; se activa tripsina.'},
            {'label': 'INFLAMACIÓN', 'title': 'Daño local y sistémico',
             'desc': 'Tripsina, lipasa y elastasa lesionan tejido; histamina y citocinas amplifican la respuesta.'},
        ],
        'explanation': 'La hipótesis de Opie propone obstrucción ampular y posible reflujo biliar en ciertas anatomías; el reflujo no es un requisito universal.',
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
            {'title': 'Íleo reflejo', 'desc': 'Ruidos reducidos pueden reflejar respuesta simpática; no confirman íleo.'},
            {'title': 'Celso / Galeno', 'desc': 'Rubor, calor, tumor y dolor; Galeno añade pérdida de función.'},
            {'title': 'Signo de Cullen', 'desc': 'Signo hemorrágico tardío e infrecuente; raro en la forma edematosa.'},
            {'title': 'Signo de Grey Turner', 'desc': 'Signo hemorrágico tardío e infrecuente; raro en la forma edematosa.'},
        ],
        'footnote': 'Cullen y Grey Turner son signos hemorrágicos tardíos e infrecuentes [9].',
    },

    # 7. Pieza macro oficial; el archivo debe insertarse desde Caso Clínico 09.pptx.
    {
        'module': 'figure',
        'kicker': 'Correlación macroscópica',
        'title': 'La pieza muestra esteatonecrosis en gotas de vela',
        'image': 'placeholder:Imagen macro oficial del Caso Clínico 09 · gotas de vela en grasa pancreática',
        'caption': 'Focos blanquecinos de esteatonecrosis y saponificación en la grasa peripancreática.',
        'credit': 'Caso Clínico 09.pptx, diapositiva 5.',
    },

    # 8. Microfotografía H&E oficial; el archivo debe insertarse desde el PPTX original.
    {
        'module': 'figure',
        'kicker': 'Correlación microscópica',
        'title': 'La microfotografía H&E muestra adipocitos anucleados',
        'image': 'placeholder:Imagen H&E oficial del Caso Clínico 09 · adipocitos anucleados',
        'caption': 'Adipocitos anucleados («células fantasma»), compatibles con esteatonecrosis pancreática.',
        'credit': 'Caso Clínico 09.pptx, diapositiva 6.',
    },

    # 9. Contraste morfológico: destacar el patrón intersticial del Caso 09.
    {
        'module': 'side_by_side',
        'kicker': 'Patrones morfológicos',
        'title': 'La forma edematosa intersticial y la necrotizante tienen patrones distintos',
        'left_card': {
            'header': 'EDEMATOSA INTERSTICIAL',
            'title': 'Patrón del Caso 09',
            'points': [
                'Edema intersticial con parénquima pancreático viable.',
                'La esteatonecrosis peripancreática puede verse como focos en gotas de vela.',
                'Cullen/Grey Turner: signos hemorrágicos infrecuentes en la forma edematosa; su no descripción no prueba examen negativo.',
            ],
        },
        'right_card': {
            'header': 'NECROTIZANTE',
            'title': 'Necrosis del páncreas o tejidos vecinos',
            'points': [
                'En TC contrastada oportuna puede verse tejido sin realce.',
                'La elastasa puede dañar la pared vascular y favorecer hemorragia.',
                'La necrosis grasa y la necrosis del parénquima son hallazgos distintos.',
            ],
        },
        'footnote': 'La morfología pancreática no reemplaza la clasificación clínica de gravedad de Atlanta.',
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
             'desc': 'Buscar cálculos y dilatación de la vía biliar.'},
            {'title': 'TC con contraste',
             'desc': 'Valorar parénquima y complicaciones ante incertidumbre o deterioro; no es rutinaria al ingreso.',
             'highlight': True},
            {'title': 'CTSI de Balthazar',
             'desc': 'CTSI: grado A–E (0–4) + necrosis (0 % = 0; <30 % = 2; 30–50 % = 4; >50 % = 6) = 0–10; complementa Atlanta.'},
        ],
        'footnote': 'TC selectiva; necrosis más visible a 48–72 h. >4 sem: pseudoquiste sin detritos; necrosis encapsulada con detritos [1,2].',
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
        'footnote': 'Ayuno 6–8 h; documentar planos longitudinal y transversal, posición y sombra acústica.',
    },

    # 12. Pauta docente de hidratación y analgesia; distinguirla del tratamiento efectivamente consignado.
    {
        'module': 'checklist',
        'kicker': 'Tratamiento durante el episodio agudo',
        'title': 'Ringer Lactato, dipirona y tramadol en el soporte inicial',
        'items': [
            {'label': 'Hidratación',
             'desc': 'Caso 09: líquidos IV; solución/volumen no consignados. Pauta de cátedra: Ringer Lactato y reevaluación de perfusión/sobrecarga.'},
            {'label': 'Racional del cristaloide',
             'desc': 'Menor carga de cloruro limita acidosis hiperclorémica; la relación entre pH bajo y activación de tripsina es mecanística.'},
            {'label': 'Analgesia según cátedra',
             'desc': 'Dipirona IV como base y tramadol de rescate. Se conserva la precaución clásica por posible espasmo del esfínter de Oddi con morfina.'},
            {'label': 'Antibióticos y nutrición',
             'desc': 'No usar profilaxis en necrosis estéril; iniciar alimentación oral/enteral según tolerancia.'},
            {'label': 'Sonda y CPRE',
             'desc': 'La sonda nasogástrica consta en el caso; CPRE ante colangitis u obstrucción biliar persistente.'},
        ],
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
        'limitation': 'Resultados aplicables a pancreatitis biliar leve; no extrapolar a necrosis/colecciones ni a un curso cuya gravedad no se ha clasificado.',
        'year': '2015',
        'credit': 'da Costa DW, et al. Lancet. 2015;386:1261–1268. doi:10.1016/S0140-6736(15)00274-3.',
        'footnote': 'APS: derivar; colecistectomía en ingreso si forma biliar leve; diferir ante necrosis/colecciones. Control a 4–6 sem.',
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
    },
]
