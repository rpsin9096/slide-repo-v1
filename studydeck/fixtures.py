# -*- coding: utf-8 -*-
"""FIXTURE DE SELF-TEST: un slide valido por cada uno de los 35 modulos.

Ejercita todas las combinaciones reales de token/superficie (pills, medallones,
paneles de acento, celdas nativas). Si un modulo nuevo no tiene fixture, el
self-test falla ruidoso en vez de dejar el modulo sin cobertura.
"""

import os
import tempfile

from .registry import MODULES

def _fixture_image():
    """Imagen determinista para el fixture (cumple el contrato: jpg, >=20 KB,
    >=300 px). Se genera una vez por proceso en temp."""
    from PIL import Image as PILImage
    p = os.path.join(tempfile.gettempdir(), 'studydeck_fixture_img.jpg')
    if os.path.exists(p):
        return p
    im = PILImage.new('RGB', (800, 600))
    px = im.load()
    for y in range(0, 600, 4):
        for x in range(0, 800, 4):
            c = ((x * 7 + y * 13) % 256)
            for dy in range(4):
                for dx in range(4):
                    px[min(x + dx, 799), min(y + dy, 599)] = (c, (c * 3) % 256, (c * 7) % 256)
    im.save(p, 'JPEG', quality=88, optimize=True)
    return p

def fixture_slides():
    """Manifest sintético compartido por self-test y matriz de contraste.
    Cubre LOS 35 MODULOS: la matriz de contraste debe ejercitar toda
    combinación token/superficie real (pills, medallones, paneles de acento),
    no solo 5 módulos. Lección del bug on_success bajo ucp (3.1:1 invisible)."""
    # Cobertura sin fisuras: si la imagen del fixture no existe, el self-test
    # NO baja a 33 modulos en silencio — falla y dice por que (Pillow es
    # dependencia declarada).
    try:
        img = _fixture_image()
    except Exception as exc:   # noqa: BLE001 - re-lanzado com a causa legivel
        raise RuntimeError(
            f'fixture sem imagem para os modulos com figura: {exc}') from exc
    S = [
        {'module': 'title', 'course': 'check', 'title': 'dry-run',
         'subtitle': '', 'institution': ''},
        {'module': 'section_divider', 'section_title': 'Sección uno'},
        {'module': 'definition', 'kicker': 'k', 'title': 't',
         'main_statement': 'Enunciado central de prueba del motor.',
         'key_points': [{'title': 'a', 'desc': 'desc a'}, {'title': 'b', 'desc': 'desc b'}]},
        {'module': 'flow_diagram', 'kicker': 'k', 'title': 't',
         'steps': [{'label': '1', 'title': 'fase 1', 'desc': 'desc a'},
                   {'label': '2', 'title': 'fase 2', 'desc': 'desc b', 'highlight': True},
                   {'label': '3', 'title': 'fase 3', 'desc': 'desc c'}]},
        {'module': 'comparison_table', 'kicker': 'k', 'title': 't',
         'headers': ['a', 'b', 'c'],
         'rows': [['1', '2', '3'], ['1', '2', '3'], ['1', '2', '3']],
         'col_widths': [1, 2, 3]},
        {'module': 'synthesis_grid', 'kicker': 'k', 'title': 't',
         'headers': ['a', 'b', 'c'],
         'matrix_data': [['1', '2', '3'], ['4', '5', '6'], ['7', '8', '9']]},
        {'module': 'stat_card', 'kicker': 'k', 'title': 't',
         'stat_num': '42%', 'stat_title': 'Resultado principal del estudio de prueba',
         'narrative_blocks': [{'title': 'b1', 'desc': 'd1'}, {'title': 'b2', 'desc': 'd2'}]},
        {'module': 'checklist', 'kicker': 'k', 'title': 't',
         'items': [{'label': 'paso uno'}, {'label': 'paso dos', 'checked': False},
                   {'label': 'paso tres'}]},
        {'module': 'fixed_schema_card', 'kicker': 'k', 'title': 't',
         'fields': [{'label': 'campo', 'value': 'valor'}, {'label': 'otro', 'value': 'dato'}]},
        {'module': 'side_by_side', 'kicker': 'k', 'title': 't',
         'left_card': {'header': 'A', 'title': 'lado A',
                       'points': ['p1', 'p2', 'p3']},
         'right_card': {'header': 'B', 'title': 'lado B',
                        'points': ['q1', 'q2', 'q3']}},
        {'module': 'taxonomy_tree', 'kicker': 'k', 'title': 't', 'root': 'raiz',
         'categories': [{'name': 'cat1', 'property': 'prop', 'examples': ['e1']},
                        {'name': 'cat2', 'property': 'prop', 'examples': ['e2']}]},
        {'module': 'algorithm', 'kicker': 'k', 'title': 't',
         'steps': [{'title': 'paso 1'}, {'title': 'paso 2', 'highlight': True},
                   {'title': 'paso 3'}]},
        {'module': 'case_block', 'kicker': 'k', 'title': 't',
         'case_stem': 'Paciente de prueba con datos suficientes para el caso.',
         'findings': ['hallazgo uno', 'hallazgo dos'],
         'reasoning': 'Razonamiento diagnóstico de prueba del módulo.',
         'diagnosis': 'Diagnóstico', 'clinical_pearl': 'Perla de prueba del módulo.'},
        {'module': 'timeline', 'kicker': 'k', 'title': 't',
         'milestones': [{'label': str(i), 'title': 'Hito ' + str(i), 'desc': 'desc'}
                        for i in range(1, 6)]},
        {'module': 'cycle_diagram', 'kicker': 'k', 'title': 't', 'center_label': 'ciclo',
         'nodes': [{'title': 'n' + str(i)} for i in range(1, 5)]},
        {'module': 'quadrant_matrix', 'kicker': 'k', 'title': 't',
         'x_label': 'eje x', 'y_label': 'eje y',
         'quadrants': [{'title': 'q' + str(i), 'points': ['p1', 'p2']} for i in range(1, 5)]},
        {'module': 'pyramid', 'kicker': 'k', 'title': 't',
         'levels': [{'title': 'nivel ' + str(i)} for i in range(1, 4)]},
        {'module': 'quote_block', 'kicker': 'k', 'title': 't',
         'quote': 'Cita de prueba del motor.', 'author': 'Autor'},
        {'module': 'socratic_question', 'kicker': 'k', 'title': 't',
         'question': 'Pregunta tutorial de prueba?',
         'scaffold': ['razonamiento uno', 'razonamiento dos']},
        {'module': 'oxford_union', 'kicker': 'k', 'title': 't',
         'motion': 'motion de prueba',
         'pro_card': {'title': 'pro', 'points': ['p1', 'p2']},
         'con_card': {'title': 'con', 'points': ['c1', 'c2']},
         'verdict': 'veredicto de prueba'},
        {'module': 'evidence_card', 'kicker': 'k', 'title': 't',
         'study_name': 'Estudio Prueba', 'design': 'rct',
         'population': 'pacientes adultos', 'intervention': 'fármaco X',
         'comparison': 'placebo', 'outcome': 'evento Y',
         'effect': 'HR 0.75', 'credit': 'Revista 2024'},
        {'module': 'viva_question', 'kicker': 'k', 'title': 't',
         'prompt': 'Pregunta de viva voce de prueba.',
         'model_answer': 'Respuesta modelo de prueba.',
         'examiner_note': 'Nota del examinador de prueba.'},
        {'module': 'mnemonic_card', 'kicker': 'k', 'title': 't',
         'acronym': 'ABC', 'expansion': ['alfa', 'beta', 'gamma'],
         'usage': 'Uso clínico de la regla mnemotécnica de prueba.'},
        {'module': 'etymology', 'kicker': 'k', 'title': 't', 'term': 'Apendicitis',
         'fragments': ['Apendic', 'itis'],
         'roots': [{'part': 'Apendic', 'origin': 'latin', 'meaning': 'apéndice'},
                   {'part': 'itis', 'origin': 'greek', 'meaning': 'inflamación'}],
         'modern': 'Inflamación del apéndice.'},
        {'module': 'venn_diagram', 'kicker': 'k', 'title': 't',
         'sets': [{'label': 'A', 'items': ['a1', 'a2']},
                  {'label': 'B', 'items': ['b1', 'b2']},
                  {'label': 'C', 'items': ['c1', 'c2']}],
         'shared': ['común']},
        {'module': 'chart_data', 'kicker': 'k', 'title': 't', 'chart_type': 'bar',
         'categories': ['c1', 'c2'],
         'series': [{'name': 's1', 'values': [1.0, 2.0]}],
         'insights': ['lectura de prueba uno', 'lectura de prueba dos']},
        {'module': 'references', 'kicker': 'k', 'title': 't',
         'refs': ['Autor A. Título de prueba. 2024.', 'Autor B. Otro título. 2023.'] +
                 ['Autor C. Referencia extra. 2022.']},
        {'module': 'learning_objectives', 'kicker': 'k', 'title': 't',
         'objectives': [
             {'verb': 'Explicar', 'text': 'la fisiopatología de la fase aguda y su manejo',
              'bloom': 'understand'},
             {'verb': 'Aplicar', 'text': 'el algoritmo de decisión en cada caso',
              'bloom': 'apply'},
             {'verb': 'Analizar', 'text': 'los hallazgos de los estudios citados',
              'bloom': 'analyze'}]},
        {'module': 'colloquy', 'kicker': 'k', 'title': 't',
         'turns': [{'speaker': 'tutor', 'text': 'turno del tutor de prueba'},
                   {'speaker': 'student', 'text': 'respuesta del estudiante'},
                   {'speaker': 'tutor', 'text': 'replica del tutor'},
                   {'speaker': 'student', 'text': 'contrarespuesta'}]},
        {'module': 'annotated_passage', 'kicker': 'k', 'title': 't',
         'passage': 'Fragmento de fuente primaria [1] con nota al margen [2].',
         'source': 'Fuente, 1900',
         'annotations': [{'ref': '1', 'note': 'nota uno'},
                         {'ref': '2', 'note': 'nota dos'}]},
        {'module': 'concept_map', 'kicker': 'k', 'title': 't', 'hub': 'concepto',
         'nodes': [{'title': 'satelite ' + str(i)} for i in range(1, 5)]},
        {'module': 'glossary', 'kicker': 'k', 'title': 't',
         'terms': [{'term': 'Fase aguda', 'def': 'Periodo inicial de mayor riesgo y demanda'},
                   {'term': 'Algoritmo', 'def': 'Secuencia de pasos con decisión'},
                   {'term': 'Caso índice', 'def': 'Primer caso que motiva el estudio'},
                   {'term': 'Perla clínica', 'def': 'Consejo de alto rendimiento'}]},
        # further_reading con tags success Y alert: ejercita on_success/on_alert
        # sobre fills de color medio (el par exacto del bug ucp 3.1:1).
        {'module': 'further_reading', 'kicker': 'k', 'title': 't',
         'entries': [{'tag': 'esencial', 'title': 'Lectura básica', 'note': 'nota'},
                     {'tag': 'avanzado', 'title': 'Lectura avanzada', 'note': 'nota'},
                     {'tag': 'complementario', 'title': 'Lectura media', 'note': 'nota'}]},
    ]
    if img:
        S.append({'module': 'figure', 'kicker': 'k', 'title': 't', 'image': img,
                  'caption': 'Microfotografía de prueba del fixture del motor.',
                  'credit': 'Motor 2026'})
        S.append({'module': 'authority_card', 'kicker': 'k', 'title': 't', 'image': img,
                  'caption': 'Retrato institucional de prueba del fixture.',
                  'credit': 'Motor 2026',
                  'name': 'Autor de Prueba', 'bio': 'Biografía breve de prueba del fixture.',
                  'legacy': 'Legado de prueba'})
    present = {s['module'] for s in S}
    missing = set(MODULES) - present
    if missing:
        # Nunca debe pasar: si un módulo nuevo no tiene fixture, fallar ruidoso.
        raise AssertionError(f'fixture self-test incompleto, faltan: {sorted(missing)}')
    return S



