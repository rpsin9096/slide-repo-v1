# -*- coding: utf-8 -*-
"""Presentación clínica guiada en español, autorada con StudyDeck v2.

Sigue SYSTEM_PROMPT.md y prompt.md (UCP-only), con perfil short, español,
contraste WCAG AA y dos ilustraciones originales generadas por IA.
Build desde la raíz del repositorio:
  studydeck all presentacion_caso4_prado_es.py presentacion_caso4_prado_es.pptx
"""

COURSE_INFO = {
    'course': 'Medicina familiar y comunitaria',
    'institution': 'Seminario clínico',
    'author': 'Caso 4 · Sr. Prado',
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
        'title': 'El dolor torácico en el sistema familiar',
        'subtitle': 'Caso 4 · Sr. Prado · Intervención sistémica planificada · Nivel 4',
        'course': 'Medicina familiar y comunitaria',
        'institution': 'Seminario clínico',
        'author': 'Caso 4 · Sr. Prado',
    },
    {
        'module': 'learning_objectives',
        'kicker': 'Apertura',
        'title': 'Objetivos de la sesión',
        'objectives': [
            {
                'verb': 'Analizar',
                'text': 'el dolor torácico recurrente con pruebas basales normales como hipótesis psicosomática, sin cerrar la evaluación clínica.',
                'bloom': 'analyze',
            },
            {
                'verb': 'Relacionar',
                'text': 'los cambios laborales, escolares y del ciclo vital con la percepción de soledad y las interacciones familiares.',
                'bloom': 'analyze',
            },
            {
                'verb': 'Planificar',
                'text': 'una entrevista familiar de Nivel 4 con acuerdos verificables para el síntoma, la escolaridad, la pareja y el embarazo.',
                'bloom': 'apply',
            },
            {
                'verb': 'Establecer',
                'text': 'un seguimiento quincenal y criterios de derivación a terapia familiar especializada.',
                'bloom': 'evaluate',
            },
        ],
        'footnote': 'Caso clínico guiado mediante pensamiento en voz alta y modelo sistémico.',
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
                'label': 'Hipótesis de trabajo',
                'value': 'El estrés y la pérdida de control pueden expresarse somáticamente; explorar esta hipótesis sin convertirla en explicación única.',
            },
        ],
        'footnote': 'Las pruebas basales normales no eliminan el dolor ni cierran la valoración clínica.',
    },
    {
        'module': 'concept_map',
        'kicker': 'Pregunta 2 · visión biopsicosocial',
        'title': 'Cinco tensiones, un mismo sistema',
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
                'desc': 'Embarazo y boda de la hija de 21 años generan incertidumbre familiar.',
            },
            {
                'title': 'Vínculo conyugal',
                'desc': 'El trabajo se interpreta como desatención; surgen reproches y aislamiento.',
            },
            {
                'title': 'Síntoma somático',
                'desc': 'Puede expresar angustia y pérdida de control; hipótesis por explorar.',
            },
        ],
        'footnote': 'El mapa plantea relaciones para explorar; no asigna culpas ni confirma una causa única.',
    },
    {
        'module': 'figure',
        'kicker': 'Lectura sistémica',
        'title': 'Los cambios familiares se influyen entre sí',
        'image': 'assets/caso4_red_familiar.png',
        'caption': 'El trabajo, la escolaridad y las transiciones vitales convergen en la vivencia de soledad del paciente.',
        'credit': 'Ilustración original generada por IA para esta presentación.',
        'footnote': 'Representación educativa del caso; no corresponde a una familia real.',
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
            ['4', 'Evaluación funcional e hipótesis sistémica', 'Convocar a la familia, observar interacciones y pactar acuerdos.'],
            ['5', 'Terapia familiar especializada', 'Derivar ante persistencia, rigidez o patología grave.'],
        ],
        'takeaway': 'El Nivel 4 añade evaluación funcional e intervención planificada; no se limita a contener la crisis.',
        'footnote': 'En los niveles 1–2 predomina el foco biomédico y preventivo; el Nivel 5 requiere atención especializada.',
    },
    {
        'module': 'figure',
        'kicker': 'Nivel 4 · entrevista planificada',
        'title': 'La familia entra en la consulta',
        'image': 'assets/entrevista_familiar_planificada.png',
        'caption': 'La entrevista conjunta permite observar alianzas y reproches, y negociar cambios sin buscar culpables.',
        'credit': 'Ilustración original generada por IA para esta presentación.',
        'footnote': 'La imagen ilustra una entrevista docente, no una intervención ya realizada.',
    },
    {
        'module': 'flow_diagram',
        'kicker': 'Intervención planificada',
        'title': 'De la hipótesis a un cambio observable',
        'explanation': 'El médico convoca a toda la familia, observa cómo se relacionan y formula hipótesis funcionales. La meta es modificar patrones concretos, no decidir quién tiene razón.',
        'steps': [
            {
                'label': '01',
                'title': 'Acordar el encuadre',
                'desc': 'Explicar que la consulta analizará el funcionamiento familiar, no quién tiene razón.',
            },
            {
                'label': '02',
                'title': 'Escuchar a todos',
                'desc': 'Reunir a la familia y conocer cómo interpreta cada persona los cambios.',
                'highlight': True,
            },
            {
                'label': '03',
                'title': 'Observar patrones',
                'desc': 'Identificar interacciones, coaliciones dañinas y reproches que mantienen la tensión.',
            },
            {
                'label': '04',
                'title': 'Pactar acciones',
                'desc': 'Definir acuerdos concretos, responsabilidades y un momento de revisión.',
            },
        ],
        'footnote': 'La intervención se centra en la función de las interacciones, no en encontrar culpables.',
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
                'label': 'Apoyar el embarazo',
                'desc': 'Frenar los reproches cruzados y organizar una red de apoyo mutuo para la gestación.',
            },
        ],
        'footnote': 'Frenar la culpa cruzada: cuidados del padre y gastos del embarazo. El registro no reemplaza la atención si cambia el dolor.',
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
