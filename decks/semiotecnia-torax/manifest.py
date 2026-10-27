# -*- coding: utf-8 -*-
"""Deck: Semiotecnia del tórax y aparato respiratorio.

Manifest StudyDeck v2 (UCP-only, es-ES). El texto sigue el capítulo 3 del PDF
adjunto; las figuras se recortaron de ese mismo PDF con
`tools/extract_figures.py`, que publica los dibujos como láminas:

    fig_3_1_3_3      cortes transversales del tórax en tonel y excavado
    fig_3_8          escoliosis dorsal, variantes A y B
    fig_3_9          mano de escultor
    fig_3_12_3_13    ganglios axilares y supraclaviculares
    fig_3_18_3_19    resistencia torácica y maniobra de Ruault
    fig_3_21_3_22    expansión de las bases por delante y por detrás
    fig_3_27_3_32    campos de Krönig y excursión de las bases
    fig_3_34_3_35    mapas de auscultación, cara anterior y posterior

Perfil `lecture`: cuatro bloques (inspección, palpación, percusión y
auscultación), cada uno abierto por su divisor. `IMAGES.max_n = 8` porque el
deck usa ocho láminas reales, no marcadores.
"""

COURSE_INFO = {
    'course': 'Semiología Médica',
    'institution': 'UCP',
    'author': '',
}

CONFIG = {
    'PALETTE': 'ucp',
    'LANG': 'es-ES',
    'PROFILE': 'lecture',
    'IMAGES': {'mode': 'web-only', 'max_n': 8,
               'allow_ai': False, 'allow_placeholder': False},
    'SHOW_FOOTER': True,
    'SHOW_SLIDE_NUMBER': True,
    'ALLOW_TERMS': ['pectus carinatum', 'pectus excavatum', 'Krönig', 'Ruault',
                    'Traube', 'Louis', 'EIC'],
}

CREDIT = 'Semiotecnia del tórax, cap. 3, {fig} (PDF adjunto)'

SLIDES = [
    # ---------------------------------------------------------------- apertura
    {'module': 'title',
     'title': 'Semiotecnia del tórax y aparato respiratorio',
     'subtitle': 'Cuatro tiempos para leer la caja torácica, la ventilación y el parénquima',
     'course': 'Semiología Médica', 'institution': 'UCP'},

    {'module': 'learning_objectives', 'kicker': 'Apertura', 'title': 'Objetivos de la sesión',
     'objectives': [
         {'verb': 'Nombrar', 'bloom': 'remember',
          'text': 'los cuatro tiempos del examen respiratorio y el orden en que se suceden.'},
         {'verb': 'Explicar', 'bloom': 'understand',
          'text': 'el sustrato biofísico de cada timbre percutorio y su topografía normal.'},
         {'verb': 'Ejecutar', 'bloom': 'apply',
          'text': 'las seis maniobras de palpación con la referencia anatómica de cada una.'},
         {'verb': 'Distinguir', 'bloom': 'analyze',
          'text': 'ruidos adventicios continuos de discontinuos por su respuesta a la tos.'}]},

    {'module': 'definition', 'kicker': 'Marco', 'title': 'La secuencia semiológica',
     'main_statement': 'Cuatro tiempos sucesivos —inspección, palpación, percusión y '
                       'auscultación— evalúan la caja torácica, la ventilación y las '
                       'alteraciones acústicas y mecánicas del parénquima pulmonar.',
     'key_points': [
         {'title': 'Inspección',
          'desc': 'Posición, conformación parietal, deformidades y dinámica ventilatoria; '
                  'los signos extratorácicos cierran el tiempo.'},
         {'title': 'Palpación',
          'desc': 'Seis maniobras descendentes: pared, cadenas ganglionares, resistencia, '
                  'expansión y frémito táctil.'},
         {'title': 'Percusión y auscultación',
          'desc': 'Mapa de timbres y límites primero; después ruidos, soplos, adventicios, '
                  'voz y tos.'}]},

    # ------------------------------------------------------------- 1 inspección
    {'module': 'section_divider', 'divider_style': 'Bloque 1',
     'section_title': 'Inspección torácica',
     'section_subtitle': 'La posición y la geometría de la pared se leen antes de tocar al '
                         'paciente: lo que la inspección describe, la palpación y la '
                         'percusión lo confirman.'},

    {'module': 'algorithm', 'kicker': 'Inspección', 'title': 'Cuatro pasos frente al paciente',
     'steps': [
         {'title': 'Preparar la exposición',
          'desc': 'Bipedestación o banquillo; brazos péndulos a los lados para las caras '
                  'anterior y posterior, manos tras la nuca para exponer las líneas axilares.'},
         {'title': 'Leer la conformación',
          'desc': 'Diámetro anteroposterior frente al transversal, protrusiones, depresiones '
                  'y retracciones parietales; comparar siempre ambos hemitórax.',
          'highlight': True},
         {'title': 'Explorar la piel',
          'desc': 'Circulación colateral, arañas vasculares, estrías, fístulas, '
                  'telangiectasias y cicatrices.'},
         {'title': 'Cronometrar la dinámica',
          'desc': 'Frecuencia, amplitud, ritmo y contracciones anómalas; vigilar tiraje, '
                  'cianosis, aleteo nasal y dedos hipocráticos.'}]},

    {'module': 'side_by_side', 'kicker': 'Inspección', 'title': 'Simetría: lo normal y lo que no lo es',
     'left_card': {
         'header': 'Fisiológica', 'title': 'El lado dominante',
         'points': [
             'El hemitórax de la extremidad dominante tiene mayor desarrollo muscular.',
             'También es mayor su volumen global: la diferencia es de grado, no de forma.',
             'No se acompaña de abovedamiento circunscrito ni de retracción parietal.',
             'Conviene registrarla antes de comparar, para no leerla como patología.']},
     'right_card': {
         'header': 'Patológica', 'title': 'Alteraciones unilaterales',
         'points': [
             'Abovedamiento circunscrito: derrame pleural o tumoración de la pared.',
             'Retracción parietal: el parénquima subyacente ha perdido volumen.',
             'El hallazgo es localizado, no un hemitórax entero más grande que el otro.',
             'Se confirma palpando el relieve y midiendo la expansión de ese lado.']}},

    {'module': 'comparison_table', 'kicker': 'Inspección', 'title': 'Cuatro deformidades parietales',
     'headers': ['Deformidad', 'Trazo diferencial', 'Qué se ve en el paciente'],
     'col_widths': [2.3, 3.1, 3.1],
     'rows': [
         ['Tórax en tonel (enfisematoso)',
          'Aumento del diámetro anteroposterior sobre el transversal',
          'Silueta globulosa, con protrusión anterior y posterior'],
         ['Tórax paralítico o asténico',
          'Disminución neta del anteroposterior, con transversal relativamente mayor',
          'Tórax plano y alargado, de perfil estrecho'],
         ['Tórax en quilla (carinatum)',
          'Prominencia esternal anterior aguda; sección circular',
          'El esternón avanza en proa y el tórax pierde el aplanamiento lateral'],
         ['Tórax excavado (pectus excavatum)',
          'Depresión del segmento esternal distal hacia el raquis',
          'Fosa retroesternal visible en el tercio inferior del esternón']],
     'takeaway': 'En las cuatro, la clave es comparar diámetros y simetría, no memorizar siluetas.'},

    {'module': 'figure', 'kicker': 'Inspección · cortes transversales',
     'title': 'Tórax en tonel y tórax excavado',
     'image': 'decks/semiotecnia-torax/imgs/fig_3_1_3_3.png',
     'caption': 'Línea continua: tórax normal. Izquierda, el anteroposterior se adelanta; '
                'derecha, el esternón se hunde.',
     'credit': CREDIT.format(fig='figs. 3-1 y 3-3')},

    {'module': 'figure', 'kicker': 'Inspección · columna dorsal',
     'title': 'Escoliosis dorsal',
     'image': 'decks/semiotecnia-torax/imgs/fig_3_8.png',
     'caption': 'La línea de apófisis espinosas se desvía: A sinistroconvexa, B dextroconvexa, '
                'ambas remarcadas a lápiz.',
     'credit': CREDIT.format(fig='fig. 3-8')},

    {'module': 'definition', 'kicker': 'Inspección', 'title': 'Cifosis: dos niveles, dos variantes',
     'main_statement': 'La cifosis acentúa la curvatura dorsal fisiológica; el nivel donde lo '
                       'hace distingue la variante senil de la juvenil.',
     'key_points': [
         {'title': 'Cifosis senil',
          'desc': 'Acentúa la curvatura dorsal en su tercio medio; el dorso se redondea sin '
                  'desviación lateral de las apófisis espinosas.'},
         {'title': 'Cifosis juvenil',
          'desc': 'Exagera la curvatura en el segmento inferior de la columna dorsal, por '
                  'debajo del tercio medio.'}]},

    {'module': 'definition', 'kicker': 'Inspección', 'title': 'Dinámica y signos extratorácicos',
     'main_statement': 'La inspección continua de frecuencia, amplitud, ritmo y contracciones '
                       'anómalas revela la mecánica ventilatoria; la facies y las extremidades '
                       'delatan su coste.',
     'key_points': [
         {'title': 'Músculos accesorios',
          'desc': 'Hipertrofia y engrosamiento rítmico inspiratorio del esternocleidomastoideo, '
                  'con depresión de las fosas supraclaviculares.'},
         {'title': 'Facies y cuello',
          'desc': 'Cianosis labial o facial, aleteo nasal, ventilación con labios fruncidos, '
                  'ingurgitación yugular, fístulas, estrías y telangiectasias.'},
         {'title': 'Extremidades',
          'desc': 'Dedos hipocráticos: acropaquia con redondeo del extremo digital e incurvación '
                  'de la uña.'}]},

    # -------------------------------------------------------------- 2 palpación
    {'module': 'section_divider', 'divider_style': 'Bloque 2',
     'section_title': 'Palpación sistemática',
     'section_subtitle': 'Seis maniobras en orden descendente convierten la inspección en dato '
                         'táctil: relieve, trofismo, tono, cadenas ganglionares, elasticidad y '
                         'expansión.'},

    {'module': 'checklist', 'kicker': 'Palpación', 'title': 'Seis maniobras, un orden',
     'items': [
         {'label': 'Mano de escultor',
          'desc': 'Deslizamiento palmar plano sobre caras anterior, posterior y laterales; '
                  'censa relieve cutáneo, deformaciones óseas y tumefacciones.'},
         {'label': 'Pared: trofismo y tono',
          'desc': 'Pinzamiento bimanual de piel y tejido subcutáneo; compresión con la punta '
                  'del índice sobre las masas musculares.'},
         {'label': 'Cadenas ganglionares',
          'desc': 'Supraclavicular desde atrás, con tres dedos y hombros elevados; axilar en '
                  'sus cinco grupos, uno por uno.'},
         {'label': 'Resistencia torácica',
          'desc': 'Compresión convergente bimanual sobre puntos homotópicos, a igual nivel por '
                  'delante y por detrás.'},
         {'label': 'Expansión y frémito',
          'desc': 'Ruault en los vértices, bases anteriores y posteriores; después vibraciones '
                  'vocales con «treinta y tres».'}]},

    {'module': 'definition', 'kicker': 'Palpación · maniobra 1',
     'title': 'La pared que la mano registra',
     'image': 'decks/semiotecnia-torax/imgs/fig_3_9.png',
     'main_statement': 'Sobre la pared, la palpación busca cuatro cosas: trofismo, tono, puntos '
                       'dolorosos y crepitación gaseosa.',
     'elaboration': 'El trofismo se explora pinzando piel y tejido subcutáneo entre pulgar e '
                    'índice: la atrofia localizada traduce un reflejo visceral.',
     'key_points': [
         {'title': 'Tono',
          'desc': 'Compresión con la punta del índice: resistencia, contractura o espasmo.'},
         {'title': 'Crepitación',
          'desc': 'Enfisema subcutáneo: gas en el tejido, palpable como roce.'}],
     'caption': 'Deslizamiento palmar plano, sin presionar: censa relieve, deformación ósea y '
                'tumefacción.',
     'credit': CREDIT.format(fig='fig. 3-9')},

    {'module': 'figure', 'kicker': 'Palpación · maniobra 2',
     'title': 'Cadenas ganglionares',
     'image': 'decks/semiotecnia-torax/imgs/fig_3_12_3_13.png',
     'caption': 'Izquierda: cinco grupos axilares (A-E). Derecha: fosa supraclavicular con tres '
                'dedos y hombros elevados.',
     'credit': CREDIT.format(fig='figs. 3-12 y 3-13')},

    {'module': 'fixed_schema_card', 'kicker': 'Palpación · maniobra 4',
     'title': 'Cuatro maniobras de expansión',
     'fields': [
         {'label': 'Vértices (Ruault)',
          'value': 'Manos en los trapecios, dedos en la fosa infraclavicular y pulgares en C7-T1; '
                   'se mide la separación del ángulo interpulgar.'},
         {'label': 'Región infraclavicular',
          'value': 'Manos planas bilaterales bajo las clavículas, en decúbito dorsal o de pie; se '
                   'busca el desplazamiento de las manos.'},
         {'label': 'Bases anteriores',
          'value': 'Dedos en la línea axilar media y pulgares convergentes bajo el apéndice '
                   'xifoides: la expansión abre el ángulo que forman.'},
         {'label': 'Bases posteriores',
          'value': 'Manos abrazando los bordes posterolaterales bajo la punta escapular y pulgares '
                   'junto a la línea media vertebral.'},
         {'label': 'Regla de lectura',
          'value': 'La excursión basal supera a la apical; toda maniobra se repite con respiración '
                   'normal y con inspiración profunda.'}]},

    {'module': 'figure', 'kicker': 'Palpación · maniobras 3 y 4',
     'title': 'Resistencia torácica y vértices',
     'image': 'decks/semiotecnia-torax/imgs/fig_3_18_3_19.png',
     'caption': 'Izquierda: compresión convergente homotópica y cese elástico. Derecha: Ruault, '
                'pulgares separados.',
     'credit': CREDIT.format(fig='figs. 3-18 y 3-19')},

    {'module': 'figure', 'kicker': 'Palpación · maniobra 4',
     'title': 'Bases anteriores y posteriores',
     'image': 'decks/semiotecnia-torax/imgs/fig_3_21_3_22.png',
     'caption': 'Delante, pulgares bajo el xifoides; detrás, bajo la punta escapular. La amplitud '
                'se lee en el ángulo.',
     'credit': CREDIT.format(fig='figs. 3-21 y 3-22')},

    {'module': 'definition', 'kicker': 'Palpación · maniobras 5 y 6', 'title': 'Frémito y vibraciones',
     'main_statement': 'El frémito se palpa con la cara palmar o el borde cubital de una sola '
                       'mano, de arriba abajo y en comparación transversal, mientras el paciente '
                       'pronuncia «treinta y tres».',
     'elaboration': 'Las vibraciones vocales son fisiológicamente más notorias en el hemitórax '
                    'derecho; la maniobra se repite hasta su desaparición, que delimita las bases '
                    'pulmonares.',
     'key_points': [
         {'title': 'Vibraciones pleurales',
          'desc': 'Roce táctil áspero por pleuras despulidas; se percibe en ambas fases '
                  'respiratorias, con franco predominio inspiratorio.'},
         {'title': 'Regla de la comparación',
          'desc': 'Una sola mano, lado a lado y a la misma altura: la asimetría es el hallazgo, '
                  'no el valor absoluto.'}]},

    # -------------------------------------------------------------- 3 percusión
    {'module': 'section_divider', 'divider_style': 'Bloque 3',
     'section_title': 'Percusión: mapeo y timbres',
     'section_subtitle': 'El dedo plexor golpea el dedo plesímetro paralelo a las costillas, o '
                         'directamente el relieve óseo, para dibujar el mapa acústico del tórax.'},

    {'module': 'comparison_table', 'kicker': 'Percusión', 'title': 'Los timbres del aire',
     'headers': ['Timbre', 'Sustrato biofísico', 'Topografía y hallazgo'],
     'col_widths': [1.5, 2.7, 3.8],
     'rows': [
         ['Sonoridad',
          'Resonancia por distensión del parénquima alveolar aireado',
          'Campos de Krönig y dorso hasta las bases; se atenúa en atelectasias y consolidaciones'],
         ['Hipersonoridad',
          'Tono más grave e intensidad aumentada por exceso de aire',
          'No existe en reposo; aparece en enfisema, crisis asmática y neumotórax'],
         ['Timpanismo',
          'Sonido musical agudo en cavidad aérea tensa y cerrada',
          'Espacio semilunar de Traube; neumotórax a tensión y cavernas de pared lisa']],
     'takeaway': 'El aire en exceso agrava el tono; el aire perdido lo apaga. El timbre traduce contenido.'},

    {'module': 'comparison_table', 'kicker': 'Percusión', 'title': 'Los grados de la amortiguación',
     'headers': ['Timbre', 'Sustrato biofísico', 'Topografía y hallazgo'],
     'col_widths': [1.5, 2.7, 3.8],
     'rows': [
         ['Sonoridad atenuada',
          'Pérdida parcial de la distensión alveolar, sin masa sólida',
          'Disminuye sin llegar al golpe sordo; atelectasias y consolidaciones iniciales'],
         ['Matidez',
          'Golpe sordo y breve sobre masa sólida desprovista de gas',
          'Desde el 5.º EIC derecho (hígado) y área precordial; consolidación masiva y derrame'],
         ['Submatidez',
          'Transición acústica entre el aire alveolar y la solidez visceral',
          '4.º a 5.º EIC derecho y área periprecordial; derrames laminares y condensaciones incompletas']],
     'takeaway': 'La submatidez es una franja, no un territorio: delata ocupación incompleta.'},

    {'module': 'figure', 'kicker': 'Percusión · protocolo',
     'title': 'De los vértices a las bases',
     'image': 'decks/semiotecnia-torax/imgs/fig_3_27_3_32.png',
     'caption': 'Izquierda: campos de Krönig. Derecha: marcas a y b de la matidez en apnea y en '
                'espiración máxima, 4 a 6 cm.',
     'credit': CREDIT.format(fig='figs. 3-27 y 3-32')},

    {'module': 'fixed_schema_card', 'kicker': 'Percusión · mapeo',
     'title': 'Protocolo de mapeo topográfico',
     'fields': [
         {'label': 'Campos de Krönig',
          'value': 'Plesímetro sobre el trapecio, de la base del cuello al hombro; la sonoridad '
                   'queda entre la matidez cervical y el tercio externo clavicular.'},
         {'label': 'Dorso y bases',
          'value': 'Percusión descendente interescapulovertebral y subescapular; la matidez basal '
                   'excursiona de 4 a 6 cm entre apnea y espiración máxima.'},
         {'label': 'Tórax anterior',
          'value': 'Desde la línea hemiclavicular: sonoridad hasta el 4.º EIC derecho y matidez '
                   'por debajo; a la izquierda, matidez cardíaca y timpanismo de Traube.'},
         {'label': 'Esqueleto óseo',
          'value': 'Esternón de la horquilla al xifoides y columna de C7 a T12: sonoros si no hay '
                   'lesión ni ocupación de la medular.'}]},

    # ----------------------------------------------------------- 4 auscultación
    {'module': 'section_divider', 'divider_style': 'Bloque 4',
     'section_title': 'Auscultación',
     'section_subtitle': 'Paciente sentado, tórax descubierto y respiración bucal ligeramente '
                         'profunda; secuencia simétrica y descendente por cara anterior, posterior '
                         'y regiones laterales.'},

    {'module': 'comparison_table', 'kicker': 'Auscultación', 'title': 'Ruidos respiratorios normales',
     'headers': ['Ruido', 'Origen', 'Dónde y cronología'],
     'col_widths': [1.7, 2.5, 3.8],
     'rows': [
         ['Respiración brónquica',
          'Flujo aéreo turbulento traqueobronquial',
          'Hueco supraclavicular y dorsal superior (T1-T4); espiración más áspera y prolongada'],
         ['Murmullo vesicular',
          'Distensión alveolar periférica',
          'Fosas infraclaviculares, axilas y bases interescapulares; inspiración:espiración de 5:1'],
         ['Respiración broncovesicular',
          'Superposición acústica de ambos componentes',
          'Articulaciones esternoclaviculares e interescapulovertebral superior']],
     'takeaway': 'Oír respiración brónquica donde corresponde murmullo vesicular ya es patología.'},

    {'module': 'figure', 'kicker': 'Auscultación · mapa',
     'title': 'Dónde suena cada ruido',
     'image': 'decks/semiotecnia-torax/imgs/fig_3_34_3_35.png',
     'caption': 'Cuadriculado: brónquica; punteado: broncovesicular; rayado: murmullo vesicular, '
                'anterior y posterior.',
     'credit': CREDIT.format(fig='figs. 3-34 y 3-35')},

    {'module': 'comparison_table', 'kicker': 'Auscultación', 'title': 'Soplos patológicos',
     'headers': ['Soplo', 'Mecanismo', 'Clave de reconocimiento'],
     'col_widths': [1.4, 3.0, 3.6],
     'rows': [
         ['Tubario',
          'Respiración brónquica en área alveolar por condensación con bronquio permeable',
          'Se ausculta periférico, donde debería oírse murmullo vesicular'],
         ['Pleurítico',
          'Variante del brónquico sobre el límite superior de un derrame pleural',
          'Predominio espiratorio y timbre suave en la vocal «e»'],
         ['Cavernoso',
          'Transmisión hueca de baja frecuencia amplificada por una caverna pulmonar',
          'Sonoridad profunda, como soplar dentro de un tubo'],
         ['Anfórico',
          'Cavernoso con timbre metálico por resonancia en gran cavidad de pared tensa',
          'Timbre metálico; puede adquirirlo la tos']],
     'takeaway': 'La condensación conserva el bronquio; el derrame lo aleja del estetoscopio.'},

    {'module': 'side_by_side', 'kicker': 'Auscultación', 'title': 'Adventicios: continuos y discontinuos',
     'left_card': {
         'header': 'Continuos', 'title': 'Roncus y sibilancias',
         'points': [
             'Roncus: grave y ronco, en ambos tiempos, por secreción viscosa en vía mayor.',
             'Sibilancias: agudo y musical, por broncoespasmo y estenosis de vía pequeña.',
             'La sibilancia predomina al final de la espiración; el roncus no respeta el tiempo.',
             'Ambos cambian o ceden con la tos: la vía aérea se limpia, el parénquima no.']},
     'right_card': {
         'header': 'Discontinuos', 'title': 'Crepitantes y burbujas',
         'points': [
             'Crepitantes: breves, homogéneos y finos en el pico inspiratorio; la tos no los cambia.',
             'Burbuja: gruesa, mediana o fina, en ambas fases, por aire que pasa en medio líquido.',
             'Los húmedos se movilizan con la tos; los crepitantes, en cambio, son inmodificables.',
             'Frotes: crujido bifásico de cuero seco, sin cambios con la tos y más intenso al '
             'presionar.']}},

    {'module': 'comparison_table', 'kicker': 'Auscultación', 'title': 'La voz y la tos como pruebas',
     'headers': ['Signo', 'Qué se oye', 'Dónde aparece'],
     'col_widths': [1.7, 2.9, 3.4],
     'rows': [
         ['Broncofonía',
          'Resonancia vocal aumentada, sin que se distingan las sílabas',
          'Consolidación; la voz gana cuerpo sobre el foco'],
         ['Pectoriloquia',
          'Palabras nítidas y articuladas al hablar',
          'Condensación con bronquio permeable; áfona si se susurran'],
         ['Egofonía',
          'Voz temblorosa, nasal y entrecortada, en «e»',
          'Borde superior de una colección pleural líquida'],
         ['Respuesta a la tos',
          'Moviliza o borra ruidos húmedos y roncus',
          'Estrena timbre cavernoso o anfórico tras toser']],
     'takeaway': 'La tos es la maniobra que separa lo que está en la vía de lo que está en el parénquima.'},

    {'module': 'viva_question', 'kicker': 'Integración', 'title': 'Pregunta de examen oral',
     'difficulty': 'Alta',
     'prompt': 'Hay matidez basal derecha. A la auscultación el murmullo está abolido y aparece un '
               'soplo con timbre en «e». ¿Derrame pleural o consolidación neumónica?',
     'model_answer': 'El derrame desplaza el parénquima y crea un límite líquido: matidez, soplo '
                     'pleurítico y egofonía sobre el borde superior. La consolidación conserva el '
                     'bronquio permeable: soplo tubario, broncofonía y pectoriloquia sobre el foco.',
     'examiner_note': 'Se espera que nombre el límite superior del derrame y que separe soplo '
                      'pleurítico de tubario antes de pedir imagen.'},

    {'module': 'glossary', 'kicker': 'Cierre', 'title': 'Glosario mínimo',
     'terms': [
         {'term': 'Sonoridad',
          'def': 'Resonancia del parénquima alveolar aireado; timbre normal del tórax.'},
         {'term': 'Hipersonoridad',
          'def': 'Tono más grave e intenso por exceso de aire: enfisema, asma, neumotórax.'},
         {'term': 'Timpanismo',
          'def': 'Sonido musical agudo de una cavidad aérea tensa y cerrada.'},
         {'term': 'Matidez',
          'def': 'Golpe sordo y breve sobre masa sólida sin gas: hígado, derrame, consolidación.'},
         {'term': 'Submatidez',
          'def': 'Transición entre sonoridad y matidez; ocupación parcial del parénquima.'},
         {'term': 'Broncofonía',
          'def': 'Resonancia vocal aumentada sin que se distingan las sílabas.'},
         {'term': 'Pectoriloquia',
          'def': 'Transmisión nítida y articulada de las palabras; áfona si son susurradas.'},
         {'term': 'Egofonía',
          'def': 'Voz temblorosa y nasal en el borde superior de una colección pleural líquida.'}]},

    {'module': 'references', 'kicker': 'Fuente', 'title': 'Origen del texto y de las figuras',
     'refs': [
         'Semiotecnia del tórax: aparato respiratorio. Capítulo 3, pp. 9-21 (PDF adjunto).',
         'Inspección y pared: figs. 3-1, 3-3 y 3-8, recortadas de las pp. 11-13 del capítulo.',
         'Cadenas ganglionares: figs. 3-12 y 3-13, pp. 14-15; mano de escultor: fig. 3-9, p. 14.',
         'Resistencia y expansión: figs. 3-18 y 3-19, p. 16; bases: figs. 3-21 y 3-22, p. 17.',
         'Percusión: figs. 3-27 y 3-32, pp. 19-20; auscultación: figs. 3-34 y 3-35, p. 21.',
         'Las láminas se extrajeron del escaneo 1-bit del PDF sin remuestreo: '
         'tools/extract_figures.py.',
         'En los cortes transversales, línea continua = tórax normal; discontinua = deformidad.',
         'El texto de cada diapositiva condensa el capítulo; las cifras (4-6 cm, 5:1, T1-T4) '
         'son las del original.']},
]
