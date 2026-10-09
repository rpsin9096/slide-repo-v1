# -*- coding: utf-8 -*-
"""Deck StudyDeck v2 (motor v3) — Tema 3: Glomerulonefritis Crónica.

Anatomía Patológica · UCP · Grupo 3 (Pregrado Médico).
Caso clínico: varón de 52 años con glomerulonefritis crónica terminal
(riñón contraído, esclerosis glomerular y fibrosis intersticial).

Estructura de 10 diapositivas según la Guía de Apoyo Visual, con guion del
orador en GUION_DEL_ORADOR.md. Idioma es-ES, paleta UCP, WCAG AA.
Imágenes locales en imgs/ como apoyo visual (esquemas didácticos generados
para esta presentación).
"""

COURSE_INFO = {'course': 'Anatomía Patológica', 'institution': 'UCP',
               'author': 'Grupo 3 — Pregrado Médico'}

CONFIG = {
    'PALETTE': 'ucp',
    'LANG': 'es-ES',
    'PROFILE': 'lecture',
    'IMAGES': {'mode': 'web-only', 'max_n': 4,
               'allow_ai': False, 'allow_placeholder': False},
    'SHOW_FOOTER': True,
    'SHOW_SLIDE_NUMBER': True,
    'ALLOW_TERMS': [],
}

SLIDES = [
    # 1 — Portada
    {'module': 'title',
     'title': 'Glomerulonefritis crónica terminal: del daño inmunológico al '
              'riñón contraído',
     'subtitle': 'Discusión anatomoclínica, correlación fisiopatológica e '
                 'integración histopatológica',
     'course': 'Anatomía Patológica · Tema 3', 'institution': 'UCP',
     'author': 'Grupo 3 · Pregrado Médico'},

    # 2 — Presentación del caso clínico (línea de tiempo)
    {'module': 'timeline',
     'kicker': 'Anamnesis', 'title': 'Veintiséis años de historia natural',
     'milestones': [
         {'label': '26 años', 'title': 'Brote nefrítico inicial',
          'desc': 'Hematuria macroscópica post-faringitis repetida; nunca '
                  'biopsiada ni tratada.'},
         {'label': '47 años', 'title': 'Hipertensión arterial',
          'desc': 'Pauta irregular desde hace 5 años; la sobrecarga presora '
                  'aceleró el colapso hemodinámico de las nefronas.'},
         {'label': '52 años (actual)', 'title': 'Síndrome urémico',
          'desc': 'Astenia, náuseas matutinas, prurito, nicturia y edemas en '
                  'miembros inferiores.'}],
     'footnote': 'Varón de 52 años, albañil, con 8 meses de evolución y '
                 'pérdida de 4 kg no voluntaria.'},

    # 3 — Estudios complementarios y diagnóstico funcional
    # (checklist: panel de verificación de los estudios realizados; el módulo
    #  stat_card con imagen solapa el panel del dato 0,80 in — verificado en
    #  el .pptx — y el fixture del motor no cubre stat_card con imagen)
    {'module': 'checklist',
     'kicker': 'Función renal',
     'title': 'Estudios complementarios: uremia terminal',
     'items': [
         {'label': 'TFGe 11 mL/min/1,73 m²',
          'desc': 'ERC estadio 5 (terminal): urea 142 mg/dL y creatinina 5,8 '
                  'mg/dL.'},
         {'label': 'Anemia normocítica',
          'desc': 'Hemoglobina 8,9 g/dL por déficit de eritropoyetina; calcio '
                  '7,8 y fósforo 6,4 mg/dL.'},
         {'label': 'Sedimento de orina',
          'desc': 'Proteinuria 1,8 g/24 h con cilindros céreos anchos y '
                  'hematíes dismórficos.'},
         {'label': 'Ecografía bilateral',
          'desc': 'Riñones simétricos de 7,5-7,8 cm, hiperecogénicos, con '
                  'corteza < 3 mm.'}],
     'image': 'imgs/eco_rinon_contraido.png',
     'caption': 'Riñón pequeño e hiperecogénico con corteza milimétrica: el '
                'patrón ecográfico del estadio terminal.',
     'credit': 'Ilustración generada para esta presentación (esquema '
               'didáctico)',
     'footnote': 'Nefrectomía bilateral previa al trasplante; la pieza se '
                 'envía a estudio histopatológico.'},

    # 4 — Estudio macroscópico
    {'module': 'figure',
     'kicker': 'Estudio macroscópico', 'title': 'El riñón contraído',
     'image': 'imgs/macro_rinon_contraido.png',
     'caption': 'Corte coronal: superficie finamente granular, corteza de '
                '2-3 mm y vasos arcuatos rígidos entreabiertos.',
     'credit': 'Ilustración generada para esta presentación (esquema '
               'didáctico)',
     'footnote': 'Caso: 7,8 cm y 70 g frente a valores normales (12 cm y '
                 '120-150 g) — reducción simétrica que confirma la lesión '
                 'crónica terminal.'},

    # 5 — Estudio microscópico
    {'module': 'figure',
     'kicker': 'Estudio microscópico', 'title': 'Esclerosis, atrofia y fibrosis',
     'image': 'imgs/micro_panel_triada.png',
     'caption': 'Tríada de la etapa terminal: obsolescencia glomerular, '
                'fibrosis intersticial masiva y tiroidización tubular.',
     'credit': 'Ilustración generada para esta presentación (esquema '
               'didáctico)',
     'footnote': 'Tinciones H&E, PAS y tricrómico de Masson · > 85% de '
                 'glomérulos con esclerosis global.'},

    # 6 — Patogenia y fisiopatología (modelo de Brenner)
    {'module': 'flow_diagram',
     'kicker': 'Fisiopatología',
     'title': 'Hiperfiltración de Brenner: vía final común',
     'steps': [
         {'label': '1', 'title': 'Injuria inmunológica',
          'desc': 'Los depósitos inmunes de la juventud destruyen nefronas; '
                  'la inflamación primaria cede sin control etiológico.'},
         {'label': '2', 'title': 'Sobrecarga adaptativa',
          'desc': 'Las nefronas residuales hipertrofian y dilatan la '
                  'arteriola aferente para sostener la filtración global.'},
         {'label': '3', 'title': 'Barotrauma glomerular', 'highlight': True,
          'desc': 'La hipertensión intraglomerular crónica daña podocitos y '
                  'endotelio por estrés mecánico sostenido.'},
         {'label': '4', 'title': 'Fibrosis terminal',
          'desc': 'TGF-β y endotelina-1 inducen matriz colágena '
                  'descontrolada; la isquemia posglomerular atrofia los '
                  'túbulos.'}],
     'explanation': 'La glomerulonefritis crónica es el punto terminal '
                    'convergente de glomerulopatías primarias no resueltas: '
                    'la pérdida crítica de masa nefronal desencadena '
                    'hiperfiltración compensatoria, hipertensión '
                    'intraglomerular y fibrosis irreversible.',
     'footnote': 'Modelo de Brenner de progresión renal · > 85% de '
                 'obsolescencia glomerular en la pieza.'},

    # 7 — Correlación clínico-patológica
    {'module': 'side_by_side',
     'kicker': 'Correlación clínico-patológica',
     'title': 'Del sustrato tisular a la clínica',
     'left_card': {'header': 'HISTOPATOLOGÍA', 'title': 'Sustrato tisular',
                   'points': [
                       'Obsolescencia glomerular global: > 85% de penachos '
                       'en esferas hialinas acelulares.',
                       'Fibrosis intersticial masiva con pérdida de células '
                       'productoras de eritropoyetina.',
                       'La arteriolosclerosis hialina estrecha la luz '
                       'vascular; determina isquemia posglomerular y '
                       'liberación desregulada de renina.',
                       'Atrofia tubular con tiroidización y pérdida del '
                       'gradiente osmótico medular.']},
     'right_card': {'header': 'MANIFESTACIÓN', 'title': 'Expresión clínica',
                    'points': [
                        'Retención de urea (142 mg/dL) y creatinina '
                        '(5,8 mg/dL): náuseas, astenia y prurito.',
                        'Anemia normocítica normocrómica Hb 8,9 g/dL por '
                        'déficit de eritropoyetina.',
                        'Eje renina-angiotensina-aldosterona hiperactivado: '
                        'hipertensión y edemas maleolares.',
                        'Isostenuria por pérdida del gradiente medular: '
                        'nicturia de 3-4 episodios por noche.']},
     'footnote': 'Cada línea del informe anatomopatológico explica un rasgo '
                 'clínico del paciente.'},

    # 8 — Diagnóstico diferencial
    {'module': 'comparison_table',
     'kicker': 'Diagnóstico diferencial',
     'title': 'Riñón terminal: cuatro entidades',
     'headers': ['Entidad', 'Tamaño renal', 'Hallazgo decisivo',
                 'Dato clave de la historia'],
     'col_widths': [2.1, 1.9, 2.9, 2.6],
     'rows': [
         ['Glomerulonefritis crónica (caso)',
          'Pequeños y simétricos (7,8 cm)',
          'Esclerosis glomerular global masiva (> 85%) y superficie finamente '
          'granular',
          'Hematuria macroscópica post-faringitis a los 26 años'],
         ['Nefroesclerosis hipertensiva benigna',
          'Simétricos, menos atróficos',
          'Hialinosis arteriolar concéntrica predominante; esclerosis '
          'glomerular secundaria',
          'Sin antecedentes de síndrome nefrítico juvenil'],
         ['Pielonefritis crónica',
          'Asimétricos con retracciones',
          'Cicatrices corticales en U y cálices deformados (cáliz en clava)',
          'Antecedentes de litiasis o reflujo vesicoureteral'],
         ['Nefropatía diabética avanzada',
          'Normales o aumentados',
          'Nódulos de Kimmelstiel-Wilson PAS-positivos en el penacho capilar',
          'Diabetes mellitus de larga evolución']],
     'takeaway': 'La atrofia simétrica con esclerosis glomerular global y el '
                 'antecedente nefrítico juvenil definen el caso.'},

    # 9 — Diagnóstico final e implicancias clínico-terapéuticas
    {'module': 'pyramid',
     'kicker': 'Diagnóstico definitivo',
     'title': 'Glomerulonefritis crónica terminal',
     'levels': [
         {'title': 'Terapia sustitutiva renal urgente',
          'desc': 'Hemodiálisis trisemanal o diálisis peritoneal inmediata.'},
         {'title': 'Control integral del riesgo',
          'desc': 'Tensión arterial estricta, quelantes de fósforo y análogos '
                  'de eritropoyetina.'},
         {'title': 'Trasplante renal', 'highlight': True,
          'desc': 'Única terapéutica curativa definitiva.'}],
     'footnote': 'ERC G5 irreversible: > 85% de obsolescencia glomerular '
                 'contraindica la inmunosupresión e impone terapia de '
                 'sustitución renal inmediata.'},

    # 10 — Conclusiones de aprendizaje
    {'module': 'concept_map',
     'kicker': 'Conclusiones', 'title': 'Lo que este caso enseña',
     'hub': 'Riñón contraído terminal',
     'nodes': [
         {'title': 'Morfología',
          'desc': 'Riñón pálido, simétrico y finamente granular: 7,8 cm y '
                  '70 g.'},
         {'title': 'Tríada histológica',
          'desc': 'Esclerosis global + atrofia con tiroidización + fibrosis '
                  'colágena.'},
         {'title': 'Hiperfiltración',
          'desc': 'Pérdida de nefronas, hipertensión intraglomerular y '
                  'fibrosis por TGF-β.'},
         {'title': 'Ventana terapéutica',
          'desc': 'Tratar la glomerulopatía antes de la fibrosis '
                  'irreversible.'}],
     'footnote': 'Diagnóstico precoz: la única estrategia que evita la '
                 'dependencia de diálisis.'},
]
