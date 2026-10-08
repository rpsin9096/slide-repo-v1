# -*- coding: utf-8 -*-
"""Actividad Integradora · Abdomen agudo inflamatorio · 12 diapositivas (es-ES).

Motor: StudyDeck v2 (UCP-only). Sin nombres de docentes ni de cátedras en la carátula.
Las dos figuras originales (macroscopía y H&E del Caso Clínico 09) NO están en el
workspace: se marcan como MARCADOR (placeholder) hasta que se reinserten.
"""

COURSE_INFO = {'course': 'Universidad Central del Paraguay (UCP) · Carrera de Medicina',
               'institution': '',
               'author': ''}

CONFIG = {
    'PALETTE': 'ucp',
    'LANG': 'es-ES',
    'PROFILE': 'short',
    'IMAGES': {'mode': 'web-only', 'max_n': 'auto',
               'allow_ai': False, 'allow_placeholder': True},
    'SHOW_FOOTER': True,
    'SHOW_SLIDE_NUMBER': True,
    'ALLOW_TERMS': ['Atlanta', 'Opie', 'Wirsung', 'Vater', 'Oddi', 'Balthazar',
                    'PONCHO', 'Ringer', 'Dipirona', 'Tramadol', 'Cullen', 'Grey-Turner',
                    'Vancouver', 'Gut', 'Lancet', 'Robbins', 'Goodman', 'Gilman', 'H&E'],
}

SLIDES = [
    # 1 · Carátula (sin nombres de docentes ni de cátedras)
    {'module': 'title',
     'title': 'Pancreatitis Aguda Edematosa Intersticial de Origen Biliar',
     'subtitle': 'Abdomen Agudo Inflamatorio · Actividad Integradora · 5.º Semestre · Sección E',
     'course': 'Universidad Central del Paraguay (UCP) · Carrera de Medicina',
     'institution': '',
     'author': ''},

    # 2 · Nómina oficial del grupo y distribución
    {'module': 'comparison_table',
     'kicker': 'Organización del grupo',
     'title': 'Nómina oficial del grupo y distribución',
     'headers': ['Rol', 'Diapositivas', 'Contenido a cargo'],
     'col_widths': [1.3, 1.1, 2.6],
     'rows': [['Relator 1', '3–4', 'Apertura, anamnesis y diagnóstico'],
              ['Relator 2', '5–6', 'Mecanismos fisiopatológicos y clínica'],
              ['Relator 3', '7–9', 'Correlación macroscópica, histopatológica e imagenológica'],
              ['Relator 4', '10–12', 'Abordaje terapéutico, prevención y síntesis']],
     'takeaway': 'Relatoría principal: 10 minutos. Bancada de sustentación (sabatina): 5 minutos.',
     'footnote': 'Sabatina: alumnos 05 a 10 en los frentes de Farmacología, Semiología, '
                 'Fisiopatología, Imagenología, Medicina Familiar y Patología.'},

    # 3 · Presentación del caso clínico (historia clínica inmutable)
    {'module': 'case_block',
     'kicker': 'Caso clínico',
     'title': 'Presentación del caso: historia clínica inmutable',
     'case_stem': 'Paciente femenina de 38 años con enfermedad vesicular de larga evolución y '
                  'cólicos biliares a repetición. Cuadro actual: dolor abdominal súbito, constante '
                  'y de intensidad severa en epigastrio y mesogastrio.',
     'findings': ['Hipersensibilidad marcada a la palpación en hemiabdomen superior',
                  'Ruidos hidroaéreos marcadamente disminuidos (íleo paralítico reflejo)'],
     'reasoning': 'Antecedente litiásico, dolor epigástrico súbito y severo, e íleo reflejo '
                  'orientan a una pancreatitis aguda de origen biliar.',
     'diagnosis': 'Pancreatitis aguda de origen biliar',
     'clinical_pearl': 'La correlación de antecedente litiásico, dolor típico y lipasa elevada '
                       'cierra la etiología biliar.'},

    # 4 · Orientación diagnóstica y criterios de Atlanta
    {'module': 'checklist',
     'kicker': 'Orientación diagnóstica',
     'title': 'Criterios de Atlanta: cumple 3 de 3 (basta 2)',
     'items': [
         {'label': 'Clínica',
          'desc': 'Dolor abdominal agudo típico en hemiabdomen superior con irradiación posterior.'},
         {'label': 'Laboratorio',
          'desc': 'Lipasa sérica > 3 veces el límite superior normal: elevación patológica marcada.'},
         {'label': 'Imagen',
          'desc': 'TC simple o contrastada con tumefacción glandular e hipodensidad líquida peripancreática.'}],
     'footnote': 'Dx definitivo: pancreatitis aguda edematosa intersticial litiásica. Diferenciales: '
                 'úlcera perforada, colecistitis, obstrucción.'},

    # 5 · Etiopatogenia y mecanismo oclusivo biliar
    {'module': 'flow_diagram',
     'kicker': 'Etiopatogenia',
     'title': 'Mecanismo oclusivo biliar',
     'steps': [
         {'label': '1', 'title': 'Génesis',
          'desc': 'Migración de microcálculos desde la vesícula biliar a través del conducto cístico.'},
         {'label': '2', 'title': 'Canal común (Opie)', 'highlight': True,
          'desc': 'Impactación litiásica transitoria en la ampolla de Vater y el esfínter de Oddi.'},
         {'label': '3', 'title': 'Hipertensión ductal retrógrada',
          'desc': 'Obstrucción del conducto de Wirsung: estasis de secreción rica en zimógenos e '
                  'hiperpresión intraductal.'}]},

    # 6 · Cascada fisiopatológica intracelular e inflamación
    {'module': 'flow_diagram',
     'kicker': 'Fisiopatología',
     'title': 'Cascada intracelular e inflamación',
     'steps': [
         {'label': '1', 'title': 'Pérdida de compartimentación',
          'desc': 'Colocalización anómala de gránulos de zimógeno y enzimas lisosomales en el acino.'},
         {'label': '2', 'title': 'Activación por catepsina B', 'highlight': True,
          'desc': 'Hidrólisis prematura del tripsinógeno en tripsina activa intracelular.'},
         {'label': '3', 'title': 'Autodigestión tisular',
          'desc': 'Fosfolipasa A2 lisa membranas; elastasa degrada fibras elásticas; lipasa digiere '
                  'triglicéridos retroperitoneales.'},
         {'label': '4', 'title': 'Respuesta inflamatoria',
          'desc': 'TNF-α, IL-1, IL-6 e histamina aumentan la permeabilidad capilar y secuestran '
                  'líquido en el tercer espacio.'}]},

    # 7 · Correlación macroscópica (pieza quirúrgica) — IMAGEN PENDIENTE
    {'module': 'figure',
     'kicker': 'Macroscopía',
     'title': 'Correlación macroscópica: pieza quirúrgica',
     'image': 'placeholder:Macroscopía del Caso Clínico 09 (archivo original pendiente de reinserción)',
     'caption': 'Edema pálido pancreático con placas en "gotas de vela" en grasa peripancreática: esteatonecrosis.',
     'credit': 'Fuente: Caso Clínico 09 (UCP), archivo original. Pendiente de reinserción.',
     'footnote': 'Flecha 1: aumento volumétrico y edema pálido. Flecha 2: placas blanquecinas '
                 'en grasa. Sin necrosis masiva ni hemorragia.'},

    # 8 · Estudio histopatológico (H&E) — IMAGEN PENDIENTE
    {'module': 'figure',
     'kicker': 'Histopatología',
     'title': 'Estudio histopatológico (H&E): saponificación',
     'image': 'placeholder:Microscopía H&E del Caso Clínico 09 (archivo original pendiente de reinserción)',
     'caption': 'Adipocitos fantasma con sales cálcicas y neutrófilos en septos: esteatonecrosis aguda.',
     'credit': 'Fuente: Caso Clínico 09 (UCP), archivo original. Pendiente de reinserción.',
     'footnote': 'Fantasmas de adipocitos anucleados con material basófilo amorfo; congestión e '
                 'infiltrado neutrofílico en septos interlobulillares.'},

    # 9 · Evaluación por imagenología y criterios anatómicos
    {'module': 'comparison_table',
     'kicker': 'Imagenología',
     'title': 'Evaluación por imagen y criterios anatómicos',
     'headers': ['Método', 'Hallazgo o indicación', 'Valor en el caso'],
     'col_widths': [1.3, 2.4, 1.7],
     'rows': [['Radiografía simple', 'Sin gas libre subdiafragmático; edema retroperitoneal y asa centinela',
               'Descarta perforación gastroduodenal'],
              ['TC contrastada', 'Indicada a las 72–96 h del inicio; atenuación homogénea y colecciones agudas',
               'Balthazar C/D sin necrosis parenquimatosa'],
              ['Ecografía abdominal', 'Imágenes hiperecogénicas móviles con sombra acústica posterior limpia',
               'Identifica litiasis vesicular']],
     'takeaway': 'La TC a las 72–96 h evita subestimar la necrosis: aquí la forma es edematosa.'},

    # 10 · Protocolo terapéutico y conducta hospitalaria
    {'module': 'checklist',
     'kicker': 'Tratamiento',
     'title': 'Protocolo terapéutico y conducta hospitalaria',
     'items': [
         {'label': 'Reanimación volémica',
          'desc': 'Ringer lactato 250–500 mL/h inicial, dirigido por metas (PAM, hematocrito, diuresis '
                  '> 0,5 mL/kg/h). Menos acidosis hiperclorémica que el SF 0,9 %.'},
         {'label': 'Descompresión gástrica',
          'desc': 'Sonda nasogástrica ante gastroparesia refractaria, distensión masiva o íleo paralítico.'},
         {'label': 'Manejo del dolor',
          'desc': 'Dipirona magnésica IV 1–2 g c/6–8 h (base); tramadol IV 50–100 mg c/8 h (rescate). '
                  'Evitar morfina: induce espasmo del esfínter de Oddi.'},
         {'label': 'Antibioticoterapia',
          'desc': 'Profilaxis antimicrobiana de rutina prohibida en formas edematosas intersticiales.'}]},

    # 11 · Prevención secundaria y enfoque en APS
    {'module': 'timeline',
     'kicker': 'Prevención secundaria',
     'title': 'Colecistectomía y seguimiento en atención primaria',
     'milestones': [
         {'label': 'Misma internación', 'title': 'Colecistectomía laparoscópica',
          'desc': 'Al remitir la clínica aguda (PONCHO). Evita la recidiva biliar: 30 % a 90 días sin cirugía.'},
         {'label': '4–6 semanas', 'title': 'Vigilancia posalta',
          'desc': 'Control de posible formación de pseudoquistes pancreáticos.'},
         {'label': 'APS', 'title': 'Prevención primaria',
          'desc': 'Ecografía ante litiasis sintomática; control de obesidad, dislipidemia y dietas hipercalóricas.'}],
     'footnote': 'APS: atención primaria de la salud.'},

    # 12 · Referencias bibliográficas (Vancouver)
    {'module': 'references',
     'kicker': 'Bibliografía',
     'title': 'Referencias bibliográficas (Vancouver)',
     'refs': [
         'Banks PA, et al. Classification of acute pancreatitis—2012: revision of the Atlanta classification and definitions. Gut. 2013;62(1):102-111.',
         'Tenner S, et al. American College of Gastroenterology Guideline: Management of Acute Pancreatitis. Am J Gastroenterol. 2024;119(3):419-437.',
         'da Costa DW, et al. Same-admission versus delayed cholecystectomy for mild gallstone pancreatitis (PONCHO). Lancet. 2015;386(10000):1261-1268.',
         'Kumar V, Abbas AK, Aster JC. Robbins y Cotran: Patología Estructural y Funcional. 10.ª ed. Elsevier; 2021.',
         'Brunton LL, Hilal-Dandan R, Knollmann BC. Goodman & Gilman: Las Bases Farmacológicas de la Terapéutica. 13.ª ed. McGraw-Hill; 2019.',
         'Argente HA, Álvarez ME. Semiología Médica: Fisiopatología, Semiotecnia y Propedéutica. 3.ª ed. Médica Panamericana; 2021.'],
     'footnote': 'Títulos abreviados por espacio; citas completas en el PDF adjunto.'},
]
