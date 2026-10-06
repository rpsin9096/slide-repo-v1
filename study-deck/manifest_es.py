# -*- coding: utf-8 -*-
"""Deck en español — Caso Clínico 09: pancreatitis aguda biliar.

Esta versión es la entrega de presentación. Los dos marcadores ``placeholder:``
reservan las imágenes oficiales (macroscopia y H&E) que deben extraerse del
PPTX original. La ilustración local es apoyo visual generado por IA.
"""

COURSE_INFO = {
    'course': 'Seminario Integrador · S5 · Sección E',
    'institution': 'Universidad Central del Paraguay (UCP)',
    'author': 'Equipo de 10 integrantes',
}

CONFIG = {
    'PALETTE': 'ucp',
    'LANG': 'es-ES',
    'PROFILE': 'custom',
    'IMAGES': {
        'mode': 'mixed',
        'max_n': 'auto',
        'allow_ai': True,
        'allow_placeholder': True,
    },
    'SHOW_FOOTER': True,
    'SHOW_SLIDE_NUMBER': True,
    # "referencias" coincide con el vocabulario oficial de la versión fuente.
    'ALLOW_TERMS': ['referencias'],
}

SLIDES = [
    {
        'module': 'title',
        'course': 'Seminario Integrador · S5 · Sección E',
        'title': 'Caso clínico 09: pancreatitis aguda biliar',
        'subtitle': 'Abdomen agudo inflamatorio · presentación integrada del grupo',
        'institution': 'Universidad Central del Paraguay (UCP) · Carrera de Medicina',
        'author': 'Equipo de 10 integrantes',
    },
    {
        'module': 'side_by_side',
        'kicker': 'Organización del grupo',
        'title': 'Una defensa, diez frentes de preparación',
        'left_card': {
            'header': 'Relatoría · 4 integrantes',
            'title': 'La exposición en 10 minutos',
            'points': [
                '01 · Apertura: historia clínica e hipótesis',
                '02 · Mecanismo: obstrucción biliar y tripsina',
                '03 · Morfología e imagen: macro, H&E y TC',
                '04 · Manejo: fase aguda, prevención y referencias',
            ],
        },
        'right_card': {
            'header': 'Sustentación · 6 integrantes',
            'title': 'La banca encuentra seis respuestas clave',
            'points': [
                '05–06 · fármacos, dolor, íleo y signos semiológicos',
                '07–08 · zimógenos, citocinas, TC y ultrasonido',
                '09–10 · APS, prevención y lesiones histopatológicas',
            ],
        },
        'footnote': 'Los rótulos 01–10 siguen el plan de trabajo; sustituir por los nombres y matrículas oficiales antes de la carga.',
    },
    {
        'module': 'case_block',
        'kicker': 'Cuadro clínico',
        'title': 'La historia orienta el primer diagnóstico',
        'case_stem': 'Mujer de 38 años, con litiasis vesicular sintomática recurrente, evoluciona con dolor abdominal súbito e intenso en el abdomen superior.',
        'findings': [
            'Hipersensibilidad marcada en el hemiabdomen superior',
            'Ruidos hidroaéreos intensamente disminuidos',
            'Evolución rápida del cuadro doloroso',
        ],
        'reasoning': 'El dolor alto, el íleo reflejo y el antecedente biliar colocan a la pancreatitis aguda litiásica en el centro de la hipótesis, sin convertir un hallazgo aislado en diagnóstico.',
        'diagnosis': 'Pancreatitis biliar intersticial edematosa',
        'clinical_pearl': 'Cullen y Grey-Turner ausentes: la forma intersticial leve no sugiere hemorragia retroperitoneal extensa.',
        'footnote': 'Caso clínico 09 · datos clínicos inmutables del material de origen.',
    },
    {
        'module': 'fixed_schema_card',
        'kicker': 'Evaluación inicial',
        'title': 'Cuatro datos cierran la orientación diagnóstica',
        'fields': [
            {'label': 'Radiografía', 'value': 'Sin neumoperitoneo; edema reflejo y distensión de asas contiguas.'},
            {'label': 'Tomografía', 'value': 'Hipodensidad pancreática difusa y colecciones líquidas peripancreáticas.'},
            {'label': 'Bioquímica', 'value': 'Lipasa sérica por encima de tres veces el límite superior de la normalidad.'},
            {'label': 'Síntesis', 'value': 'Principal: pancreatitis biliar. Diferenciales: úlcera perforada, colecistitis, isquemia mesentérica y obstrucción alta.'},
        ],
        'footnote': 'La combinación de cuadro típico, lipasa elevada e imagen compatible sustenta la hipótesis principal.',
    },
    {
        'module': 'definition',
        'kicker': 'Mecanismo',
        'title': 'El cálculo migra; el páncreas responde',
        'main_statement': 'La obstrucción transitoria en la ampolla de Vater aumenta la presión ductal y acerca los zimógenos al desencadenante de la autodigestión.',
        'elaboration': 'Los microcálculos dejan la vesícula, recorren el colédoco y pueden impactarse en la ampolla; el jugo pancreático queda estancado.',
        'key_points': [
            {'title': 'Canal común', 'desc': 'La teoría de Opie conecta el cálculo biliar con la obstrucción transitoria del flujo pancreático.'},
            {'title': 'Imagen de apoyo', 'desc': 'La anatomía visualiza el punto de impacto; el diagnóstico sigue dependiendo del cuadro clínico y la bioquímica.'},
        ],
        'image': 'study-deck/assets/ai_obstrucao_biliar.png',
        'caption': 'El punto de impacto biliar explica la hipertensión ductal que precede a la activación enzimática.',
        'credit': 'Apoyo visual generado por IA; revisión anatómica del equipo.',
    },
    {
        'module': 'flow_diagram',
        'kicker': 'Cascada inflamatoria',
        'title': 'De la célula acinar al tercer espacio',
        'steps': [
            {'label': '01', 'title': 'Colocalización', 'desc': 'Los gránulos de zimógeno se fusionan con vesículas lisosomales en la célula acinar.'},
            {'label': '02', 'title': 'Tripsina activa', 'desc': 'La catepsina B convierte el tripsinógeno en tripsina antes del momento adecuado.', 'highlight': True},
            {'label': '03', 'title': 'Autodigestión', 'desc': 'La elastasa lesiona vasos; la fosfolipasa A2 rompe membranas; la lipasa causa esteatonecrosis.'},
            {'label': '04', 'title': 'SIRS y edema', 'desc': 'TNF-alfa, IL-1, IL-6 e histamina elevan la permeabilidad y secuestran volumen.'},
        ],
        'explanation': 'La sobrecarga sostenida de calcio citosólico reduce el ATP, favorece la necrosis acinar y mantiene la activación patológica de tripsina.',
        'footnote': 'La lesión local puede hacerse sistémica cuando la permeabilidad capilar y el tercer espacio superan la reserva circulatoria.',
    },
    {
        'module': 'figure',
        'kicker': 'Morfología macroscópica',
        'title': 'La pieza traduce la forma edematosa',
        'image': 'placeholder:macroscopia oficial del Caso 09 · insertar imagen del PPTX original',
        'caption': 'La tumefacción y la saponificación peripancreática muestran la acción enzimática sobre la grasa.',
        'credit': 'Fuente reservada: fotografía macroscópica oficial del Caso 09, PPTX original.',
    },
    {
        'module': 'figure',
        'kicker': 'Microscopía · H&E',
        'title': 'La lámina confirma la inflamación intersticial',
        'image': 'placeholder:microfotografía H&E oficial del Caso 09 · insertar imagen del PPTX original',
        'caption': 'La H&E muestra esteatonecrosis, calcio, neutrófilos y edema interacinar.',
        'credit': 'Fuente reservada: microfotografía H&E oficial del Caso 09, PPTX original.',
    },
    {
        'module': 'comparison_table',
        'kicker': 'Correlación por imagen',
        'title': 'La imagen califica la inflamación y la causa',
        'headers': ['Método', 'Hallazgo clave', 'Lectura clínica'],
        'col_widths': [1.0, 1.35, 1.15],
        'rows': [
            ['Radiografía', 'Sin aire libre; edema reflejo y asa centinela.', 'Reduce la probabilidad de perforación.'],
            ['TC', 'Páncreas aumentado, bordes imprecisos y líquido peripancreático.', 'Balthazar C/D, sin necrosis: proceso leve a moderado.'],
            ['Ultrasonido', 'Cálculos y signos de litiasis vesicular.', 'Sustenta la etiología biliar y orienta la prevención.'],
        ],
        'takeaway': 'La TC entre las 72 y 96 horas es más útil para mapear la necrosis; la gravedad clínica debe reevaluarse continuamente.',
    },
    {
        'module': 'checklist',
        'kicker': 'Fase aguda',
        'title': 'Manejo inicial: metas antes que excesos',
        'items': [
            {'label': 'Hidratar con objetivos', 'desc': 'Ringer Lactato IV, inicialmente 250–500 mL/h; controlar hematocrito y diuresis superior a 0,5 mL/kg/h.'},
            {'label': 'Descomprimir si es necesario', 'desc': 'Sonda nasogástrica ante vómitos incoercibles, íleo paralítico o gastroparesia.'},
            {'label': 'Tratar el dolor', 'desc': 'Dipirona o AINE en la fase inicial; tramadol como rescate según respuesta y seguridad.'},
            {'label': 'No indicar profilaxis', 'desc': 'El antibiótico no es rutinario en la forma edematosa ni en la necrosis estéril; investigar colangitis o infección.'},
            {'label': 'Realimentar pronto', 'desc': 'Tras la mejoría del dolor y del tránsito, iniciar tolerancia oral con dieta hipograsa.'},
        ],
        'footnote': 'La conducta se guía por la respuesta clínica; evitar el ayuno prolongado y las intervenciones sin indicación.',
    },
    {
        'module': 'timeline',
        'kicker': 'Después del alta',
        'title': 'Prevenir la recurrencia es parte del tratamiento',
        'milestones': [
            {'label': 'Fase aguda', 'title': 'Estabilizar y reevaluar', 'desc': 'Dolor, perfusión, diuresis, hematocrito y signos de complicación orientan la evolución.'},
            {'label': 'Misma internación', 'title': 'Resolver la causa', 'desc': 'Colecistectomía laparoscópica precoz, tras resolver la inflamación, reduce la recurrencia.'},
            {'label': 'APS y seguimiento', 'title': 'Vigilar y educar', 'desc': 'Controlar peso y dieta; confirmar la cirugía e investigar dolor recurrente o pseudoquiste.'},
        ],
        'footnote': 'La APS también identifica cólico biliar y litiasis sintomática antes de un nuevo episodio grave.',
    },
    {
        'module': 'references',
        'kicker': 'Base bibliográfica',
        'title': 'Referencias esenciales',
        'refs': [
            '1. Brunicardi FC, et al. Schwartz: Principios de Cirugía. 11.ª ed. McGraw-Hill; 2020.',
            '2. Kumar V, Abbas AK, Aster JC. Robbins y Cotran: Patología Estructural y Funcional. 10.ª ed. Elsevier; 2021.',
            '3. Brunton LL, Hilal-Dandan R, Knollmann BC. Goodman y Gilman: Las Bases Farmacológicas de la Terapéutica. 13.ª ed. McGraw-Hill; 2019.',
            '4. Argente HA, Álvarez ME. Semiología Médica: Fisiopatología, Semiotecnia y Propedéutica. 3.ª ed. Médica Panamericana; 2021.',
            '5. Tenner S, et al. American College of Gastroenterology Guideline: Management of Acute Pancreatitis. Am J Gastroenterol. 2024;119(3):419–437.',
        ],
        'footnote': 'Versión de trabajo para la presentación integrada · verificar la paginación según la edición consultada.',
    },
]
