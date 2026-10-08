# -*- coding: utf-8 -*-
"""Presentación clínica guiada en español, autorada con StudyDeck v2.

Sigue SYSTEM_PROMPT.md y prompt.md (UCP-only), con perfil short, español,
contraste WCAG AA y dos ilustraciones originales generadas por IA.
Build desde la raíz del repositorio:
  studydeck all presentacion_caso4_prado_es.py presentacion_caso4_prado_es.pptx
"""

COURSE_INFO = {
    'course': 'Medicina familiar y comunitaria',
    'institution': 'Universidad Central del Paraguay (UCP)',
    'author': 'Dra. Rossana Gauto',
}

CONFIG = {
    'PALETTE': 'ucp',
    'LANG': 'es-ES',
    'PROFILE': 'short',
    'IMAGES': {
        # Archivos locales generados con IA; mixed permite incrustar sus píxeles.
        'mode': 'mixed',
        'max_n': 2,
        'allow_ai': True,
        'allow_placeholder': False,
    },
    'SHOW_FOOTER': True,
    'SHOW_SLIDE_NUMBER': True,
    'ALLOW_TERMS': [],
}

SLIDES = [
    {
        'module': 'title',
        'title': 'Trabajo 3: Casos clínicos de intervención en crisis familiar',
        'subtitle': 'Interpretación de los niveles de intervención · Caso 4: Sr. Prado · Dolor torácico',
        'course': 'Cátedra: Medicina Familiar · 3.er Año · 5.º Semestre · Unidad II',
        'institution': 'Universidad Central del Paraguay (UCP)',
        'author': 'Docente: Dra. Rossana Gauto · Nombre: ________ · Fecha: ___/___/____',
    },
    {
        'module': 'fixed_schema_card',
        'kicker': 'Competencias de la cátedra',
        'title': 'Objetivos de aprendizaje',
        'fields': [
            {
                'label': 'Conceptual',
                'value': 'Explicar el Nivel 4 como evaluación funcional e intervención planificada; distinguir la hipótesis sistémica del diagnóstico orgánico confirmado.',
            },
            {
                'label': 'Procedimental',
                'value': 'Formular hipótesis, convocar a la familia, observar pautas de interacción y acordar cambios verificables con seguimiento a 15 días.',
            },
            {
                'label': 'Actitudinal',
                'value': 'Escuchar sin culpabilizar, rechazar coaliciones y no tomar partido; mantener una posición clínica neutral ante los reproches.',
            },
            {
                'label': 'Evidencias',
                'value': 'Presentar el mapa de tensiones, cuatro acuerdos verificables, indicadores de seguimiento y criterios de derivación al Nivel 5.',
            },
        ],
        'footnote': 'Trabajo 3 · Caso 4 · Niveles de intervención en crisis familiar.',
    },
    {
        'module': 'fixed_schema_card',
        'kicker': 'Caso clínico · pregunta 1',
        'title': 'Sr. Prado, 42 años: síntoma y contexto',
        'fields': [
            {
                'label': 'Motivo de consulta',
                'value': 'Consulta repetidamente por dolor torácico recurrente pese a seguir el tratamiento médico.',
            },
            {
                'label': 'Pruebas basales',
                'value': 'Los estudios clínicos y complementarios disponibles se mantienen dentro de parámetros normales.',
            },
            {
                'label': 'Cambios en 6 meses',
                'value': 'La esposa trabaja fuera limpiando; el hijo de 17 años trabaja tras el colegio; la hija de 21 anunció embarazo y matrimonio.',
            },
            {
                'label': 'Vivencia',
                'value': 'Se siente solo, desatendido e irritable; interpreta el empleo de su esposa como falta de atención a su salud y al hogar.',
            },
            {
                'label': 'Síntoma funcional',
                'value': 'El dolor puede ser una expresión psicosomática: malestar psicológico asociado a síntomas físicos; hipótesis a explorar, no explicación única.',
            },
        ],
        'footnote': 'Las pruebas basales normales no eliminan el dolor ni cierran la valoración clínica.',
    },
    {
        'module': 'concept_map',
        'kicker': 'Pregunta 2 · visión biopsicosocial',
        'title': 'Tensiones y crisis en el ciclo vital',
        'hub': 'Sistema familiar',
        'nodes': [
            {
                'title': 'Economía y trabajo',
                'desc': 'La esposa limpia fuera para aumentar ingresos; disminuye el tiempo compartido.',
            },
            {
                'title': 'Rol del adolescente',
                'desc': 'El hijo de 17 trabaja tras el colegio y pone en riesgo sus estudios.',
            },
            {
                'title': 'Ciclo vital',
                'desc': 'Embarazo y boda de la hija de 21 años descolocan a los padres.',
            },
            {
                'title': 'Vínculo conyugal',
                'desc': 'El trabajo se interpreta como desatención; surgen reproches y aislamiento.',
            },
            {
                'title': 'Trastorno psicosomático',
                'desc': 'Dolor físico asociado a factores psicológicos; valorar el contexto familiar.',
            },
        ],
        'footnote': 'Crisis normativa del ciclo vital: embarazo y matrimonio; estresores no normativos: presión económica y trabajo adolescente.',
    },
    {
        'module': 'figure',
        'kicker': 'Lectura sistémica',
        'title': 'Los cambios familiares se influyen entre sí',
        'image': 'assets/caso4_red_familiar.png',
        'caption': 'El trabajo, la escolaridad y las transiciones vitales convergen en la vivencia de soledad del paciente.',
        'credit': 'Ilustración generada con IA.',
    },
    {
        'module': 'comparison_table',
        'kicker': 'Pregunta 2 · niveles de intervención',
        'title': 'Por qué este caso requiere Nivel 4',
        'headers': ['Nivel', 'Foco clínico', 'Intervención del médico'],
        'col_widths': [0.75, 1.25, 2.2],
        'rows': [
            ['1–2', 'Evaluación biomédica y consejería preventiva', 'Evaluar el síntoma y orientar la prevención.'],
            ['3', 'Contención emocional inmediata ante una crisis', 'Acompañar y contener la crisis actual.'],
            ['4', 'Hipótesis de trastorno psicosomático; pautas de interacción, no contenido.', 'Entrevista planificada; rechazar coaliciones y no tomar partido.'],
            ['5', 'Terapia familiar especializada', 'Derivar ante persistencia, rigidez o patología grave.'],
        ],
        'takeaway': 'El Nivel 4 pasa de la contención a cambiar pautas de interacción, sin asignar culpables ni tomar partido.',
        'footnote': 'Trastorno psicosomático: síntoma físico asociado a factores psicológicos; hipótesis clínica por explorar.',
    },
    {
        'module': 'definition',
        'kicker': 'Marco teórico · Rol del médico familiar',
        'title': 'Nivel 4: evaluación funcional e intervención planificada',
        'main_statement': 'El médico investiga y formula hipótesis sistémicas centradas en las relaciones familiares y en las pautas recurrentes de interacción; desplaza el foco del contenido superficial y de las causas aisladas.',
        'elaboration': 'Indicaciones: crisis no normativa que supera el Nivel 3; problemas de salud mental o disfunción familiar consolidada; crisis normativa con reorganización compleja (enfermedad crónica, invalidez, muerte o duelo).',
        'key_points': [
            {
                'title': 'Detectar problemas psicosomáticos',
                'desc': 'Trastornos físicos asociados a factores psicológicos y tensiones relacionales; reconocer también disfunción familiar manifiesta.',
            },
            {
                'title': 'Convocar a toda la familia',
                'desc': 'Comprometer al grupo completo en una entrevista planificada y estructurada.',
            },
            {
                'title': 'Neutralidad clínica estricta',
                'desc': 'Apoyar por igual, rechazar coaliciones y evitar activamente tomar partido por cualquier integrante.',
            },
        ],
        'footnote': 'En el Sr. Prado, dolor y pruebas basales orientan una hipótesis; no confirman una causa única.',
    },
    {
        'module': 'figure',
        'kicker': 'Nivel 4 · entrevista planificada',
        'title': 'Entrevista conjunta, posición neutral',
        'image': 'assets/entrevista_familiar_planificada.png',
        'caption': 'El clínico observa las pautas de interacción y escucha a la familia sin validar ataques ni tomar partido.',
        'credit': 'Ilustración generada con IA.',
    },
    {
        'module': 'flow_diagram',
        'kicker': 'Nivel 4 · entrevista planificada',
        'title': 'Observar pautas y neutralizar coaliciones',
        'explanation': 'En el Nivel 4, el médico interviene en las pautas de interacción y no sobre las causas atribuidas o el contenido de las quejas. Rechaza coaliciones, no toma partido y deshace la triangulación de los hijos en el conflicto conyugal.',
        'steps': [
            {
                'label': '01',
                'title': 'Priorizar las pautas',
                'desc': 'Intervenir en las pautas de interacción, no sobre las causas atribuidas ni el contenido de las quejas.',
            },
            {
                'label': '02',
                'title': 'Escuchar a la familia',
                'desc': 'Convocar a todos y observar turnos, alianzas y reproches en el contexto de los cambios.',
            },
            {
                'label': '03',
                'title': 'Rechazar coaliciones',
                'desc': 'La hija culpa a la madre por no cuidar al padre; el hijo la defiende y acusa a la hermana por el gasto.',
                'highlight': True,
            },
            {
                'label': '04',
                'title': 'Deshacer la triangulación',
                'desc': 'No tomar partido: sacar a los hijos del conflicto conyugal y pactar apoyo, responsabilidades y seguimiento.',
            },
        ],
        'footnote': 'El objetivo es modificar el patrón relacional sin decidir quién tiene razón.',
    },
    {
        'module': 'checklist',
        'kicker': 'Pregunta 3 · acuerdos a corto plazo',
        'title': 'Acuerdos funcionales, no culpables',
        'items': [
            {
                'label': 'Registrar el dolor',
                'desc': 'Anotar frecuencia, intensidad y estrés del día; revisar el patrón en consulta, no cada episodio de forma aislada.',
            },
            {
                'label': 'Proteger la escuela',
                'desc': 'Priorizar la asistencia; limitar el trabajo del hijo a fines de semana o, como máximo, 2 horas diarias.',
            },
            {
                'label': 'Cuidar la pareja',
                'desc': 'Fijar un diálogo diario sin reproches y redistribuir tareas según la capacidad del padre.',
            },
            {
                'label': 'Neutralizar coaliciones',
                'desc': 'La hija culpa a la madre; el hijo se alía con ella y reprocha los gastos del embarazo. El médico no toma partido y pacta apoyo mutuo.',
            },
        ],
        'footnote': 'El registro del dolor no sustituye la reevaluación clínica si cambia el cuadro.',
    },
    {
        'module': 'stat_card',
        'kicker': 'Pregunta 4 · seguimiento',
        'title': 'Revisar acuerdos con indicadores concretos',
        'stat_num': '15 días',
        'stat_title': 'entre consultas de seguimiento',
        'narrative_blocks': [
            {
                'title': 'Dolor torácico',
                'desc': 'Medir intensidad y frecuencia para comprobar si disminuyen.',
            },
            {
                'title': 'Asistencia escolar',
                'desc': 'Verificar la asistencia completa del hijo de 17 años.',
            },
            {
                'title': 'Acuerdos de pareja',
                'desc': 'Revisar el diálogo cotidiano y la redistribución de tareas.',
            },
        ],
        'footnote': 'La revisión quincenal valora síntomas, escolaridad y convivencia; ajustar según la evolución clínica.',
    },
    {
        'module': 'checklist',
        'kicker': 'Escalamiento · Nivel 5',
        'title': 'Criterios de derivación especializada',
        'items': [
            {
                'label': 'Síntoma persistente',
                'desc': 'El dolor persiste o empeora pese a los acuerdos y al seguimiento planificado.',
            },
            {
                'label': 'Dinámica familiar rígida',
                'desc': 'Fracasan repetidamente los acuerdos y continúan la culpabilización o las alianzas destructivas entre padres e hijos.',
            },
            {
                'label': 'Patología grave o riesgo',
                'desc': 'Depresión mayor, ideación suicida o violencia intrafamiliar requieren derivación inmediata a terapia familiar y salud mental.',
            },
        ],
        'footnote': 'La ideación suicida o la violencia intrafamiliar no se aplazan a la revisión quincenal.',
    },
    {
        'module': 'definition',
        'kicker': 'Cierre clínico',
        'title': 'Del síntoma al funcionamiento familiar',
        'main_statement': 'En el Nivel 4, el dolor torácico conserva su importancia clínica y, a la vez, se examina en relación con los cambios y las interacciones familiares.',
        'elaboration': 'La entrevista planificada transforma una hipótesis sistémica en acuerdos observables; el seguimiento indica si funcionan o si hace falta terapia familiar especializada.',
        'key_points': [
            {
                'title': 'No buscar culpables',
                'desc': 'Frenar reproches y explorar cómo cada miembro interpreta los cambios.',
            },
            {
                'title': 'Proteger funciones',
                'desc': 'Cuidar salud, escolaridad, vínculo de pareja y apoyo a la gestación.',
            },
            {
                'title': 'Medir y escalar',
                'desc': 'Revisar dolor, asistencia y convivencia; derivar ante persistencia, rigidez o riesgo.',
            },
        ],
        'footnote': 'La hipótesis psicosomática se revisa junto con la evolución clínica.',
    },
]
