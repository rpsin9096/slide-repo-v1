# -*- coding: utf-8 -*-
"""Seminario Integrador · Caso Clínico 09: Abdomen Agudo de Origen Pancreatobiliar
12 diapositivas + anexos de sabatina · español médico · 10 min + 5 min.

Motor: StudyDeck v2, paleta UCP, Montserrat.
ESTRATEGIA: módulos nativos del motor cargan TODO el texto teórico; las
imágenes son sólo apoyo visual (esquema ampolar, macro, hematoxilina-eosina,
gráfico de lipasa). Los anexos para la sabatina llevan los esquemas complejos
(colocalización acinar, vía del dolor, ecografía, Ringer versus solución
fisiológica, histología comparativa).

Todas las abreviaturas se escriben por extenso la primera vez; luego se puede
utilizar el término completo o la sigla ya explicada.
"""

COURSE_INFO = {'course': 'Carrera de Medicina',
               'institution': 'Universidad Central del Paraguay (UCP)',
               'author': ''}

CONFIG = {
    'PALETTE': 'ucp',
    'LANG': 'es-ES',
    'PROFILE': 'short',
    'IMAGES': {'mode': 'mixed', 'max_n': 10,
               'allow_ai': False, 'allow_placeholder': True},
    'SHOW_FOOTER': True,
    'SHOW_SLIDE_NUMBER': True,
    'ALLOW_TERMS': ['Atlanta', 'Balthazar', 'Opie', 'Wirsung', 'Vater', 'Oddi',
                    'SPINK1', 'Ringer', 'Tramadol', 'Ondansetrón', 'Omeprazol',
                    'Jobert', 'PONCHO', 'Vancouver', 'Robbins', 'Harrison',
                    'Argente', 'Goodman', 'Gilman', 'hematoxilina-eosina',
                    'lipasa', 'amilasa', 'Auerbach', 'zimógeno', 'catepsina'],
}

SLIDES = [

    # 1
    {'module': 'title',
     'title': 'Caso Clínico 09: Abdomen Agudo de Origen Pancreatobiliar',
     'subtitle': 'Seminario Integrador · Quinto Semestre',
     'course': 'Universidad Central del Paraguay — Centro Tecnológico I',
     'institution': 'Ciudad del Este, Paraguay · 2026',
     'author': ''},

    # 2
    {'module': 'comparison_table',
     'kicker': 'Equipo',
     'title': 'Nómina de integrantes',
     'headers': ['Participación', 'Integrante', 'Matrícula'],
     'col_widths': [1.5, 2.5, 1.2],
     'rows': [['Relator uno', '[Apellidos, nombres]', '[Número de matrícula]'],
              ['Relator dos', '[Apellidos, nombres]', '[Número de matrícula]'],
              ['Relator tres', '[Apellidos, nombres]', '[Número de matrícula]'],
              ['Relator cuatro', '[Apellidos, nombres]', '[Número de matrícula]']],
     'takeaway': 'Cuatro relatores en tribuna (diez minutos); bancada de '
                 'sustentación para la sabatina (cinco minutos).',
     'footnote': 'Completar los diez a doce integrantes en orden alfabético antes de la defensa.'},

    # 3 — Historia clínica (case_block)
    {'module': 'case_block',
     'kicker': 'Caso clínico',
     'title': 'Historia clínica inmutable',
     'case_stem': 'Mujer de treinta y ocho años con colelitiasis de larga data que '
                  'ingresa por dolor brusco, constante y severo en epigastrio.',
     'findings': ['Hipersensibilidad marcada en hemiabdomen superior',
                  'Ruidos hidroaéreos disminuidos (íleo paralítico reflejo)',
                  'Lipasa elevada; sin neumoperitoneo; tomografía con edema '
                  'peripancreático'],
     'reasoning': 'Antecedente litiásico más dolor típico más lipasa elevada más '
                  'hallazgos imagenológicos orientan a pancreatitis biliar.',
     'diagnosis': 'Pancreatitis aguda litiásica',
     'clinical_pearl': 'La tríada litiásica más dolor en cinturón más lipasa por '
                       'encima de tres veces lo normal cierra la etiología biliar.'},

    # 4 — Criterios Atlanta + diferenciales
    {'module': 'checklist',
     'kicker': 'Juicio clínico',
     'title': 'Criterios Atlanta 2012: tres de tres cumplidos',
     'items': [
         {'label': 'Clínica',
          'desc': 'Dolor agudo típico en epigastrio y mesogastrio con irradiación '
                  'dorsal en cinturón.'},
         {'label': 'Laboratorio',
          'desc': 'Lipasa sérica por encima de tres veces el límite superior normal '
                  '(elevada entre siete y catorce días; ventana diagnóstica más '
                  'amplia que la amilasa).'},
         {'label': 'Imagen',
          'desc': 'Tomografía con tumefacción glandular, colecciones líquidas y '
                  'densificación de la grasa peripancreática (grado Balthazar C-D).'},
         {'label': 'Exclusiones',
          'desc': 'Signo de Jobert negativo; Murphy no focal; electrocardiograma y '
                  'troponinas normales que descartan infarto.'}],
     'footnote': 'Diagnóstico definitivo: pancreatitis aguda edematosa intersticial litiásica.'},

    # 5 — Macro (foto real)
    {'module': 'figure',
     'kicker': 'Macroscopía',
     'title': 'Hallazgos macroscópicos de la pieza quirúrgica',
     'image': 'assets/panel_05_macro.png',
     'caption': 'Glándula tumefacta: congestión y petequias, y esteatonecrosis '
                'peripancreática en «gotas de cera».',
     'credit': 'Fotografía macroscópica del Caso 09 (Carrera de Medicina, UCP).',
     'footnote': 'Clasificación Atlanta 2012: forma edematosa intersticial (grado '
                 'Balthazar C-D), sin necrosis hemorrágica.'},

    # 6 — Hematoxilina-eosina (foto real)
    {'module': 'figure',
     'kicker': 'Histopatología (H y E)',
     'title': 'Esteatonecrosis con saponificación cálcica',
     'image': 'assets/panel_06_histo.png',
     'caption': '① Adipocitos «fantasma»; ② necrosis acinar yuxtapuesta; '
                '③ neutrófilos y calcio basófilo.',
     'credit': 'Micrografía en hematoxilina y eosina del Caso 09 (Carrera de Medicina, UCP).',
     'footnote': 'Los depósitos basófilos son jabones cálcicos insolubles formados '
                 'sobre ácidos grasos libres.'},

    # 7 — Cascada fisiopatológica (definition con imagen ampolar + 3 tarjetas)
    {'module': 'definition',
     'kicker': 'Fisiopatología',
     'title': 'Cascada etiopatogénica',
     'main_statement': 'Un microcálculo en la ampolla de Vater eleva la presión '
                       'retrógrada en el conducto de Wirsung y activa de forma '
                       'prematura el tripsinógeno dentro del acino.',
     'elaboration': 'La activación enzimática intracelular explica tanto la morfología '
                    'macroscópica como el patrón de lesión histológica.',
     'key_points': [
         {'title': '① Bloqueo ampolar (hipótesis de Opie)',
          'desc': 'Impactación litiásica transitoria; hipertensión retrógrada y '
                  'reflujo biliar dentro del conducto pancreático.'},
         {'title': '② Fusión y colocalización zimógeno-lisosoma',
          'desc': 'En vacuolas ácidas, la catepsina B escinde el tripsinógeno en '
                  'tripsina activa (el inhibidor SPINK1 es rebasado).'},
         {'title': '③ Autodigestión tisular',
          'desc': 'La elastasa produce congestión y petequias; la fosfolipasa A '
                  'subíndice dos produce necrosis acinar; la lipasa produce saponificación.'}],
     'image': 'assets/esquema_obstruccion_ampular.png',
     'caption': 'Microcálculo impactado en la ampolla: el conducto de Wirsung queda '
                'obstruido y eleva su presión.',
     'credit': 'Esquema anatómico; la colocalización acinar se detalla en el anexo.',
     'footnote': 'La tripsina activa es el gatillo común de las tres lesiones enzimáticas.'},

    # 8 — Semiología (flow_diagram de la vía)
    {'module': 'flow_diagram',
     'kicker': 'Semiología',
     'title': 'Vía del dolor y correlación clínica',
     'steps': [
         {'label': '1', 'title': 'Distensión pancreática',
          'desc': 'El edema y el estrés capsular activan los nociceptores viscerales.'},
         {'label': '2', 'title': 'Fibras A delta y C esplácnicas', 'highlight': True,
          'desc': 'Aferencias viscerales que conducen al plexo celíaco.'},
         {'label': '3', 'title': 'Plexo celíaco y segmentos T5 a T9',
          'desc': 'Asta dorsal medular; vía espinotalámica hasta el tálamo.'},
         {'label': '4', 'title': 'Dolor en cinturón',
          'desc': 'Epigastrio y mesogastrio con irradiación dorsal metamérica.'}],
     'explanation': 'El peritonismo químico en la transcavidad de los epiplones '
                    '(hipersensibilidad en hemiabdomen superior) y el íleo paralítico '
                    'reflejo por inhibición del plexo mientérico de Auerbach (ruidos '
                    'hidroaéreos disminuidos) completan la tríada semiológica del caso.',
     'footnote': 'Los ruidos disminuidos indican íleo paralítico reflejo, no una oclusión mecánica.'},

    # 9 — Biomarcadores e Imagen
    {'module': 'comparison_table',
     'kicker': 'Diagnóstico',
     'title': 'Biomarcadores y evaluación imagenológica',
     'headers': ['Método', 'Hallazgo en el caso', 'Lectura clínica'],
     'col_widths': [1.4, 2.4, 1.9],
     'rows': [
         ['Lipasa sérica',
          'Mayor de tres veces el límite superior normal; sensibilidad 95 por '
          'ciento y especificidad 99 por ciento; elevada entre siete y catorce días.',
          'Confirma la pancreatitis aguda según Atlanta 2012.'],
         ['Ecografía vesicular',
          'Imagen hiperecogénica móvil con sombra acústica posterior limpia.',
          'Identifica la litiasis como causa etiológica.'],
         ['Radiografía simple de abdomen',
          'Signo de Jobert negativo; borramiento del psoas; asa centinela y gas difuso.',
          'Descarta perforación; orienta a edema retroperitoneal e íleo.'],
         ['Tomografía con contraste',
          'Glándula aumentada de tamaño; líquido y densidad grasa peripancreáticos; '
          'sin necrosis por encima de 30 por ciento.',
          'Grado Balthazar C-D (edematosa); guía el manejo.']],
     'takeaway': 'La lipasa confirma; la ecografía identifica la causa; la '
                 'radiografía descarta perforación; la tomografía estratifica.',
     'footnote': 'El gráfico con los valores de sensibilidad y especificidad de lipasa y '
                 'amilasa se presenta en el anexo de diagnóstico.'},

    # 10 — Farmacología
    {'module': 'comparison_table',
     'kicker': 'Tratamiento',
     'title': 'Soporte farmacológico y medidas en sala',
     'headers': ['Recurso', 'Mecanismo', 'Pauta', 'Reacciones adversas y matices'],
     'col_widths': [1.4, 1.85, 1.55, 1.7],
     'rows': [
         ['Ringer lactato',
          'Cristaloide balanceado (109 miliequivalentes por litro de cloruro); el '
          'lactato se transforma en bicarbonato en el hígado y evita la acidosis '
          'hiperclorémica.',
          'Doscientos a doscientos cincuenta mililitros por hora; bolo de diez '
          'a veinte por kilo si inestabilidad; orina sobre 0,5 mililitros por '
          'kilo cada hora.',
          'Sobrecarga volumétrica; vigilar el potasio si existe insuficiencia renal.'],
         ['Tramadol (con rescate de fentanilo)',
          'Agonista del receptor opioide mu más inhibición de la recaptación de '
          'noradrenalina y serotonina; ofrece analgesia sin espasmo franco del '
          'esfínter de Oddi.',
          'Tramadol: cincuenta a cien miligramos en vena cada seis u ocho horas '
          '(cuatrocientos al día); fentanilo: uno o dos microgramos por kilo '
          'si refractario.',
          'Náuseas, vómitos, sedación, mareo, estreñimiento.'],
         ['Ondansetrón más omeprazol',
          'Antiemesis por antagonismo del receptor de serotonina 5-HT subíndice '
          'tres; inhibición de la bomba H+/K+ ATPasa para gastroprotección.',
          'Ondansetrón: cuatro a ocho miligramos por vía intravenosa cada ocho '
          'horas; omeprazol: cuarenta miligramos por vía intravenosa al día.',
          'Cefalea, prolongación asintomática del intervalo QT; diarrea leve, '
          'malestar epigástrico.'],
         ['Sonda nasogástrica',
          'Descompresión mecánica por íleo paralítico con distensión refractaria; '
          'previene la broncoaspiración.',
          'No es de rutina; se indica sólo ante vómitos persistentes o estasis gástrica.',
          'Molestia faríngea; sinusitis si el uso se prolonga.']],
     'takeaway': 'La fluidoterapia agresiva con Ringer lactato en las primeras '
                 'veinticuatro horas es la piedra angular del tratamiento.',
     'footnote': 'El comparativo bioquímico entre Ringer lactato y solución fisiológica '
                 'al 0,9 por ciento se muestra en el anexo de farmacología.'},

    # 11
    {'module': 'algorithm',
     'kicker': 'Resolución',
     'title': 'Resolución definitiva y prevención de recurrencias',
     'steps': [
         {'label': '01', 'title': 'Colecistectomía laparoscópica precoz',
          'desc': 'Durante la misma internación tras la resolución; postergarla se '
                  'asocia con un 17 a 30 por ciento de recidiva (ensayo PONCHO, '
                  'Lancet 2015).'},
         {'label': '02', 'title': 'Colangiopancreatografía retrógrada endoscópica',
          'desc': 'En las primeras veinticuatro a cuarenta y ocho horas sólo ante '
                  'colangitis bacteriana, ictericia obstructiva progresiva o sepsis.'},
         {'label': '03', 'title': 'Prevención y seguimiento en atención primaria',
          'desc': 'Dieta hipolipídica, suspensión del alcohol; vigilancia ecográfica '
                  'a las cuatro a seis semanas para descartar pseudoquistes.'}],
     'footnote': 'Resolver la causa es prevenir recurrencias potencialmente letales.'},

    # 12
    {'module': 'references',
     'kicker': 'Bibliografía',
     'title': 'Referencias bibliográficas (estilo Vancouver)',
     'refs': [
         'Kumar V, Abbas AK, Aster JC. Robbins y Cotran: Patología estructural y '
         'funcional. Décima edición. Elsevier; 2021. Capítulo 19; páginas 953-968.',
         'Loscalzo J, et al. Harrison: Principios de medicina interna. Vigésima '
         'primera edición. McGraw-Hill; 2022. Capítulo 347; páginas 2515-2531.',
         'Argente HA, Álvarez ME. Semiología médica. Tercera edición. Médica '
         'Panamericana; 2021. Sección V; páginas 690-710.',
         'Brunton LL, et al. Goodman y Gilman: Bases farmacológicas de la '
         'terapéutica. Decimocuarta edición. McGraw-Hill; 2023. Sección II; '
         'páginas 385-410.',
         'da Costa DW, et al. Same-admission versus delayed cholecystectomy for '
         'mild gallstone pancreatitis (estudio PONCHO). Lancet. 2015;386:1261-1268.'],
     'footnote': 'Quedamos a disposición de la mesa examinadora para la sabatina.'},

    # ==================== ANEXOS (sabatina) ====================
    {'module': 'figure',
     'kicker': 'Anexo · Fisiopatología',
     'title': 'Colocalización acinar y activación del tripsinógeno',
     'image': 'assets/anexo_acino_colocalizacion.png',
     'caption': 'La catepsina B activa el tripsinógeno dentro de vacuolas ácidas, '
                'no en los gránulos de cimógeno.',
     'credit': 'Esquema didáctico; no es una imagen clínica.',
     'footnote': 'La activación prematura es el gatillo enzimático del daño tisular.'},

    {'module': 'figure',
     'kicker': 'Anexo · Fisiología del dolor',
     'title': 'Vía del dolor pancreático y proyección metamérica',
     'image': 'assets/anexo_via_dolor.png',
     'caption': 'Las aferencias A delta y C al plexo celíaco (T5 a T9) producen '
                'dolor en cinturón con irradiación dorsal.',
     'credit': 'Esquema didáctico; no es una imagen clínica.',
     'footnote': 'Apoya la explicación del patrón de irradiación dorsal.'},

    {'module': 'figure',
     'kicker': 'Anexo · Diagnóstico',
     'title': 'Cinética de lipasa y amilasa séricas',
     'image': 'assets/panel_09_lipasa.png',
     'caption': 'Lipasa 95/99 (7 a 14 días); amilasa 82/88 (48 a 72 horas), '
                'sensibilidad y especificidad.',
     'credit': 'Gráfico elaborado por el equipo.',
     'footnote': 'La ventana diagnóstica de la lipasa es mayor que la de la amilasa '
                 'debido a su vida media más prolongada.'},

    {'module': 'figure',
     'kicker': 'Anexo · Imagenología',
     'title': 'Ecografía vesicular: cálculo, barro y pólipo',
     'image': 'assets/ecografia_vesicular_esquema.png',
     'caption': 'El cálculo es hiperecogénico, móvil, con sombra acústica posterior; '
                'el pólipo es fijo y no produce sombra.',
     'credit': 'Esquema didáctico; no es una imagen clínica.',
     'footnote': 'El esquema aclara por qué la sombra acústica identifica una litiasis.'},

    {'module': 'figure',
     'kicker': 'Anexo · Farmacología',
     'title': 'Ringer lactato frente a solución fisiológica al 0,9 por ciento',
     'image': 'assets/anexo_ringer_vs_salina.png',
     'caption': 'La solución fisiológica favorece la acidosis; el Ringer lactato '
                'es la elección inicial.',
     'credit': 'Esquema didáctico; composiciones de referencia.',
     'footnote': 'La resucitación guiada por metas valora la diuresis, la presión '
                 'arterial media y el lactato sérico.'},

    {'module': 'figure',
     'kicker': 'Anexo · Anatomía patológica',
     'title': 'Pancreatitis edematosa frente a necrohemorrágica',
     'image': 'assets/anexo_histologia_comparativa.png',
     'caption': 'Edematosa (nuestro caso): acinos viables, esteatonecrosis focal; '
                'necrohemorrágica: destrucción y hemorragia.',
     'credit': 'Esquema comparativo; no es la lámina del Caso 09.',
     'footnote': 'La clasificación de Atlanta 2012 distingue claramente ambas formas.'},
]
