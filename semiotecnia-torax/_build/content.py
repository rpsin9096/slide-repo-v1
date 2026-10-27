"""Contenido del documento (fuente única para DOCX y PDF).

El texto reproduce fielmente el material provisto por el usuario; sólo se
agrega estructura (títulos, láminas, epígrafes y apéndices de procedencia).
Cada bullet es (término, etiqueta, cuerpo, nivel).
"""

TITLE = "Semiotecnia del Tórax y Aparato Respiratorio"
SUBTITLE = "Documento ilustrado — Figuras 3-1 a 3-35 recortadas del PDF fuente"
INTRO = (
    "El examen semiológico respiratorio evalúa la caja torácica, la ventilación y las "
    "alteraciones acústicas y mecánicas del parénquima pulmonar mediante cuatro tiempos "
    "sucesivos: inspección, palpación, percusión y auscultación."
)

# Epígrafes cortos para las láminas: id -> (título, nota de lectura o None)
FIGCAP = {
    "3-01": ("Tórax enfisematoso, en tonel (corte transversal)", "Trazo continuo: tórax normal; trazo interrumpido: tórax enfisematoso. Predomina el diámetro anteroposterior."),
    "3-02": ("Tórax de pollo, en quilla —pectus carinatum— (corte transversal)", "Trazo continuo: tórax normal; trazo interrumpido: tórax de pollo. Se caracteriza por la prominencia esternal."),
    "3-03": ("Tórax excavado —pectus excavatum— (corte transversal)", "Trazo continuo: tórax normal; trazo interrumpido: tórax excavado. Se caracteriza por la depresión esternal."),
    "3-04": ("Tórax piriforme (corte transversal)", "Trazo continuo: tórax normal; trazo interrumpido: tórax piriforme. Se caracteriza por su forma circular."),
    "3-05": ("Tórax paralítico o asténico (corte transversal)", "Trazo continuo: tórax normal; trazo interrumpido: tórax paralítico, con aumento relativo del diámetro transversal y disminución del anteroposterior."),
    "3-06": ("Tórax cifótico senil", "Exageración de la cifosis fisiológica en la parte media de la región dorsal de la columna."),
    "3-07": ("Tórax cifótico juvenil", "Exageración de la cifosis fisiológica en la parte inferior de la región dorsal de la columna."),
    "3-08a": ("Tórax escoliótico — A: escoliosis dorsal sinistroconvexa", None),
    "3-08b": ("Tórax escoliótico — B: escoliosis dorsal dextroconvexa", None),
    "3-09": ("Palpación de tórax: «mano de escultor»", None),
    "3-10": ("Examen del trofismo del tórax", "Pinzamiento de la piel entre índice y pulgar en regiones simétricas."),
    "3-11": ("Examen del tono", "Presión con la punta del dedo índice sobre las masas musculares."),
    "3-12": ("Localización de grupos ganglionares axilares", "A: grupo central · B: grupo axilar externo · C: grupo pectoral · D: grupo infraclavicular · E: grupo subescapular. (Tomado de Bailey.)"),
    "3-13": ("Palpación de ganglios supraclaviculares", "Examinador detrás del paciente; tres dedos medios en el hueco supraclavicular mientras el paciente eleva los hombros."),
    "3-14": ("Grupos ganglionares axilares, parte I", "Brazo a la altura del hombro; palma hacia el vértice de la axila, sobre la pared torácica lateral."),
    "3-15": ("Grupos ganglionares axilares, parte II", "Brazo péndulo; descenso desde el vértice con los dedos aplicados a la pared del tórax."),
    "3-16": ("Grupos ganglionares axilares, parte III: grupo subescapular", "Abordaje posterior; palpación de la superficie anterointerna del dorsal ancho."),
    "3-17": ("Grupos ganglionares axilares, parte IV: grupo infraclavicular", None),
    "3-18": ("Elasticidad o resistencia torácica", "Presión convergente bimanual sobre superficies anterior y posterior a la misma altura."),
    "3-19": ("Expansión torácica: maniobra de Ruault (vértices)", "La expansión se reconoce por la separación simétrica de ambos pulgares."),
    "3-20": ("Expansión torácica infraclavicular", None),
    "3-21": ("Expansión de las bases por delante", "Pulgares reunidos bajo el apéndice xifoides; su separación abre el ángulo interpulgar."),
    "3-22": ("Expansión de las bases por detrás", None),
    "3-23": ("Palpación del ángulo de Louis: reconocimiento de espacios intercostales", "Del hueco supraesternal a la cresta transversal (ángulo de Louis); lateral a ella, el 2.º cartílago costal y, debajo, el 2.º espacio intercostal."),
    "3-24": ("Vibraciones vocales: región anterior", "Mano transversal, de arriba abajo, mientras el paciente repite «treinta y tres»."),
    "3-25": ("Vibraciones vocales: región posterior", "Recorrido descendente hasta la desaparición de las vibraciones."),
    "3-26": ("Vibraciones vocales: delimitación de las bases", "Mano transversal apoyada por su borde cubital para precisar el límite basal."),
    "3-27": ("Delimitación de los campos de Krönig", "Sobre el borde superior del trapecio, desde la base del cuello hacia el hombro."),
    "3-28": ("Percusión de las clavículas", "Percusión directa, sin dedo plesímetro, de la articulación esternoclavicular a la acromioclavicular."),
    "3-29": ("Percusión del esternón", "De la horquilla al apéndice xifoides, con el plesímetro perpendicular al eje del hueso."),
    "3-30": ("Percusión anterior: borde superior hepático (detalle digito-digital)", "Plesímetro en los espacios intercostales, paralelo a las costillas, siguiendo la línea hemiclavicular."),
    "3-31": ("Percusión del tórax por detrás", "Del trapecio a las bases, por el espacio interescapulovertebral y bajo el ángulo inferior de la escápula."),
    "3-32": ("Excursión de las bases pulmonares", "a: marca en inspiración forzada (apnea inspiratoria) · b: marca en espiración forzada. Entre ambas, la excursión basal (4 a 6 cm)."),
    "3-33": ("Percusión de la columna", "De C7 a T12, directa sobre la apófisis espinosa o con dedo plesímetro interpuesto."),
    "3-34": ("Auscultación pulmonar: cara anterior", "Cuadriculado: respiración bronquial · Punteado: respiración broncovesicular · Rayado: murmullo vesicular."),
    "3-35": ("Auscultación pulmonar: cara posterior", "Cuadriculado: respiración bronquial · Punteado: respiración broncovesicular · Rayado: murmullo vesicular."),
}

PERCUSSION_TABLE = [
    ["Sonido percutorio", "Sustrato biofísico", "Topografía fisiológica", "Hallazgo patológico"],
    ["Sonoridad", "Resonancia por distensión de parénquima alveolar aireado.", "Campos de Krönig, dorso hasta bases, hemitórax derecho hasta 4.º EIC, izquierdo hasta 3.º EIC.", "Atenuada en atelectasias o consolidaciones."],
    ["Hipersonoridad", "Ruido de tono más grave e intensidad aumentada por exceso aéreo.", "No existe en reposo fisiológico.", "Enfisema pulmonar, crisis asmática, neumotórax."],
    ["Timpanismo", "Sonido musical agudo generado en cavidad aérea tensa cerrada.", "Espacio semilunar de Traube (cámara gástrica).", "Neumotórax a tensión, cavernas superficiales de pared lisa."],
    ["Matidez", "Golpe sordo y breve sobre masa sólida desprovista de gas.", "A partir del 5.º EIC derecho (hígado), área precordial cardíaca.", "Consolidación neumónica masiva, derrame pleural."],
    ["Submatidez", "Transición acústica entre el aire alveolar y la solidez visceral.", "4.º a 5.º EIC derecho (borde hepático superior), área periprecordial.", "Derrames laminares incipientes, condensaciones incompletas."],
]

# Bloques: ("h1", txt) ("h2", txt) ("p", txt) ("bullets", [...]) ("plate", [ids]) ("perc_table",)
BLOCKS = [
    ("h1", "1. Inspección torácica"),
    ("h2", "Posición y conformación anatómica"),
    ("bullets", [
        ("Posición del paciente", "Contexto", "Bipedestación o sentado en banquillo. Brazos péndulos a los lados para cara anterior y posterior; manos tras la nuca para exponer líneas axilares y caras laterales.", 0),
        ("Asimetría fisiológica", "Contexto", "Hemitórax correspondiente a la extremidad dominante presenta mayor desarrollo muscular y volumétrico.", 0),
    ]),
    ("h2", "Deformidades esqueléticas y parietales"),
    ("bullets", [
        ("Tórax enfisematoso (en tonel)", "Contexto", "Aumento del diámetro anteroposterior sobre el transversal; protrusión y morfología globulosa (Fig. 3-1).", 0),
        ("Tórax paralítico o asténico", "Contexto", "Disminución neta del diámetro anteroposterior con incremento relativo del diámetro transversal (Fig. 3-5).", 0),
        ("Tórax en quilla (pectus carinatum / piriforme)", "Contexto", "Prominencia esternal anterior aguda; sección circular torácica (Fig. 3-2, 3-4).", 0),
        ("Tórax excavado (pectus excavatum)", "Contexto", "Depresión del segmento esternal distal hacia el raquis (Fig. 3-3).", 0),
        ("Cifosis senil vs. juvenil", "Contexto", "La variante senil acentúa la curvatura dorsal fisiológica en su tercio medio (Fig. 3-6); la variante juvenil la exagera en el segmento inferior de la columna dorsal (Fig. 3-7).", 0),
        ("Escoliosis dorsal", "Contexto", "Desviación lateral de la línea de apófisis espinosas; evaluada de espaldas, remarcada con lápiz dermográfico e intensificada por flexión anterior del tronco sin doblar rodillas (Fig. 3-8A sinistroconvexa; Fig. 3-8B dextroconvexa).", 0),
        ("Alteraciones unilaterales", "Contexto", "Abovedamientos circunscritos (derrame, tumoración) o retracciones parietales.", 0),
    ]),
    ("plate", ["3-01", "3-02"]),
    ("plate", ["3-03", "3-04"]),
    ("plate", ["3-05"]),
    ("plate", ["3-06", "3-07"]),
    ("plate", ["3-08a", "3-08b"]),
    ("h2", "Dinámica ventilatoria y signos extratorácicos"),
    ("bullets", [
        ("Parámetros dinámicos", "Contexto", "Inspección continua de frecuencia, amplitud, ritmo y contracciones anómalas (mioclonías, fasciculaciones).", 0),
        ("Músculos accesorios", "Contexto", "Hipertrofia/engrosamiento rítmico inspiratorio del esternocleidomastoideo con depresión de fosas supraclaviculares.", 0),
        ("Facies y extremidades", "Contexto", "Cianosis labial/facial, aleteo nasal, ventilación con labios fruncidos, ingurgitación yugular, fístulas, estrías, telangiectasias y dedos hipocráticos (acropaquia).", 0),
    ]),

    ("h1", "2. Palpación sistemática"),
    ("p", "La exploración táctil sigue un protocolo descendente y ordenado en seis maniobras:"),
    ("h2", "1) Mano de escultor"),
    ("bullets", [
        ("Mano de escultor", "Maniobra", "Deslizamiento palmar plano sobre superficies anterior, posterior y laterales; censa relieve cutáneo, deformaciones óseas y tumefacciones (Fig. 3-9).", 0),
    ]),
    ("plate", ["3-09"]),
    ("h2", "2) Examen de pared y cadenas ganglionares"),
    ("bullets", [
        ("Trofismo", "Maniobra", "Pinzamiento bimanual comparativo de piel y tejido subcutáneo entre pulgar e índice; detecta atrofias viscerorreflejas (Fig. 3-10).", 0),
        ("Tono", "Maniobra", "Compresión con la punta del índice sobre masas musculares; evalúa resistencia, contractura muscular o espasmo (Fig. 3-11).", 0),
        ("Pared", "Maniobra", "Registro de puntos dolorosos, edema y crepitación gaseosa de enfisema subcutáneo.", 0),
        ("Cadena supraclavicular", "Maniobra", "Examinador posterior; pulpejos de tres dedos medios en fosas supraclaviculares mientras el paciente eleva activamente los hombros (Fig. 3-13).", 0),
        ("Grupos axilares", "Maniobra", "Exploración secuencial del grupo central, axilar externo, pectoral (anterior), subescapular (borde del dorsal ancho con abordaje posterior) e infraclavicular (Fig. 3-12, 3-14, 3-15, 3-16, 3-17).", 0),
    ]),
    ("plate", ["3-10", "3-11"]),
    ("plate", ["3-12", "3-13"]),
    ("plate", ["3-14", "3-15"]),
    ("plate", ["3-16", "3-17"]),
    ("h2", "3) Resistencia torácica"),
    ("bullets", [
        ("Resistencia torácica", "Maniobra", "Compresión convergente bimanual sobre puntos homotópicos anteriores y posteriores a igual nivel (Fig. 3-18); cese elástico abolido por ocupación masiva o calcificación costal.", 0),
    ]),
    ("plate", ["3-18"]),
    ("h2", "4) Expansión torácica (maniobras de Ruault y basales)"),
    ("bullets", [
        ("Vértices (Ruault)", "Maniobra", "Examinador posterior; manos sobre trapecios, cuatro dedos en fosa infraclavicular, pulgares en C7-T1; se mide separación simétrica del ángulo interpulgar (Fig. 3-19).", 0),
        ("Región infraclavicular", "Maniobra", "Manos planas bilaterales bajo clavículas en decúbito dorsal o de pie (Fig. 3-20).", 0),
        ("Bases anteriores", "Maniobra", "Manos en caras anterolaterales, dedos en línea axilar media, pulgares convergentes bajo el apéndice xifoides (Fig. 3-21).", 0),
        ("Bases posteriores", "Maniobra", "Manos abrazando bordes posterolaterales bajo la punta escapular, pulgares adyacentes a la línea media vertebral (Fig. 3-22). La excursión basal supera a la apical.", 0),
    ]),
    ("plate", ["3-19", "3-20"]),
    ("plate", ["3-21", "3-22"]),
    ("h2", "5) Frémito táctil (vibraciones vocales)"),
    ("bullets", [
        ("Frémito táctil (vibraciones vocales)", "Maniobra", "Palpación comparativa transversal con cara palmar o borde cubital de una sola mano de arriba abajo mientras el paciente pronuncia «treinta y tres» (Fig. 3-24, 3-25, 3-26). Fisiológicamente más notorias en hemitórax derecho.", 0),
    ]),
    ("plate", ["3-24", "3-25", "3-26"]),
    ("h2", "6) Vibraciones pleurales"),
    ("bullets", [
        ("Vibraciones pleurales", "Signo", "Roce táctil áspero por pleuras despulidas; perceptible en ambas fases respiratorias con franco predominio inspiratorio.", 0),
    ]),

    ("h1", "3. Percusión: mapeo y timbres"),
    ("p", "Percusión digito-digital (dedo plexor sobre plesímetro paralelo a costillas) o directa sobre relieve óseo."),
    ("perc_table",),
    ("h2", "Protocolo de mapeo topográfico"),
    ("bullets", [
        ("Campos de Krönig", None, "Plesímetro sobre el trapecio desde la base del cuello al hombro; sonoridad apical delimitada internamente por matidez cervical y externamente a nivel del tercio externo clavicular (Fig. 3-27). Se complementa con percusión digital directa sobre clavículas (Fig. 3-28).", 0),
        ("Región posterior y excursión basal", None, "Percusión descendente interescapulovertebral y subescapular (Fig. 3-31). Matidez basal marcada en apnea inspiratoria (a) y en espiración máxima (b): excursión fisiológica entre 4 y 6 cm (Fig. 3-32).", 0),
        ("Tórax anterior", None, "Percusión desde línea hemiclavicular; en lado derecho sonoridad hasta 4.º EIC, submatidez en 5.º EIC y matidez inferior; en lado izquierdo delimita matidez cardíaca y timpanismo en espacio de Traube (Fig. 3-30).", 0),
        ("Esqueleto óseo", None, "Esternón percutido perpendicularmente desde la horquilla al xifoides (sonoridad uniforme) (Fig. 3-29); columna vertebral percutida desde C7 hasta T12 (sonora fisiológicamente entre C7 y T11) (Fig. 3-33).", 0),
    ]),
    ("plate", ["3-27", "3-28"]),
    ("plate", ["3-29", "3-30"]),
    ("plate", ["3-31", "3-32"]),
    ("plate", ["3-33"]),

    ("h1", "4. Auscultación"),
    ("p", "Se ejecuta con el paciente sentado, tórax descubierto, respirando a boca entreabierta a ritmo ligeramente profundo y sin emitir ruidos guturales. Secuencia simétrica y descendente: cara anterior, posterior y regiones laterales (Fig. 3-34, 3-35)."),
    ("plate", ["3-34", "3-35"]),
    ("h2", "Ruidos respiratorios normales"),
    ("bullets", [
        ("Respiración brónquica (tubárica)", None, "Flujo aéreo turbulento traqueobronquial; espiración más prolongada y áspera que la inspiración; auscultable en hueco supraclavicular y región dorsal superior (T1-T4).", 0),
        ("Murmullo vesicular", None, "Ruido respiratorio suave originado por distensión alveolar periférica; relación temporal inspiración:espiración de 5:1; audible en fosas infraclaviculares, axilas y bases interescapulares.", 0),
        ("Respiración broncovesicular", None, "Superposición acústica de ambos componentes; presente en articulaciones esternoclaviculares y región interescapulovertebral superior.", 0),
    ]),
    ("h2", "Soplos patológicos"),
    ("bullets", [
        ("Soplo tubario (brónquico patológico)", None, "Percepción de respiración brónquica en áreas periféricas alveolares por condensación que conserva el bronquio permeable.", 0),
        ("Soplo pleurítico", None, "Variante del soplo brónquico auscultable sobre el límite superior de un derrame pleural; predominantemente espiratorio con timbre suave en vocal «e».", 0),
        ("Soplo cavernoso (cavitario)", None, "Transmisión hueca de baja frecuencia amplificada por caverna pulmonar.", 0),
        ("Soplo anfórico", None, "Modificación del soplo cavernoso dotada de timbre metálico por resonancia en gran cavidad vacía de pared tensa.", 0),
    ]),
    ("h2", "Ruidos agregados (adventicios)"),
    ("bullets", [
        ("Roncus", None, "Ruido continuo, grave, ronco, en ambos tiempos respiratorios por secreciones viscosas en vías aéreas mayores; se modifica o limpia tras la tos.", 0),
        ("Sibilancias", None, "Ruido continuo, agudo y musical por broncoespasmo y estenosis de la vía aérea de pequeño calibre; predomina al final de la espiración.", 0),
        ("Estertores crepitantes", None, "Ruidos breves, discontinuos, homogéneos y finos generados por el despegamiento alveolar húmedo en el pico de la inspiración; inmodificables con la tos.", 0),
        ("Estertores de burbuja (húmedos)", None, "Ruidos heterogéneos generados por paso de aire en medio líquido traqueobronquial (gruesa, mediana o fina burbuja); abarcan inspiración y espiración y se modifican activamente con la tos.", 0),
        ("Frotes pleurales", None, "Crujido superficial bifásico semejante a fricción de cuero seco; generado por contacto entre hojas pleurales inflamadas; no se alteran con la tos y aumentan su intensidad al presionar el estetoscopio.", 0),
    ]),
    ("h2", "Auscultación de la voz y tos"),
    ("bullets", [
        ("Broncofonía", None, "Resonancia vocal aumentada sin discernimiento de las sílabas.", 0),
        ("Pectoriloquia", None, "Transmisión nítida, precisa y articulada de las palabras habladas.", 0),
        ("Pectoriloquia áfona", None, "Percepción clara de palabras emitidas en voz susurrada o cuchicheada.", 0),
        ("Egofonía (voz caprina)", None, "Transmisión temblorosa, nasal y entrecortada en borde superior de colecciones pleurales líquidas.", 0),
        ("Respuesta a la tos", None, "Provoca movilización o desaparición de ruidos húmedos/roncus y desencadena soplos cavernosos o anfóricos.", 0),
    ]),
]

APPENDIX_NOTES = [
    "Correspondencia Fig. 3-2 / 3-4: el texto base agrupa «tórax en quilla (pectus carinatum / piriforme)». En los epígrafes originales, la Fig. 3-2 es el tórax de pollo (en quilla) y la Fig. 3-4 el tórax piriforme; ambas láminas se reproducen con su título original para no forzar la correspondencia.",
    "La Fig. 3-8 se separó en dos recortes (3-8A y 3-8B) porque el texto base las cita por separado; en el libro forman una única figura con dos paneles (p. 13).",
    "La Fig. 3-30 es, en el original, un detalle cercano de manos en percusión digito-digital (sin vista completa del tórax); se recortó tal como está impresa.",
    "Método de extracción: render directo de cada página del PDF adjunto con clip a 300 dpi (PyMuPDF), limpieza a escala de grises con nivel de blancos y recorte de márgenes (Pillow). No se redibujó ni se generó ninguna imagen. Coordenadas y tamaños de cada recorte: véase figuras-manifiesto.csv.",
    "Fuente: PDF adjunto «semiotecnia del torax.pdf» (14 páginas; capítulo 3, pp. 9-21 del libro; la p. 14 del PDF está en blanco). Los números de página citados en cada epígrafe indican primero la página del PDF y luego la página impresa del libro.",
]
