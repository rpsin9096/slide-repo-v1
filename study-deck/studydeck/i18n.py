# -*- coding: utf-8 -*-
"""Etiquetas de motor en los 3 idiomas soportados (pt-BR por defecto) y guard
de deriva contra calcos del idioma equivocado.

El guard es BLOQUEANTE en lint para el idioma objetivo: solo se aplica a las
palabras listadas, con limites de palabra, para no penalizar terminos
cientificos compartidos entre los tres idiomas.
"""

import re

DEFAULT_LANG = 'pt-BR'
LANGS = ('pt-BR', 'es-ES', 'en-US')

_KEYS = ('central', 'chapter', 'phase', 'takeaway', 'source', 'join', 'vignette',
         'findings', 'reasoning', 'diagnosis', 'pearl', 'yes', 'no', 'house', 'proposition',
         'opposition', 'verdict', 'tutorial', 'scaffold', 'clinical_use',
         'model_answer', 'examiner', 'reading', 'shared', 'origin', 'modern_use',
         'limitation', 'legacy', 'references', 'viva', 'objectives', 'tutor',
         'student', 'marginalia', 'glossary', 'further_reading')

LABELS = {
    'pt-BR': {
        'central': 'DECLARAÇÃO CENTRAL', 'chapter': 'CAPÍTULO', 'phase': 'FASE',
        'takeaway': 'CONCLUSÃO EDITORIAL:  ', 'source': 'Fonte / Crédito: {c}',
        'join': '{f}  •  Crédito: {c}', 'vignette': 'VINHETA CLÍNICA',
        'findings': 'ACHADOS CLÍNICOS & EXAMES', 'reasoning': 'RAZIOCÍNIO DIAGNÓSTICO',
        'diagnosis': 'DIAGNÓSTICO DEFINITIVO', 'pearl': 'PÉROLA CLÍNICA',
        'yes': 'SIM', 'no': 'NÃO',
        'house': 'DEBATE', 'proposition': 'PROPOSIÇÃO',
        'opposition': 'OPOSIÇÃO', 'verdict': 'VEREDITO DO MODERADOR:',
        'tutorial': 'PERGUNTA DE TUTORIA', 'scaffold': 'ANDAIME DE RACIOCÍNIO',
        'clinical_use': 'USO CLÍNICO', 'model_answer': 'RESPOSTA MODELO',
        'examiner': 'NOTA DO EXAMINADOR', 'reading': 'LEITURA DOS DADOS',
        'shared': 'COMUM', 'origin': 'ORIGEM', 'modern_use': 'ACEPCIÓN ATUAL',
        'limitation': 'LIMITAÇÃO', 'legacy': 'LEGADO', 'references': 'REFERÊNCIAS',
        'viva': 'PROVA ORAL', 'objectives': 'OBJETIVOS DE APRENDIZAGEM',
        'tutor': 'TUTOR', 'student': 'ESTUDANTE', 'marginalia': 'MARGINALIA',
        'glossary': 'GLOSSÁRIO', 'further_reading': 'LEITURAS RECOMENDADAS',
    },
    'es-ES': {
        'central': 'ENUNCIADO CENTRAL', 'chapter': 'CAPÍTULO', 'phase': 'FASE',
        'takeaway': 'CONCLUSIÓN EDITORIAL:  ', 'source': 'Fuente / Crédito: {c}',
        'join': '{f}  •  Crédito: {c}', 'vignette': 'VIÑETA CLÍNICA',
        'findings': 'HALLAZGOS CLÍNICOS & PRUEBAS',
        'reasoning': 'JUICIO DIAGNÓSTICO & RAZONAMIENTO',
        'diagnosis': 'DIAGNÓSTICO DEFINITIVO', 'pearl': 'PERLA CLÍNICA',
        'yes': 'SÍ', 'no': 'NO',
        'house': 'DEBATE', 'proposition': 'PROPOSICIÓN',
        'opposition': 'OPOSICIÓN', 'verdict': 'VEREDICTO DEL MODERADOR:',
        'tutorial': 'PREGUNTA TUTORIAL', 'scaffold': 'ANDAMIAJE DE RAZONAMIENTO',
        'clinical_use': 'USO CLÍNICO', 'model_answer': 'RESPUESTA MODELO',
        'examiner': 'NOTA DEL EXAMINADOR', 'reading': 'LECTURA DE LOS DATOS',
        'shared': 'COMPARTIDO', 'origin': 'ORIGEN', 'modern_use': 'ACEPCIÓN ACTUAL',
        'limitation': 'LIMITACIÓN', 'legacy': 'LEGADO', 'references': 'REFERENCIAS',
        'viva': 'EXAMEN ORAL', 'objectives': 'OBJETIVOS DE APRENDIZAJE',
        'tutor': 'TUTOR', 'student': 'ESTUDIANTE', 'marginalia': 'MARGINALIA',
        'glossary': 'GLOSARIO', 'further_reading': 'LECTURAS RECOMENDADAS',
    },
    'en-US': {
        'central': 'CENTRAL STATEMENT', 'chapter': 'CHAPTER', 'phase': 'PHASE',
        'takeaway': 'EDITORIAL TAKEAWAY:  ', 'source': 'Source / Credit: {c}',
        'join': '{f}  •  Credit: {c}', 'vignette': 'CLINICAL VIGNETTE',
        'findings': 'CLINICAL FINDINGS & TESTS',
        'reasoning': 'DIAGNOSTIC REASONING & JUDGMENT',
        'diagnosis': 'DEFINITIVE DIAGNOSIS', 'pearl': 'CLINICAL PEARL',
        'yes': 'YES', 'no': 'NO',
        'house': 'DEBATE', 'proposition': 'PROPOSITION',
        'opposition': 'OPPOSITION', 'verdict': "MODERATOR'S VERDICT:",
        'tutorial': 'TUTORIAL QUESTION', 'scaffold': 'REASONING SCAFFOLD',
        'clinical_use': 'CLINICAL USE', 'model_answer': 'MODEL ANSWER',
        'examiner': "EXAMINER'S NOTE", 'reading': 'READING THE DATA',
        'shared': 'SHARED', 'origin': 'ORIGIN', 'modern_use': 'MODERN MEANING',
        'limitation': 'LIMITATION', 'legacy': 'LEGACY', 'references': 'REFERENCES',
        'viva': 'ORAL EXAM', 'objectives': 'LEARNING OBJECTIVES', 'tutor': 'TUTOR',
        'student': 'STUDENT', 'marginalia': 'MARGINALIA', 'glossary': 'GLOSSARY',
        'further_reading': 'FURTHER READING',
    },
}

BLOOM = {
    'pt-BR': {'remember': 'lembrar', 'understand': 'compreender', 'apply': 'aplicar',
              'analyze': 'analisar', 'evaluate': 'avaliar', 'create': 'criar'},
    'es-ES': {'remember': 'recordar', 'understand': 'comprender', 'apply': 'aplicar',
              'analyze': 'analizar', 'evaluate': 'evaluar', 'create': 'crear'},
    'en-US': {'remember': 'remember', 'understand': 'understand', 'apply': 'apply',
              'analyze': 'analyze', 'evaluate': 'evaluate', 'create': 'create'},
}

# Calcos del idioma equivocado -> forma correcta en el idioma objetivo.
# Solo palabras que NO existen en el idioma objetivo: los terminos cientificos
# compartidos (celular, diagnostico, paciente) no se listan nunca.
DRIFT = {
    'pt-BR': {
        'desarrollo': 'desenvolvimento', 'desarrollar': 'desenvolver',
        'estudio': 'estudo', 'el': 'o', 'la': 'a', 'los': 'os', 'las': 'as',
        'del': 'do', 'los': 'os', 'más': 'mais', 'también': 'também',
        'the': 'o/a', 'and': 'e', 'with': 'com', 'from': 'a partir de',
        'this': 'este', 'that': 'esse', 'which': 'que',
    },
    'es-ES': {
        'desenvolvimento': 'desarrollo', 'desenvolver': 'desarrollar',
        'aprendizagem': 'aprendizaje', 'também': 'también', 'mais': 'más',
        'patologia': 'patología', 'fisiopatologia': 'fisiopatología',
        'tratamento': 'tratamiento', 'clinico': 'clínico', 'referencias': 'referencias',
    },
    'en-US': {
        'desarrollo': 'development', 'patologia': 'pathology',
        'clinico': 'clinical', 'tratamiento': 'treatment',
        'diagnóstico': 'diagnosis', 'aprendizagem': 'learning',
    },
}

_UI_LANG = DEFAULT_LANG
_CACHE = {}


def lang_pack(lang):
    """lang_pack: documented behavior of the module."""
    lang = lang if lang in LABELS else DEFAULT_LANG
    if lang not in _CACHE:
        _CACHE[lang] = {'labels': dict(LABELS[lang]), 'bloom': dict(BLOOM[lang])}
    return _CACHE[lang]


def set_ui(lang):
    """set_ui: documented behavior of the module."""
    global _UI_LANG
    _UI_LANG = lang if lang in LABELS else DEFAULT_LANG
    return _UI_LANG


def current():
    """current: documented behavior of the module."""
    return _UI_LANG


def T(key):
    """T: documented behavior of the module."""
    return lang_pack(_UI_LANG)['labels'][key]


def bloom(key):
    """bloom: documented behavior of the module."""
    return lang_pack(_UI_LANG)['bloom'].get(str(key).lower(), key)


def drift_hits(text, lang):
    """[(palanca, correccion)] de calcos del idioma equivocado en `text`."""
    lang = lang if lang in DRIFT else DEFAULT_LANG
    if not isinstance(text, str) or not text:
        return []
    hits = []
    for word, fix in DRIFT[lang].items():
        if re.search(r'(?<!\w)' + re.escape(word) + r'(?!\w)', text, re.IGNORECASE):
            hits.append((word, fix))
    return hits