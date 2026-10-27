#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
=============================================================================
OMC KIT v7.9.6 — UCP EDITION · CONTRAST TOKEN ENGINE
=============================================================================
Layout engine pedagógico/visual (Oxford · Harvard · Yale · Cambridge · UCP).
CLI único: preflight -> new -> ledger -> imgprep -> schema -> lint ->
build/audit/all/contrast.

Contratos estables (no regresar):
  - Idioma: blacklist de deriva pt->es-ES BLOQUEA en lint; la huella estadística
    es tripwire WARN-only en audit (nunca bloquea).
  - Suelo de contenido: núcleo-4 + variedad distinta (>=8; >=12 si >=20 slides).
  - Honestidad: el ledger ATU se verifica solo por numeración/continuidad/rangos.
  - Imágenes: 20 KB-4 MB, >=300 px lado menor.
  - Build fail-fast: lint antes de render (`all` = lint->build->audit).

v7.9.6 (Contrast Token Engine):
  - Tokens derivados por tema (WCAG): on_primary · on_primary_soft · on_accent ·
    ink_accent · ink_success · on_success · on_alert · subtitle_on_primary.
    Los hex de marca quedan intactos para gráfica; solo el TEXTO migra a tokens.
    Overrides manuales: PALETTE_OVERRIDES = {<tema>: {<token>: 'RRGGBB'}}.
  - Compuerta `contrast`: instrumentación runtime (OMC_CONTRAST=1 o comando),
    matriz 5 temas en self-test, sección 5 en audit. Exenciones: decorativos
    (deco=True) y superficies desconocidas (tablas/gráficos nativos).
  - est_height consciente de fuente (Montserrat ~14% más ancha que Calibri).
  - Pulido geométrico: pills 0.34in/rad .12, halo en venn.shared, corredor NO,
    anillo del primer hito del timeline.
=============================================================================
"""

import sys
import os
import re as _re
import math as _math
import hashlib as _hashlib
import datetime as _dt
import tempfile as _tf
import types as _types
import importlib.util
import unicodedata
import json as _json
from collections import Counter

# Dynamic import handles for python-pptx (imported lazily — see _import_pptx)
Presentation = None
Inches = None
Pt = None
RGBColor = None
PP_ALIGN = None
MSO_ANCHOR = None
MSO_SHAPE = None
_PPTX_OK = False

def _import_pptx():
    global Presentation, Inches, Pt, RGBColor, PP_ALIGN, MSO_ANCHOR, MSO_SHAPE, _PPTX_OK
    if _PPTX_OK:
        return True
    try:
        from pptx import Presentation as _P
        from pptx.util import Inches as _I, Pt as _Pt
        from pptx.dml.color import RGBColor as _RC
        from pptx.enum.text import PP_ALIGN as _PA, MSO_ANCHOR as _MA
        from pptx.enum.shapes import MSO_SHAPE as _MS
        Presentation = _P
        Inches = _I
        Pt = _Pt
        RGBColor = _RC
        PP_ALIGN = _PA
        MSO_ANCHOR = _MA
        MSO_SHAPE = _MS
        _PPTX_OK = True
        return True
    except ImportError:
        _PPTX_OK = False
        return False

def _module_available(name):
    # v8.4: find_spec en vez de __import__ — evita importar el módulo solo para sondear.
    if name in sys.modules:
        return True
    try:
        importlib.util.find_spec(name)
        return True
    except (ImportError, AttributeError, ValueError):
        return False

KIT_VERSION = 'OMC KIT v9.6.1 (UCP Edition · Contrast Token Engine · Fidelity Chain)'

# Typography tokens: Classic Scholarly Serif for Headers, Modern Crisp Sans for Body
FONT_TITLE = "Georgia"
FONT_BODY = "Calibri"

# Ancho medio de glifo como fracción del pt (por fuente) — estimador de ajuste.
_CHAR_W_BY_FONT = {"Montserrat": 0.57, "Georgia": 0.50, "Calibri": 0.47}
_CHAR_W_DEFAULT = 0.50

# Collegiate Palettes
PALETTES = {
    "oxford": {
        "primary": "002147", "accent": "B08D57", "bg": "FAF9F6", "text": "1C2430",
        "text_muted": "616A75", "alert": "8B0000", "success": "1B5E20",
        "border": "DCD8CE", "card": "FFFFFF", "soft": "F3EFE6", "highlight": "EAE4D5",
    },
    "harvard": {
        "primary": "A51C30", "accent": "B88B4A", "bg": "FBFBF9", "text": "21272A",
        "text_muted": "6A737D", "alert": "9E0000", "success": "2E6930",
        "border": "E2DDD4", "card": "FFFFFF", "soft": "F5F0E8", "highlight": "ECE4D8",
    },
    "yale": {
        "primary": "0F4D92", "accent": "C5A059", "bg": "FAFAFA", "text": "1E293B",
        "text_muted": "64748B", "alert": "991B1B", "success": "166534",
        "border": "DCE2EA", "card": "FFFFFF", "soft": "EEF2F6", "highlight": "E2E8F0",
    },
    "cambridge": {
        "primary": "1B365D", "accent": "007788", "bg": "F8FAF9", "text": "1C2833",
        "text_muted": "5D6D7E", "alert": "922B21", "success": "196F3D",
        "border": "D4E1DF", "card": "FFFFFF", "soft": "EDF4F2", "highlight": "DCECE8",
    },
    "ucp": {
        "primary": "3854CC", "accent": "D92A2B", "bg": "F8F9FF", "text": "2B2C4A",
        "text_muted": "606383", "alert": "B91C1C", "success": "1E8A5A",
        "border": "D9DDF2", "card": "FFFFFF", "soft": "EEF0FF", "highlight": "E0E4FF",
    }
}

# ===================== P0 — NÚCLEO DE CONTRASTE (WCAG) =====================
# v9.1/A2 — umbrales WCAG como constantes (antes hardcodeados ~10×)
WCAG_AA_TEXT = 4.5     # texto normal
WCAG_AA_DISPLAY = 3.0  # texto grande/display (>=18pt o bold >=14pt)

def _rel_lum(hexc):
    hexc = str(hexc).lstrip('#')
    def ch(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(int(hexc[i:i+2], 16)) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def _ratio(fg, bgc):
    l1, l2 = sorted((_rel_lum(fg), _rel_lum(bgc)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

def _pick(candidates, surface, target):
    """Primer candidato que cumple el ratio sobre `surface`; None si ninguno."""
    for cand in candidates:
        if cand and _ratio(cand, surface) >= target:
            return cand
    return None

def _shade_until(hexcolor, surface, target, max_steps=12):
    """Oscurece el tono conservando matiz hasta alcanzar el ratio objetivo."""
    c = str(hexcolor).lstrip('#')
    for step in range(1, max_steps + 1):
        f = 1.0 - step * 0.07
        c = ''.join(f'{max(0, round(int(c[i:i+2], 16) * f)):02X}' for i in (0, 2, 4))
        if _ratio(c, surface) >= target:
            return c
    return c

# Overrides manuales por tema (control fino sin tocar el motor).
PALETTE_OVERRIDES = {
    # 'oxford': {'ink_accent': '7A5F33'},
}

def derive_tokens(key, P):
    """Tokens de TEXTO derivados por tema. Hex de marca intactos para gráfica."""
    ov = dict(PALETTE_OVERRIDES.get(key, {}))
    acc, pri = P["accent"], P["primary"]
    t = {}
    # Texto sobre fill primario: prefiere el acento de marca SI es legible
    # (preserva oro-sobre-navy de Oxford); si no, blanco/highlight/tinta.
    t['on_primary'] = ov.get('on_primary') or (
        _pick([acc], pri, WCAG_AA_TEXT) or _pick(["FFFFFF", P["highlight"], P["text"]], pri, WCAG_AA_TEXT) or "FFFFFF")
    t['on_primary_soft'] = ov.get('on_primary_soft') or (
        _pick([acc, P["highlight"], "FFFFFF"], pri, WCAG_AA_TEXT) or "FFFFFF")
    # Texto sobre fill de acento: oro -> tinta; rojo/teal -> blanco.
    t['on_accent'] = ov.get('on_accent') or (
        _pick(["FFFFFF", P["text"]], acc, WCAG_AA_TEXT) or P["text"])
    # Acento COMO texto sobre superficies claras: deriva a bronce/tinta si hace falta.
    t['ink_accent'] = ov.get('ink_accent') or (
        _pick([acc], P["soft"], WCAG_AA_TEXT) or _shade_until(acc, P["soft"], WCAG_AA_TEXT))
    t['ink_success'] = ov.get('ink_success') or (
        _pick([P["success"]], P["soft"], WCAG_AA_TEXT) or _shade_until(P["success"], P["soft"], WCAG_AA_TEXT))
    # v9.A — sobre fills de color MEDIO (verde/rojo de marca) el blanco puede quedarse
    # en 3-4.4:1 (ucp success #1E8A5A da 4.34 con blanco): se oscurece la TINTA hasta
    # cumplir 4.5 en vez de aceptar un par bajo. El fill de marca queda intacto.
    t['on_success'] = ov.get('on_success') or (
        _pick(["FFFFFF", P["text"]], P["success"], WCAG_AA_TEXT)
        or _shade_until(P["text"], P["success"], WCAG_AA_TEXT))
    t['on_alert'] = ov.get('on_alert') or (
        _pick(["FFFFFF", P["text"]], P["alert"], WCAG_AA_TEXT) or P["text"])
    t['subtitle_on_primary'] = ov.get('subtitle_on_primary') or (
        _pick([P["highlight"], "FFFFFF"], pri, WCAG_AA_TEXT) or "FFFFFF")
    return t

# Tokens activos (se fijan en _render / cmd_contrast; vacío fuera de render).
TOK = {}

def _set_tokens(pal_key):
    global TOK
    TOK = derive_tokens(pal_key, PALETTES.get(pal_key, PALETTES['oxford']))

def _on(P, fill):
    """Foreground legible para texto SOBRE un fill de color dado."""
    return _pick(["FFFFFF", P["text"]], fill, WCAG_AA_TEXT) or P["text"]

def _ink(P):
    """Tinta de acento legible sobre superficies claras (v9.B/F3)."""
    return TOK.get('ink_accent', P["accent"])

def _sub_primary():
    return TOK.get('subtitle_on_primary', "D8E2EC")

def _ok_ink(P):
    return TOK.get('ink_success', P["success"])

def pill(slide, x, y, w, h, text, fill, fg, size=8.5, font=None, rad=0.12):
    """Píldora/badge: rect redondeado + texto centrado en negrita sobre la MISMA caja
    (v9.B/F1 — 11 sitios idénticos en renderers)."""
    if font is None:
        font = FONT_BODY
    rect(slide, x, y, w, h, fill=fill, line=None, rounded=True, rad=rad)
    tx(slide, x, y, w, h, text, size=size, color=fg,
       bold=True, align=PP_ALIGN.CENTER, font=font)

# Helpers legados (misma firma que v7.9.5; ahora token-backed).
def _fg_on_primary(P, fallback=None):
    return TOK.get('on_primary') or (fallback or P["accent"])

def _fg_on_primary_soft(P):
    return TOK.get('on_primary_soft') or P["accent"]

# ===================== P5 — INSTRUMENTACIÓN DE CONTRASTE =====================
_CONTRAST_ON = os.environ.get('OMC_CONTRAST') == '1'   # toggle vía OMC_CONTRAST=1 o cmd_contrast/cmd_all
_CONTRAST_LOG = []            # entradas: dict(fg,bg,size,bold,deco,slide,module)
_SURFACE_STACK = []           # (x, y, w, h, fill) por diapositiva, orden de pintado
_MEASURE_OFF = False          # tablas/gráficos nativos fuera del gate
_CTX = {"slide": 0, "module": "?"}

from contextlib import contextmanager as _ctxmgr

@_ctxmgr
def _contrast_instrumented(clear_surfaces=True):
    """v9.1/A4 — activa el gate de contraste para un render y lo restaura al salir.
    clear_surfaces=True además limpia _SURFACE_STACK (usado por scans aislados;
    el build real de `all` no necesita heredar superficies de un run previo)."""
    global _CONTRAST_ON
    prev = _CONTRAST_ON
    _CONTRAST_ON = True
    _CONTRAST_LOG.clear()
    if clear_surfaces:
        _SURFACE_STACK.clear()
    try:
        yield
    finally:
        _CONTRAST_ON = prev

@_ctxmgr
def _measure_off():
    """v9.1/A3 — suspende la medición de contraste (tablas/gráficos nativos)."""
    global _MEASURE_OFF
    _prev = _MEASURE_OFF
    _MEASURE_OFF = True
    try:
        yield
    finally:
        _MEASURE_OFF = _prev

def _note_surface(fill, x, y, w, h):
    if fill:
        _SURFACE_STACK.append((float(x), float(y), float(w), float(h), str(fill)))

def _surface_at(px, py):
    """Relleno visible bajo el punto: último rect pintado que lo contiene."""
    if px is None:
        return None
    for x, y, w, h, fill in reversed(_SURFACE_STACK):
        if x <= px <= x + w and y <= py <= y + h:
            return fill
    return None

def _required_ratio(size, bold):
    return WCAG_AA_DISPLAY if (size >= 18 or (bold and size >= 14)) else WCAG_AA_TEXT

def _log_text(fg, size, bold, deco, px=None, py=None):
    if not (_CONTRAST_ON and str(fg) and not _MEASURE_OFF and not deco):
        return
    surf = _surface_at(px, py)
    if surf:
        _CONTRAST_LOG.append({'fg': str(fg), 'bg': surf, 'size': float(size),
                              'bold': bool(bold), 'deco': False,
                              'slide': _CTX["slide"], 'module': _CTX["module"]})

def _contrast_failures(log=None):
    out = []
    for e in (log if log is not None else _CONTRAST_LOG):
        req = _required_ratio(e['size'], e['bold'])
        r = _ratio(e['fg'], e['bg'])
        if r < req:
            out.append({'slide': e['slide'], 'module': e['module'], 'fg': e['fg'],
                        'bg': e['bg'], 'ratio': round(r, 2), 'required': req})
    return out

# ===================== I18N — LANGUAGE-AGNOSTIC ENGINE LABELS =====================
I18N = {
 'es-ES': {'central': 'ENUNCIADO CENTRAL', 'chapter': 'CAPÍTULO', 'phase': 'FASE',
   'takeaway': 'CONCLUSIÓN EDITORIAL:  ', 'source': 'Fuente / Crédito: {c}',
   'join': '{f}  •  Crédito: {c}', 'vignette': 'VIÑETA CLÍNICA',
   'findings': 'HALLAZGOS CLÍNICOS & PRUEBAS', 'reasoning': 'JUICIO DIAGNÓSTICO & RAZONAMIENTO',
   'diagnosis': 'DIAGNÓSTICO DEFINITIVO', 'pearl': 'PERLA CLÍNICA',
   'footer': 'SERIE DE MONOGRAFÍAS ACADÉMICAS', 'yes': 'SÍ', 'no': 'NO',
   'course_default': 'PROGRAMA DE FORMACIÓN CLÍNICA AVANZADA',
   'institution_default': 'FACULTAD DE MEDICINA • PROGRAMA ACADÉMICO',
   'house': 'LA CÁMARA SOSTIENE QUE', 'proposition': 'PROPOSICIÓN', 'opposition': 'OPOSICIÓN',
   'verdict': 'VEREDICTO DEL MODERADOR:', 'tutorial': 'PREGUNTA TUTORIAL',
   'scaffold': 'ANDAMIAJE DE RAZONAMIENTO', 'clinical_use': 'USO CLÍNICO',
   'model_answer': 'RESPUESTA MODELO', 'examiner': 'NOTA DEL EXAMINADOR',
   'reading': 'LECTURA DE LOS DATOS', 'shared': 'COMPARTIDO', 'origin': 'ORIGEN',
   'modern_use': 'ACEPCIÓN ACTUAL', 'limitation': 'LIMITACIÓN', 'legacy': 'LEGADO',
   'references': 'REFERENCIAS', 'viva': 'VIVA VOCE',
   'objectives': 'OBJETIVOS DE APRENDIZAJE', 'tutor': 'TUTOR', 'student': 'ESTUDIANTE',
   'marginalia': 'MARGINALIA', 'glossary': 'GLOSARIO', 'further_reading': 'LECTURAS RECOMENDADAS'},
 'en-US': {'central': 'CENTRAL STATEMENT', 'chapter': 'CHAPTER', 'phase': 'PHASE',
   'takeaway': 'EDITORIAL TAKEAWAY:  ', 'source': 'Source / Credit: {c}',
   'join': '{f}  •  Credit: {c}', 'vignette': 'CLINICAL VIGNETTE',
   'findings': 'CLINICAL FINDINGS & TESTS', 'reasoning': 'DIAGNOSTIC REASONING & JUDGMENT',
   'diagnosis': 'DEFINITIVE DIAGNOSIS', 'pearl': 'CLINICAL PEARL',
   'footer': 'ACADEMIC MONOGRAPH SERIES', 'yes': 'YES', 'no': 'NO',
   'course_default': 'ADVANCED CLINICAL TRAINING PROGRAM',
   'institution_default': 'FACULTY OF MEDICINE • ACADEMIC PROGRAM',
   'house': 'THIS HOUSE BELIEVES THAT', 'proposition': 'PROPOSITION', 'opposition': 'OPPOSITION',
   'verdict': "MODERATOR'S VERDICT:", 'tutorial': 'TUTORIAL QUESTION',
   'scaffold': 'REASONING SCAFFOLD', 'clinical_use': 'CLINICAL USE',
   'model_answer': 'MODEL ANSWER', 'examiner': "EXAMINER'S NOTE",
   'reading': 'READING THE DATA', 'shared': 'SHARED', 'origin': 'ORIGIN',
   'modern_use': 'MODERN MEANING', 'limitation': 'LIMITATION', 'legacy': 'LEGACY',
   'references': 'REFERENCES', 'viva': 'VIVA VOCE',
   'objectives': 'LEARNING OBJECTIVES', 'tutor': 'TUTOR', 'student': 'STUDENT',
   'marginalia': 'MARGINALIA', 'glossary': 'GLOSSARY', 'further_reading': 'FURTHER READING'},
 'pt-BR': {'central': 'DECLARAÇÃO CENTRAL', 'chapter': 'CAPÍTULO', 'phase': 'FASE',
   'takeaway': 'CONCLUSÃO EDITORIAL:  ', 'source': 'Fonte / Crédito: {c}',
   'join': '{f}  •  Crédito: {c}', 'vignette': 'VINHETA CLÍNICA',
   'findings': 'ACHADOS CLÍNICOS & EXAMES', 'reasoning': 'RACIOCÍNIO DIAGNÓSTICO',
   'diagnosis': 'DIAGNÓSTICO DEFINITIVO', 'pearl': 'PÉROLA CLÍNICA',
   'footer': 'SÉRIE DE MONOGRAFIAS ACADÊMICAS', 'yes': 'SIM', 'no': 'NÃO',
   'course_default': 'PROGRAMA DE FORMAÇÃO CLÍNICA AVANÇADA',
   'institution_default': 'FACULDADE DE MEDICINA • PROGRAMA ACADÊMICO',
   'house': 'A CÂMARA ACREDITA QUE', 'proposition': 'PROPOSIÇÃO', 'opposition': 'OPOSIÇÃO',
   'verdict': 'VEREDITO DO MODERADOR:', 'tutorial': 'QUESTÃO DE TUTORIA',
   'scaffold': 'ANDAIME DE RACIOCÍNIO', 'clinical_use': 'USO CLÍNICO',
   'model_answer': 'RESPOSTA MODELO', 'examiner': 'NOTA DO EXAMINADOR',
   'reading': 'LEITURA DOS DADOS', 'shared': 'COMUM', 'origin': 'ORIGEM',
   'modern_use': 'ACEPÇÃO ATUAL', 'limitation': 'LIMITAÇÃO', 'legacy': 'LEGADO',
   'references': 'REFERÊNCIAS', 'viva': 'VIVA VOCE',
   'objectives': 'OBJETIVOS DE APRENDIZAGEM', 'tutor': 'TUTOR', 'student': 'ESTUDANTE',
   'marginalia': 'MARGINALIA', 'glossary': 'GLOSSÁRIO', 'further_reading': 'LEITURAS RECOMENDADAS'},
 'fr-FR': {'central': 'ÉNONCÉ CENTRAL', 'chapter': 'CHAPITRE', 'phase': 'PHASE',
   'takeaway': 'CONCLUSION ÉDITORIALE :  ', 'source': 'Source / Crédit : {c}',
   'join': '{f}  •  Crédit : {c}', 'vignette': 'VIGNETTE CLINIQUE',
   'findings': 'SIGNES CLINIQUES & TESTS', 'reasoning': 'RAISONNEMENT DIAGNOSTIQUE',
   'diagnosis': 'DIAGNOSTIC DÉFINITIF', 'pearl': 'PERLE CLINIQUE',
   'footer': 'SÉRIE DE MONOGRAPHIES ACADÉMIQUES', 'yes': 'OUI', 'no': 'NON',
   'course_default': 'PROGRAMME DE FORMATION CLINIQUE AVANCÉE',
   'institution_default': 'FACULTÉ DE MÉDECINE • PROGRAMME ACADÉMIQUE',
   'house': 'CETTE ASSEMBLÉE ESTIME QUE', 'proposition': 'POUR', 'opposition': 'CONTRE',
   'verdict': 'VERDICT DU MODÉRATEUR :', 'tutorial': 'QUESTION DE TUTORAT',
   'scaffold': 'ÉCHAFAUDAGE DE RAISONNEMENT', 'clinical_use': 'USAGE CLINIQUE',
   'model_answer': 'RÉPONSE TYPE', 'examiner': "NOTE DE L'EXAMINATEUR",
   'reading': 'LECTURE DES DONNÉES', 'shared': 'COMMUN', 'origin': 'ORIGINE',
   'modern_use': 'SENS ACTUEL', 'limitation': 'LIMITE', 'legacy': 'HÉRITAGE',
   'references': 'RÉFÉRENCES', 'viva': 'VIVA VOCE',
   'objectives': 'OBJECTIFS PÉDAGOGIQUES', 'tutor': 'TUTEUR', 'student': 'ÉTUDIANT',
   'marginalia': 'MARGINALIA', 'glossary': 'GLOSSAIRE', 'further_reading': 'LECTURES RECOMMANDÉES'},
 'de-DE': {'central': 'KERNAUSSAGE', 'chapter': 'KAPITEL', 'phase': 'PHASE',
   'takeaway': 'REDAKTIONELLES FAZIT:  ', 'source': 'Quelle / Credit: {c}',
   'join': '{f}  •  Credit: {c}', 'vignette': 'KLINISCHER FALLBERICHT',
   'findings': 'KLINISCHE BEFUNDE & TESTS', 'reasoning': 'DIAGNOSTISCHE BEURTEILUNG',
   'diagnosis': 'DEFINITIVE DIAGNOSE', 'pearl': 'KLINISCHE PERLE',
   'footer': 'AKADEMISCHE MONOGRAPHIENREIHE', 'yes': 'JA', 'no': 'NEIN',
   'course_default': 'PROGRAMM FÜR KLINISCHE FORTBILDUNG',
   'institution_default': 'FAKULTÄT FÜR MEDIZIN • AKADEMISCHES PROGRAMM',
   'house': 'DAS HAUS IST DER ANSICHT, DASS', 'proposition': 'PRO', 'opposition': 'CONTRA',
   'verdict': 'URTEIL DES MODERATORS:', 'tutorial': 'TUTORIALFRAGE',
   'scaffold': 'DENKGERÜST', 'clinical_use': 'KLINISCHE ANWENDUNG',
   'model_answer': 'MUSTERANTWORT', 'examiner': 'ANMERKUNG DES PRÜFERS',
   'reading': 'DATENINTERPRETATION', 'shared': 'GEMEINSAM', 'origin': 'URSPRUNG',
   'modern_use': 'HEUTIGE BEDEUTUNG', 'limitation': 'EINSCHRÄNKUNG', 'legacy': 'VERMÄCHTNIS',
   'references': 'LITERATUR', 'viva': 'VIVA VOCE',
   'objectives': 'LERNZIELE', 'tutor': 'TUTOR', 'student': 'STUDENT',
   'marginalia': 'MARGINALIEN', 'glossary': 'GLOSSAR', 'further_reading': 'WEITERFÜHRENDE LITERATUR'},
 'it-IT': {'central': 'ENUNCIATO CENTRALE', 'chapter': 'CAPITOLO', 'phase': 'PHASE',
   'takeaway': 'CONCLUSIONE EDITORIALE:  ', 'source': 'Fonte / Credito: {c}',
   'join': '{f}  •  Credito: {c}', 'vignette': 'CASO CLINICO',
   'findings': 'RISCONTRI CLINICI & TEST', 'reasoning': 'GIUDIZIO DIAGNOSTICO',
   'diagnosis': 'DIAGNOSI DEFINITIVA', 'pearl': 'PERLA CLINICA',
   'footer': 'SERIE DI MONOGRAFIE ACCADEMICHE', 'yes': 'SÌ', 'no': 'NO',
   'course_default': 'PROGRAMMA DI FORMAZIONE CLINICA AVANZATA',
   'institution_default': 'FACOLTÀ DI MEDICINA • PROGRAMMA ACCADEMICO',
   'house': "L'ASSEMBLEA RITIENE CHE", 'proposition': 'PRO', 'opposition': 'CONTRO',
   'verdict': 'VERDITTIVO DEL MODERATORE:', 'tutorial': 'DOMANDA TUTORIALE',
   'scaffold': 'IMPALCATURA DI RAGIONAMENTO', 'clinical_use': 'USO CLINICO',
   'model_answer': 'RISPOSTA MODELLO', 'examiner': "NOTA DELL'ESAMINATORE",
   'reading': 'LETTURA DEI DATI', 'shared': 'COMUNE', 'origin': 'ORIGINE',
   'modern_use': 'ACCEZIONE ATTUALE', 'limitation': 'LIMITAZIONE', 'legacy': 'EREDITÀ',
   'references': 'RIFERIMENTI', 'viva': 'VIVA VOCE',
   'objectives': 'OBIETTIVI DI APPRENDIMENTO', 'tutor': 'TUTOR', 'student': 'STUDENTE',
   'marginalia': 'MARGINALIA', 'glossary': 'GLOSSARIO', 'further_reading': 'LETTURE CONSIGLIATE'},
}
BLOOM_I18N = {
 'en-US': {'remember':'remember','understand':'understand','apply':'apply','analyze':'analyze','evaluate':'evaluate','create':'create'},
 'es-ES': {'remember':'recordar','understand':'comprender','apply':'aplicar','analyze':'analizar','evaluate':'evaluar','create':'crear'},
 'pt-BR': {'remember':'lembrar','understand':'entender','apply':'aplicar','analyze':'analisar','evaluate':'avaliar','create':'criar'},
 'fr-FR': {'remember':'se souvenir','understand':'comprendre','apply':'appliquer','analyze':'analyser','evaluate':'évaluer','create':'créer'},
 'de-DE': {'remember':'erinnern','understand':'verstehen','apply':'anwenden','analyze':'analysieren','evaluate':'bewerten','create':'erschaffen'},
 'it-IT': {'remember':'ricordare','understand':'comprendere','apply':'applicare','analyze':'analizzare','evaluate':'valutare','create':'creare'},
}

# v8.0 — Punto de entrada unificado por idioma: consolida I18N / BLOOM_I18N /
# UCP_I18N_OVERRIDES en un solo pack. Añadir un idioma nuevo = 1 bloque por
# estructura (ya no hay que tocar el consumidor).
_LANG_PACK_CACHE = {}

def lang_pack(lang):
    """{'labels', 'bloom', 'palette_overrides'} para un idioma dado (cacheado)."""
    if lang not in _LANG_PACK_CACHE:
        _LANG_PACK_CACHE[lang] = {
            'labels': I18N.get(lang, I18N['en-US']),
            'bloom': BLOOM_I18N.get(lang, BLOOM_I18N['en-US']),
            'palette_overrides': UCP_I18N_OVERRIDES.get(lang, {}),
        }
    return _LANG_PACK_CACHE[lang]

def bloom_t(bloom_key):
    return lang_pack(_UI_LANG)['bloom'].get(bloom_key.lower(), bloom_key)

_UI_LANG = 'es-ES'

def set_ui(lang):
    global _UI_LANG
    _UI_LANG = lang if lang in I18N else 'en-US'

_PALETTE = 'oxford'
UCP_I18N_OVERRIDES = {
    # Tags neutros bajo paleta ucp: sin referencia universitaria.
    'es-ES': {'pearl': 'PERLA CLÍNICA'},
    'en-US': {'pearl': 'CLINICAL PEARL'},
    'pt-BR': {'pearl': 'PÉROLA CLÍNICA'},
    'fr-FR': {'pearl': 'PERLE CLINIQUE'},
    'de-DE': {'pearl': 'KLINISCHE PERLE'},
    'it-IT': {'pearl': 'PERLA CLINICA'},
}

def T(key):
    # La paleta ucp anula etiquetas Oxbridge (tags neutros).
    pk = lang_pack(_UI_LANG)
    if _PALETTE == 'ucp' and key in pk['palette_overrides']:
        return pk['palette_overrides'][key]
    return pk['labels'][key]

# v9.C decisión de geometría (tier b): el ancho de contenido DE FACTO es CONTENT_W
# (borde derecho real 12.65; margen izq 0.65 / der 0.683, asimetría histórica
# aceptada — NO "corregirla" silenciosamente). SAFE_X1 queda documental.
CANVAS_W, CANVAS_H = 13.333, 7.500
SAFE_X0, SAFE_Y0 = 0.650, 1.550
SAFE_X1 = CANVAS_W - SAFE_X0          # 12.683 (documental)
CONTENT_W = 12.0                      # de-facto: x=SAFE_X0 + w=12.0 → borde 12.65

def C(h):
    return RGBColor.from_string(h)

def rect(slide, x, y, w, h, fill=None, line=None, lw=0.5, rounded=True, rad=0.04):
    """Refined box helper with gentle, professional corner rounding."""
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        try: shp.adjustments[0] = rad
        except Exception: pass
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = C(fill)
        _note_surface(fill, x, y, w, h)
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = C(line)
        shp.line.width = Pt(lw)
    shp.shadow.inherit = False
    return shp

def tx(slide, x, y, w, h, text, size=13, color="1C2430", bold=False, italic=False,
       align=None, font=None, anchor=None, sp_after=3, line_sp=1.08, deco=False):
    if font is None:
        font = FONT_BODY
    if align is None: align = PP_ALIGN.LEFT
    if anchor is None: anchor = MSO_ANCHOR.TOP
    _log_text(color, size, bold, deco, x + w / 2.0, y + h / 2.0)
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    lines = text.split("\n") if isinstance(text, str) else text
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(sp_after)
        p.line_spacing = line_sp
        r = p.add_run()
        r.text = ln
        f = r.font
        f.size = Pt(size)
        f.bold = bold
        f.italic = italic
        f.color.rgb = C(color)
        f.name = font
    return box

def para(tf, text, size, color, bold=False, italic=False, align=None,
         font=None, sp_before=0, sp_after=3, first=False, line_sp=1.08, deco=False):
    if font is None:
        font = FONT_BODY
    if align is None: align = PP_ALIGN.LEFT
    box = getattr(tf, '_omc_box', None)
    if box:
        _log_text(color, size, bold, deco, box[0] + box[2] / 2.0, box[1] + box[3] / 2.0)
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(sp_before)
    p.space_after = Pt(sp_after)
    p.line_spacing = line_sp
    r = p.add_run()
    r.text = text
    f = r.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = C(color)
    f.name = font
    return p

def textframe(slide, x, y, w, h, anchor=None):
    if anchor is None: anchor = MSO_ANCHOR.TOP
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    try: tf._omc_box = (float(x), float(y), float(w), float(h))
    except Exception: pass
    return tf

def bg(slide, P, color=None):
    rect(slide, 0, 0, CANVAS_W, 7.5, fill=color or P["bg"], line=None, rounded=False)

def header(slide, P, data, idx):
    """Scholarly editorial header with discrete category kicker and serif title."""
    kicker = data.get("kicker", "")
    title = data.get("title", "")
    if kicker:
        tx(slide, SAFE_X0, 0.32, 11.0, 0.28, kicker.upper(), size=9.5,
           color=_ink(P), bold=True, font=FONT_BODY)
    tx(slide, SAFE_X0, 0.58, CONTENT_W, SAFE_X0, title, size=23, color=P["primary"], bold=True, font=FONT_TITLE)
    rect(slide, SAFE_X0, 1.28, 1.3, 0.03, fill=P["accent"], rounded=False)
    rect(slide, 1.98, 1.29, 10.7, 0.01, fill=P["border"], rounded=False)

def footer(slide, P, idx, course, config=None):
    """Discreet editorial slide footer — SHOW_FOOTER / SHOW_SLIDE_NUMBER toggles (default True)."""
    config = config or {}
    legacy = config.get('SHOW_REFERENCES')  # alias v7.8: una bandera controlaba pie + número
    show_footer = config.get('SHOW_FOOTER', True if legacy is None else legacy)
    show_number = config.get('SHOW_SLIDE_NUMBER', True if legacy is None else legacy)
    if show_footer:
        course_str = course.upper() if course else T('footer')
        tx(slide, SAFE_X0, 7.10, 8.5, 0.28, course_str, size=8.5, color=P["text_muted"], font=FONT_BODY)
    if show_number:
        tx(slide, 11.8, 7.10, 0.9, 0.28, f"§ {idx:02d}", size=9.0, color=P["text_muted"],
           align=PP_ALIGN.RIGHT, font=FONT_TITLE, bold=True)

def footnote(slide, P, data, y=6.75):
    fn = data.get("footnote", "")
    credit = data.get("credit", "")
    combined = fn
    if credit and not fn:
        combined = T('source').format(c=credit)
    elif credit and fn and credit not in fn:
        combined = T('join').format(f=fn, c=credit)
    # v9.2/B4 — trazabilidad visible: si el slide reclama un ATU del ledger,
    # se añade la cita ATU al pie (no bloquea; solo si hay vínculo declarado).
    atu = data.get('atu')
    if isinstance(atu, int) and not isinstance(atu, bool) and _ATU_FOOTNOTE:
        tag = f" · ATU {atu}" if combined else f"ATU {atu}"
        combined = (combined + tag) if combined else tag
    if combined:
        tx(slide, SAFE_X0, y, CONTENT_W, 0.28, combined, size=9.0, color=P["text_muted"], italic=True)

def stack_layout(y0, zone_h, n, gap, cap=None):
    """Capped row height + vertically centered top offset for card stacks."""
    n = max(n, 1)
    row_h = (zone_h - gap * (n - 1)) / n
    if cap:
        row_h = min(row_h, cap)
    return row_h, y0 + (zone_h - (row_h * n + gap * (n - 1))) / 2.0

def row_layout(x0, total_w, n, gap, center=False):
    """v9.B/F5 — hermano horizontal de stack_layout: ancho de ítem + x de inicio.
    center=True centra el grupo dentro de total_w (caso mnemonic)."""
    n = max(n, 1)
    item_w = min((total_w - gap * (n - 1)) / n, total_w) if not center else \
        min(1.35, (total_w - gap * (n - 1)) / n)
    start_x = x0
    if center:
        total = item_w * n + gap * (n - 1)
        start_x = x0 + (total_w - total) / 2.0
    return item_w, start_x


# Image metadata cache: each file opened with PIL exactly once per process.
_IMG_CACHE = {}

def _image_size(path):
    if path in _IMG_CACHE:
        return _IMG_CACHE[path]
    from PIL import Image as _PILImage
    with _PILImage.open(path) as _im:
        size = _im.size
    _IMG_CACHE[path] = size
    return size



def _place_image(slide, path, x, y, w, h, P=None):
    """Places an image with an academic framed border."""
    iw, ih = _image_size(path)
    ar = iw / float(ih)
    box_ar = w / float(h)
    if ar > box_ar:
        pw, ph = w, w / ar
    else:
        pw, ph = h * ar, h
    px = x + (w - pw) / 2.0
    py = y + (h - ph) / 2.0
    if P:
        rect(slide, px - 0.04, py - 0.04, pw + 0.08, ph + 0.08, fill=P["card"],
             line=P["border"], lw=0.75, rounded=True, rad=0.02)
    slide.shapes.add_picture(path, Inches(px), Inches(py), Inches(pw), Inches(ph))

def _set_fill_alpha(shape, opacity_pct):
    """Apply transparency to a solid-filled shape (opacity_pct: 0-100). Needed for venn overlap."""
    from pptx.oxml.ns import qn
    from lxml import etree
    spPr = shape._element.spPr
    sF = spPr.find(qn('a:solidFill'))
    if sF is None:
        return
    clr = sF.find(qn('a:srgbClr'))
    if clr is None:
        return
    for old in clr.findall(qn('a:alpha')):
        clr.remove(old)
    etree.SubElement(clr, qn('a:alpha'), val=str(int(opacity_pct * 1000)))

# ===================== MODULE RENDERERS — CORE & CLASSIC SET =====================

def m_title(slide, d, P, info):
    """Academic title slide with crest layout — supports optional author."""
    bg(slide, P, P["primary"])
    rect(slide, 0, 0, CANVAS_W, 0.18, fill=P["accent"], rounded=False)
    rect(slide, 0, 7.32, CANVAS_W, 0.18, fill=P["accent"], rounded=False)
    rect(slide, 0.8, 0.7, 11.733, 6.1, fill=None, line=P["accent"], lw=1.0, rounded=True, rad=0.03)
    course_name = d.get("course", info.get("course", T('course_default')))
    title_txt = d.get("title") or course_name or T('course_default')  # fallback: course as title
    course_color = _fg_on_primary(P)        # token on_primary
    inst_color = _fg_on_primary_soft(P)     # token on_primary_soft
    sub_color = _sub_primary()
    tx(slide, 1.2, 1.35, 10.933, 0.4, course_name.upper(), size=12, color=course_color,
       bold=True, align=PP_ALIGN.CENTER, font=FONT_BODY)
    tx(slide, 1.2, 2.1, 10.933, 2.1, title_txt, size=38, color="FFFFFF",
       bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE, line_sp=1.08)
    rect(slide, 5.86, 4.45, 1.6, 0.03, fill=P["accent"], rounded=False)
    tx(slide, 1.5, 4.75, 10.333, 0.7, d.get("subtitle", ""), size=15, color=sub_color,
       align=PP_ALIGN.CENTER, italic=True, font=FONT_BODY)
    inst = d.get("institution", info.get("institution", T('institution_default')))
    tx(slide, 1.5, 5.85, 10.333, 0.4, inst.upper(), size=10, color=inst_color,
       align=PP_ALIGN.CENTER, font=FONT_BODY, bold=True)
    author = d.get("author", info.get("author", ""))
    if author:
        tx(slide, 1.5, 6.25, 10.333, 0.35, author, size=11, color="FFFFFF",
           align=PP_ALIGN.CENTER, font=FONT_BODY, italic=True)

def m_section_divider(slide, d, P, info):
    """Section transition divider — supports optional author. BG = primario (UCP: azul estándar #3854CC)."""
    bg(slide, P, P["primary"])
    rect(slide, 0, 0, 0.4, 7.5, fill=P["accent"], rounded=False)
    style = d.get("divider_style", T('chapter'))
    sub_color = _sub_primary()
    if style:
        tx(slide, 1.2, 1.5, 11.0, 0.5, style.upper(), size=14, color=_fg_on_primary(P),
           bold=True, align=PP_ALIGN.LEFT, font=FONT_BODY)
    tx(slide, 1.2, 2.2, 11.0, 1.8, d.get("section_title", ""), size=36, color="FFFFFF",
       bold=True, align=PP_ALIGN.LEFT, font=FONT_TITLE, line_sp=1.1)
    rect(slide, 1.2, 4.25, 2.0, 0.03, fill=P["accent"], rounded=False)
    tx(slide, 1.2, 4.6, 10.5, 1.5, d.get("section_subtitle", ""), size=15, color=sub_color,
       align=PP_ALIGN.LEFT, italic=True, line_sp=1.2, font=FONT_BODY)
    author = d.get("author", info.get("author", ""))
    if author:
        tx(slide, 1.2, 6.3, 10.5, 0.35, author, size=11, color=_fg_on_primary_soft(P),
           align=PP_ALIGN.LEFT, font=FONT_BODY, italic=True)

def m_definition(slide, d, P, info):
    """Academic thesis/definition module with structured proposition cards."""
    img = bool(d.get("image"))
    cw = 7.6 if img else CONTENT_W
    rect(slide, SAFE_X0, SAFE_Y0, cw, 1.45, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    rect(slide, SAFE_X0, SAFE_Y0, 0.09, 1.45, fill=P["primary"], rounded=False)
    pill(slide, 0.95, 1.68, 1.6, 0.24, T('central'), P["soft"], P["primary"], rad=0.08)
    tx(slide, 0.95, 1.98, cw - 0.5, 0.95, d.get("main_statement", ""), size=15.5,
       color=P["primary"], bold=True, font=FONT_TITLE, line_sp=1.1)
    y = 3.15
    if d.get("elaboration"):
        rect(slide, SAFE_X0, y, cw, 0.85, fill=P["soft"], line=P["border"], lw=0.4, rounded=True)
        tx(slide, 0.85, y + 0.12, cw - 0.4, SAFE_X0, d["elaboration"], size=12.0,
           color=P["text"], line_sp=1.15, font=FONT_BODY)
        y += 1.0
    kps = d.get("key_points", [])
    if kps:
        n = len(kps)
        gap = 0.22
        w = (cw - gap * (n - 1)) / n
        ch = 6.6 - y
        for i, kp in enumerate(kps):
            x = SAFE_X0 + i * (w + gap)
            rect(slide, x, y, w, ch, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
            rect(slide, x, y, w, 0.05, fill=P["accent"], rounded=False)
            tf = textframe(slide, x + 0.2, y + 0.18, w - 0.4, ch - 0.3)
            para(tf, kp.get("title", ""), 12.5, P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=4)
            para(tf, kp.get("desc", ""), 11.0, P["text"], line_sp=1.1)
    if img:
        _place_image(slide, d["image"], 8.45, SAFE_Y0, 4.2, 5.0, P)
    footnote(slide, P, d)

def m_flow_diagram(slide, d, P, info):
    """Linear pathway; steps with decision:True render as diamonds (straight arrow = YES,
    bottom corridor bypass to step i+2 = NO, labeled by that step's `desc`)."""
    steps = d.get("steps", [])
    expl = d.get("explanation", "")
    yes_color = _ok_ink(P)
    sub_color = _sub_primary()
    h = 3.6 if expl else 4.6
    y = 1.65
    n = max(len(steps), 1)
    aw = 0.35
    w = (CONTENT_W - aw * (n - 1)) / n
    yb = y + h + 0.22  # NO-branch corridor
    for i, st in enumerate(steps):
        x = SAFE_X0 + i * (w + aw)
        hi = st.get("highlight", False)
        dec = bool(st.get("decision"))
        if dec:
            dsz = min(w * 0.92, h * 0.72)
            dx, dy = x + (w - dsz) / 2.0, y + (h - dsz) / 2.0
            dm = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(dx), Inches(dy), Inches(dsz), Inches(dsz))
            dm.fill.solid(); dm.fill.fore_color.rgb = C(P["card"])
            _note_surface(P["card"], dx, dy, dsz, dsz)
            dm.line.color.rgb = C(P["accent"]); dm.line.width = Pt(1.2)
            dm.shadow.inherit = False
            tf = dm.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = Inches(0.04)
            para(tf, st.get("title", ""), 10.5, P["primary"], bold=True, font=FONT_TITLE,
                 first=True, align=PP_ALIGN.CENTER, sp_after=0, line_sp=1.0)
        else:
            rect(slide, x, y, w, h, fill=(P["primary"] if hi else P["card"]),
                 line=(P["accent"] if hi else P["border"]), lw=1.0 if hi else 0.6, rounded=True)
            badge_bg = P["accent"] if hi else P["soft"]
            badge_fg = _on(P, P["accent"]) if hi else P["primary"]
            pill(slide, x + 0.18, y + 0.18, 0.8, 0.28, st.get("label", f"{T('phase')} {i+1}").upper(),
             badge_bg, badge_fg, size=9, rad=0.08)
            tf = textframe(slide, x + 0.2, y + 0.58, w - 0.4, h - 0.75)
            para(tf, st.get("title", ""), 13.5, "FFFFFF" if hi else P["primary"], bold=True,
                 font=FONT_TITLE, first=True, sp_after=6)
            para(tf, st.get("desc", ""), 11.0, sub_color if hi else P["text"], line_sp=1.1)
        if i < n - 1:
            ax, ay = x + w + 0.05, y + (h / 2.0) - 0.12
            ar = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(ax), Inches(ay), Inches(aw - 0.1), Inches(0.24))
            ar.fill.solid(); ar.fill.fore_color.rgb = C(P["accent"])
            ar.line.fill.background(); ar.shadow.inherit = False
            bypass = dec and (i < n - 2) and not expl
            if dec:
                tx(slide, ax - 0.12, ay - 0.3, 0.6, 0.24, T("yes"), size=8.5,
                   color=yes_color, bold=True, align=PP_ALIGN.CENTER)
                if bypass:  # NO branch: elbow under the row to card i+2
                    xc = x + w / 2.0
                    xt = SAFE_X0 + (i + 2) * (w + aw) + w / 2.0
                    rect(slide, xc - 0.0125, y + h + 0.02, 0.025, yb - (y + h) - 0.02, fill=P["alert"], rounded=False)
                    rect(slide, min(xc, xt), yb, abs(xt - xc), 0.025, fill=P["alert"], rounded=False)
                    up = slide.shapes.add_shape(MSO_SHAPE.UP_ARROW, Inches(xt - 0.09), Inches(y + h + 0.04), Inches(0.18), Inches(0.18))
                    up.fill.solid(); up.fill.fore_color.rgb = C(P["alert"])
                    up.line.fill.background(); up.shadow.inherit = False
                    # v8.3: caption DEBAJO del corredor — antes colisionaba con la línea
                    tx(slide, (xc + xt) / 2.0 - 0.8, yb + 0.06, 1.6, 0.24,
                       st.get("desc") or T("no"), size=8.5, color=P["alert"], bold=True, align=PP_ALIGN.CENTER)
                elif st.get("desc"):
                    # v8.3: sin bypass el corredor no existe; banda reservada a y+h+0.30
                    tx(slide, x + 0.05, y + h + 0.30, w - 0.1, 0.5, st["desc"], size=9.0,
                       color=P["text_muted"], align=PP_ALIGN.CENTER, line_sp=1.0)
        elif dec and st.get("desc"):
            # Decision as final step: no outgoing arrow — show NO-branch caption below.
            tx(slide, x + 0.05, y + h + 0.30, w - 0.1, 0.5, st["desc"], size=9.0,
               color=P["text_muted"], align=PP_ALIGN.CENTER, line_sp=1.0)
    if expl:
        ey = y + h + 0.25
        rect(slide, SAFE_X0, ey, CONTENT_W, 6.6 - ey, fill=P["soft"], line=P["border"], lw=0.5, rounded=True)
        tx(slide, 0.9, ey + 0.1, 11.5, 6.4 - ey, expl, size=11.5, color=P["text"],
           line_sp=1.12, anchor=MSO_ANCHOR.MIDDLE)
    footnote(slide, P, d, y=6.78)

def _render_table_academic(slide, d, P, y_top=1.6, header_key="headers", rows_key="rows"):
    """Oxford/Lancet academic table styling with crisp horizontal rules and soft fills.
    Superficie marcada desconocida durante la tabla: el gate no mide celdas nativas."""
    headers = d.get(header_key, [])
    rows = d.get(rows_key, [])
    if not headers:
        raise KeyError(f"missing '{header_key}' (tabla con rows_key='{rows_key}')")
    with _measure_off():
        takeaway = d.get("takeaway", "")
        tbl_h = (4.3 if takeaway else 4.9)
        gf = slide.shapes.add_table(len(rows) + 1, len(headers),
                                    Inches(SAFE_X0), Inches(y_top), Inches(CONTENT_W), Inches(tbl_h))
        table = gf.table
        cw = d.get("col_widths")
        if cw and len(cw) == len(headers):
            total = sum(cw)
            for j, wgt in enumerate(cw):
                table.columns[j].width = Inches(CONTENT_W * wgt / total)
        for j, htxt in enumerate(headers):
            cell = table.cell(0, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = C(P["primary"])
            cell.margin_left = cell.margin_right = Inches(0.14)
            cell.margin_top = cell.margin_bottom = Inches(0.08)
            tf = cell.text_frame
            tf.word_wrap = True
            para(tf, str(htxt).upper(), 11.0, "FFFFFF", bold=True, font=FONT_TITLE, first=True, sp_after=0)
        for i, row in enumerate(rows):
            is_even = (i % 2 == 0)
            row_bg = P["card"] if is_even else P["soft"]
            for j in range(len(headers)):
                val = row[j] if j < len(row) else ""
                cell = table.cell(i + 1, j)
                cell.fill.solid()
                cell.fill.fore_color.rgb = C(row_bg)
                cell.margin_left = cell.margin_right = Inches(0.14)
                cell.margin_top = cell.margin_bottom = Inches(0.06)
                tf = cell.text_frame
                tf.word_wrap = True
                is_lead = (j == 0)
                para(tf, str(val), 11.0, P["primary"] if is_lead else P["text"],
                     bold=is_lead, font=FONT_BODY, first=True, sp_after=0, line_sp=1.05)
    if takeaway:
        y = y_top + tbl_h + 0.2
        rect(slide, SAFE_X0, y, CONTENT_W, 0.58, fill=P["soft"], line=P["accent"], lw=0.9, rounded=True)
        tx(slide, 0.9, y + 0.05, 11.5, 0.48, T('takeaway') + takeaway,
           size=11.5, color=P["primary"], bold=True, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)

def m_comparison_table(slide, d, P, info):
    _render_table_academic(slide, d, P)
    footnote(slide, P, d, y=6.85)

def m_synthesis_grid(slide, d, P, info):
    _render_table_academic(slide, d, P, rows_key="matrix_data")
    footnote(slide, P, d, y=6.85)

def m_stat_card(slide, d, P, info):
    """Impactful hero metric slide with clinical narrative support."""
    rect(slide, SAFE_X0, SAFE_Y0, 4.4, 4.95, fill=P["primary"], line=None, rounded=True)
    rect(slide, SAFE_X0, SAFE_Y0, 4.4, 0.06, fill=P["accent"], rounded=False)
    tx(slide, 0.85, 2.2, 4.0, 1.6, d.get("stat_num", ""), size=52, color=_fg_on_primary(P),
       bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE)
    # Barra divisoria centrada respecto al bloque del dígito (x .85 w 4.0 → centro 2.85).
    rect(slide, 2.25, 4.0, 1.2, 0.025, fill=P["accent"], rounded=False)
    tx(slide, 0.9, 4.25, 3.9, 1.8, d.get("stat_title", ""), size=13.5, color="FFFFFF",
       align=PP_ALIGN.CENTER, line_sp=1.15, font=FONT_BODY)
    img = bool(d.get("image"))
    bw = 3.6 if img else 7.3
    bx = 4.25 if img else 5.35
    blocks = d.get("narrative_blocks", [])
    n = max(len(blocks), 1)
    gap = 0.2
    bh = (4.95 - gap * (n - 1)) / n
    for i, b in enumerate(blocks):
        y = SAFE_Y0 + i * (bh + gap)
        rect(slide, bx, y, bw, bh, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, bx, y, 0.06, bh, fill=P["accent"], rounded=False)
        tf = textframe(slide, bx + 0.25, y + 0.12, bw - 0.45, bh - 0.24, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, b.get("title", ""), 12.5, P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=3)
        para(tf, b.get("desc", ""), 11.0, P["text"], line_sp=1.1)
    if img:
        _place_image(slide, d["image"], 8.05, SAFE_Y0, 4.6, 4.95, P)
    footnote(slide, P, d)

def m_checklist(slide, d, P, info):
    """Clinical protocol verification checklist."""
    items = d.get("items", [])
    ok_color = _ok_ink(P)
    n = max(len(items), 1)
    gap = 0.16
    ih, y_first = stack_layout(SAFE_Y0, 4.95, n, gap, cap=1.0)
    rw = 7.5 if d.get("image") else CONTENT_W
    for i, it in enumerate(items):
        y = y_first + i * (ih + gap)
        checked = it.get("checked", True)
        mark, mcol = ("✓", ok_color) if checked else ("✕", P["alert"])
        rect(slide, SAFE_X0, y, rw, ih, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, 0.85, y + (ih / 2.0) - 0.18, 0.36, 0.36, fill=P["soft"], line=mcol, lw=1.2, rounded=True, rad=0.08)
        tx(slide, 0.85, y + (ih / 2.0) - 0.20, 0.36, 0.36, mark, size=14, color=mcol, bold=True, align=PP_ALIGN.CENTER)
        tf = textframe(slide, 1.4, y + 0.08, rw - 0.85, ih - 0.16, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, it.get("label", ""), 12.5, P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=2)
        if it.get("desc"):
            para(tf, it["desc"], 10.8, P["text"], line_sp=1.05)
    if d.get("image"):
        _place_image(slide, d["image"], 8.35, SAFE_Y0, 4.3, 4.95, P)
    footnote(slide, P, d)

def m_fixed_schema_card(slide, d, P, info):
    """Structured diagnostic criteria / entity schema."""
    fields = d.get("fields", [])
    n = max(len(fields), 1)
    gap = 0.16
    fh, y_first = stack_layout(SAFE_Y0, 4.95, n, gap, cap=1.1)
    for i, f in enumerate(fields):
        y = y_first + i * (fh + gap)
        rect(slide, SAFE_X0, y, 3.4, fh, fill=P["primary"], line=None, rounded=True)
        tx(slide, 0.85, y, 3.0, fh, f.get("label", "").upper(), size=11.0, color=_on(P, P["primary"]),
           bold=True, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        rect(slide, 4.15, y, 8.5, fh, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        tx(slide, 4.35, y, 8.1, fh, f.get("value", ""), size=11.5, color=P["text"],
           anchor=MSO_ANCHOR.MIDDLE, line_sp=1.1)
    footnote(slide, P, d)

def _render_column_card(slide, P, x, w, card, accent_color):
    rect(slide, x, SAFE_Y0, w, 4.95, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    rect(slide, x, SAFE_Y0, w, 0.48, fill=accent_color, rounded=False)
    tx(slide, x + 0.25, 1.62, w - 0.5, 0.35, card.get("header", "").upper(), size=10.5,
       color=_on(P, accent_color), bold=True, font=FONT_BODY)
    tx(slide, x + 0.25, 2.15, w - 0.5, 0.55, card.get("title", ""), size=15.0,
       color=P["primary"], bold=True, font=FONT_TITLE)
    tf = textframe(slide, x + 0.25, 2.75, w - 0.5, 3.6)
    for i, pt in enumerate(card.get("points", [])):
        para(tf, "• " + pt, 11.2, P["text"], first=(i == 0), sp_after=7, line_sp=1.1)

def m_side_by_side(slide, d, P, info):
    """Dichotomous comparative module (e.g., Condition A vs Condition B)."""
    m_w = 5.88
    _render_column_card(slide, P, SAFE_X0, m_w, d.get("left_card", {}), P["primary"])
    _render_column_card(slide, P, 6.77, m_w, d.get("right_card", {}), P["accent"])
    footnote(slide, P, d)

def m_taxonomy_tree(slide, d, P, info):
    """Hierarchical classification tree."""
    cats = d.get("categories", [])
    ink = _ink(P)
    n = max(len(cats), 1)
    gap = 0.28
    w, _x0 = row_layout(SAFE_X0, CONTENT_W, n, gap)
    root = d.get("root", d.get("title", ""))
    rect(slide, 4.15, 1.5, 5.0, 0.55, fill=P["primary"], line=None, rounded=True)
    tx(slide, 4.25, 1.5, 4.8, 0.55, root.upper(), size=12.5, color="FFFFFF", bold=True,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
    rect(slide, 6.64, 2.05, 0.02, 0.35, fill=P["accent"], rounded=False)
    rect(slide, SAFE_X0 + w / 2, 2.4, CONTENT_W - w, 0.02, fill=P["accent"], rounded=False)
    for i, c in enumerate(cats):
        x = SAFE_X0 + i * (w + gap)
        rect(slide, x + w / 2 - 0.01, 2.4, 0.02, 0.3, fill=P["accent"], rounded=False)
        rect(slide, x, 2.7, w, 3.85, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, x, 2.7, w, 0.45, fill=P["soft"], rounded=False)
        tx(slide, x + 0.15, 2.75, w - 0.3, 0.35, c.get("name", "").upper(), size=11.0,
           color=P["primary"], bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE)
        tf = textframe(slide, x + 0.2, 3.25, w - 0.4, 3.2)
        para(tf, c.get("property", ""), 11.0, ink, italic=True, font=FONT_BODY, first=True, sp_after=6)
        for ex in c.get("examples", []):
            para(tf, "• " + ex, 10.5, P["text"], sp_after=4, line_sp=1.08)
    footnote(slide, P, d)

def m_algorithm(slide, d, P, info):
    """Clinical algorithmic cascade with decision medallions."""
    steps = d.get("steps", [])
    n = max(len(steps), 1)
    gap = 0.16
    sh, y_first = stack_layout(SAFE_Y0, 4.95, n, gap, cap=1.2)
    for i, st in enumerate(steps):
        y = y_first + i * (sh + gap)
        hi = st.get("highlight", False)
        med_fill = P["accent"] if hi else P["primary"]
        rect(slide, SAFE_X0, y, 0.9, sh, fill=med_fill, line=None, rounded=True)
        tx(slide, SAFE_X0, y, 0.9, sh, st.get("label", f"{i+1:02d}"), size=16, color=_on(P, med_fill),
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        if i < n - 1:
            rect(slide, 1.09, y + sh, 0.02, gap, fill=P["border"], rounded=False)
        rect(slide, 1.7, y, 10.95, sh, fill=P["card"],
             line=P["accent"] if hi else P["border"], lw=1.0 if hi else 0.6, rounded=True)
        tf = textframe(slide, 1.95, y + 0.08, 10.4, sh - 0.16, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, st.get("title", ""), 12.5, P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=2)
        if st.get("desc"):
            para(tf, st["desc"], 10.8, P["text"], line_sp=1.05)
    footnote(slide, P, d)

def m_case_block(slide, d, P, info):
    """NEJM-styled clinical vignette presentation card."""
    img = bool(d.get("image"))
    ink = _ink(P)
    lw = 4.6 if img else 5.85
    rx = 5.45 if img else 6.75
    rw = 4.6 if img else 5.9
    tw = lw - 0.4
    rect(slide, SAFE_X0, SAFE_Y0, lw, 2.15, fill=P["primary"], line=None, rounded=True)
    tx(slide, 0.85, 1.7, tw, 0.25, T('vignette'), size=9.5, color=_fg_on_primary(P),
       bold=True, font=FONT_BODY)
    tx(slide, 0.85, 1.98, tw, 1.6, d.get("case_stem", ""), size=11.5, color="FFFFFF", line_sp=1.1, font=FONT_BODY)
    rect(slide, SAFE_X0, 3.85, lw, 2.65, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    tf = textframe(slide, 0.85, 4.0, tw, 2.4)
    para(tf, T('findings'), 10.0, ink, bold=True, font=FONT_BODY, first=True, sp_after=5)
    for fdg in d.get("findings", []):
        para(tf, "• " + fdg, 10.5 if img else 11.0, P["text"], sp_after=3, line_sp=1.05)
    rect(slide, rx, SAFE_Y0, rw, 2.15, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    tf_r = textframe(slide, rx + 0.25, 1.7, rw - 0.5, 1.9)
    para(tf_r, T('reasoning'), 10.0, ink, bold=True, font=FONT_BODY, first=True, sp_after=4)
    para(tf_r, d.get("reasoning", ""), 10.8, P["text"], line_sp=1.1)
    rect(slide, rx, 3.85, rw, 1.15, fill=P["soft"], line=P["accent"], lw=0.9, rounded=True)
    tf_d = textframe(slide, rx + 0.25, 3.95, rw - 0.5, 0.95, anchor=MSO_ANCHOR.MIDDLE)
    para(tf_d, T('diagnosis'), 9.5, P["alert"], bold=True, first=True, sp_after=2)
    para(tf_d, d.get("diagnosis", ""), 12.5, P["primary"], bold=True, font=FONT_TITLE)
    rect(slide, rx, 5.15, rw, 1.35, fill=P["accent"], line=None, rounded=True)
    pearl_fg = _on(P, P["accent"])
    tf_p = textframe(slide, rx + 0.25, 5.25, rw - 0.5, 1.15, anchor=MSO_ANCHOR.MIDDLE)
    para(tf_p, T('pearl'), 9.5, pearl_fg, bold=True, first=True, sp_after=2)
    para(tf_p, d.get("clinical_pearl", ""), 10.8, pearl_fg, line_sp=1.08)
    if img:
        _place_image(slide, d["image"], 10.25, SAFE_Y0, 2.4, 4.95, P)
    footnote(slide, P, d)

def m_figure(slide, d, P, info):
    """Full-bleed clinical figure showcase."""
    _place_image(slide, d["image"], SAFE_X0, SAFE_Y0, CONTENT_W, 4.75, P)
    caption_txt = d.get("caption", "")
    if caption_txt:
        tx(slide, SAFE_X0, 6.4, CONTENT_W, 0.28, caption_txt, size=10.0, color=P["text"], italic=True)
    footnote(slide, P, d, y=6.75)

# ===================== MODULE RENDERERS — DIAGRAM EXTENSIONS =====================

_TIMELINE_MAX = 5  # v8.3/v8.4: cap único compartido por renderer y contrato lint

def m_timeline(slide, d, P, info):
    """Chronological axis with alternating milestone cards."""
    miles = d.get("milestones", [])[:_TIMELINE_MAX]  # defensa silenciosa; el lint bloquea >cap
    ink = _ink(P)
    n = max(len(miles), 1)
    y_mid, x0, x1 = 4.0, 1.0, 12.35
    rect(slide, x0, y_mid, x1 - x0, 0.035, fill=P["accent"], rounded=False)
    span = (x1 - x0) / n
    for i, ms in enumerate(miles):
        cx = x0 + span * (i + 0.5)
        up = (i % 2 == 0)
        cw = min(span - 0.3, 2.6)
        ch = 1.7 if n <= 4 else 2.05
        fsz = 10.2 if n <= 4 else 9.3
        cy = (y_mid - 0.25 - ch) if up else y_mid + 0.25
        rect(slide, cx - 0.09, y_mid - 0.075, 0.18, 0.18, fill=P["primary"], rounded=True, rad=0.5)
        if i == 0:  # jerarquía sin depender del color: anillo en el hito inicial
            ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - 0.13), Inches(y_mid - 0.135),
                                          Inches(0.26), Inches(0.26))
            ring.fill.background()
            ring.line.color.rgb = C(P["accent"]); ring.line.width = Pt(1.5)
            ring.shadow.inherit = False
        if up:
            rect(slide, cx - 0.01, cy + ch, 0.02, (y_mid - 0.09) - (cy + ch), fill=P["border"], rounded=False)
        else:
            rect(slide, cx - 0.01, y_mid + 0.11, 0.02, cy - (y_mid + 0.11), fill=P["border"], rounded=False)
        rect(slide, cx - cw / 2, cy, cw, ch, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, cx - cw / 2, cy, cw, 0.05, fill=P["accent"] if up else P["primary"], rounded=False)
        tf = textframe(slide, cx - cw / 2 + 0.15, cy + 0.15, cw - 0.3, ch - 0.3)
        para(tf, ms.get("label", ""), 9.5, ink, bold=True, first=True, sp_after=2)
        para(tf, ms.get("title", ""), 12.0, P["primary"], bold=True, font=FONT_TITLE, sp_after=3)
        if ms.get("desc"):
            para(tf, ms["desc"], fsz, P["text"], line_sp=1.05)
    footnote(slide, P, d)

def m_cycle_diagram(slide, d, P, info):
    """Closed-loop process (3–6 nodes) con flechas de cuerda rotadas y hub opcional;
    geometría calibrada contra el solape con el centro."""
    nodes = d.get("nodes", [])
    sub_color = _sub_primary()
    n = max(len(nodes), 1)
    cx = 6.666
    cy = 4.0 if n <= 4 else 3.85
    R = 2.35 if n <= 4 else 2.20
    card_w, card_h = 2.4, 1.15
    centers = []
    for i in range(n):
        rad = _math.radians(-90 + i * (360.0 / n))
        centers.append((cx + R * _math.cos(rad), cy + R * _math.sin(rad) * 0.82))
    for i in range(n):
        x1, y1 = centers[i]
        x2, y2 = centers[(i + 1) % n]
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        vx, vy = mx - cx, my - cy
        dist = _math.hypot(vx, vy) or 1.0
        mx += 0.5 * vx / dist; my += 0.5 * vy / dist  # push arrow outward, clear of hub
        ang = _math.degrees(_math.atan2(y2 - y1, x2 - x1))
        ar = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(mx - 0.22), Inches(my - 0.11), Inches(0.44), Inches(0.22))
        ar.rotation = ang
        ar.fill.solid(); ar.fill.fore_color.rgb = C(P["accent"])
        ar.line.fill.background(); ar.shadow.inherit = False
    for i, (cxx, cyy) in enumerate(centers):
        nd = nodes[i]
        hi = nd.get("highlight", False)
        rect(slide, cxx - card_w / 2, cyy - card_h / 2, card_w, card_h,
             fill=P["primary"] if hi else P["card"],
             line=P["accent"] if hi else P["border"], lw=1.0 if hi else 0.6, rounded=True)
        tf = textframe(slide, cxx - card_w / 2 + 0.12, cyy - card_h / 2 + 0.1, card_w - 0.24, card_h - 0.2, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, nd.get("title", ""), 11.5, "FFFFFF" if hi else P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=2)
        if nd.get("desc"):
            para(tf, nd["desc"], 9.5, sub_color if hi else P["text"], line_sp=1.05)
    if d.get("center_label"):
        # Hub compacto para evitar solape con las tarjetas laterales.
        rect(slide, cx - 0.85, cy - 0.35, 1.7, 0.70, fill=P["soft"], line=P["accent"], lw=0.9, rounded=True, rad=0.12)
        tx(slide, cx - 0.75, cy - 0.35, 1.5, 0.70, d["center_label"], size=10, color=P["primary"],
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
    footnote(slide, P, d)

def m_quadrant_matrix(slide, d, P, info):
    """2x2 matrix (TL, TR, BL, BR) with optional axis labels."""
    quads = d.get("quadrants", [])
    # v8.3: cuadrantes suben a y0=SAFE_Y0 (inicio estándar de contenido) — la etiqueta X
    # gana ~0.16in de aire sobre el footnote en vez de rozarlo.
    x0, y0, qw, qh, gap = 2.3, SAFE_Y0, 4.9, 2.4, 0.12
    if d.get("y_label"):
        lb = slide.shapes.add_textbox(Inches(0.35), Inches(y0), Inches(0.5), Inches(2 * qh + gap))
        tf = lb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = d["y_label"].upper()
        r.font.size = Pt(10); r.font.bold = True
        r.font.color.rgb = C(P["text_muted"]); r.font.name = FONT_BODY
        lb.rotation = 270
    if d.get("x_label"):
        tx(slide, x0, y0 + 2 * qh + gap + 0.12, 2 * qw + gap, 0.3, d["x_label"].upper(),
           size=10, color=P["text_muted"], align=PP_ALIGN.CENTER, bold=True)
    coords = [(x0, y0), (x0 + qw + gap, y0), (x0, y0 + qh + gap), (x0 + qw + gap, y0 + qh + gap)]
    accents = [P["primary"], P["accent"], P["accent"], P["primary"]]
    for (qx0, qy0), q, ac in zip(coords, quads, accents):
        rect(slide, qx0, qy0, qw, qh, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, qx0, qy0, qw, 0.05, fill=ac, rounded=False)
        tf = textframe(slide, qx0 + 0.2, qy0 + 0.15, qw - 0.4, qh - 0.3)
        para(tf, q.get("title", ""), 13.0, P["primary"], bold=True, font=FONT_TITLE, first=True, sp_after=4)
        for pt in q.get("points", []):
            para(tf, "• " + pt, 10.8, P["text"], sp_after=3, line_sp=1.08)
    footnote(slide, P, d)

def m_pyramid(slide, d, P, info):
    """Step-pyramid hierarchy; levels[0] = base. Side annotations to the right."""
    levels = d.get("levels", [])
    n = max(len(levels), 1)
    base_w, cx = 8.2, 6.666
    lh = min(0.95, 4.6 / n)
    stack_h = n * lh + 0.08 * (n - 1)
    top0 = SAFE_Y0 + (4.95 - stack_h) / 2.0
    for i, lv in enumerate(levels):
        w = base_w * (i + 1) / n
        ly = top0 + stack_h - (i + 1) * lh - 0.08 * i
        hi = lv.get("highlight", False)
        lv_fill = P["primary"] if hi else P["card"]
        rect(slide, cx - w / 2, ly, w, lh, fill=lv_fill,
             line=P["accent"] if hi else P["border"], lw=0.8 if hi else 0.6, rounded=True)
        tx(slide, cx - w / 2 + 0.25, ly, w - 0.5, lh, lv.get("title", ""), size=12,
           color="FFFFFF" if hi else P["primary"], bold=True, anchor=MSO_ANCHOR.MIDDLE,
           align=PP_ALIGN.CENTER, font=FONT_TITLE)
        if lv.get("desc"):
            tx(slide, cx + base_w / 2 + 0.25, ly, 1.6, lh, lv["desc"], size=9.5,
               color=P["text_muted"], anchor=MSO_ANCHOR.MIDDLE, line_sp=1.05)
    footnote(slide, P, d)

# ===================== MODULE RENDERERS — SCHOLARLY PACK =====================

def m_quote_block(slide, d, P, info):
    """Epigraph: seminal quotation in scholarly serif with attribution."""
    tx(slide, 1.0, 1.45, 1.4, 1.3, '\u201C', size=88, color=P["accent"], bold=True,
       font=FONT_TITLE, deco=True)  # ornamento exento del gate
    tx(slide, 2.2, 1.9, 9.4, 2.3, d.get("quote", ""), size=20, color=P["text"], italic=True,
       font=FONT_TITLE, align=PP_ALIGN.CENTER, line_sp=1.25)
    rect(slide, 5.87, 4.45, 1.6, 0.03, fill=P["accent"], rounded=False)
    tx(slide, 2.2, 4.65, 9.4, 0.35, "— " + d.get("author", "").upper(), size=13, color=P["primary"],
       bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE)
    src = " · ".join(x for x in (d.get("source", ""), d.get("year", "")) if x)
    if src:
        tx(slide, 2.2, 5.02, 9.4, 0.3, src, size=10.5, color=P["text_muted"],
           italic=True, align=PP_ALIGN.CENTER)
    if d.get("context"):
        rect(slide, 2.2, 5.55, 9.4, 0.8, fill=P["soft"], line=P["border"], lw=0.4, rounded=True)
        tx(slide, 2.45, 5.66, 8.9, 0.6, d["context"], size=10.5, color=P["text"],
           align=PP_ALIGN.CENTER, line_sp=1.1)
    footnote(slide, P, d)

def m_socratic_question(slide, d, P, info):
    """Oxford tutorial prompt: hero question + numbered reasoning scaffold."""
    ink = _ink(P)
    ov = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.75), Inches(1.8), Inches(1.5), Inches(1.5))
    ov.fill.solid(); ov.fill.fore_color.rgb = C(P["primary"])
    _note_surface(P["primary"], 0.75, 1.8, 1.5, 1.5)
    ov.line.color.rgb = C(P["accent"]); ov.line.width = Pt(1.5)
    ov.shadow.inherit = False
    otf = ov.text_frame
    otf.word_wrap = False
    otf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(otf, "?", 44, "FFFFFF", bold=True, font=FONT_TITLE, first=True, align=PP_ALIGN.CENTER, sp_after=0)
    tx(slide, 2.55, 1.75, 9.9, 0.3, T('tutorial'), size=10, color=ink, bold=True)
    tx(slide, 2.55, 2.1, 9.9, 1.6, d.get("question", ""), size=20, color=P["primary"],
       italic=True, font=FONT_TITLE, line_sp=1.2)
    if d.get("context"):
        tx(slide, 2.55, 3.75, 9.9, 0.45, d["context"], size=10.5,
           color=P["text_muted"], line_sp=1.15)
    sc = d.get("scaffold", [])
    n = len(sc)
    if n:
        gap = 0.25
        w, sx = row_layout(SAFE_X0, CONTENT_W, n, gap)
        for i, s in enumerate(sc):
            x = sx + i * (w + gap)
            rect(slide, x, 4.35, w, 1.75, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
            rect(slide, x, 4.35, w, 0.05, fill=P["accent"], rounded=False)
            bd = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.18), Inches(4.55), Inches(0.4), Inches(0.4))
            bd.fill.solid(); bd.fill.fore_color.rgb = C(P["primary"])
            _note_surface(P["primary"], x + 0.18, 4.55, 0.4, 0.4)
            bd.line.fill.background(); bd.shadow.inherit = False
            btf = bd.text_frame
            btf.word_wrap = False
            btf.vertical_anchor = MSO_ANCHOR.MIDDLE
            para(btf, str(i + 1), 12, "FFFFFF", bold=True, first=True, align=PP_ALIGN.CENTER, sp_after=0)
            tf = textframe(slide, x + 0.7, 4.55, w - 0.9, 1.4)
            para(tf, s, 10.8, P["text"], first=True, line_sp=1.12)
    if d.get("reading"):
        tx(slide, SAFE_X0, 6.42, CONTENT_W, 0.3, d["reading"], size=9.5, color=P["text_muted"], italic=True)
    footnote(slide, P, d)

def m_oxford_union(slide, d, P, info):
    """Union-style motion debate: motion banner, proposition vs opposition, verdict."""
    rect(slide, SAFE_X0, 1.5, CONTENT_W, 1.15, fill=P["primary"], line=None, rounded=True)
    tx(slide, 0.95, 1.62, 11.4, 0.28, T('house'), size=9.5, color=_fg_on_primary(P), bold=True)
    tx(slide, 0.95, 1.92, 11.4, 0.68, '"' + d.get("motion", "") + '"', size=17, color="FFFFFF",
       bold=True, font=FONT_TITLE, line_sp=1.05)
    for x, key, bar in ((SAFE_X0, 'pro_card', P["primary"]), (6.77, 'con_card', P["accent"])):
        card = d.get(key, {})
        rect(slide, x, 2.9, 5.88, 2.95, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, x, 2.9, 5.88, 0.44, fill=bar, rounded=False)
        tx(slide, x + 0.25, 2.97, 5.38, 0.32, card.get("title", "").upper(), size=10.5,
           color=_on(P, bar), bold=True)
        tf = textframe(slide, x + 0.25, 3.5, 5.38, 2.2)
        for i, p in enumerate(card.get("points", [])):
            para(tf, "• " + p, 11.0, P["text"], first=(i == 0), sp_after=6, line_sp=1.1)
    rect(slide, SAFE_X0, 6.05, CONTENT_W, 0.6, fill=P["soft"], line=P["accent"], lw=0.9, rounded=True)
    tx(slide, 0.9, 6.1, 11.5, 0.5, T('verdict') + " " + d.get("verdict", ""), size=11,
       color=P["primary"], bold=True, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
    footnote(slide, P, d, y=6.85)

def m_evidence_card(slide, d, P, info):
    """Landmark trial appraisal: PICO rows + effect hero + limitation strip."""
    rect(slide, SAFE_X0, 1.5, CONTENT_W, 0.95, fill=P["primary"], line=None, rounded=True)
    tx(slide, 0.95, 1.6, 9.0, 0.5, d.get("study_name", ""), size=17, color="FFFFFF",
       bold=True, font=FONT_TITLE)
    if d.get("year"):
        rect(slide, 10.85, 1.64, 1.5, 0.38, fill=P["accent"], line=None, rounded=True, rad=0.12)
        tx(slide, 10.85, 1.64, 1.5, 0.38, str(d["year"]), size=11, color=_on(P, P["accent"]),
           bold=True, align=PP_ALIGN.CENTER)
    design_color = _fg_on_primary_soft(P)   # token on_primary_soft
    pico_color = _fg_on_primary(P)          # token on_primary
    tx(slide, 0.95, 2.06, 9.6, 0.3, d.get("design", "").upper(), size=9.5, color=design_color, bold=True)
    rows = [(l, d.get(f, "")) for l, f in (('P', 'population'), ('I', 'intervention'),
            ('C', 'comparison'), ('O', 'outcome')) if d.get(f)]
    rh, gp = 0.85, 0.12
    for i, (ltr, txt) in enumerate(rows):
        y = 2.65 + i * (rh + gp)
        rect(slide, SAFE_X0, y, 0.55, 0.55, fill=P["primary"], line=None, rounded=True, rad=0.15)
        tx(slide, SAFE_X0, y, 0.55, 0.55, ltr, size=15, color=pico_color, bold=True,
           align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        tx(slide, 1.35, y, 6.5, rh, txt, size=11.0, color=P["text"], line_sp=1.1)
    rect(slide, 8.15, 2.65, 4.5, 1.7, fill=P["accent"], line=None, rounded=True)
    hero_fg = _on(P, P["accent"])
    tx(slide, 8.3, 2.82, 4.2, 0.9, d.get("effect", ""), size=36, color=hero_fg,
       bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE)
    tx(slide, 8.35, 3.78, 4.1, 0.45, d.get("effect_desc", ""), size=10.5, color=hero_fg,
       align=PP_ALIGN.CENTER, line_sp=1.05)
    if d.get("limitation"):
        rect(slide, 8.15, 4.55, 4.5, 1.85, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, 8.15, 4.55, 0.06, 1.85, fill=P["alert"], rounded=False)
        tx(slide, 8.4, 4.7, 4.0, 0.28, T('limitation'), size=9, color=P["alert"], bold=True)
        tx(slide, 8.4, 5.0, 4.0, 1.3, d["limitation"], size=10.5, color=P["text"], line_sp=1.1)
    footnote(slide, P, d, y=6.85)  # credit = full citation (Vancouver)

def m_viva_question(slide, d, P, info):
    """Viva voce: question card, model answer, examiner's note."""
    ink = _ink(P)
    rect(slide, SAFE_X0, SAFE_Y0, 5.7, 4.95, fill=P["primary"], line=None, rounded=True)
    tx(slide, 0.95, 1.75, 5.1, 0.3, T('viva'), size=10, color=_fg_on_primary(P), bold=True)
    if d.get("difficulty"):
        pill(slide, 0.95, 2.13, 1.7, 0.34, d["difficulty"].upper(), P["accent"], _on(P, P["accent"]))
    tx(slide, 0.95, 2.65, 5.1, 3.6, d.get("prompt", ""), size=16, color="FFFFFF",
       font=FONT_TITLE, line_sp=1.2)
    rect(slide, 6.55, SAFE_Y0, 6.1, 2.75, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    tx(slide, 6.8, 1.72, 5.6, 0.3, T('model_answer'), size=10, color=ink, bold=True)
    tx(slide, 6.8, 2.12, 5.6, 2.0, d.get("model_answer", ""), size=11.5, color=P["text"], line_sp=1.12)
    rect(slide, 6.55, 4.5, 6.1, 2.0, fill=P["soft"], line=P["border"], lw=0.6, rounded=True)
    rect(slide, 6.55, 4.5, 0.06, 2.0, fill=P["alert"], rounded=False)
    tx(slide, 6.8, 4.65, 5.6, 0.3, T('examiner'), size=10, color=P["alert"], bold=True)
    tx(slide, 6.8, 5.02, 5.6, 1.35, d.get("examiner_note", ""), size=10.8, color=P["text"], line_sp=1.1)
    footnote(slide, P, d)

def m_mnemonic_card(slide, d, P, info):
    """Acronym expansion: letter medallions + aligned terms + clinical use panel."""
    ink = _ink(P)
    acr = d.get("acronym", "")
    exp = d.get("expansion", [])
    n = max(len(acr), 1)
    gap = 0.15
    cw = min(1.35, (CONTENT_W - gap * (n - 1)) / n)
    total = cw * n + gap * (n - 1)
    x0 = SAFE_X0 + (CONTENT_W - total) / 2.0
    if d.get("domain"):
        pill(slide, 10.55, 1.20, 2.1, 0.34, d["domain"].upper(), P["soft"], P["primary"])
    for i, ch in enumerate(acr):
        x = x0 + i * (cw + gap)
        rect(slide, x, 1.95, cw, 0.95, fill=P["primary"], line=None, rounded=True, rad=0.12)
        tx(slide, x, 1.95, cw, 0.95, ch.upper(), size=28, color="FFFFFF", bold=True,
           align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        tx(slide, x - 0.15, 3.0, cw + 0.3, 0.8, exp[i] if i < len(exp) else "", size=9.5,
           color=P["text"], align=PP_ALIGN.CENTER, line_sp=1.05)
    rect(slide, SAFE_X0, 4.1, CONTENT_W, 1.7, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    rect(slide, SAFE_X0, 4.1, CONTENT_W, 0.05, fill=P["accent"], rounded=False)
    tx(slide, 0.95, 4.28, 11.4, 0.3, T('clinical_use'), size=10, color=ink, bold=True)
    tx(slide, 0.95, 4.62, 11.4, 1.05, d.get("usage", ""), size=12, color=P["text"], line_sp=1.15)
    footnote(slide, P, d)

def m_etymology(slide, d, P, info):
    """Philological deconstruction: colored term fragments + root cards."""
    roots = d.get("roots", [])
    frags = d.get("fragments", [])
    ink = _ink(P)
    tf = textframe(slide, SAFE_X0, 1.85, CONTENT_W, 1.25)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    frag_cols = [P["primary"], ink]  # v8.3: sin alert rojo decorativo (semántica falsa)
    parts = frags if (frags and len(frags) == len(roots)) else [d.get("term", "")]
    for i, fr in enumerate(parts):
        r = p.add_run()
        r.text = fr
        r.font.size = Pt(40)
        r.font.bold = True
        r.font.name = FONT_TITLE
        r.font.color.rgb = C(frag_cols[i % 3] if len(parts) > 1 else P["primary"])
    rect(slide, 5.87, 3.2, 1.6, 0.03, fill=P["accent"], rounded=False)
    n = max(len(roots), 1)
    gap = 0.3
    w, sx = row_layout(SAFE_X0, CONTENT_W, n, gap)
    for i, rt in enumerate(roots):
        x = sx + i * (w + gap)
        rect(slide, x, 3.5, w, 1.85, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, x, 3.5, w, 0.05, fill=P["accent"], rounded=False)
        tfc = textframe(slide, x + 0.2, 3.68, w - 0.4, SAFE_Y0)
        para(tfc, rt.get("part", ""), 15, P["primary"], bold=True, font=FONT_TITLE, first=True,
             sp_after=3, align=PP_ALIGN.CENTER)
        para(tfc, T('origin') + " · " + rt.get("origin", "").upper(), 9, ink, bold=True,
             sp_after=5, align=PP_ALIGN.CENTER)
        para(tfc, rt.get("meaning", ""), 10.5, P["text"], line_sp=1.1, align=PP_ALIGN.CENTER)
    rect(slide, SAFE_X0, 5.6, CONTENT_W, 0.8, fill=P["soft"], line=P["border"], lw=0.4, rounded=True)
    tx(slide, 0.9, 5.68, 11.5, 0.28, T('modern_use'), size=9.5, color=ink, bold=True)
    tx(slide, 0.9, 5.96, 11.5, 0.38, d.get("modern", ""), size=11.5, color=P["primary"], bold=True)
    footnote(slide, P, d)

def m_venn_diagram(slide, d, P, info):
    """Set overlap (2-3 translucent circles); 'shared' = intersection zone (con halo)."""
    sets_l = d.get("sets", [])
    shared = d.get("shared", [])
    n = len(sets_l)
    def _circle(cx, cy, r, color):
        ov = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r), Inches(cy - r),
                                    Inches(2 * r), Inches(2 * r))
        ov.fill.solid(); ov.fill.fore_color.rgb = C(color)
        ov.line.color.rgb = C(P["border"]); ov.line.width = Pt(1.25)
        ov.shadow.inherit = False
        _set_fill_alpha(ov, 42)
    def _halo(cx, cy, w, h):
        shp = rect(slide, cx - w / 2 - 0.05, cy - h / 2 - 0.05, w + 0.10, h + 0.10,
                   fill=P["card"], line=None, rounded=True, rad=0.10)
        _set_fill_alpha(shp, 88)
    def _items(cx, cy, w, h, items, size=10.5):
        if not items:
            return
        tfi = textframe(slide, cx - w / 2, cy - h / 2, w, h, anchor=MSO_ANCHOR.MIDDLE)
        for i, it in enumerate(items):
            para(tfi, "• " + it, size, P["text"], first=(i == 0), sp_after=4,
                 line_sp=1.08, align=PP_ALIGN.CENTER)
    def _label(cx, y, text):
        tx(slide, cx - 1.35, y, 2.7, 0.32, str(text).upper(), size=11, color=P["primary"],
           bold=True, align=PP_ALIGN.CENTER, font=FONT_TITLE)
    if n == 3:
        for (cx, cyy), col in zip(((6.666, 3.0), (5.35, 4.85), (7.98, 4.85)),
                                  (P["primary"], P["accent"], P["primary"])):
            _circle(cx, cyy, 1.5, col)
        _label(6.666, 1.5, sets_l[0].get("label", ""))
        _label(5.35, 6.45, sets_l[1].get("label", ""))
        _label(7.98, 6.45, sets_l[2].get("label", ""))
        # v8.3: zonas de ítems ampliadas y fuente menor — 3-4 ítems ya no desbordan la lente
        _items(6.666, 2.40, 1.9, 1.3, sets_l[0].get("items", []), size=9.5)
        _items(4.50, 5.42, 1.7, 1.5, sets_l[1].get("items", []), size=9.5)
        _items(8.83, 5.42, 1.7, 1.5, sets_l[2].get("items", []), size=9.5)
        _halo(6.666, 4.3, 1.35, 0.95)
        _items(6.666, 4.3, 1.35, 0.95, shared, size=9.0)
    else:
        _circle(5.55, 4.1, 1.85, P["primary"])
        _circle(7.78, 4.1, 1.85, P["accent"])
        _label(5.55, 1.95, sets_l[0].get("label", "") if sets_l else "")
        _label(7.78, 1.95, sets_l[1].get("label", "") if len(sets_l) > 1 else "")
        _items(4.6, 4.1, 1.8, 2.0, sets_l[0].get("items", []) if sets_l else [])
        _items(8.73, 4.1, 1.8, 2.0, sets_l[1].get("items", []) if len(sets_l) > 1 else [])
        _halo(6.665, 4.1, 1.45, 2.1)
        _items(6.665, 4.1, 1.45, 2.1, shared, size=9.5)
    footnote(slide, P, d)

def m_chart_data(slide, d, P, info):
    """Native editable chart (bar/line) with scholarly interpretation panel."""
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
    ink = _ink(P)
    cats = d.get("categories", [])
    series = d.get("series", [])
    is_bar = d.get("chart_type", "bar") != "line"
    data = CategoryChartData()
    data.categories = cats
    for s in series:
        data.add_series(s.get("name", ""), tuple(s.get("values", [])))
    with _measure_off():
        ctype = XL_CHART_TYPE.COLUMN_CLUSTERED if is_bar else XL_CHART_TYPE.LINE_MARKERS
        gf = slide.shapes.add_chart(ctype, Inches(SAFE_X0), Inches(1.6), Inches(8.1), Inches(4.85), data)
        chart = gf.chart
        chart.has_title = False
        chart.has_legend = len(series) > 1
        if chart.has_legend:
            chart.legend.position = XL_LEGEND_POSITION.BOTTOM
            chart.legend.include_in_layout = False
            chart.legend.font.size = Pt(10)
            chart.legend.font.name = FONT_BODY
        pal2 = [P["primary"], P["accent"]]
        for idx, ser in enumerate(chart.plots[0].series):
            col = C(pal2[idx % 2])
            if is_bar:
                ser.format.fill.solid()
                ser.format.fill.fore_color.rgb = col
                ser.format.line.fill.background()
            else:
                ser.format.line.color.rgb = col
                ser.format.line.width = Pt(2.5)
                try:
                    ser.smooth = False
                except Exception:
                    pass
        chart.category_axis.tick_labels.font.size = Pt(10)
        chart.category_axis.tick_labels.font.name = FONT_BODY
        chart.value_axis.tick_labels.font.size = Pt(10)
        chart.value_axis.tick_labels.font.name = FONT_BODY
    rect(slide, 9.0, 1.6, 3.65, 4.85, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
    rect(slide, 9.0, 1.6, 3.65, 0.05, fill=P["accent"], rounded=False)
    tx(slide, 9.25, 1.78, 3.15, 0.3, T('reading'), size=10, color=ink, bold=True)
    tfi = textframe(slide, 9.25, 2.2, 3.15, 4.0)
    for i, ins in enumerate(d.get("insights", [])):
        para(tfi, "• " + ins, 10.8, P["text"], first=(i == 0), sp_after=8, line_sp=1.12)
    footnote(slide, P, d)

def m_references(slide, d, P, info):
    """Vancouver-style numbered bibliography in two balanced columns."""
    refs = d.get("refs", [])
    ink = _ink(P)
    n = len(refs)
    pill(slide, 10.85, 1.20, 1.8, 0.34, f"{T('references')} · {n}", P["soft"], P["primary"])
    per = max((n + 1) // 2, 1)
    for ci, col in enumerate([refs[:per], refs[per:]]):
        cx = SAFE_X0 + ci * 6.15
        for j, ref in enumerate(col):
            y = 2.05 + j * 0.88
            tx(slide, cx, y, 0.45, 0.35, f"{ci * per + j + 1}.", size=12, color=ink,
               bold=True, font=FONT_TITLE)
            tx(slide, cx + 0.5, y, 5.35, 0.9, ref, size=10.5, color=P["text"], line_sp=1.1)
    footnote(slide, P, d)

def m_authority_card(slide, d, P, info):
    """Hall-portrait biography: framed image, name, dates, bio, legacy."""
    ink = _ink(P)
    _place_image(slide, d["image"], SAFE_X0, SAFE_Y0, 3.7, 4.95, P)
    tx(slide, 4.75, 1.7, 7.8, 0.6, d.get("name", ""), size=24, color=P["primary"],
       bold=True, font=FONT_TITLE)
    if d.get("dates"):
        tx(slide, 4.75, 2.38, 7.8, 0.3, d["dates"], size=11, color=ink, bold=True)
    if d.get("epithet"):
        tx(slide, 4.75, 2.72, 7.8, 0.35, d["epithet"], size=11.5, color=P["text_muted"], italic=True)
    tx(slide, 4.75, 3.2, 7.8, 2.4, d.get("bio", ""), size=11.5, color=P["text"], line_sp=1.18)
    if d.get("legacy"):
        rect(slide, 4.75, 5.75, 7.8, 0.75, fill=P["soft"], line=P["border"], lw=0.5, rounded=True)
        rect(slide, 4.75, 5.75, 0.06, 0.75, fill=P["accent"], rounded=False)
        tx(slide, 5.0, 5.83, 7.3, 0.28, T('legacy'), size=9, color=ink, bold=True)
        tx(slide, 5.0, 6.1, 7.3, 0.35, d["legacy"], size=10.5, color=P["primary"], bold=True)
    footnote(slide, P, d)

# ===================== MODULE RENDERERS — PEDAGOGY PACK =====================

def m_learning_objectives(slide, d, P, info):
    """Bloom-verb numbered learning objectives with optional Bloom-level pills."""
    ink = _ink(P)
    pill(slide, SAFE_X0, 1.20, 2.9, 0.34, T('objectives'), P["soft"], P["primary"])
    objs = d.get("objectives", [])
    n = max(len(objs), 1)
    gap = 0.14
    rh, y_first = stack_layout(2.15, 4.5, n, gap, cap=1.25)
    for i, obj in enumerate(objs):
        y = y_first + i * (rh + gap)
        rect(slide, SAFE_X0, y, CONTENT_W, rh, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, SAFE_X0, y, 0.07, rh, fill=P["accent"], rounded=False)
        rect(slide, 0.9, y + rh / 2 - 0.22, 0.44, 0.44, fill=P["primary"], line=None, rounded=True, rad=0.5)
        tx(slide, 0.9, y + rh / 2 - 0.22, 0.44, 0.44, str(i + 1), size=12, color="FFFFFF",
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        tf = textframe(slide, SAFE_Y0, y + 0.1, 8.85, rh - 0.2, anchor=MSO_ANCHOR.MIDDLE)
        p = tf.paragraphs[0]
        p.line_spacing = 1.12
        r1 = p.add_run(); r1.text = str(obj.get("verb", "")).upper() + " — "
        r1.font.size = Pt(11.5); r1.font.bold = True
        r1.font.color.rgb = C(P["primary"]); r1.font.name = FONT_BODY
        r2 = p.add_run(); r2.text = str(obj.get("text", ""))
        r2.font.size = Pt(11.5); r2.font.color.rgb = C(P["text"]); r2.font.name = FONT_BODY
        if obj.get("bloom"):
            pill(slide, 10.6, y + rh / 2 - 0.17, 1.85, 0.34,
                 bloom_t(str(obj["bloom"])).upper(), P["soft"], ink, size=8)
    footnote(slide, P, d)

def m_colloquy(slide, d, P, info):
    """Tutorial dialogue: alternating tutor (primary, left) / student (card, right) turns."""
    turns = d.get("turns", [])
    n = max(len(turns), 1)
    gap = 0.12
    th, y_first = stack_layout(SAFE_Y0, 5.05, n, gap, cap=1.15)
    for i, t in enumerate(turns):
        y = y_first + i * (th + gap)
        is_tutor = str(t.get("speaker", "tutor")).lower() == "tutor"
        letter = T('tutor')[0] if is_tutor else T('student')[0]
        av_x = SAFE_X0 if is_tutor else 12.26
        av_fill = P["primary"] if is_tutor else P["accent"]
        av = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(av_x), Inches(y + th / 2 - 0.21),
                                    Inches(0.42), Inches(0.42))
        av.fill.solid(); av.fill.fore_color.rgb = C(av_fill)
        _note_surface(av_fill, av_x, y + th / 2 - 0.21, 0.42, 0.42)
        av.line.fill.background(); av.shadow.inherit = False
        atf = av.text_frame
        atf.word_wrap = False
        atf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para(atf, letter, 12, _on(P, av_fill), bold=True, first=True, align=PP_ALIGN.CENTER, sp_after=0)
        bx = 1.25 if is_tutor else 4.3
        bw = 7.8
        rect(slide, bx, y, bw, th, fill=av_fill,
             line=None if is_tutor else P["border"], lw=0.6, rounded=True)
        # v9.A: fg derivado del FILL real (antes texto oscuro fijo sobre accent
        # fallaba en cambridge/ucp: 2.85 y 2.76).
        tx(slide, bx + 0.25, y, bw - 0.5, th, t.get("text", ""), size=10.8,
           color=_on(P, av_fill), anchor=MSO_ANCHOR.MIDDLE, line_sp=1.12)
    footnote(slide, P, d)

def m_annotated_passage(slide, d, P, info):
    """Primary source text (serif, left) with numbered marginalia (right).
    Author embeds markers like [1] inside the passage; annotations carry matching refs."""
    ink = _ink(P)
    rect(slide, SAFE_X0, SAFE_Y0, 7.3, 4.95, fill=P["soft"], line=P["border"], lw=0.5, rounded=True)
    tx(slide, 0.95, 1.75, 6.7, 4.15, d.get("passage", ""), size=13, color=P["text"],
       italic=True, font=FONT_TITLE, line_sp=1.25)
    if d.get("source"):
        rect(slide, 0.95, 6.0, 1.2, 0.025, fill=P["accent"], rounded=False)
        # v9.A: text_muted crudo sobre panel soft daba 4.23-4.24 en harvard/yale;
        # se deriva tinta legible del par (muted vs soft).
        src_col = P["text_muted"] if _ratio(P["text_muted"], P["soft"]) >= 4.5 \
            else _shade_until(P["text_muted"], P["soft"], WCAG_AA_TEXT)
        tx(slide, 0.95, 6.08, 6.7, 0.3, "— " + d["source"], size=10,
           color=src_col, italic=True)
    tx(slide, 8.25, 1.20, 4.4, 0.3, T('marginalia'), size=9.5, color=ink, bold=True)
    anns = d.get("annotations", [])
    n = max(len(anns), 1)
    gap = 0.12
    ah, y_first = stack_layout(2.0, 4.55, n, gap, cap=1.05)
    for i, a in enumerate(anns):
        y = y_first + i * (ah + gap)
        rect(slide, 8.25, y, 4.4, ah, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        rect(slide, 8.25, y, 0.5, 0.5, fill=P["accent"], line=None, rounded=True, rad=0.15)
        tx(slide, 8.25, y, 0.5, 0.5, str(a.get("ref", i + 1)), size=11, color=_on(P, P["accent"]),
           bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
        tx(slide, 8.9, y + 0.06, 3.65, ah - 0.12, a.get("note", ""), size=10, color=P["text"],
           anchor=MSO_ANCHOR.MIDDLE, line_sp=1.1)
    footnote(slide, P, d)

def m_concept_map(slide, d, P, info):
    """Radial hub-and-spoke: central concept with 4-6 satellite nodes."""
    nodes = d.get("nodes", [])
    sub_color = _sub_primary()
    n = max(len(nodes), 1)
    cx, cy = 6.666, 4.05
    rx, ry = 3.9, 2.0
    card_w, card_h = 2.5, 1.05
    centers = []
    for i in range(n):
        ang = _math.radians(-90 + i * (360.0 / n))
        centers.append((cx + rx * _math.cos(ang), cy + ry * _math.sin(ang)))
    try:
        from pptx.enum.shapes import MSO_CONNECTOR
    except ImportError:
        MSO_CONNECTOR = None
    if MSO_CONNECTOR:
        for (nx, ny) in centers:
            vx, vy = nx - cx, ny - cy
            dist = _math.hypot(vx, vy) or 1.0
            sx, sy = cx + vx / dist * 1.35, cy + vy / dist * 1.35
            conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                              Inches(sx), Inches(sy), Inches(nx), Inches(ny))
            conn.line.color.rgb = C(P["border"])
            conn.line.width = Pt(1.5)
    rect(slide, cx - 1.25, cy - 0.5, 2.5, 1.0, fill=P["primary"], line=None, rounded=True, rad=0.12)
    tx(slide, cx - 1.15, cy - 0.5, 2.3, 1.0, d.get("hub", ""), size=13, color="FFFFFF", bold=True,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font=FONT_TITLE)
    for i, (nx, ny) in enumerate(centers):
        nd = nodes[i] if i < len(nodes) else {}
        hi = nd.get("highlight", False)
        px = min(max(nx - card_w / 2, SAFE_X0), CANVAS_W - SAFE_X0 - card_w)
        py = ny - card_h / 2
        rect(slide, px, py, card_w, card_h, fill=P["primary"] if hi else P["card"],
             line=P["accent"] if hi else P["border"], lw=1.0 if hi else 0.6, rounded=True)
        tf = textframe(slide, px + 0.15, py + 0.08, card_w - 0.3, card_h - 0.16, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, nd.get("title", ""), 11.5, "FFFFFF" if hi else P["primary"], bold=True,
             font=FONT_TITLE, first=True, sp_after=2, align=PP_ALIGN.CENTER)
        if nd.get("desc"):
            para(tf, nd["desc"], 9.5, sub_color if hi else P["text"], line_sp=1.05, align=PP_ALIGN.CENTER)
    footnote(slide, P, d)

def m_glossary(slide, d, P, info):
    """Two-column terminology: bold serif terms with concise definitions."""
    terms = d.get("terms", [])
    n = len(terms)
    # Tag en banda superior (y=1.20) para no colisionar con los términos cuando per=5.
    pill(slide, 10.55, 1.20, 2.1, 0.34, T('glossary'), P["soft"], P["primary"])
    per = max((n + 1) // 2, 1)
    gap = 0.12
    # Arranque en 2.05 garantiza holgura bajo header+tag; centrado vertical vía stack_layout.
    # v8.3: cap 1.35 — con 5 términos/columna la caja def quedaba en ~0.8in para 130 car.
    eh, y_first = stack_layout(2.05, 4.5, per, gap, cap=1.35)
    for ci, col in enumerate([terms[:per], terms[per:]]):
        cx = SAFE_X0 + ci * 6.12
        for j, e in enumerate(col):
            y = y_first + j * (eh + gap)
            tx(slide, cx, y, 5.88, 0.3, e.get("term", "").upper(), size=12, color=P["primary"],
               bold=True, font=FONT_TITLE)
            tx(slide, cx, y + 0.34, 5.88, eh - 0.38, e.get("def", ""), size=10.5, color=P["text"], line_sp=1.1)
            if j < len(col) - 1:
                rect(slide, cx, y + eh - 0.02, 5.88, 0.012, fill=P["border"], rounded=False)
    footnote(slide, P, d)

def _tag_color(tag, P):
    """Difficulty tag -> pill color heuristic (advanced=alert, intro/essential=success, else accent)."""
    t = str(tag).lower()
    if any(k in t for k in ('adv', 'avan', 'fortg', 'esperto', 'avanz')):
        return P["alert"]
    if any(k in t for k in ('intro', 'bás', 'bas', 'fund', 'esencial', 'essential', 'core', 'indispens')):
        return P["success"]
    return P["accent"]

def _tag_text(pc, P):
    """Foreground del texto dentro de una pill según su fill."""
    if pc == P["success"]:
        return TOK.get('on_success', "FFFFFF")
    if pc == P["alert"]:
        return TOK.get('on_alert', "FFFFFF")
    return TOK.get('on_accent', "FFFFFF")

def m_further_reading(slide, d, P, info):
    """Graded reading list: color-coded difficulty pills + citation + annotation."""
    entries = d.get("entries", [])
    n = max(len(entries), 1)
    gap = 0.14
    rh, y_first = stack_layout(1.6, 4.95, n, gap, cap=1.2)
    for i, e in enumerate(entries):
        y = y_first + i * (rh + gap)
        rect(slide, SAFE_X0, y, CONTENT_W, rh, fill=P["card"], line=P["border"], lw=0.6, rounded=True)
        pc = _tag_color(e.get("tag", ""), P)
        pill(slide, 0.85, y + rh / 2 - 0.17, 2.0, 0.34, e.get("tag", "").upper(), pc, _tag_text(pc, P))
        tx(slide, 3.1, y + 0.1, 9.3, 0.35, e.get("title", ""), size=12, color=P["primary"],
           bold=True, font=FONT_TITLE)
        if e.get("note"):
            tx(slide, 3.1, y + 0.52, 9.3, rh - 0.6, e.get("note", ""), size=10.5, color=P["text"], line_sp=1.08)
    footnote(slide, P, d)

# ===================== DISPATCH & MODULE REGISTRY =====================

dispatch_map = {
    # Core
    "title": m_title,
    "figure": m_figure,
    "section_divider": m_section_divider,
    "definition": m_definition,
    # Classic set
    "flow_diagram": m_flow_diagram,
    "comparison_table": m_comparison_table,
    "stat_card": m_stat_card,
    "checklist": m_checklist,
    "fixed_schema_card": m_fixed_schema_card,
    "side_by_side": m_side_by_side,
    "taxonomy_tree": m_taxonomy_tree,
    "algorithm": m_algorithm,
    "case_block": m_case_block,
    "synthesis_grid": m_synthesis_grid,
    # Diagram extensions
    "timeline": m_timeline,
    "cycle_diagram": m_cycle_diagram,
    "quadrant_matrix": m_quadrant_matrix,
    "pyramid": m_pyramid,
    # Scholarly pack
    "quote_block": m_quote_block,
    "socratic_question": m_socratic_question,
    "oxford_union": m_oxford_union,
    "evidence_card": m_evidence_card,
    "viva_question": m_viva_question,
    "mnemonic_card": m_mnemonic_card,
    "etymology": m_etymology,
    "venn_diagram": m_venn_diagram,
    "chart_data": m_chart_data,
    "references": m_references,
    "authority_card": m_authority_card,
    # Pedagogy pack
    "learning_objectives": m_learning_objectives,
    "colloquy": m_colloquy,
    "annotated_passage": m_annotated_passage,
    "concept_map": m_concept_map,
    "glossary": m_glossary,
    "further_reading": m_further_reading,
}

OPTIONAL_MODULES = ['timeline', 'cycle_diagram', 'quadrant_matrix', 'pyramid',
    'quote_block', 'socratic_question', 'oxford_union', 'evidence_card',
    'viva_question', 'mnemonic_card', 'etymology', 'venn_diagram',
    'chart_data', 'references', 'authority_card',
    'learning_objectives', 'colloquy', 'annotated_passage', 'concept_map',
    'glossary', 'further_reading']


# ===================== LINTER & LANGUAGE DRIFT CONTRACTS =====================
# NOTE: caption/credit limits aligned with the OMC protocol (110/130).
B = {
 'title':            {'title': 80, 'subtitle': 100, 'course': 70, 'institution': 70, 'author': 70},
 'figure':           {'caption': 110, 'credit': 130},
 'section_divider':  {'section_title': 70, 'section_subtitle': 180, 'divider_style': 40, 'author': 70},
 'definition':       {'main_statement': 240, 'elaboration': 260, 'footnote': 120,
                      'caption': 110, 'credit': 130,
                      '_list': ('key_points', 2, 3, {'title': 45, 'desc': 150})},
 'flow_diagram':     {'explanation': 340,
                      '_list': ('steps', 3, 4, {'label': 12, 'title': 35, 'desc': 170}),
                      '_desc_by_count': ('steps', {3: 220, 4: 170}),
                      '_highlight': ('steps', 1, 1),
                      '_decision_flow': (2, 40)},
 'comparison_table': {'takeaway': 140, '_table': ('rows', 3, 4, 3, 4, 160)},
 'synthesis_grid':   {'takeaway': 140, '_table': ('matrix_data', 3, 3, 3, 3, 220)},
 'stat_card':        {'stat_num': 10, 'stat_title': 120, 'caption': 110, 'credit': 130,
                      '_list': ('narrative_blocks', 1, 3, {'title': 45, 'desc': 180})},
 'checklist':        {'_list': ('items', 2, 5, {'label': 65, 'desc': 150}),
                      'caption': 110, 'credit': 130},
 'fixed_schema_card':{'_list': ('fields', 2, 5, {'label': 30, 'value': 170})},
 'side_by_side':     {'_cards': ({'header': 35, 'title': 50}, 3, 4, 125)},
 'taxonomy_tree':    {'root': 50,
                      '_list': ('categories', 2, 3, {'name': 30, 'property': 65}),
                      '_examples': (3, 90)},
 'algorithm':        {'_list': ('steps', 2, 4, {'title': 70, 'desc': 200}),
                      '_highlight': ('steps', 0, 1)},
 'case_block':       {'case_stem': 240, 'reasoning': 250, 'diagnosis': 50,
                      'clinical_pearl': 160, '_strlist': ('findings', 2, 5, 80),
                      'caption': 110, 'credit': 130},
 'timeline':         {'_list': ('milestones', 3, _TIMELINE_MAX, {'label': 20, 'title': 40, 'desc': 110}),
                      '_desc_by_count': ('milestones', {3: 110, 4: 95, 5: 70})},
 'cycle_diagram':    {'center_label': 40,
                      '_list': ('nodes', 3, 6, {'title': 40, 'desc': 90}),
                      '_highlight': ('nodes', 0, 2)},
 'quadrant_matrix':  {'x_label': 45, 'y_label': 45, '_quads': (40, 2, 5, 110)},
 'pyramid':          {'_list': ('levels', 3, 5, {'title': 55, 'desc': 90}),
                      '_highlight': ('levels', 0, 1)},
 'quote_block':      {'quote': 260, 'author': 60, 'source': 90, 'year': 12, 'context': 160},
 'socratic_question':{'question': 220, 'context': 160, 'reading': 130,
                      '_strlist': ('scaffold', 2, 4, 90)},
 'oxford_union':     {'motion': 140, 'verdict': 160,
                      '_debate': ({'title': 30}, 2, 4, 110)},
 'evidence_card':    {'study_name': 60, 'design': 60, 'population': 140, 'intervention': 140,
                      'comparison': 140, 'outcome': 140, 'effect': 14, 'effect_desc': 120,
                      'limitation': 160, 'year': 10, 'credit': 130},
 'viva_question':    {'prompt': 220, 'model_answer': 260, 'examiner_note': 180, 'difficulty': 12},
 'mnemonic_card':    {'acronym': 8, 'usage': 200, 'domain': 30,
                      '_acronym': ('expansion', 30)},
 'etymology':        {'term': 30, 'modern': 160,
                      '_list': ('roots', 2, 3, {'part': 20, 'origin': 20, 'meaning': 70})},
 'venn_diagram':     {'_venn': (30, 2, 4, 45, 1, 3, 45)},
 'chart_data':       {'chart_type': 6, 'credit': 130,
                      '_chart': (2, 8, 1, 2, 30, 2, 3, 120, 25)},
 'references':       {'_strlist': ('refs', 3, 10, 160)},
 'authority_card':   {'name': 60, 'dates': 30, 'epithet': 80, 'bio': 300,
                      'legacy': 120, 'caption': 110, 'credit': 130},
 'learning_objectives': {'_objectives': (3, 6, 25, 130)},
 'colloquy':         {'_colloquy': (4, 8, 160)},
 'annotated_passage':{'passage': 520, 'source': 90,
                      '_list': ('annotations', 2, 5, {'ref': 6, 'note': 110})},
 'concept_map':      {'hub': 40,
                      '_list': ('nodes', 4, 6, {'title': 35, 'desc': 80}),
                      '_highlight': ('nodes', 0, 2)},
 'glossary':         {'_list': ('terms', 4, 10, {'term': 30, 'def': 130})},
 'further_reading':  {'_list': ('entries', 3, 6, {'title': 90, 'tag': 20, 'note': 100})},
}
COMMON = {'kicker': 55, 'title': 75, 'footnote': 140}

REQUIRED_NONEMPTY = {
    'title':            ['title'],
    'figure':           ['image', 'caption', 'credit'],
    'section_divider':  ['section_title'],
    'definition':       ['main_statement'],
    'flow_diagram':     [],
    'comparison_table': ['headers'],
    'synthesis_grid':   ['headers'],
    'stat_card':        ['stat_num', 'stat_title'],
    'checklist':        [],
    'fixed_schema_card':[],
    'side_by_side':     [],
    'taxonomy_tree':    ['root'],
    'algorithm':        [],
    'case_block':       ['case_stem', 'reasoning', 'diagnosis', 'clinical_pearl'],
    'timeline':         [],
    'cycle_diagram':    [],
    'quadrant_matrix':  [],
    'pyramid':          [],
    'quote_block':      ['quote', 'author'],
    'socratic_question':['question'],
    'oxford_union':     ['motion', 'verdict'],
    'evidence_card':    ['study_name', 'design', 'population', 'intervention', 'outcome', 'effect', 'credit'],
    'viva_question':    ['prompt', 'model_answer', 'examiner_note'],
    'mnemonic_card':    ['acronym', 'usage'],
    'etymology':        ['term', 'modern'],
    'venn_diagram':     [],
    'chart_data':       [],
    'references':       [],
    'authority_card':   ['image', 'name', 'bio'],
    'learning_objectives': [],
    'colloquy':         [],
    'annotated_passage':['passage'],
    'concept_map':      ['hub'],
    'glossary':         [],
    'further_reading':  [],
}
# v9.B — el inventario de módulos vive en 3 estructuras por disciplina; que no derive.
assert set(dispatch_map) == set(B) == set(REQUIRED_NONEMPTY), (
    'inventarios de módulos desincronizados: dispatch_map vs B vs REQUIRED_NONEMPTY')

# Núcleo-4 siempre requerido; el suelo de variedad sustituye a la lista obligatoria-14.
CORE_MODULES = ['title', 'definition', 'section_divider', 'figure']
MIN_DISTINCT = 8        # minimum distinct modules in any deck
MIN_DISTINCT_FULL = 12  # minimum distinct modules for decks of >= 20 slides
FULL_DECK_THRESHOLD = 20

# --- Contrato de deriva: portugués infiltrando decks es-ES (único par probado).
PTBR_DRIFT = [
    (r'[a-záéíóúüñãõ]*ç[a-záéíóúüñãõ]*', 'es-ES no usa "ç" (pt -ção -> es -ción)'),
    (r'\bchumbo\b', 'plomo'),
    (r'\blinha\b', 'línea'),
    (r'\blivres?\b', 'libre(s)'),
    (r'\bapoptose\b', 'apoptosis'),
    (r'\bnecrose\b', 'necrosis'),
    (r'\bfibrose\b', 'fibrosis'),
    (r'\bexames?\b', 'examen(es)'),
    (r'\bintensidade\b', 'intensidad'),
    (r'\bduração\b', 'duración'),
    (r'\bcondições\b', 'condiciones'),
    (r'\bsequ[êe]ncia(s)?\b', 'secuencia(s)'),
    (r'\bacidose\b', 'acidosis'),
    (r'\befeitos\b', 'efectos'),
    (r'\bnão\b', 'no'),
    (r'\biônica(s)?\b', 'iónica(s)'),
    (r'\biônicos\b', 'iónicos'),
    (r'\bcromossomos?\b', 'cromosoma(s)'),
    (r'\bcritérios?\b', 'criterio(s)'),
    (r'\bfalha\b', 'falla'),
    (r'\btumefa\b', 'hinchazón / tumefacción'),
    (r'\bextravasamentos?\b', 'extravasamiento'),
    (r'\bconteúdos?\b', 'contenido(s)'),
    (r'\bcérebro\b', 'cerebro'),
    (r'\boxigênio\b', 'oxígeno'),
    (r'\bcálcio\b', 'calcio'),
    (r'\bcorpos\b', 'cuerpos'),
    (r'\bmassa\b', 'masa'),
    (r'\bmorte\b', 'muerte'),
    (r'\bmorrer\b', 'morir'),
    (r'\bviscosidade\b', 'viscosidad'),
    (r'\btermolábeis\b', 'termolábiles'),
    (r'\bhemácias\b', 'hematíes / eritrocitos'),
    (r'\bdor\b', 'dolor'),
    (r'\bfebre\b', 'fiebre'),
    (r'\bachados\b', 'hallazgos'),
    (r'\bestágios?\b', 'estadio(s) / fase(s)'),
    (r'\bdebridamento\b', 'desbridamiento'),
    (r'\bbaço\b', 'bazo'),
    (r'\bfígado\b', 'hígado'),
    (r'\brins?\b', 'riñón / riñones'),
    (r'\bpulmão\b', 'pulmón'),
    (r'\bpulmões\b', 'pulmones'),
    (r'\bsangue\b', 'sangre'),
    (r'\bquadro\b', 'cuadro'),
    (r'\bdoenças?\b', 'enfermedad(es)'),
]
DRIFT_CONTRACTS = {'es-ES': PTBR_DRIFT}

# ============ v8.0 — DERIVA SIMÉTRICA (caracteres diagnósticos) ============
# Un carácter imposible en el idioma declarado es señal de alta precisión de
# infiltración de otro idioma. Se generan contratos bloqueantes para CADA idioma
# UI a partir de los caracteres exclusivos de los demás (antes solo pt->es-ES).
# Excepciones por pack para préstamos léxicos legítimos (raro; vacío por defecto).
DRIFT_CHAR_EXCEPTIONS = {
    # 'es-ES': {'ç'},   # p. ej. si un deck es-ES cita topónimos franceses con ç
}
# v9.F — excepciones POR PALABRA (para reglas léxicas/morfológicas): palabras que
# un patrón marcaría pero son legítimas en el idioma objetivo. Lección del FP
# '-dades' (modalidades/velocidades son español legítimo).
DRIFT_WORD_EXCEPTIONS = {
    # 'es-ES': {'modalidades', 'velocidades', 'ciudades'},
}
_MORPH_RULES = {
    # Reglas morfológicas inversas: morfología del idioma A apareciendo en B.
    # NOTA v8.4.2: '-dades' se RETIRÓ del par es-ES — el plural español legítimo
    # de -dad ES -dades (modalidades, velocidades) y generaba falsos positivos
    # bloqueantes. El singular '-dade' sí es exclusivo del portugués.
    ('es-ES', 'pt-BR'): [(r'\b\w+ção\b', 'pt -ção -> es -ción'),
                         (r'\b\w+ções\b', 'pt -ções -> es -ciones'),
                         (r'\b\w+dade\b', 'pt -dade -> es -dad')],
    ('pt-BR', 'es-ES'): [(r'\b\w+ción\b', 'es -ción -> pt -ção'),
                         (r'\b\w+ciones\b', 'es -ciones -> pt -ções')],
}

def _build_symmetric_drift():
    """Para cada lang UI, compila patrones bloqueantes con caracteres imposibles
    tomados de los DEMÁS packs + reglas morfológicas + léxico heredado.
    v8.4: llamada perezosa (primera compilación de patrones), no al importar."""
    langs = list(_LANG_CHARS_LANGS())
    for target in langs:
        contracts = list(DRIFT_CONTRACTS.get(target, []))  # hereda léxico manual
        seen_pats = {p for p, _f in contracts}
        morph = []
        exc = set(DRIFT_CHAR_EXCEPTIONS.get(target, []))
        for ch, contrib in _LANG_CHARS.items():
            if target in contrib or ch in exc:
                continue  # el carácter existe legítimamente en el idioma objetivo
            src = max(contrib, key=lambda lg: contrib[lg])  # señal más fuerte
            pat = _re.escape(ch)
            if pat not in seen_pats:
                seen_pats.add(pat)
                contracts.append(
                    (pat, f'carácter {ch!r} no existe en {target} (señal de {src})'))
        for (tgt, src), rules in _MORPH_RULES.items():
            if tgt == target:
                morph.extend(rules)
        DRIFT_CONTRACTS[target] = contracts
        _SYM_MORPH[target] = morph

def _LANG_CHARS_LANGS():
    langs = set(I18N)
    for contrib in _LANG_CHARS.values():
        langs.update(contrib)
    return sorted(langs)

_SYM_MORPH = {}

_DRIFT_COMPILED = {}
_DRIFT_CACHE = {}

def _drift_patterns(lang):
    if not _SYM_MORPH and not _DRIFT_COMPILED:
        # v8.0 — deriva simétrica generada perezosamente (primera consulta).
        _build_symmetric_drift()
    if lang not in _DRIFT_COMPILED:
        pats = [(_re.compile(p), f) for p, f in DRIFT_CONTRACTS.get(lang, [])]
        pats += [(_re.compile(p), f) for p, f in _SYM_MORPH.get(lang, [])]
        _DRIFT_COMPILED[lang] = pats
    return _DRIFT_COMPILED[lang]

def _drift_hits(text, lang):
    pats = _drift_patterns(lang)
    if not pats:
        return []
    key = (lang, text)
    if key in _DRIFT_CACHE:
        return _DRIFT_CACHE[key]
    norm = _norm(text)
    word_exc = DRIFT_WORD_EXCEPTIONS.get(lang, set())
    spans, found = [], []
    for pat, fix in pats:
        for m in pat.finditer(norm):
            s0, e0 = m.span()
            if any(s0 < e1 and e0 > s1 for s1, e1 in spans):
                continue
            if m.group(0) in word_exc:
                continue  # v9.F: palabra legítima eximida por pack
            spans.append((s0, e0))
            found.append((m.group(0), fix))
    if len(_DRIFT_CACHE) > 4096:
        _DRIFT_CACHE.clear()
    _DRIFT_CACHE[key] = found
    return found

# ============ LANGUAGE TRIPWIRE (audit-only, WARN — never blocks) ============
_LANG_PROFILE = {
 'en-US': {'the':3,'of':2,'and':2,'to':2,'is':3,'are':3,'with':2,'for':2,'from':2,
           'this':2,'that':2,'which':3,'when':2,'than':3,'then':2,'each':2,'between':2,
           'during':2,'after':2,'before':2,'should':3,'must':3,'can':2,'may':2,'not':2,
           'or':1,'as':1,'at':1,'by':1,'on':1,'be':1,'an':1,'it':1,'both':2,'all':1,
           'any':1,'in':1,'its':3,'their':3,'these':2,'those':2,'into':2,'upon':3},
 'es-ES': {'el':2,'la':1,'los':3,'las':3,'del':3,'y':2,'es':2,'son':3,'con':2,'para':1,
           'por':1,'una':2,'un':1,'que':1,'se':1,'al':1,'como':2,'más':3,'pero':3,
           'cuando':3,'entre':1,'sobre':2,'este':2,'esta':2,'cada':2,'sin':2,'tras':3,
           'según':3,'también':3,'su':1,'sus':2,'sí':3,'hasta':3,'desde':2,'porque':3,
           'aunque':3,'además':3,'muy':2,'ya':2},
 'pt-BR': {'os':3,'as':2,'do':2,'da':2,'dos':3,'das':3,'em':1,'é':3,'são':3,'com':2,
           'para':1,'por':1,'um':1,'uma':2,'que':1,'se':1,'ao':2,'à':1,'aos':3,'mais':2,
           'mas':3,'quando':1,'entre':1,'sobre':1,'cada':1,'sem':2,'após':3,'segundo':1,
           'também':3,'não':3,'seu':2,'sua':2,'pelo':3,'pela':3,'no':1,'na':1,'nos':2,
           'nas':2,'até':2,'porque':2,'embora':3,'além':3,'já':2,'muito':3},
 'fr-FR': {'le':2,'la':1,'les':3,'de':2,'des':2,'du':2,'et':2,'est':3,'sont':3,'avec':3,
           'pour':2,'par':2,'une':2,'un':1,'que':1,'qui':3,'se':1,'au':2,'aux':3,'plus':2,
           'mais':3,'quand':1,'sur':2,'ce':1,'cette':2,'chaque':2,'sans':2,'après':2,
           'selon':3,'aussi':2,'ou':1,'son':1,'ses':2,'dans':2,'dont':3,'chez':3,
           'ont':3,'peut':2,'doit':2,'être':3},
 'de-DE': {'der':3,'die':3,'das':3,'den':3,'dem':3,'und':3,'ist':3,'sind':3,'mit':2,
           'für':3,'von':2,'zu':1,'ein':1,'eine':2,'einen':3,'einem':3,'einer':3,
           'dass':3,'sich':2,'bei':2,'als':2,'aber':3,'wenn':3,'zwischen':3,'über':2,
           'jede':2,'jeder':2,'ohne':2,'nach':2,'auch':2,'oder':3,'nicht':3,'im':2,
           'am':1,'vom':2,'zum':2,'zur':2,'werden':3,'wird':3,'kann':2,'soll':2,'hat':2},
 'it-IT': {'il':3,'lo':2,'la':1,'gli':3,'le':1,'di':2,'del':2,'della':3,'dello':3,
           'dei':3,'degli':3,'delle':3,'è':3,'sono':3,'con':1,'per':1,'che':3,'si':1,
           'al':1,'alla':2,'più':3,'ma':2,'quando':1,'tra':2,'fra':2,'sopra':2,'questo':2,
           'questa':2,'ogni':2,'senza':2,'dopo':2,'secondo':1,'anche':3,'non':1,'nel':2,
           'nella':3,'sul':2,'sulla':3,'come':2,'dove':2,'invece':3,'molto':2},
}

_LANG_CHARS = {'ñ': {'es-ES': 4}, 'ã': {'pt-BR': 4}, 'õ': {'pt-BR': 4},
               'ß': {'de-DE': 4}, 'ä': {'de-DE': 2}, 'ö': {'de-DE': 2}, 'ü': {'de-DE': 2},
               'ì': {'it-IT': 3}, 'ò': {'it-IT': 3}, 'ù': {'fr-FR': 2, 'it-IT': 2},
               'â': {'fr-FR': 1}, 'ê': {'fr-FR': 1, 'pt-BR': 1}, 'ô': {'fr-FR': 2},
               'û': {'fr-FR': 2}, 'ç': {'fr-FR': 1, 'pt-BR': 2}}

_TOKEN_RE = _re.compile(r'[^\W\d_]+', _re.UNICODE)

def _norm(text):
    """Normalización canónica (NFC + lower) — única para drift, huella y fidelidad."""
    return unicodedata.normalize('NFC', str(text)).lower()

MIN_DECK_TOKENS = 40   # below this: detection skipped ([FILL])
MIN_MARGIN = 1.6       # winner/runner-up ratio for a confident verdict

def _iter_strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for k, vv in v.items():
            if k != 'image':
                yield from _iter_strings(vv)
    elif isinstance(v, (list, tuple)):
        for vv in v:
            yield from _iter_strings(vv)

def _lang_scores(texts):
    """Aggregate weighted language scores over an iterable of strings."""
    scores = {lg: 0.0 for lg in _LANG_PROFILE}
    n_tokens = 0
    for text in texts:
        norm = _norm(text)
        toks = _TOKEN_RE.findall(norm)
        n_tokens += len(toks)
        if not toks:
            continue
        cnt = Counter(toks)
        for lg, prof in _LANG_PROFILE.items():
            scores[lg] += sum(prof.get(t, 0) * c for t, c in cnt.items())
        for ch, contrib in _LANG_CHARS.items():
            k = norm.count(ch)
            if k:
                for lg, w in contrib.items():
                    scores[lg] += w * min(k, 20)
    return scores, n_tokens

def _lang_verdict(scores, n_tokens, min_tokens):
    """Returns (winner|None, ranked[(lang, score)], margin). None = insufficient signal."""
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top, second = ranked[0], ranked[1]
    if n_tokens < min_tokens or top[1] <= 0:
        return None, ranked, 0.0
    margin = (top[1] / second[1]) if second[1] > 0 else float('inf')
    return top[0], ranked, margin

# ---- Text-fit estimator (prevents silent clipping; consciente de la fuente) ----
def est_height(text, width_in, size_pt, line_sp=1.1, sp_after=3, font=None):
    if not text:
        return 0.0
    # v9.1/A6: leer el global en el CUERPO (no default-arg) — un default captura
    # el valor al importar y los cambios de _apply_fonts no se propagan.
    if font is None:
        font = FONT_BODY
    char_w = _CHAR_W_BY_FONT.get(font, _CHAR_W_DEFAULT)
    cpl = max(1, int((width_in * 72.0) / (size_pt * char_w)))
    lines = 0
    for seg in str(text).split('\n'):
        cur, ln = 0, 1
        for wd in seg.split(' '):
            wl = len(wd) + (1 if cur else 0)
            if cur + wl > cpl and cur:
                ln += 1; cur = len(wd)
            else:
                cur += wl
        lines += ln
    return lines * size_pt * line_sp * 1.02 / 72.0 + sp_after / 72.0

FIT_RULES = {  # module -> callable(d) -> [(field, box_w_in, box_h_in, font_pt)]
 'title':          lambda d: [('title', 10.933, 2.1, 38.0)],
 'section_divider':lambda d: [('section_title', 11.0, 1.8, 36.0), ('section_subtitle', 10.5, 1.5, 15.0)],
 'definition':     lambda d: [('main_statement', (7.1 if d.get('image') else 11.5), 0.95, 15.5),
                              ('elaboration', (7.2 if d.get('image') else 11.6), SAFE_X0, CONTENT_W)],
 'stat_card':      lambda d: [('stat_title', 3.9, 1.8, 13.5)],
 'case_block':     lambda d: [('case_stem', (4.2 if d.get('image') else 5.45), 1.6, 11.5),
                              ('reasoning', (4.1 if d.get('image') else 5.4), 1.9, 10.8),
                              ('clinical_pearl', (4.1 if d.get('image') else 5.4), 1.15, 10.8)],
 'quote_block':    lambda d: [('quote', 9.4, 2.3, 20.0)],
 'socratic_question': lambda d: [('question', 9.9, 1.6, 20.0)],
 'oxford_union':   lambda d: [('motion', 11.4, 0.68, 17.0)],
 'viva_question':  lambda d: [('prompt', 5.1, 3.6, 16.0), ('model_answer', 5.6, 2.0, 11.5)],
 'authority_card': lambda d: [('bio', 7.8, 2.4, 11.5)],
 'evidence_card':  lambda d: [('population', 6.5, 0.85, 11.0), ('intervention', 6.5, 0.85, 11.0),
                              ('comparison', 6.5, 0.85, 11.0), ('outcome', 6.5, 0.85, 11.0)],
 'annotated_passage': lambda d: [('passage', 6.7, 4.15, 13.0)],
}

_BLOOM_VERBS = ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')


# ===================== DECK PROFILES =====================
PROFILES = {
 'lecture': {'slides': (22, 34), 'distinct': 12, 'figures': (2, 10),
             'desc': 'clase magistral completa'},
 'seminar': {'slides': (14, 22), 'distinct': 10, 'figures': (1, 8),
             'desc': 'seminario o ateneo'},
 'short':   {'slides': (10, 14), 'distinct': 8,  'figures': (1, 5),
             'desc': 'cápsula breve / journal club'},
 'custom':  {'slides': (6, 40), 'distinct': 2,  'figures': (0, 10),
             'desc': 'personalizado libre - solo titulo y seccion obligatorios'},
}
DEFAULT_PROFILE = 'lecture'

def resolve_profile(mod=None, override=None):
    name = (override or (getattr(mod, 'CONFIG', {}) or {}).get('PROFILE') or DEFAULT_PROFILE)
    name = str(name).strip().lower()
    if name not in PROFILES:
        name = DEFAULT_PROFILE
    return name, PROFILES[name]

# ---------- SLIDE ANCHORS & LEDGER RESOLUTION ----------
_ANCHOR_RE = _re.compile(r'^[a-z0-9][a-z0-9-]{1,39}$')

def slide_anchors(slides):
    """anchor -> 1-based slide index. Anchors are optional but must be unique slugs."""
    out = {}
    for i, d in enumerate(slides, start=1):
        a = str(d.get('anchor', '')).strip()
        if a:
            out[a] = i
    return out

def parse_ledger(path='work/atu_ledger.md'):
    """[(section_title, [(atu:int, ref:str, quote:str|None), ...]), ...];
    ref = slide number or #anchor; quote = fragmento verbatim del source (columna
    opcional 4 del ledger) usado para el chequeo de fidelidad en el audit."""
    if not os.path.exists(path):
        return None
    txt = open(path, encoding='utf-8').read()
    parts = _re.split(r'^#{1,3}\s+', txt, flags=_re.M)[1:]
    sections = []
    for p in parts:
        name = p.splitlines()[0].strip()
        rows = _re.findall(
            r'^\|\s*(\d+)\s*\|[^|]*\|\s*([^|]+?)\s*\|(?:[ \t]*([^|]*?)\s*\|)?[ \t]*$',
            p, flags=_re.M)
        if not rows:
            continue
        sections.append((name, [(int(a), r.strip(),
                                 (q or '').strip().strip('"“”«»') or None)
                                for a, r, q in rows]))
    return sections

# ---- v8.1 — Honestidad de imágenes y cadena de fidelidad al source ----
# Rol efectivo de la imagen: 'figure' es por defecto EVIDENCE (su propósito es
# presentar contenido); imágenes embebidas en módulos mixtos son por defecto
# ILLUSTRATIVE (apoyo decorativo que NO desarrolla contenido). Manifiestos
# v7.9.x sin el campo conservan su comportamiento anterior.
# v9.D: el default vive en MODULES[...]['image_role_default'] (declaración
# explícita por módulo); _EVIDENCE_DEFAULT_MODULES queda como vista derivada.
_EVIDENCE_DEFAULT_MODULES = {'figure'}

def _effective_image_role(d):
    spec = MODULES.get(d.get('module'), {})
    default = spec.get('image_role_default',
                       'evidence' if d.get('module') in _EVIDENCE_DEFAULT_MODULES
                       else 'illustrative')
    return str(d.get('image_role', default)).strip().lower()

def _is_atu_claim(a):
    """ATU válido reclamado por un slide: int real (bool NO cuenta como int)."""
    return isinstance(a, int) and not isinstance(a, bool)

def _atu_claims(slides):
    """{atu: índice de la primera slide que lo reclama} — fuente única para
    lint (cobertura) y audit (fidelidad)."""
    claims = {}
    for i, d in enumerate(slides, start=1):
        a = d.get('atu')
        if _is_atu_claim(a):
            claims.setdefault(a, i)
    return claims

_SALIENT_MIN_LEN = 4      # tokens con longitud >= N cuentan como salientes
_PARAPHRASE_MIN_Q = 6     # debajo de este nº de tokens la cita no es medible
_PARAPHRASE_FLOOR = 0.25  # solape mínimo esperado slide vs source_quote
_FIGURE_CAPTION_MIN = 15  # pie analítico mínimo (v8.4)

def _paraphrase_weak(slides, sections, claims):
    """(weak, measured, skipped): mide solape léxico slide vs source_quote.
    Pure function — _write_audit solo formatea."""
    weak, measured, skipped = [], 0, 0
    for name, rows in sections:
        for a, _ref, quote in rows:
            if not quote:
                continue
            i = claims.get(a)
            if not i:
                continue
            qtoks = _salient_tokens(quote)
            if len(qtoks) < _PARAPHRASE_MIN_Q:
                skipped += 1
                continue
            stoks = set()
            for fld, val in slides[i - 1].items():
                if fld in ('image', 'anchor', 'module', 'atu', 'image_role'):
                    continue
                stoks |= _salient_tokens(val)
            overlap = len(qtoks & stoks) / len(qtoks)
            measured += 1
            if overlap < _PARAPHRASE_FLOOR:
                weak.append((a, i, round(overlap, 2)))
    return weak, measured, skipped

def _salient_tokens(text):
    return {w for w in _TOKEN_RE.findall(unicodedata.normalize('NFC', str(text)).lower())
            if len(w) >= _SALIENT_MIN_LEN}

def resolve_ref(ref, anchors, n_slides):
    """Return (index|None, error|None). Accepts '12', '#anchor' or 'anchor'."""
    r = str(ref).strip().lstrip('#')
    if r.isdigit():
        i = int(r)
        return (i, None) if 1 <= i <= n_slides else (None, f'índice {i} fuera de rango 1-{n_slides}')
    if r in anchors:
        return anchors[r], None
    return None, f"ancla '#{r}' no existe en el manifest (añada 'anchor': '{r}' a la diapositiva)"

# v9.1/A2 — módulos sin header/footer estándar
_NO_HEADER_MODULES = ('title', 'section_divider')
_COLLOQUY_SPEAKERS = ('tutor', 'student')  # v9.1/A2
# v9.2/B4 — cita ATU en el pie de slides con "atu": N (activable vía CONFIG['ATU_FOOTNOTE'])
_ATU_FOOTNOTE = True

# ===================== v9.3/C2 — VALIDATOR TABLE de check() =====================
# Cada rama '_xxx' de spec vive en un handler con firma uniforme:
#   handler(val, d, m, loc0, over, errs)
# Los MENSAJES son byte-idénticos a los inline que reemplazan (_ERR_RE del
# contrato --json los parsea). check() solo itera SPEC_VALIDATORS.

def _v_list(val, d, m, loc0, over, errs, spec=None):
    key, lo, hi, fl = val
    items = d.get(key, [])
    if spec and '_desc_by_count' in spec and spec['_desc_by_count'][0] == key:
        dl = spec['_desc_by_count'][1].get(len(items))
        if dl: fl = dict(fl, desc=dl)
    if not lo <= len(items) <= hi:
        errs.append(f'{loc0}.{key}: {len(items)} ítems, esperado {lo}-{hi}')
    for j, it in enumerate(items):
        for fk, flim in fl.items():
            over(f'{loc0}.{key}[{j}].{fk}', it.get(fk, ''), flim)

def _v_strlist(val, d, m, loc0, over, errs):
    key, lo, hi, lim = val
    items = d.get(key, [])
    if not lo <= len(items) <= hi:
        errs.append(f'{loc0}.{key}: {len(items)} ítems, esperado {lo}-{hi}')
    for s_ in items: over(f'{loc0}.{key}', s_, lim)

def _v_examples(val, d, m, loc0, over, errs):
    mx, lim = val
    for j, c in enumerate(d.get('categories', [])):
        exs = c.get('examples', [])
        if len(exs) > mx:
            errs.append(f'{loc0}.categories[{j}].examples: {len(exs)} > {mx}')
        for e in exs: over(f'{loc0}.categories[{j}].examples', e, lim)

def _v_sided_cards(val, d, m, loc0, over, errs, sides):
    fl, plo, phi, plim = val
    for side in sides:
        c = d.get(side, {})
        for fk, flim in fl.items():
            over(f'{loc0}.{side}.{fk}', c.get(fk, ''), flim)
        pts = c.get('points', [])
        if not plo <= len(pts) <= phi:
            errs.append(f'{loc0}.{side}.points: {len(pts)}, esperado {plo}-{phi}')
        for p in pts: over(f'{loc0}.{side}.points', p, plim)

def _v_cards(val, d, m, loc0, over, errs):
    _v_sided_cards(val, d, m, loc0, over, errs, ('left_card', 'right_card'))

def _v_debate(val, d, m, loc0, over, errs):
    _v_sided_cards(val, d, m, loc0, over, errs, ('pro_card', 'con_card'))

def _v_highlight(val, d, m, loc0, over, errs):
    key, lo, hi = val
    n = sum(1 for s_ in d.get(key, []) if s_.get('highlight'))
    if not lo <= n <= hi:
        errs.append(f'{loc0}: {n} {key} destacados, esperado {lo}-{hi}')

def _v_quads(val, d, m, loc0, over, errs):
    tlim, plo, phi, plim = val
    quads = d.get('quadrants', [])
    if len(quads) != 4:
        errs.append(f'{loc0}.quadrants: {len(quads)} cuadrantes, esperado 4')
    for j, q in enumerate(quads):
        over(f'{loc0}.quadrants[{j}].title', q.get('title', ''), tlim)
        pts = q.get('points', [])
        if not plo <= len(pts) <= phi:
            errs.append(f'{loc0}.quadrants[{j}].points: {len(pts)}, esperado {plo}-{phi}')
        for p in pts: over(f'{loc0}.quadrants[{j}].points', p, plim)

def _v_decision_flow(val, d, m, loc0, over, errs):
    max_dec, dlim = val
    steps_l = d.get('steps', [])
    ndec = sum(1 for s_ in steps_l if s_.get('decision'))
    if ndec > max_dec:
        errs.append(f'{loc0}: {ndec} decisiones, máximo {max_dec}')
    if ndec and d.get('explanation'):
        errs.append(f'{loc0}: steps.decision no es compatible con explanation')
    for j, s_ in enumerate(steps_l):
        if s_.get('decision'):
            over(f'{loc0}.steps[{j}].desc (ramificación NO)', s_.get('desc', ''), dlim)

def _v_acronym(val, d, m, loc0, over, errs):
    key, lim = val
    acr = str(d.get('acronym', ''))
    exp = d.get(key, [])
    if len(exp) != len(acr):
        errs.append(f'{loc0}.{key}: {len(exp)} términos para {len(acr)} letras')
    for j, e in enumerate(exp):
        over(f'{loc0}.{key}[{j}]', e, lim)

def _v_venn(val, d, m, loc0, over, errs):
    flab, slo, shi, ilim, hlo, hhi, hlim = val
    sets_l = d.get('sets', [])
    if not 2 <= len(sets_l) <= 3:
        errs.append(f'{loc0}.sets: {len(sets_l)} conjuntos, esperado 2-3')
    for j, st in enumerate(sets_l):
        over(f'{loc0}.sets[{j}].label', st.get('label', ''), flab)
        its = st.get('items', [])
        if not slo <= len(its) <= shi:
            errs.append(f'{loc0}.sets[{j}].items: {len(its)}, esperado {slo}-{shi}')
        for e in its: over(f'{loc0}.sets[{j}].items', e, ilim)
    sh = d.get('shared', [])
    if not hlo <= len(sh) <= hhi:
        errs.append(f'{loc0}.shared: {len(sh)}, esperado {hlo}-{hhi}')
    for e in sh: over(f'{loc0}.shared', e, hlim)

def _v_chart(val, d, m, loc0, over, errs):
    clo, chi, snlo, snhi, snlim, inlo, inhi, inlim, catlim = val
    cats_l = d.get('categories', [])
    series_l = d.get('series', [])
    ins = d.get('insights', [])
    if d.get('chart_type', 'bar') not in ('bar', 'line'):
        errs.append(f'{loc0}.chart_type: usar "bar" o "line"')
    if not clo <= len(cats_l) <= chi:
        errs.append(f'{loc0}.categories: {len(cats_l)}, esperado {clo}-{chi}')
    for j, cv in enumerate(cats_l):
        over(f'{loc0}.categories[{j}]', cv, catlim)
    if not snlo <= len(series_l) <= snhi:
        errs.append(f'{loc0}.series: {len(series_l)}, esperado {snlo}-{snhi}')
    for j, sr in enumerate(series_l):
        over(f'{loc0}.series[{j}].name', sr.get('name', ''), snlim)
        vals = sr.get('values', [])
        if len(vals) != len(cats_l):
            errs.append(f'{loc0}.series[{j}].values: {len(vals)} vs {len(cats_l)} categorías')
        for k_, v in enumerate(vals):
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errs.append(f'{loc0}.series[{j}].values[{k_}]: valor no numérico ({v!r})')
    if not inlo <= len(ins) <= inhi:
        errs.append(f'{loc0}.insights: {len(ins)}, esperado {inlo}-{inhi}')
    for e in ins: over(f'{loc0}.insights', e, inlim)

def _v_objectives(val, d, m, loc0, over, errs):
    lo, hi, vlim, tlim = val
    objs = d.get('objectives', [])
    if not lo <= len(objs) <= hi:
        errs.append(f'{loc0}.objectives: {len(objs)} objetivos, esperado {lo}-{hi}')
    for j, o in enumerate(objs):
        over(f'{loc0}.objectives[{j}].verb', o.get('verb', ''), vlim)
        over(f'{loc0}.objectives[{j}].text', o.get('text', ''), tlim)
        bl = str(o.get('bloom', '')).strip().lower()
        if bl and bl not in _BLOOM_VERBS:
            errs.append(f'{loc0}.objectives[{j}].bloom: {bl!r} no válido '
                        f'({"|".join(_BLOOM_VERBS)})')

def _v_colloquy(val, d, m, loc0, over, errs):
    lo, hi, tlim = val
    turns = d.get('turns', [])
    if not lo <= len(turns) <= hi:
        errs.append(f'{loc0}.turns: {len(turns)} turnos, esperado {lo}-{hi}')
    for j, t in enumerate(turns):
        sp = str(t.get('speaker', '')).strip().lower()
        if sp not in _COLLOQUY_SPEAKERS:
            errs.append(f'{loc0}.turns[{j}].speaker: {sp!r} no válido (tutor|student)')
        over(f'{loc0}.turns[{j}].text', t.get('text', ''), tlim)

def _v_table(val, d, m, loc0, over, errs):
    key, rlo, rhi, clo, chi, lim = val
    rows = d.get(key, [])
    hdrs = d.get('headers', [])
    cw = d.get('col_widths')
    if not rlo <= len(rows) <= rhi:
        errs.append(f'{loc0}.{key}: {len(rows)} filas, esperado {rlo}-{rhi}')
    if not clo <= len(hdrs) <= chi:
        errs.append(f'{loc0}.headers: {len(hdrs)} columnas, esperado {clo}-{chi}')
    if cw and len(cw) != len(hdrs):
        errs.append(f'{loc0}.col_widths: {len(cw)} pesos vs {len(hdrs)} encabezados '
                    f'— un peso por encabezado, ni uno más (ver: schema {m})')
    if cw:
        if not isinstance(cw, (list, tuple)):
            errs.append(f'{loc0}.col_widths: usar lista de pesos numéricos')
        else:
            for j, w in enumerate(cw):
                if isinstance(w, bool) or not isinstance(w, (int, float)):
                    errs.append(f'{loc0}.col_widths[{j}]: peso no numérico ({w!r})')
                elif w <= 0:
                    errs.append(f'{loc0}.col_widths[{j}]: peso debe ser > 0')
    for r, row in enumerate(rows):
        if len(row) != len(hdrs):
            errs.append(f'{loc0}.{key}[{r}]: {len(row)} celdas vs {len(hdrs)} encabezados '
                        f'— no existe columna de etiqueta implícita: la 1.ª celda ES la 1.ª '
                        f'columna de headers (ver: schema {m})')
        for j, cell in enumerate(row):
            over(f'{loc0}.{key}[{r}][{j}]', cell, lim)

SPEC_VALIDATORS = {
    '_list': _v_list,       # recibe spec para aplicar _desc_by_count
    '_strlist': _v_strlist,
    '_table': _v_table,
    '_examples': _v_examples,
    '_cards': _v_cards,
    '_debate': _v_debate,
    '_highlight': _v_highlight,
    '_quads': _v_quads,
    '_decision_flow': _v_decision_flow,
    '_acronym': _v_acronym,
    '_venn': _v_venn,
    '_chart': _v_chart,
    '_objectives': _v_objectives,
    '_colloquy': _v_colloquy,
}

MODULE_VALIDATORS = {
    'etymology': lambda d, m, loc0, over, errs: (
        (lambda frags_l: (
            errs.append(f'{loc0}.fragments: debe concatenar exactamente en term y '
                        f'tener len(roots) elementos (tiene {len(frags_l)})')
            if frags_l and (len(frags_l) != len(d.get('roots', []))
                            or ''.join(frags_l) != str(d.get('term', ''))) else None
        ))(d.get('fragments') or [])
    ),
    'annotated_passage': lambda d, m, loc0, over, errs: (
        (lambda marks, have: (
            errs.append(f'{loc0}: marcadores {sorted(marks - have, key=int)} del passage '
                        f'sin nota en annotations')
            if marks - have else None
        ))(
            set(_re.findall(r'\[(\d+)\]', str(d.get('passage', '')))),
            {str(a.get('ref', '')).strip() for a in d.get('annotations', [])}
        )
    ),
}

def _check_image_fields(d, m, loc0, errs):
    if m not in IMG_MODS:
        errs.append(f'{loc0}: módulo {m} no soporta imágenes (permitidos: {", ".join(IMG_MODS)})')
    for k in ('caption', 'credit'):
        if not str(d.get(k, '')).strip():
            errs.append(f'{loc0}.{k}: campo obligatorio cuando hay imagen')
    # v8.4 (idea del v8.0.0 paralelo): el pie de una figura debe ser ANALÍTICO,
    # no decorativo — longitud mínima sustantiva.
    if m == 'figure':
        cap_len = len(str(d.get('caption', '')).strip())
        if cap_len < _FIGURE_CAPTION_MIN:
            errs.append(f'{loc0}.caption: {cap_len} caracteres < {_FIGURE_CAPTION_MIN}'
                        f' — la figura debe tener un pie analítico sustantivo, '
                        f'no decorativo')
    pth = str(d.get('image', '')).strip()
    if not os.path.exists(pth):
        errs.append(f'{loc0}: archivo de imagen no encontrado: {pth}')
        return
    if pth.lower().rsplit('.', 1)[-1] not in ('jpg', 'jpeg', 'png'):
        errs.append(f'{loc0}: extensión no soportada (usar jpg/jpeg/png)')
    sz = os.path.getsize(pth)
    if not _IMG_MIN_B <= sz <= _IMG_MAX_B:
        errs.append(f'{loc0}: tamaño de imagen ({sz} B) fuera del rango 20 KB - 4 MB')
    try:
        if min(_image_size(pth)) < _IMG_MIN_PX:
            errs.append(f'{loc0}: dimensión mínima < 300 px')
    except Exception:
        errs.append(f'{loc0}: imagen no legible por Pillow')

def check(slides, lang='es-ES', profile=None):
    """Content-contract lint. Language enforcement here is LIMITED to the es-ES
    drift blacklist; the statistical fingerprint lives in the audit (WARN-only)."""
    errs = []
    def over(loc, s, lim):
        if isinstance(s, str) and len(s) > lim:
            errs.append(f'{loc}: {len(s)} > {lim} carácteres (sobran {len(s) - lim}; '
                        f'recorte al menos {len(s) - lim} y apunte a <= {int(lim * 0.9)} '
                        f'para dejar margen): "{s[:45]}..."')
    def walk_lang(v, loc):
        if isinstance(v, str):
            for w, fix in _drift_hits(v, lang):
                errs.append(f'{loc}: drift {w!r} -> {fix} (reescribir en el idioma objetivo)')
        elif isinstance(v, dict):
            for k, vv in v.items():
                if k != 'image':
                    walk_lang(vv, f'{loc}.{k}')
        elif isinstance(v, (list, tuple)):
            for j, vv in enumerate(v):
                walk_lang(vv, f'{loc}[{j}]')

    # v9.D: IMG_MODS ahora es module-level (derivado de MODULES); ver arriba.
    n_img = 0
    for i, d in enumerate(slides, 1):
        m = d.get('module')
        if m not in MODULES:
            errs.append(f'slide {i}: módulo desconocido {m!r}')
            continue
        loc0 = f'slide {i} [{m}]'
        spec = MODULES[m]['schema']
        if m not in _NO_HEADER_MODULES:
            for k, lim in COMMON.items():
                over(f'{loc0}.{k}', d.get(k, ''), lim)
        for k, lim in spec.items():
            if k.startswith('_'): continue
            over(f'{loc0}.{k}', d.get(k, ''), lim)
        for k in MODULES[m]['required_nonempty']:
            if not str(d.get(k, '')).strip():
                errs.append(f'{loc0}.{k}: campo obligatorio ausente o vacío')

        if d.get('image'):
            n_img += 1
            _check_image_fields(d, m, loc0, errs)

        # v9.3/C2 — validator table: cada rama '_xxx' vive en SPEC_VALIDATORS
        def over2(loc, txt, lim):
            over(loc, txt, lim)
        for sk_, sv in spec.items():
            if not sk_.startswith('_'):
                continue
            if sk_ == '_desc_by_count':
                continue  # se aplica dentro de _v_list
            fn_ = SPEC_VALIDATORS.get(sk_)
            if fn_ is None:
                continue
            if sk_ == '_list':
                _v_list(sv, d, m, loc0, over, errs, spec=spec)
            else:
                fn_(sv, d, m, loc0, over, errs)
        mv = MODULE_VALIDATORS.get(m)
        if mv:
            mv(d, m, loc0, over, errs)
        # v8.1 — rol de imagen honesto + trazabilidad ATU por diapositiva
        if d.get('image'):
            role = _effective_image_role(d)
            if role not in ('evidence', 'illustrative'):
                errs.append(f'{loc0}.image_role: {role!r} no válido (evidence|illustrative)')
            if d.get('atu') is not None and m == 'figure' and role != 'evidence':
                errs.append(f'{loc0}.atu: un ATU no puede resolver únicamente a una figura '
                            f'illustrative — márquela image_role="evidence" o mueva el ATU '
                            f'a un módulo que desarrolle el contenido')
        if d.get('atu') is not None:
            if isinstance(d['atu'], bool) or not isinstance(d['atu'], int):
                errs.append(f'{loc0}.atu: debe ser el número entero del ATU en el ledger '
                            f'(recibido {d["atu"]!r})')

        fit_fn = MODULES[m]['fit_rule']
        if fit_fn:
            for fld, bw, bh, fsz in fit_fn(d):
                need = est_height(d.get(fld, ''), bw, fsz)
                if need > bh * 1.06:
                    errs.append(f'{loc0}.{fld}: desborde estimado ({need:.2f}in > {bh}in) — acortar texto')
        # v9.2/B3-etapa1: la ausencia de fit-rule ya no es silenciosa — se reporta
        # una vez por deck (deck-level) para que quede visible qué módulos carecen
        # de protección de overflow (23/35 hoy).
        walk_lang(d, loc0)

    # ---- Deck-level coverage: core-4 + distinct-module floor (anti-fabricación) ----
    if n_img > 10:
        errs.append(f'deck: {n_img} diapositivas con imagen, máximo permitido es 10')
    present = {d.get('module') for d in slides}
    if profile == 'custom':
        core_needed = ['title', 'section_divider']
    else:
        core_needed = CORE_MODULES
    missing = [m for m in core_needed if m not in present]
    if missing:
        errs.append(f'deck: falta(n) módulo(s) núcleo obligatorio(s): {", ".join(missing)}')
    seen_anchors = {}
    for i, d in enumerate(slides, start=1):
        a = str(d.get('anchor', '')).strip()
        if not a:
            continue
        if not _ANCHOR_RE.match(a):
            errs.append(f"slide {i}: anchor {a!r} inválido (minúsculas, dígitos y guiones, 2-40 car.)")
        if a in seen_anchors:
            errs.append(f'slide {i}: anchor {a!r} duplicado (ya usado en slide {seen_anchors[a]})')
        seen_anchors[a] = i
    # v9.2/B3-etapa1 — visibilidad de cobertura fit: INFO por deck (no bloquea)
    no_fit = sorted(m_ for m_ in present if MODULES[m_]['fit_rule'] is None)
    if no_fit:
        errs.append(f'deck: INFO — módulos sin verificación de overflow tipográfico '
                    f'(sin fit-rule): {", ".join(no_fit)}')
    distinct = len(present)
    if profile == 'custom':
        # custom: sólo el suelo de variedad del perfil, no el global MIN_DISTINCT
        need = PROFILES.get(profile, {}).get('distinct', 2)
    else:
        need = MIN_DISTINCT_FULL if len(slides) >= FULL_DECK_THRESHOLD else MIN_DISTINCT
        if profile:
            need = max(need, PROFILES.get(profile, {}).get('distinct', need))
    if distinct < need:
        errs.append(f'deck: {distinct} módulos distintos, mínimo {need} '
                    f'(variedad estructural; no fabrique contenido para cumplirla — '
                    f'considere ampliar el temario o reducir la extensión)')
    return errs

# ===================== CLI PIPELINE =====================
def _self_hash():
    return _hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()

def _load_manifest(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f'manifest no encontrado: {path}')
    spec = importlib.util.spec_from_file_location('omc_manifest', os.path.abspath(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _load_slides(path):
    """Shared loader: clean errors + SLIDES validation (no silent empty decks)."""
    mod = _load_manifest(path)
    slides = getattr(mod, 'SLIDES', None)
    if not isinstance(slides, list) or not slides:
        raise ValueError('SLIDES vacío o ausente en el manifest')
    return mod, slides

def _get_lang(mod):
    return str(getattr(mod, 'CONFIG', {}).get('LANG', 'es-ES'))

def _get_pal_key(mod):
    return str((getattr(mod, 'CONFIG', {}) or {}).get('PALETTE', 'oxford')).lower()

def _apply_fonts(pal_key):
    """Tipografía por tema; idempotente. Se aplica ANTES del lint (est_height) y en render."""
    global FONT_TITLE, FONT_BODY
    if pal_key == 'ucp':
        FONT_TITLE = FONT_BODY = "Montserrat"
    else:
        FONT_TITLE, FONT_BODY = "Georgia", "Calibri"

def _render(mod, out):
    if not _PPTX_OK and not _import_pptx():
        raise RuntimeError('python-pptx no disponible')
    info = getattr(mod, 'COURSE_INFO', {})
    config = getattr(mod, 'CONFIG', {})
    slides = getattr(mod, 'SLIDES', [])
    set_ui(config.get('LANG', 'es-ES'))
    pal_key = config.get('PALETTE', 'oxford').lower()
    pal = PALETTES.get(pal_key, PALETTES['oxford'])
    global _PALETTE
    _PALETTE = pal_key
    _apply_fonts(pal_key)   # Montserrat 100% bajo ucp; Georgia/Calibri si no
    _set_tokens(pal_key)
    # v9.2/B4 — el toggle de cita ATU en footnotes vive en CONFIG (default on)
    global _ATU_FOOTNOTE
    _ATU_FOOTNOTE = bool(config.get('ATU_FOOTNOTE', True))

    prs = Presentation()
    prs.slide_width = Inches(CANVAS_W)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    for i, d in enumerate(slides, start=1):
        mname = d.get('module')
        if mname not in dispatch_map:
            raise KeyError(f"módulo desconocido {mname!r} (slide {i}) — "
                       f"ejecute `schema` para el listado válido")
        _CTX["slide"], _CTX["module"] = i, mname
        s = prs.slides.add_slide(blank)
        _SURFACE_STACK.clear()
        bg(s, pal)
        if mname not in _NO_HEADER_MODULES:
            header(s, pal, d, i)
            footer(s, pal, i, info.get('course', ''), config)
        dispatch_map[mname](s, d, pal, info)
    prs.save(out)
    return len(slides)

def _ledger_section_count(path='work/atu_ledger.md'):
    if not os.path.exists(path):
        return None
    txt = open(path, encoding='utf-8').read()
    parts = _re.split(r'^#{1,3}\s+', txt, flags=_re.M)[1:]
    n = 0
    for p in parts:
        if _re.findall(r'^\|\s*(\d+)\s*\|[^|]*\|\s*(\d+)\s*\|', p, flags=_re.M):
            n += 1
    return n or None

def _lint_slides(slides, lang='es-ES', profile=None):
    """Full lint: content contract + ledger/divider cross-check + ATU reference resolution."""
    errs = check(slides, lang, profile)
    sections = parse_ledger()
    anchors = slide_anchors(slides)
    if sections:
        for name, rows in sections:
            for atu, ref, _quote in rows:
                _, err = resolve_ref(ref, anchors, len(slides))
                if err:
                    errs.append(f'ledger [{name}] ATU {atu}: {err}')
    # v9.B/Q-F3c: derivar el conteo de parse_ledger (acepta anclas) en vez del
    # regex antiguo que exigía refs numéricas — con ledgers basados en anclas
    # (los que genera `new`) la regla divider-por-sección NUNCA disparaba.
    n_sections = len(sections) if sections is not None else _ledger_section_count()
    n_dividers = sum(1 for s in slides if s.get('module') == 'section_divider')
    if n_sections is not None and n_dividers != n_sections:
        errs.append(f'deck: {n_dividers} section_divider(s), esperado {n_sections} según ledger '
                    f'(work/atu_ledger.md) — regla: UN section_divider por sección del ledger, '
                    f'en el mismo orden. Ajuste el manifest o fusione secciones del ledger.')

    # v8.1 — cobertura bidirecional ATU <-> slide (los huérfanos dejan de ser invisibles)
    if sections:
        ledger_atus = {}
        for name, rows in sections:
            for a, ref, _q in rows:
                if a in ledger_atus:
                    errs.append(f'ledger [{name}]: ATU {a} duplicado (ya en [{ledger_atus[a]}])')
                else:
                    ledger_atus[a] = name
        claimed = _atu_claims(slides)   # atu -> primera slide que lo reclama
        for i, d in enumerate(slides, start=1):
            a = d.get('atu')
            if _is_atu_claim(a) and a not in ledger_atus:
                errs.append(f'slide {i}: reclama ATU {a} que no existe en el ledger '
                            f'(work/atu_ledger.md)')
        orphans = sorted(set(ledger_atus) - set(claimed))
        if orphans:
            errs.append(f'deck: ATU sin ninguna diapositiva que los desarrolle: {orphans} '
                        f'— añada "atu": <N> al slide correspondiente o elimine el ATU del ledger')
    return errs

def _fixture_image():
    """Imagen determinista para el fixture (cumple el contrato: jpg, >=20 KB,
    >=300 px). Se genera una vez por proceso en temp."""
    from PIL import Image as _PILImage
    p = os.path.join(_tf.gettempdir(), 'omc_fixture_img.jpg')
    if os.path.exists(p):
        return p
    im = _PILImage.new('RGB', (800, 600))
    px = im.load()
    for y in range(0, 600, 4):
        for x in range(0, 800, 4):
            c = ((x * 7 + y * 13) % 256)
            for dy in range(4):
                for dx in range(4):
                    px[min(x + dx, 799), min(y + dy, 599)] = (c, (c * 3) % 256, (c * 7) % 256)
    im.save(p, 'JPEG', quality=88, optimize=True)
    return p

def _self_test_slides():
    """Manifest sintético compartido por self-test y matriz de contraste.
    v9.A: cubre LOS 35 MÓDULOS — la matriz de contraste debe ejercitar toda
    combinación token/superficie real (pills, medallones, paneles de acento),
    no solo 5 módulos. Lección del bug on_success bajo ucp (3.1:1 invisible)."""
    img = None
    try:
        img = _fixture_image()
    except Exception:
        img = None  # sin Pillow el fixture cae a módulos sin imagen
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
    missing = set(dispatch_map) - present
    if missing:
        # Nunca debe pasar: si un módulo nuevo no tiene fixture, fallar ruidoso.
        raise AssertionError(f'fixture self-test incompleto, faltan: {sorted(missing)}')
    return S

def _synthetic_manifest(pal_key):
    return _types.SimpleNamespace(
        COURSE_INFO={'course': 'OXFORD MEDICAL CHECK'}, CONFIG={'PALETTE': pal_key},
        SLIDES=_self_test_slides())

def _contrast_scan(modlike):
    """Renderiza con instrumentación activa y devuelve las violaciones de contraste."""
    if not _PPTX_OK and not _import_pptx():
        return [{'error': 'python-pptx no disponible'}]
    out = os.path.join(_tf.gettempdir(), 'omc_contrast_scan.pptx')
    try:
        with _contrast_instrumented():
            _render(modlike, out)
            return _contrast_failures()
    except Exception as e:
        return [{'error': f'scan falló: {e}'}]
    finally:
        try:
            if os.path.exists(out):
                os.remove(out)
        except OSError:
            pass

def _self_test():
    """Dry-run render + linter self-test on a synthetic manifest. Used by check and preflight."""
    m = _synthetic_manifest('oxford')
    out = os.path.join(_tf.gettempdir(), 'omc_dryrun.pptx')
    try:
        n = _render(m, out)
        print(f'  dry-run: OK ({n} slides, {os.path.getsize(out)} bytes)')
    except Exception as e:
        print(f'  dry-run: FAIL — {e}')
        return False
    finally:
        try:
            if os.path.exists(out):
                os.remove(out)
        except OSError:
            pass
    errs = check(m.SLIDES)
    slide_errs = [e for e in errs if not e.startswith('deck:')]
    if slide_errs:
        print('  [SELF-TEST] Error en auto-test del linter:')
        for e in slide_errs: print('    X ' + e)
        return False
    # v9.F — regresión de drift: casos de falso positivo conocidos DEBEN pasar
    # limpios y los casos de infiltración real DEBEN bloquear. Sin esto, una regla
    # nueva puede reintroducir el bug '-dades' sin que nadie lo note.
    _DRIFT_FP_CASES = [
        ('es-ES', 'las modalidades y velocidades del tratamiento', False),
        ('es-ES', 'ciudades y oportunidades de formación', False),
        ('es-ES', 'a nacionalidade e cidadania brasileira', True),   # pt real
        ('es-ES', 'coração e feijões', True),                        # chars pt
        ('pt-BR', 'la inflamación y sus complicaciones', True),      # es real
        ('en-US', 'der Straßenverkehr und die Überwachung', True),   # de real
        ('fr-FR', 'el niño y la niña', True),                        # es char en fr
        ('de-DE', 'die Entzündung des Patienten', False),
    ]
    drift_bad = []
    for lang, text, expect_hit in _DRIFT_FP_CASES:
        got = bool(_drift_hits(text, lang))
        if got != expect_hit:
            drift_bad.append(f'[{lang}] {text!r} -> {"bloquea" if got else "pasa"} '
                             f'(esperado {"bloquea" if expect_hit else "pasa"})')
    if drift_bad:
        print('  [SELF-TEST] Regresión de drift (FP o infiltración no detectada):')
        for b in drift_bad: print('    X ' + b)
        return False
    print(f'  [SELF-TEST] Drift simétrico: {len(_DRIFT_FP_CASES)} casos OK (FP + infiltración).')
    print('  [SELF-TEST] PASS — Engine y Linter validados.')
    return True

def _ensure_deps(tag):
    """Las dependencias pueden desaparecer entre sesiones: recupera automáticamente."""
    if _deps_ready():
        return True
    print(f'[{tag}] Dependencias ausentes — reinstalando (python-pptx, Pillow)...')
    _pip_install(['python-pptx', 'Pillow'])
    if _deps_ready():
        print(f'[{tag}] Dependencias restauradas.')
        return True
    print(f'[{tag}] FAIL — no se pudieron instalar las dependencias. Ejecute preflight.')
    return False

def cmd_check():
    print(f"{KIT_VERSION}")
    print(f"sha256: {_self_hash()}")
    if not _import_pptx():
        print('python-pptx: MISSING — ejecute preflight')
        return 1
    print('python-pptx: OK')
    if not _module_available('PIL'):
        print('Pillow: MISSING — ejecute preflight (requerido para figuras)')
        return 1
    print('Pillow: OK')
    return 0 if _self_test() else 1

def _lint_imgprep(slides):
    """v8.2 — pre-paso imgprep automático: valida el pool referenciado antes del
    contrato de contenido. Solo informa; los errores de imagen ya bloquean en check(),
    esto adelanta el diagnóstico (formato/bytes/px) al paso lint."""
    msgs = []
    seen = set()
    for i, d in enumerate(slides, start=1):
        pth = str(d.get('image', '')).strip()
        if not pth or pth in seen or not os.path.exists(pth):
            continue
        seen.add(pth)
        st, msg, _out = _imgprep_one(pth, fix=False)
        if st != 'OK':
            msgs.append(f'slide {i} [{d.get("module")}]: {os.path.basename(pth)} — {msg}')
    return msgs

def cmd_lint(path, as_json=False, profile=None):
    try:
        mod, slides = _load_slides(path)
    except Exception as e:
        if as_json:
            print(_json.dumps({'kit': KIT_VERSION, 'status': 'FAIL', 'error_count': 1,
                               'errors': [{'scope': 'manifest', 'message': str(e), 'raw': str(e)}]},
                              ensure_ascii=False, indent=2))
        else:
            print(f'[OMC Lint] FAIL — {e}')
        return 1
    _apply_fonts(_get_pal_key(mod))  # est_height consciente de fuente (Montserrat)
    lang = _get_lang(mod)
    pname, _ = resolve_profile(mod, profile)
    # v8.2 — imgprep implícito: diagnóstico temprano del pool de figuras
    img_msgs = _lint_imgprep(slides) if _module_available('PIL') else []
    if img_msgs and not as_json:
        print('[OMC Lint] Aviso del pool de imágenes (imgprep implícito):')
        for m in img_msgs:
            print('  ! ' + m)
    errs = _lint_slides(slides, lang, pname)
    # v9.2/B3: las líneas 'deck: INFO —' son informativas; no cuentan como fallo.
    info_lines = [e for e in errs if e.startswith('deck: INFO —')]
    hard_errs = [e for e in errs if not e.startswith('deck: INFO —')]
    if as_json:
        payload = errs_to_json(hard_errs, slides, pname, lang)
        if info_lines:
            payload['info'] = info_lines
        print(_json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if hard_errs else 0
    if hard_errs:
        print(f'[OMC Lint] FAIL — {len(hard_errs)} violación(es) detectadas (perfil {pname}):')
        for e in hard_errs: print('  X ' + e)
        for e in info_lines: print('  ℹ ' + e)
        return 1
    for e in info_lines:
        print('[OMC Lint] ' + e)
    print(f'[OMC Lint] PASS — {len(slides)} diapositivas cumplen con el contrato académico '
          f'(perfil {pname}, idioma {lang}).')
    return 0

def cmd_build(path, out='deck.pptx', profile=None):
    try:
        mod, slides = _load_slides(path)
    except Exception as e:
        print(f'[OMC Engine] FAIL — {e}')
        return 1
    _apply_fonts(_get_pal_key(mod))
    # Fail-fast: nunca gastar un ciclo de render en un manifest que viola el contrato.
    pname, _ = resolve_profile(mod, profile)
    errs = _lint_slides(slides, _get_lang(mod), pname)
    if errs:
        print(f'[OMC Engine] Build cancelado (fail-fast): {len(errs)} violación(es):')
        for e in errs[:25]: print('  X ' + e)
        if len(errs) > 25:
            print(f'  ... y {len(errs) - 25} más (ejecute: lint {path})')
        return 1
    if not _ensure_deps('OMC Engine'):
        return 1
    n = _render(mod, out)
    print(f'[OMC Engine] Presentación compilada exitosamente: {out} ({n} diapositivas)')
    return 0

def _write_audit(mod, slides, deck_path, out_md='work/completeness_audit_updated.md',
                 lint_errs=None, lang='es-ES', profile=None, contrast_fails=None,
                 sections=None):
    cfg = getattr(mod, 'CONFIG', {})
    present = {s.get('module') for s in slides}
    n = len(slides)
    deck_ok = os.path.exists(deck_path) and os.path.getsize(deck_path) > 0
    size = os.path.getsize(deck_path) if deck_ok else 0
    pname, prof = resolve_profile(mod, profile)
    if lint_errs is None:
        lint_errs = check(slides, lang, pname)

    L = [
        f'# OXBRIDGE COMPLETENESS & INTEGRITY AUDIT — {KIT_VERSION}',
        f'## Fecha: {_dt.date.today().isoformat()}',
        f'## Diapositivas en Manifest: {n}',
        f'## Idioma Declarado: {lang}',
        f'## PPTX Generado: {deck_path} ({size:,} bytes)' if deck_ok else f'## PPTX Generado: {deck_path} (MISSING)',
        '',
        '### 0. Contrato Editorial (Lint)'
    ]
    # v9.5.1 — las INFO de cobertura fit no son violaciones (bug hallado en el
    # cold-run real: audit contaba "1 fallos" por una línea informativa).
    info_errs = [e for e in lint_errs if e.startswith('deck: INFO —')]
    hard_lint = [e for e in lint_errs if not e.startswith('deck: INFO —')]
    if hard_lint:
        L.append(f'- [FAIL] Lint: {len(hard_lint)} violación(es) detectada(s)')
        for e in hard_lint:
            L.append(f'  - {e}')
        for e in info_errs:
            L.append(f'  - ℹ {e}')
    else:
        L.append('- [PASS] Lint: 0 violaciones')
        for e in info_errs:
            L.append(f'- [INFO] {e}')

    L.append('')
    L.append(f'### 1. Cobertura de Módulos (perfil: {pname} — {prof["desc"]})')
    audit_core = ['title', 'section_divider'] if pname == 'custom' else CORE_MODULES
    for m in audit_core:
        L.append(f'- [{"PASS" if m in present else "FAIL"}] Módulo núcleo: {m}')
    distinct = len(present)
    if pname == 'custom':
        need = prof['distinct']
    else:
        need = max(MIN_DISTINCT_FULL if n >= FULL_DECK_THRESHOLD else MIN_DISTINCT, prof['distinct'])
    L.append(f'- [{"PASS" if distinct >= need else "FAIL"}] Variedad estructural: '
             f'{distinct} módulos distintos (mínimo {need})')
    opt = [m for m in OPTIONAL_MODULES if m in present]
    L.append(f'- [INFO] Módulos opcionales presentes ({len(opt)}/{len(OPTIONAL_MODULES)}): '
             f'{", ".join(opt) if opt else "ninguno"}')

    L.append('')
    L.append('### 2. Mapeo ATU (work/atu_ledger.md)')
    if sections is None:  # v9.1/A5: reutiliza el parse del pipeline cuando existe
        sections = parse_ledger()
    anchors = slide_anchors(slides)
    if sections:
        all_atu, n_anchor_refs, n_unresolved = [], 0, 0
        for name, rows in sections:
            atus = [a for a, _r, _q in rows]
            all_atu += atus
            idx, bad = [], 0
            for a, ref, _q in rows:
                if not str(ref).strip().lstrip('#').isdigit():
                    n_anchor_refs += 1
                i, err = resolve_ref(ref, anchors, n)
                if err:
                    bad += 1
                else:
                    idx.append(i)
            n_unresolved += bad
            rng = f'{min(idx)}–{max(idx)}' if idx else 'sin resolver'
            L.append(f'- [{"PASS" if bad == 0 else "FAIL"}] {name} — {len(atus)} ATU '
                     f'({min(atus)}–{max(atus)}) → slides {rng}'
                     + (f' · {bad} referencia(s) irresoluble(s)' if bad else ''))
        dup = len(all_atu) - len(set(all_atu))
        gap = len(sorted(set(range(1, max(all_atu) + 1)) - set(all_atu))) if all_atu else 0
        L.append(f'- [{"PASS" if all_atu and dup == 0 and gap == 0 else "FAIL"}] '
                 f'Integridad ATU (numeración/continuidad/rangos): {len(set(all_atu))} únicas, '
                 f'{dup} duplicadas, {gap} saltos')
        mode = ('anclas' if n_anchor_refs == len(all_atu) else
                'índices numéricos' if n_anchor_refs == 0 else 'mixto (anclas + índices)')
        L.append(f'- [INFO] Referencias del ledger: {mode}'
                 + ('' if n_anchor_refs else ' — considere anclas (#slug) para evitar renumeración'))
    else:
        L.append('- [FILL] Ledger no encontrado.')

    L.append('')
    L.append('### 3. Verificación Editorial & Estilística')
    def _cnt_drift(v, lg):
        if isinstance(v, str): return len(_drift_hits(v, lg))
        if isinstance(v, dict): return sum(_cnt_drift(vv, lg) for k, vv in v.items() if k != 'image')
        if isinstance(v, (list, tuple)): return sum(_cnt_drift(vv, lg) for vv in v)
        return 0
    n_drift = sum(_cnt_drift(s, lang) for s in slides)
    pal_name = str(cfg.get("PALETTE", "oxford")).title()
    L.append(f'- [{"PASS" if n_drift == 0 else "FAIL"}] Pureza Idiomática ({lang}): {n_drift} desvíos')
    L.append(f'- [INFO] Paleta Universitaria: {pal_name}')
    L.append(f"- [INFO] Modo Cognitivo: {cfg.get('MODE', 'declarative')} (convención de autoría, no verificada por el motor)")
    n_img = sum(1 for s in slides if s.get('image'))
    L.append(f'- [{"PASS" if n_img <= 10 else "FAIL"}] Curaduría Visual: {n_img}/10 figuras')
    # v8.1 — honestidad de imágenes: evidencia vs ilustrativa
    n_evid = sum(1 for s in slides if s.get('image') and _effective_image_role(s) == 'evidence')
    L.append(f'- [INFO] Roles de imagen: {n_evid} evidence (desarrollan contenido) · '
             f'{n_img - n_evid} illustrative (apoyo decorativo; no satisfacen cobertura)')
    slo, shi = prof['slides']
    L.append(f'- [{"PASS" if slo <= n <= shi else "WARN"}] Extensión del deck: {n} diapositivas '
             f'(perfil {pname}: {slo}-{shi}; aviso no bloqueante)')
    flo, fhi = prof['figures']
    L.append(f'- [{"PASS" if flo <= n_evid <= fhi else "WARN"}] Presupuesto visual del perfil: '
             f'{n_evid} figuras evidence (esperado {flo}-{fhi})'
             + ('' if n_img == n_evid else
                f' · {n_img - n_evid} illustrative no cuentan (usar evidence para figuras '
                f'del source)'))

    # v8.1 — fidelidad al source: paráfrasis débil slide vs source_quote (WARN-only)
    if sections:
        weak, measured, skipped = _paraphrase_weak(slides, sections, _atu_claims(slides))
        tag = 'PASS' if not weak else 'WARN'
        L.append(f'- [{tag}] Fidelidad al source: {measured} ATU con cita medida'
                 + (f' · {skipped} citas cortas no medibles' if skipped else '')
                 + ('' if weak else ' — solape léxico suficiente'))
        for a, i, ov in weak:
            L.append(f'  - ATU {a} → slide {i}: solape {ov:.0%} < {_PARAPHRASE_FLOOR:.0%} '
                     f'— verifique que la paráfrasis no cambie la intención del source '
                     f'(no fortalecer, generalizar ni eliminar cualificadores)')

    L.append('')
    L.append('### 4. Idioma (tripwire, no bloqueante)')
    L.append(f'- Idioma declarado (CONFIG): {lang}')
    scores_d, toks_d = _lang_scores(_iter_strings(slides))
    win_d, rank_d, marg_d = _lang_verdict(scores_d, toks_d, MIN_DECK_TOKENS)
    top3 = ', '.join(f'{lg}: {sc:.0f}' for lg, sc in rank_d[:3])
    if win_d is None:
        L.append(f'- [FILL] Texto insuficiente para verificación ({toks_d} tokens < {MIN_DECK_TOKENS}).')
    elif win_d == lang:
        tag = 'PASS' if marg_d >= MIN_MARGIN else 'WARN'
        L.append(f'- [{tag}] Detectado {win_d} = declarado (margen {marg_d:.2f}; {top3})')
    else:
        L.append(f'- [WARN] Posible desvío: declarado {lang}, detectado {win_d} '
                 f'(margen {marg_d:.2f}; {top3}) — revisar manualmente antes de entregar')

    L.append('')
    L.append('### 5. Contraste WCAG (gate)')
    if contrast_fails is None:
        L.append('- [INFO] No escaneado en esta pasada (use `contrast` o `all`).')
    elif contrast_fails:
        L.append(f'- [FAIL] Contraste: {len(contrast_fails)} par(es) bajo umbral')
        for cf in contrast_fails[:20]:
            L.append(f"  - slide {cf.get('slide')} [{cf.get('module')}]: "
                     f"fg #{cf.get('fg')} sobre #{cf.get('bg')} = {cf.get('ratio')} "
                     f"(requiere {cf.get('required')})")
        if len(contrast_fails) > 20:
            L.append(f'  - ... y {len(contrast_fails) - 20} más')
    else:
        L.append('- [PASS] Contraste: 0 pares bajo umbral (texto medido contra superficie efectiva)')

    os.makedirs(os.path.dirname(out_md) or '.', exist_ok=True)
    open(out_md, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    fails = sum(1 for x in L if x.startswith('- [FAIL]'))
    warns = sum(1 for x in L if x.startswith('- [WARN]'))
    print(f'[OMC Audit] Reporte generado en: {out_md} ({fails} fallos, {warns} avisos)')
    return 0 if fails == 0 else 1

def cmd_audit(manifest_path, deck_path, out_md='work/completeness_audit_updated.md',
              profile=None):
    try:
        mod, slides = _load_slides(manifest_path)
    except Exception as e:
        print(f'[OMC Audit] FAIL — {e}')
        return 1
    _apply_fonts(_get_pal_key(mod))
    cfails = _contrast_scan(mod)
    return _write_audit(mod, slides, deck_path, out_md, lang=_get_lang(mod),
                        profile=profile, contrast_fails=cfails)

def cmd_all(path, out='deck.pptx', profile=None):
    """Single-process pipeline: lint -> build -> audit (+contraste) en un proceso."""
    print(f'[OMC All] 1/3 — Lint: {path}')
    try:
        mod, slides = _load_slides(path)
    except Exception as e:
        print(f'[OMC All] FAIL — {e}')
        return 1
    _apply_fonts(_get_pal_key(mod))
    lang = _get_lang(mod)
    pname, prof = resolve_profile(mod, profile)
    _sections_parsed = parse_ledger()  # v9.1/A5: una sola lectura del ledger
    errs = _lint_slides(slides, lang, pname)
    # v9.2/B3: las INFO de cobertura fit no son fallos (se muestran como ℹ)
    info_all = [e for e in errs if e.startswith('deck: INFO —')]
    errs = [e for e in errs if not e.startswith('deck: INFO —')]
    if errs:
        print(f'[OMC All] Lint FAIL — {len(errs)} violación(es) (perfil {pname}):')
        for e in errs: print('  X ' + e)
        return 1
    for e in info_all: print('  ℹ ' + e)
    print(f'[OMC All] Lint PASS — {len(slides)} diapositivas '
          f'(idioma: {lang} · perfil: {pname} — {prof["desc"]}).')
    print('[OMC All] 2/3 — Build...')
    if not _ensure_deps('OMC All'):
        return 1
    # v8.2 — un solo render: la instrumentación de contraste corre sobre el build REAL
    # (antes se re-renderizaba el deck completo solo para el escaneo).
    with _contrast_instrumented(clear_surfaces=False):
        n = _render(mod, out)
    cfails = _contrast_failures()
    print(f'[OMC All] Build OK: {out} ({n} diapositivas)')
    print('[OMC All] 3/3 — Audit + contraste...')
    if cfails:
        print(f'[OMC All] Contraste: {len(cfails)} violación(es) — ver sección 5 del audit.')
    return _write_audit(mod, slides, out, lint_errs=errs, lang=lang, profile=pname,
                        contrast_fails=cfails,
                        sections=_sections_parsed)

def cmd_contrast(manifest_path=None, as_json=False, profile=None):
    """Gate WCAG: matriz de los 5 temas (sin manifest) o escaneo de un manifest."""
    if manifest_path:
        try:
            mod, slides = _load_slides(manifest_path)
        except Exception as e:
            if as_json:
                print(_json.dumps({'kit': KIT_VERSION, 'status': 'FAIL', 'error': str(e)},
                                  ensure_ascii=False, indent=2))
            else:
                print(f'[OMC Contrast] FAIL — {e}')
            return 1
        _apply_fonts(_get_pal_key(mod))
        pname, _ = resolve_profile(mod, profile)
        fails = _contrast_scan(mod)
        if as_json:
            # v9.2/B1: mismo envelope que lint --json (status/error_count/errors)
            print(_json.dumps({'kit': KIT_VERSION, 'mode': 'manifest', 'profile': pname,
                               'lang': _get_lang(mod),
                               'status': 'PASS' if not fails else 'FAIL',
                               'error_count': len(fails), 'errors': fails},
                              ensure_ascii=False, indent=2))
            return 0 if not fails else 1
        if fails:
            print(f'[OMC Contrast] FAIL — {len(fails)} par(es) bajo umbral (perfil {pname}):')
            for cf in fails:
                print(f"  X slide {cf.get('slide')} [{cf.get('module')}]: "
                      f"#{cf.get('fg')} sobre #{cf.get('bg')} = {cf.get('ratio')} < {cf.get('required')}")
            return 1
        print(f'[OMC Contrast] PASS — 0 violaciones ({len(slides)} diapositivas, perfil {pname}).')
        return 0
    # Matriz 5 temas sobre el manifest sintético.
    report, total = {}, 0
    for key in PALETTES:
        fails = _contrast_scan(_synthetic_manifest(key))
        report[key] = fails
        total += len(fails)
    if as_json:
        # v9.2/B1: envelope unificado (error_count como lint)
        print(_json.dumps({'kit': KIT_VERSION, 'mode': 'matrix',
                           'status': 'PASS' if total == 0 else 'FAIL',
                           'error_count': total,
                           'palettes': {k: {'failure_count': len(v), 'failures': v}
                                        for k, v in report.items()}},
                          ensure_ascii=False, indent=2))
        return 0 if total == 0 else 1
    print('[OMC Contrast] Matriz de contraste (manifest sintético × 5 temas):')
    for key, fails in report.items():
        mark = 'PASS' if not fails else f'FAIL ({len(fails)})'
        print(f'  [{mark}] {key}')
        for cf in fails[:5]:
            print(f"      slide {cf.get('slide')} [{cf.get('module')}]: "
                  f"#{cf.get('fg')} sobre #{cf.get('bg')} = {cf.get('ratio')} < {cf.get('required')}")
    print(f'[OMC Contrast] {"PASS — 0 violaciones en los 5 temas." if total == 0 else f"FAIL — {total} violación(es)."}')
    return 0 if total == 0 else 1

def _pip_install(pkgs):
    import subprocess
    r = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', *pkgs])
    if r.returncode != 0:
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet',
                            '--break-system-packages', *pkgs])
    return r.returncode == 0

def _deps_ready():
    return _import_pptx() and _module_available('PIL')

def _preflight_cache_path():
    return os.path.join(os.path.expanduser('~'), '.omc', 'preflight_cache.json')

def _deps_signature():
    """v9.H — versiones de las deps en la firma: un upgrade de python-pptx/Pillow
    invalida el PASS cacheado (antes solo importabilidad contaba → stale-PASS)."""
    sig = {}
    try:
        import pptx
        sig['pptx'] = getattr(pptx, '__version__', 'unknown')
    except Exception:
        return None
    try:
        from PIL import __version__ as _pilv
        sig['PIL'] = _pilv
    except Exception:
        return None
    return sig

def _preflight_cache_load(expected_hash):
    """Devuelve el reporte cacheado si el sha256 del kit Y las versiones de deps
    coinciden; None si no."""
    try:
        with open(_preflight_cache_path(), encoding='utf-8') as f:
            data = _json.load(f)
        if data.get('sha256') == expected_hash and data.get('status') == 'PASS':
            if data.get('deps') != _deps_signature():
                print('[OMC Preflight] Cache invalidada: cambiaron las versiones de '
                      'python-pptx/Pillow. Re-ejecutando self-test + matriz...')
                return None
            return data
    except (OSError, ValueError):
        pass
    return None

def _preflight_cache_store(expected_hash, extra):
    try:
        os.makedirs(os.path.dirname(_preflight_cache_path()), exist_ok=True)
        with open(_preflight_cache_path(), 'w', encoding='utf-8') as f:
            _json.dump({'sha256': expected_hash, 'status': 'PASS',
                        'kit': KIT_VERSION, 'deps': _deps_signature(), **extra}, f)
    except OSError:
        pass

def cmd_preflight(expected=None, force=False, as_json=False):
    def _emit(status, **kw):
        if as_json:
            print(_json.dumps({'kit': KIT_VERSION, 'command': 'preflight',
                               'status': status, **kw}, ensure_ascii=False))
        return status
    """One step: hash verify + deps + workspace + engine self-test + matriz de contraste.
    v8.2: self-test + matriz se cachean por sha256 del kit — arranque frío repetido
    salta los 6 renders sintéticos cuando el kit no cambió (`--force` re-ejecuta)."""
    print(f"{KIT_VERSION}")
    h = _self_hash()
    print(f"sha256: {h}")
    if expected is not None and h.lower() != str(expected).strip().lower():
        print(f'[OMC Preflight] FAIL: Hash mismatch. Obtenido: {h}')
        if as_json:
            print(_json.dumps({'kit': KIT_VERSION, 'command': 'preflight', 'status': 'FAIL',
                               'reason': 'hash_mismatch', 'sha256': h}, ensure_ascii=False))
        return 1
    if not force:
        cached = _preflight_cache_load(h)
        if cached and _deps_ready():
            print('python-pptx: OK | Pillow: OK')
            print(f"[OMC Preflight] Cache vigente (kit sin cambios desde "
                  f"{cached.get('date', '?')}): self-test y matriz de contraste omitidos. "
                  f"Use preflight --force para re-ejecutar.")
            print('[OMC Preflight] PASS — Entorno listo para compilación.')
            if as_json:
                print(_json.dumps({'kit': KIT_VERSION, 'command': 'preflight',
                                   'status': 'PASS', 'cached': True,
                                   'sha256': h}, ensure_ascii=False))
            return 0
    if not _deps_ready():
        print('Instalando dependencias de presentación...')
        if not _pip_install(['python-pptx', 'Pillow']):
            print('[OMC Preflight] FAIL — instalación de dependencias fallida.')
            return 1
        if not _deps_ready():
            print('[OMC Preflight] FAIL — dependencias ausentes tras la instalación.')
            return 1
    print('python-pptx: OK | Pillow: OK')
    os.makedirs('work', exist_ok=True)
    os.makedirs('work/imgs', exist_ok=True)
    print('[OMC Preflight] Auto-test del motor:')
    if not _self_test():
        return 1
    print('[OMC Preflight] Matriz de contraste (5 temas):')
    if cmd_contrast(None, as_json=False) != 0:
        print('[OMC Preflight] FAIL — la compuerta de contraste detecta violaciones.')
        return 1
    _preflight_cache_store(h, {'date': _dt.date.today().isoformat()})
    print('[OMC Preflight] PASS — Entorno listo para compilación.')
    if as_json:
        print(_json.dumps({'kit': KIT_VERSION, 'command': 'preflight',
                           'status': 'PASS', 'cached': False,
                           'sha256': h}, ensure_ascii=False))
    print('[OMC Preflight] Antes de redactar: `schema <módulo>` publica campos, cardinalidades y '
          'presupuestos de caracteres; `imgprep work/imgs` valida y normaliza las figuras.')
    return 0

# ===================== AUTHORING AIDS (schema / imgprep) =====================
MODULE_GOTCHAS = {
 'comparison_table': 'La 1.ª columna de headers ES la columna de criterio: cada fila '
                     'debe tener exactamente len(headers) celdas.',
 'synthesis_grid':   'NO tiene columna de etiqueta implícita. matrix_data es una malla '
                     'de 3 filas x len(headers) celdas; la 1.ª celda ya es la 1.ª columna.',
 'flow_diagram':     'Exactamente 1 paso con highlight=True. Si algún paso lleva '
                     'decision=True, NO puede existir la clave explanation, y desc pasa '
                     'a ser la etiqueta de la rama NO (máx. 40 car.).',
 'etymology':        'fragments debe concatenarse EXACTAMENTE en term y tener el mismo '
                     'número de elementos que roots.',
 'mnemonic_card':    'len(expansion) debe ser igual a len(acronym): un término por letra.',
 'chart_data':       'chart_type solo admite "bar" o "line"; cada series.values debe tener '
                     'la misma longitud que categories y ser numérico.',
 'venn_diagram':     'shared representa SOLO la intersección; 2-3 conjuntos.',
 'learning_objectives': 'bloom debe ser remember|understand|apply|analyze|evaluate|create.',
 'colloquy':         'speaker debe ser exactamente "tutor" o "student".',
 'figure':           'image debe ser .jpg/.jpeg/.png existente, 20 KB-4 MB y >= 300 px de '
                     'lado menor. Ejecute `imgprep work/imgs` antes del lint. '
                     'caption ANALÍTICO (15-110 car.): describa qué muestra la figura, '
                     'no la decore.',
 'authority_card':   'Requiere retrato: mismas reglas de imagen que figure.',
 'case_block':       'findings es una lista de STRINGS cortas (no dicts).',
 'annotated_passage':'Los marcadores [1], [2]... del passage deben existir en annotations.ref.',
}

# ===================== v9.D — REGISTRO UNIFICADO DE MÓDULOS =====================
# Fuente única de VERDAD DECLARATIVA: tier e image_role_default por módulo.
# v9.3/C1 — el registro ahora TAMBIÉN ensambla schema (B), required_nonempty,
# gotcha y fit: los consumidores siguen leyendo las vistas legacy (B, etc.) para
# compat, pero MODULES es la referencia; añadir un módulo nuevo toca UN bloque.
_MODULES_TIER_EXPLICIT = {
    'title': 'core', 'definition': 'core', 'section_divider': 'core', 'figure': 'core',
}
_MODULES_IMAGE_ROLE = {m: 'evidence' for m in (
    'figure',)}
_MODULES_IMAGE_ROLE.update({m: 'illustrative' for m in (
    'definition', 'case_block', 'stat_card', 'checklist', 'authority_card')})

MODULES = {}
for _m in dispatch_map:
    MODULES[_m] = {
        'tier': _MODULES_TIER_EXPLICIT.get(
            _m, 'optional' if _m in OPTIONAL_MODULES else 'classic'),
        'image_role_default': _MODULES_IMAGE_ROLE.get(_m, None),
        # C1: referencias a las estructuras canónicas (migración de ENTRADAS
        # completa en release posterior; aquí consolidamos el acceso).
        'schema': B.get(_m, {}),
        'required_nonempty': REQUIRED_NONEMPTY.get(_m, []),
        'fit_rule': FIT_RULES.get(_m),
        'gotcha': MODULE_GOTCHAS.get(_m),
    }
del _m, _MODULES_TIER_EXPLICIT

def modules_of_tier(tier):
    """Vista derivada: nombres de módulo por tier ('core'|'optional'|'classic')."""
    return [m for m in dispatch_map if MODULES[m]['tier'] == tier]

assert set(CORE_MODULES) == set(modules_of_tier('core')), 'tier core desincronizado'
assert set(OPTIONAL_MODULES) == set(modules_of_tier('optional')), \
    'tier optional desincronizado'
# C1 — integridad del registro: schema y required_nonempty cubren 35/35
assert all(MODULES[m]['schema'] for m in MODULES), 'hay módulos sin schema en B'
assert all(isinstance(MODULES[m]['required_nonempty'], tuple) or
           isinstance(MODULES[m]['required_nonempty'], list)
           for m in MODULES), 'REQUIRED_NONEMPTY incompleto'

# v9.D — derivados del registro (módulos que soportan imagen = con rol declarado)
IMG_MODS = tuple(m for m in dispatch_map if MODULES[m]['image_role_default'])

_PLACE = '<= {} car.>'

def _skel_field(lim):
    return _PLACE.format(lim)

def _module_skeleton(m):
    """Paste-ready minimal dict that satisfies the contract for module m.
    v9.6/C3: consume MODULES (no B directo) — el registro es la única vía."""
    spec = MODULES[m]['schema']
    d = {'module': m}
    if m not in _NO_HEADER_MODULES:
        d['kicker'] = _skel_field(COMMON['kicker'])
        d['title'] = _skel_field(COMMON['title'])
    for k, v in spec.items():
        if k.startswith('_'):
            continue
        d[k] = _skel_field(v) if isinstance(v, int) else v
    if m in ('figure', 'authority_card') or 'image' in MODULES[m]['required_nonempty']:
        d['image'] = 'work/imgs/nombre_snake_case.jpg'
    if '_list' in spec:
        key, lo, hi, fl = spec['_list']
        d[key] = [{fk: _skel_field(fv) for fk, fv in fl.items()} for _ in range(lo)]
        if '_examples' in spec:
            mx, lim = spec['_examples']
            for it in d[key]:
                it['examples'] = [_skel_field(lim)] * min(mx, 2)
    if '_strlist' in spec:
        key, lo, hi, lim = spec['_strlist']
        d[key] = [_skel_field(lim)] * lo
    if '_table' in spec:
        key, rlo, rhi, clo, chi, lim = spec['_table']
        d['headers'] = [_skel_field(lim)] * clo
        d['col_widths'] = [2.0] * clo
        d[key] = [[_skel_field(lim)] * clo for _ in range(rlo)]
    # v9.B/F7: _cards y _debate comparten forma
    for spec_key, sides in (('_cards', ('left_card', 'right_card')),
                            ('_debate', ('pro_card', 'con_card'))):
        if spec_key in spec:
            fl, plo, phi, plim = spec[spec_key]
            for side in sides:
                d[side] = {fk: _skel_field(fv) for fk, fv in fl.items()}
                d[side]['points'] = [_skel_field(plim)] * plo
    if '_quads' in spec:
        tlim, plo, phi, plim = spec['_quads']
        d['quadrants'] = [{'title': _skel_field(tlim),
                           'points': [_skel_field(plim)] * plo} for _ in range(4)]
    if '_venn' in spec:
        flab, slo, shi, ilim, hlo, hhi, hlim = spec['_venn']
        d['sets'] = [{'label': _skel_field(flab), 'items': [_skel_field(ilim)] * slo}
                     for _ in range(2)]
        d['shared'] = [_skel_field(hlim)] * hlo
    if '_chart' in spec:
        clo, chi, snlo, snhi, snlim, inlo, inhi, inlim, catlim = spec['_chart']
        d['chart_type'] = 'bar'
        d['categories'] = [_skel_field(catlim)] * clo
        d['series'] = [{'name': _skel_field(snlim), 'values': [0.0] * clo} for _ in range(snlo)]
        d['insights'] = [_skel_field(inlim)] * inlo
    if '_acronym' in spec:
        key, lim = spec['_acronym']
        d['acronym'] = 'ABC'
        d[key] = [_skel_field(lim)] * 3
    if '_objectives' in spec:
        lo, hi, vlim, tlim = spec['_objectives']
        d['objectives'] = [{'verb': _skel_field(vlim), 'text': _skel_field(tlim),
                            'bloom': 'understand'} for _ in range(lo)]
    if '_colloquy' in spec:
        lo, hi, tlim = spec['_colloquy']
        d['turns'] = [{'speaker': 'tutor' if i % 2 == 0 else 'student',
                       'text': _skel_field(tlim)} for i in range(lo)]
    if '_highlight' in spec:
        key, lo, hi = spec['_highlight']
        if lo >= 1 and isinstance(d.get(key), list) and d[key]:
            d[key][0]['highlight'] = True
    if m == 'etymology':
        d['term'] = 'Apendicitis'
        d['fragments'] = ['Apendic', 'itis']
    if m not in _NO_HEADER_MODULES:
        d.setdefault('footnote', _skel_field(COMMON['footnote']))
    return d

def _fmt_constraints(m):
    spec = MODULES[m]['schema']  # v9.6/C3: vía única de acceso
    out = []
    spec_m = MODULES[m]
    req = spec_m['required_nonempty']
    if req:
        out.append(f'  obligatorios (no vacíos): {", ".join(req)}')
    for k, v in spec.items():
        if not k.startswith('_'):
            out.append(f'  {k}: máx {v} car.')
    if m not in _NO_HEADER_MODULES:
        out.append(f'  kicker: máx {COMMON["kicker"]} car. · title: máx {COMMON["title"]} car. '
                   f'· footnote: máx {COMMON["footnote"]} car. (opcional)')
    if '_list' in spec:
        key, lo, hi, fl = spec['_list']
        flds = ' · '.join(f'{a}: máx {b}' for a, b in fl.items())
        out.append(f'  {key}: lista de {lo}-{hi} dicts [{flds}]')
    if '_desc_by_count' in spec:
        key, table = spec['_desc_by_count']
        out.append(f'  {key}.desc: el límite varía con el número de ítems -> ' +
                   ', '.join(f'{n} ítems = {lim} car.' for n, lim in table.items()))
    if '_strlist' in spec:
        key, lo, hi, lim = spec['_strlist']
        out.append(f'  {key}: lista de {lo}-{hi} strings, máx {lim} car. c/u')
    if '_table' in spec:
        key, rlo, rhi, clo, chi, lim = spec['_table']
        out.append(f'  headers: {clo}-{chi} columnas · {key}: {rlo}-{rhi} filas x '
                   f'len(headers) celdas, máx {lim} car. c/u · col_widths: '
                   f'un peso numérico > 0 por encabezado')
    # v9.B/F7: _cards y _debate comparten forma
    for spec_key, sides in (('_cards', ('left_card', 'right_card')),
                            ('_debate', ('pro_card', 'con_card'))):
        if spec_key in spec:
            fl, plo, phi, plim = spec[spec_key]
            out.append(f'  {" / ".join(sides)}: {" · ".join(f"{a}: máx {b}" for a, b in fl.items())}'
                       f' + points: {plo}-{phi} strings de máx {plim} car.')
    if '_quads' in spec:
        tlim, plo, phi, plim = spec['_quads']
        out.append(f'  quadrants: EXACTAMENTE 4 dicts [title: máx {tlim}] + points: '
                   f'{plo}-{phi} strings de máx {plim} car.')
    if '_venn' in spec:
        flab, slo, shi, ilim, hlo, hhi, hlim = spec['_venn']
        out.append(f'  sets: 2-3 dicts [label: máx {flab}, items: {slo}-{shi} de máx {ilim}] · '
                   f'shared: {hlo}-{hhi} strings de máx {hlim}')
    if '_chart' in spec:
        clo, chi, snlo, snhi, snlim, inlo, inhi, inlim, catlim = spec['_chart']
        out.append(f'  categories: {clo}-{chi} (máx {catlim} car.) · series: {snlo}-{snhi} '
                   f'[name máx {snlim}, values numéricos = len(categories)] · '
                   f'insights: {inlo}-{inhi} de máx {inlim}')
    if '_acronym' in spec:
        key, lim = spec['_acronym']
        out.append(f'  {key}: un término (máx {lim} car.) POR CADA letra de acronym')
    if '_examples' in spec:
        mx, lim = spec['_examples']
        out.append(f'  categories[].examples: máx {mx} strings de máx {lim} car.')
    if '_highlight' in spec:
        key, lo, hi = spec['_highlight']
        out.append(f'  {key}[].highlight: entre {lo} y {hi} ítems con highlight=True')
    if '_decision_flow' in spec:
        mx, dlim = spec['_decision_flow']
        out.append(f'  steps[].decision: máx {mx} decisiones; desc de un paso decision = '
                   f'etiqueta de rama NO (máx {dlim} car.); incompatible con explanation')
    if '_objectives' in spec:
        lo, hi, vlim, tlim = spec['_objectives']
        out.append(f'  objectives: {lo}-{hi} dicts [verb: máx {vlim}, text: máx {tlim}, '
                   f'bloom: {"|".join(_BLOOM_VERBS)}]')
    if '_colloquy' in spec:
        lo, hi, tlim = spec['_colloquy']
        out.append(f'  turns: {lo}-{hi} dicts [speaker: tutor|student, text: máx {tlim}]')
    fit = spec_m['fit_rule']
    if fit:
        try:
            flds = fit({})
            out.append('  ajuste tipográfico verificado (desborde bloquea el build): ' +
                       ', '.join(f'{f} en caja {w}x{h} in @ {p} pt' for f, w, h, p in flds))
        except Exception:
            pass
    if MODULES[m]['gotcha']:
        out.append(f'  AVISO: {spec_m["gotcha"]}')
    return '\n'.join(out)

def cmd_schema(module=None):
    """Publish the authoring contract: fields, cardinalities, budgets, skeleton, tokens."""
    if module in (None, 'all', '--all'):
        print(f'{KIT_VERSION} — contrato de autoría')
        print(f'\nMódulos núcleo (obligatorios en todo deck): {", ".join(CORE_MODULES)}')
        print(f'Variedad mínima: {MIN_DISTINCT} módulos distintos '
              f'({MIN_DISTINCT_FULL} si el deck tiene >= {FULL_DECK_THRESHOLD} diapositivas)')
        print('Perfiles (CONFIG["PROFILE"]): ' + ' · '.join(
            f'{k}: {v["slides"][0]}-{v["slides"][1]} slides, >={v["distinct"]} módulos, '
            f'{v["figures"][0]}-{v["figures"][1]} figuras' for k, v in PROFILES.items()))
        print(f'Figuras: máx 10 diapositivas con imagen · jpg/jpeg/png · 20 KB-4 MB · >= 300 px')
        print(f'Comunes a todo módulo: kicker <= {COMMON["kicker"]} · title <= {COMMON["title"]} '
              f'· footnote <= {COMMON["footnote"]}')
        print('\nTokens de contraste por tema (texto; los hex de marca quedan para gráfica):')
        hdr = f'  {"tema":<10}{"on_primary":<12}{"on_prm_soft":<12}{"on_accent":<11}{"ink_accent":<11}{"ink_success":<12}{"subtitle":<9}'
        print(hdr)
        for key, P in PALETTES.items():
            t = derive_tokens(key, P)
            print(f'  {key:<10}{t["on_primary"]:<12}{t["on_primary_soft"]:<12}'
                  f'{t["on_accent"]:<11}{t["ink_accent"]:<11}{t["ink_success"]:<12}'
                  f'{t["subtitle_on_primary"]:<9}')
        print('  Override fino: PALETTE_OVERRIDES = {<tema>: {<token>: "RRGGBB"}} en el kit.')
        print('\nREGLAS DE ESTRUCTURA DEL LEDGER (work/atu_ledger.md):')
        print('  · UNA sección `##` por cada section_divider del manifest, en el mismo orden.')
        print('  · refs por #ancla (columna Slide); cada ATU debe ser desarrollado por >=1')
        print('    slide con "atu": N; source_quote verbatim en columna 4 (recomendado).')
        print('\nMódulos disponibles ({}):'.format(len(dispatch_map)))
        for name in sorted(dispatch_map):
            tag = 'núcleo   ' if name in CORE_MODULES else ('opcional ' if name in OPTIONAL_MODULES else 'clásico  ')
            print(f'  [{tag}] {name}')
        print('\nUso: python3 uploads/omc_kit.py schema <módulo>   # contrato + esqueleto pegable')
        return 0
    if module not in dispatch_map:
        import difflib
        near = difflib.get_close_matches(module, list(dispatch_map), n=3)
        print(f"Módulo desconocido: {module!r}" + (f' — ¿quiso decir {", ".join(near)}?' if near else ''))
        print('Ejecute: python3 uploads/omc_kit.py schema   (para el listado completo)')
        return 2
    print(f'{KIT_VERSION} — módulo: {module}')
    print('\nCONTRATO:')
    print(_fmt_constraints(module))
    print('\nESQUELETO (copiar al manifest y sustituir los marcadores):')
    import pprint as _pp
    print(_pp.pformat(_module_skeleton(module), width=98, sort_dicts=False))
    print('\nRecordatorio: los límites son de CARACTERES (con espacios y tildes). '
          'Redacte al 90% del límite para absorber correcciones.')
    return 0

# ---------------------------------------------------------------- imgprep
_IMG_MIN_B, _IMG_MAX_B, _IMG_MIN_PX = 20000, 4000000, 300

def _imgprep_one(path, fix=True):
    """Return (status, message, final_path). Normalizes format/bytes; never upscales fake detail."""
    from PIL import Image
    base, ext = os.path.splitext(path)
    ext_l = ext.lower().lstrip('.')
    try:
        im = Image.open(path)
        # v8.4: decode perezoso — validar cabecera (.size) no requiere decodificar
        # los píxeles; solo se cargan cuando se va a MUTAR la imagen (fix=True).
        if fix:
            im.load()
    except Exception as e:
        return ('FAIL', f'ilegible por Pillow ({e})', path)
    w, h = im.size
    if min(w, h) < _IMG_MIN_PX:
        return ('FAIL', f'{w}x{h} px: lado menor < {_IMG_MIN_PX} px — descarte esta imagen y '
                        f'busque una fuente de mayor resolución (no se hace upscaling sintético)', path)
    out = path
    changed = []
    if ext_l not in ('jpg', 'jpeg', 'png'):
        if not fix:
            return ('FAIL', f'formato .{ext_l} no admitido (use jpg/png)', path)
        out = base + '.png'
        im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB').save(out, 'PNG', optimize=True)
        changed.append(f'.{ext_l} -> .png')
        try:
            os.remove(path)
        except OSError:
            pass
    size = os.path.getsize(out)
    if size > _IMG_MAX_B:
        if not fix:
            return ('FAIL', f'{size} B > 4 MB', out)
        im2 = Image.open(out)
        im2 = im2.convert('RGB')
        q, scale = 88, 1.0
        target = base + '.jpg'
        while True:
            tmp = im2 if scale == 1.0 else im2.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            tmp.save(target, 'JPEG', quality=q, optimize=True)
            if os.path.getsize(target) <= _IMG_MAX_B or (q <= 60 and scale <= 0.5):
                break
            q -= 8
            if q < 60:
                q, scale = 82, scale * 0.8
        if target != out and os.path.exists(out):
            os.remove(out)
        out = target
        changed.append(f'recomprimida a {os.path.getsize(out)} B')
        size = os.path.getsize(out)
    if size < _IMG_MIN_B:
        if not fix:
            return ('FAIL', f'{size} B < 20 KB', out)
        im3 = Image.open(out)
        png = base + '.png'
        im3.save(png, 'PNG', optimize=False)
        if os.path.getsize(png) >= _IMG_MIN_B:
            if png != out and os.path.exists(out):
                os.remove(out)
            out = png
            changed.append(f'reescrita como PNG sin pérdida ({os.path.getsize(out)} B)')
        else:
            return ('FAIL', f'{size} B < 20 KB incluso en PNG — imagen demasiado pobre, sustitúyala', out)
    # v9.1/A7: una sola reapertura para el mensaje final (antes 2×).
    with Image.open(out) as _im_final:
        w_f, h_f = _im_final.size
    return ('OK', (', '.join(changed) if changed else 'cumple el contrato') +
            f' · {w_f}x{h_f} px · {os.path.getsize(out)} B', out)

def cmd_imgprep(target='work/imgs', fix=True, as_json=False):
    """Validate/normalize the visual pool BEFORE authoring figure slides."""
    if not _module_available('PIL'):
        print('[OMC Imgprep] FAIL — Pillow ausente. Ejecute preflight.')
        return 1
    files = []
    if os.path.isdir(target):
        for f in sorted(os.listdir(target)):
            fp = os.path.join(target, f)
            if os.path.isfile(fp) and not f.startswith('.'):
                files.append(fp)
    elif os.path.isfile(target):
        files = [target]
    else:
        print(f'[OMC Imgprep] FAIL — ruta no encontrada: {target}')
        return 1
    if not files:
        print(f'[OMC Imgprep] Sin imágenes en {target}.')
        return 0
    bad = 0
    _results = []
    print(f'[OMC Imgprep] {len(files)} archivo(s) en {target} '
          f'(contrato: jpg/png · 20 KB-4 MB · >= {_IMG_MIN_PX} px)')
    for fp in files:
        st, msg, out = _imgprep_one(fp, fix=fix)
        if st != 'OK':
            bad += 1
        _results.append({'file': os.path.basename(fp), 'status': st, 'message': msg})
        name = os.path.basename(out)
        if name != os.path.basename(fp):
            name = f'{os.path.basename(fp)} -> {name}'
        print(f'  [{st}] {name}: {msg}')
    if as_json:
        print(_json.dumps({'kit': KIT_VERSION, 'command': 'imgprep',
                           'status': 'PASS' if not bad else 'FAIL',
                           'error_count': bad, 'files': _results}, ensure_ascii=False))
    if bad:
        print(f'[OMC Imgprep] {bad} imagen(es) NO utilizable(s): sustitúyalas antes del lint.')
        return 1
    print('[OMC Imgprep] PASS — todas las imágenes cumplen el contrato del linter.')
    return 0

# ===================== v9.4/D4 — IMGGEN (placeholders honestos) =====================
_IMGGEN_KINDS = ('flujo', 'piramide', 'venn', 'ciclo', 'barras', 'abstracto')

def _imggen_draw(kind, dr, W, H, colors):
    """Dibuja un esquema content-aware según el tipo pedido (determinista)."""
    from PIL import Image as _Img, ImageDraw as _IDraw
    prim, acc, soft, hi = colors
    if kind == 'flujo':
        # 4 cajas conectadas por flechas
        bw, bh, y0 = 280, 180, H // 2 - 90
        for i in range(4):
            x0 = 120 + i * 360
            dr.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=24,
                                 fill=soft, outline=prim, width=8)
            dr.rectangle([x0, y0 - 14, x0 + bw, y0], fill=acc)
            if i < 3:
                ax = x0 + bw + 10
                dr.polygon([(ax, y0 + bh//2 - 30), (ax + 50, y0 + bh//2),
                            (ax, y0 + bh//2 + 30)], fill=acc)
                dr.rectangle([ax - 40, y0 + bh//2 - 12, ax + 6, y0 + bh//2 + 12], fill=acc)
    elif kind == 'piramide':
        # 4 niveles apilados centrados
        for i in range(4):
            w_top = 300 + i * 260
            y0 = 150 + i * 230
            x0 = (W - w_top) // 2
            fill = [soft, hi, prim, acc][i]
            ol = prim if i != 3 else prim
            dr.polygon([(x0 + 60, y0 + 190), (x0 + w_top - 60, y0 + 190),
                        (x0 + w_top, y0), (x0, y0)], fill=fill, outline=ol)
    elif kind == 'venn':
        # 2-3 círculos translúcidos superpuestos
        r = 330
        cy = H // 2
        for cx, col in ((W//2 - 160, prim), (W//2 + 160, acc)):
            ov = _Img.new('RGBA', (W, H), (0, 0, 0, 0))
            od = _IDraw.Draw(ov)
            od.ellipse([cx - r, cy - r, cx + r, cy + r],
                       fill=tuple(int(col[j:j+2], 16) for j in (1, 3, 5)) + (110,),
                       outline=col, width=8)
            dr._image.paste(ov, (0, 0), ov)
    elif kind == 'ciclo':
        # 4 nodos en círculo con flechas de cuerda
        import math as _m
        cx, cy, R = W // 2, H // 2, 360
        pts = [(cx + R * _m.cos(_m.radians(-90 + i * 90)),
                cy + R * _m.sin(_m.radians(-90 + i * 90))) for i in range(4)]
        for j, (px, py) in enumerate(pts):
            qx, qy = pts[(j + 1) % 4]
            mx, my = (px + qx) / 2, (py + qy) / 2
            dr.line([px, py, qx, qy], fill=soft, width=16)
            ang = _m.atan2(qy - py, qx - px)
            ah = 42
            dr.polygon([(mx + ah * _m.cos(ang), my + ah * _m.sin(ang)),
                        (mx + ah * _m.cos(ang + 2.5), my + ah * _m.sin(ang + 2.5)),
                        (mx + ah * _m.cos(ang - 2.5), my + ah * _m.sin(ang - 2.5))], fill=acc)
        for j, (px, py) in enumerate(pts):
            dr.ellipse([px - 95, py - 95, px + 95, py + 95],
                       fill=prim if j % 2 == 0 else acc)
    elif kind == 'barras':
        # gráfico de barras con eje
        vals = [0.45, 0.75, 0.55, 0.9, 0.65]
        x0, y_base, bw = 200, H - 220, 170
        dr.line([x0 - 60, 140, x0 - 60, y_base], fill=prim, width=8)
        dr.line([x0 - 60, y_base, x0 + len(vals) * 250, y_base], fill=prim, width=8)
        for i, v in enumerate(vals):
            bx = x0 + i * 250
            bh = int((y_base - 180) * v)
            dr.rectangle([bx, y_base - bh, bx + bw, y_base],
                         fill=prim if i % 2 == 0 else acc)
    else:  # abstracto (retrocompatible)
        for b in range(5):
            y_0 = 80 + b * 220
            dr.rectangle([100 + b * 60, y_0, 1500 - b * 40, y_0 + 140],
                         fill=colors[b % len(colors)])
        for c_ in range(6):
            cx_, cy_ = 250 + c_ * 230, 300 + (c_ % 3) * 280
            r = 90 + (c_ * 37) % 60
            dr.ellipse([cx_ - r, cy_ - r, cx_ + r, cy_ + r],
                       outline=colors[(c_ + 2) % len(colors)], width=14)

def cmd_imggen(count=1, out_dir='work/imgs', palette='ucp', kind='esquema'):
    """Genera placeholders Pillow content-aware según `kind`, con la paleta elegida,
    >=300 px y dentro del contrato de bytes. HONESTIDAD: se marcan para usar con
    image_role='illustrative' (un esquema decorativo no es evidencia).
    kinds: flujo | piramide | venn | ciclo | barras | abstracto"""
    from PIL import Image, ImageDraw
    if palette not in PALETTES:
        print(f'[OMC Imggen] FAIL — paleta {palette!r} no válida ({", ".join(PALETTES)})')
        return 2
    if kind == 'esquema':
        kind = 'abstracto'  # retrocompat nombre v9.5
    if kind not in _IMGGEN_KINDS:
        print(f'[OMC Imggen] FAIL — kind {kind!r} no válido ({", ".join(_IMGGEN_KINDS)})')
        return 2
    P = PALETTES[palette]
    os.makedirs(out_dir, exist_ok=True)
    made = []
    colors = ['#' + P['primary'], '#' + P['accent'], '#' + P['soft'],
              '#' + P['highlight']]
    kdraw = 'abstracto' if kind == 'esquema' else kind  # retrocompat kind viejo
    for i in range(1, count + 1):
        im = Image.new('RGB', (1600, 1200), '#' + P['bg'])
        dr = ImageDraw.Draw(im)
        dr._image = im  # para composición RGBA (venn)
        _imggen_draw(kdraw, dr, 1600, 1200, colors)
        path = os.path.join(out_dir, f'placeholder_{kdraw}_{palette}_{i:02d}.jpg')
        q = 88
        while True:
            im.save(path, 'JPEG', quality=q, optimize=True)
            sz = os.path.getsize(path)
            if _IMG_MIN_B <= sz <= _IMG_MAX_B or q <= 40:
                break
            q -= 8
        st, msg, _out = _imgprep_one(path, fix=False)
        if st != 'OK':
            print(f'[OMC Imggen] AVISO — {os.path.basename(path)} no cumple el contrato: {msg}')
        made.append(path)
    print(f'[OMC Imggen] {len(made)} placeholder(s) generados en {out_dir} '
          f'(paleta {palette}).')
    print('[OMC Imggen] ÚSELOS con image_role="illustrative" — un esquema generado '
          'no es evidencia; reemplácelos por figuras reales cuando existan.')
    return 0

# ===================== v9.4/D1 — INGEST (source -> outline + ledger stub) =====================
# Filosofía: el motor EXTRAE y ESTRUCTURA, nunca inventa contenido. La autoría de
# ATUs y del manifest sigue siendo del agente/autor; ingest solo elimina la
# transcripción manual y garantiza source_quotes verbatim por construcción.

def _extract_source_text(path):
    """Texto plano del source (.pdf vía pypdf; .txt/.md directo)."""
    ext = str(path).lower().rsplit('.', 1)[-1]
    if ext in ('txt', 'md'):
        return open(path, encoding='utf-8', errors='replace').read()
    if ext == 'pdf':
        try:
            from pypdf import PdfReader
        except ImportError:
            raise SystemExit('[OMC Ingest] FAIL — falta pypdf: uv pip install pypdf')
        reader = PdfReader(path)
        return '\n'.join((pg.extract_text() or '') for pg in reader.pages)
    raise SystemExit(f'[OMC Ingest] FAIL — formato .{ext} no soportado (pdf/txt/md)')

def _ingest_outline(text):
    """[(kind, content)] — 'heading' para líneas-título cortas numeradas o en Title Case,
    'para' para el resto. Heurística simple, determinista, sin IA."""
    outline = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        is_heading = (
            # v9.E/H1: excluir números con 3 decimales-de-miles (2.345 pacientes…)
            _re.match(r'^\d{1,2}(\.\d{1,3})*[\.)]?\s+\S', line) is not None
            and not _re.match(r'^\d{1,2}\.\d{3}\s', line)
            and len(line) <= 80
            and not line.rstrip().endswith('.')
        ) or (line.istitle() and 3 <= len(line.split()) <= 10
              and not line.rstrip().endswith('.'))
        outline.append(('heading' if is_heading else 'para', line))
    return outline

def _split_sentences(para_text):
    return [s.strip() for s in _re.split(r'(?<=[\.\!\?])\s+', para_text) if len(s.strip()) >= 25]

def _best_quote_for(claim_tokens, paragraphs):
    """v9.5.1/F2 — devuelve la mejor ORACIÓN del párrafo con mayor solape (no el
    párrafo entero): citas dentro del límite de 160 car. del ledger, verbatim.
    Si ninguna oración alcanza solape, cae al párrafo completo si supera el umbral."""
    ct = _salient_tokens(claim_tokens)
    best_sent, best_sent_ov = None, 0.0
    best_para, best_para_ov = None, 0.0
    for para in paragraphs:
        pt = _salient_tokens(para)
        if not pt:
            continue
        ov_para = len(ct & pt) / max(len(pt), 1)
        if ov_para > best_para_ov:
            best_para, best_para_ov = para, ov_para
        for sent in _split_sentences(para):
            st = _salient_tokens(sent)
            if not st:
                continue
            # solape sobre tokens de la ORACIÓN: ¿cuánto de la oración cubre el claim?
            ov = len(ct & st) / max(len(st), 1)
            if ov > best_sent_ov and len(sent) <= 160:
                best_sent, best_sent_ov = sent, ov
    if best_sent_ov >= 0.5:
        return best_sent
    return best_para if best_para_ov >= 0.2 else None

def cmd_ingest(source_path, out_dir='work', as_json=False):
    """v9.4/D1 — extrae texto del source y produce:
    - work/ingest_outline.md   (secciones + párrafos detectados)
    - work/atu_ledger_stub.md  (esqueleto de ledger con citas verbatim candidatas)
    El agente autorea ATU/manifest desde aquí; `all` verifica.

    Comportamiento del matching de citas (documentado v9.E):
    · la cita devuelta es el PÁRRAFO contenedor completo, no la oración suelta
      (puede exceder 160 car.: el autor recorta dentro del párrafo citado);
    · claims muy cortos o sin solape >=20% quedan SIN cita (<cita no hallada>)
      por diseño — mejor ninguna que una débil;
    · la cita SIEMPRE es texto verbatim del source, jamás reescrita."""
    import os as _os
    if not _os.path.exists(source_path):
        print(f'[OMC Ingest] FAIL — source no encontrado: {source_path}')
        return 1
    text = _extract_source_text(source_path)
    outline = _ingest_outline(text)
    paras = [c for k, c in outline if k == 'para']
    # idioma declarado sugerido por huella estadística (tripwire ya existente)
    scores, ntok = _lang_scores(_iter_strings(paras))
    win, ranked, margin = _lang_verdict(scores, ntok, MIN_DECK_TOKENS)
    _os.makedirs(out_dir, exist_ok=True)

    L = [f'# OUTLINE — {source_path}', '',
         f'Idioma detectado: {win or "indeterminado"} '
         f'(margen {margin:.2f}; tokens {ntok})', '']
    section = '<sin sección>'
    sections_seen = {}
    for kind, content in outline:
        if kind == 'heading':
            section = content
            sections_seen.setdefault(section, [])
            L.append(f'\n## {section}')
        else:
            sections_seen.setdefault(section, []).append(content)
            L.append(f'- {content}')
    open(_os.path.join(out_dir, 'ingest_outline.md'), 'w',
         encoding='utf-8').write('\n'.join(L) + '\n')

    S = ['# LEDGER STUB (de ingest) — complete Aseveración y ajuste Slide', '',
         f'Source: {source_path} · Idioma detectado: {win or "?"}', '',
         '| ATU | Aseveración | Slide | Source quote |', '|---|---|---|---|']
    atu_n = 0
    for sec, ps in sections_seen.items():
        sents = []
        for para in ps:
            sents.extend(_split_sentences(para))
        if not sents:
            continue
        S.append(f'\n## {sec}\n')
        for sent in sents[:12]:  # v9.5.1/F2: más candidatos (el autor filtra)
            atu_n += 1
            q = _best_quote_for(sent, paras)
            qtxt = f'"{q}"' if q else '<cita no hallada — redactar del source>'
            S.append(f'| {atu_n} | <aseveración a partir de>: {sent[:90]}... | #ancla | {qtxt} |')
    stub_path = _os.path.join(out_dir, 'atu_ledger_stub.md')
    open(stub_path, 'w', encoding='utf-8').write('\n'.join(S) + '\n')

    print(f'[OMC Ingest] OK — {len(outline)} bloques ({len(paras)} párrafos), '
          f'{len(sections_seen)} secciones, {atu_n} ATU candidatos.')
    print(f'[OMC Ingest] Outline: {out_dir}/ingest_outline.md')
    print(f'[OMC Ingest] Ledger stub: {stub_path}')
    print(f'[OMC Ingest] Idioma detectado: {win or "indeterminado"} (margen {margin:.2f})')
    if as_json:
        print(_json.dumps({'kit': KIT_VERSION, 'command': 'ingest',
                           'status': 'PASS', 'source': source_path,
                           'lang_detected': win, 'margin': round(margin, 2),
                           'blocks': len(outline), 'paragraphs': len(paras),
                           'sections': len(sections_seen), 'atu_candidates': atu_n,
                           'outline_path': f'{out_dir}/ingest_outline.md',
                           'stub_path': stub_path}, ensure_ascii=False))
    # v9.4/D3 — pre-scan de drift sobre el SOURCE: un source rico en otro idioma
    # explica desvíos futuros; avisar ANTES de autoría, no después del build.
    if win and win != 'en-US':
        drift_src = []
        for para in paras:
            drift_src.extend(_drift_hits(para, win))
        if drift_src:
            print(f'[OMC Ingest] AVISO — el source contiene señales de otros idiomas '
                  f'({len(drift_src)}):')
            seen = set()
            for w, fix in drift_src:
                if w not in seen:
                    seen.add(w)
                    print(f'    · {w!r} -> {fix}')
            print('[OMC Ingest] Si el source es multilingüe por diseño, considere '
                  'DRIFT_CHAR_EXCEPTIONS/WORD_EXCEPTIONS en el kit.')
    return 0

# v9.4/D2 — make: pipeline completo en un comando. El AGENTE autorea entre
# ingest y all; make NO fabrica contenido (invariante anti-fabricación).
def cmd_make(source_path, out='deck.pptx', profile='lecture', pal_key=None,
             lang=None, skip_ingest=False):
    print(f'[OMC Make] 1/4 — Ingest de {source_path}')
    if not skip_ingest:
        rc = cmd_ingest(source_path)
        if rc != 0:
            return rc
    # sugerencia de idioma desde la huella del source
    detected = None
    try:
        text = _extract_source_text(source_path)
        paras = [c.strip() for k, c in _ingest_outline(text) if k == 'para']
        scores, ntok = _lang_scores(_iter_strings(paras))
        detected, _ranked, margin = _lang_verdict(scores, ntok, MIN_DECK_TOKENS)
    except Exception:
        pass
    manifest_path = 'manifest.py'
    print(f'[OMC Make] 2/4 — Scaffold {manifest_path} '
          f'(perfil {profile}' + (f', idioma sugerido {detected}' if detected else '') + ')')
    if os.path.exists(manifest_path):
        print(f'[OMC Make] manifest.py ya existe — se conserva (autoría en curso).')
    else:
        rc = cmd_new(profile, manifest_path, pal_key=pal_key)
        if rc != 0:
            return rc
    # v9.E/H2: el stub de ingest (con citas verbatim) REEMPLAZA al ledger genérico
    # de cmd_new — un solo ledger real, sin riesgo de editar el equivocado.
    stub = os.path.join('work', 'atu_ledger_stub.md')
    real = os.path.join('work', 'atu_ledger.md')
    if os.path.exists(stub) and os.path.exists(real):
        import shutil
        shutil.copy(stub, real)
        print('[OMC Make] work/atu_ledger.md reemplazado por el stub de ingest '
              '(citas verbatim). Edite ESE archivo.')
    print('[OMC Make] 3/4 — AUTORÍA REQUERIDA:')
    print('  · complete ATUs y source quotes desde work/atu_ledger_stub.md')
    print(f'  · edite {manifest_path} (contenido real, no marcadores)')
    if detected and detected != 'en-US':
        print(f'  · fije CONFIG["LANG"] = "{detected}"')
    print('  · luego re-ejecute: make ' + source_path + ' ' + out + ' --continue')
    print('[OMC Make] 4/4 — verificación diferida hasta que el manifest esté autorado.')
    return 2  # 2 = "listo para autoría" (no es error)

def _make_continue(out='deck.pptx'):
    """Fase de verificación de make sobre un manifest ya autorado."""
    print('[OMC Make] 4/4 — lint -> build -> audit sobre el manifest actual...')
    if not os.path.exists('manifest.py'):
        print('[OMC Make] FAIL — manifest.py no existe. Ejecute primero '
              'make <source> (fase de autoría).')
        return 1
    rc = cmd_all('manifest.py', out)
    if rc != 0:
        print('[OMC Make] El manifest aún viola el contrato — corrija y re-ejecute '
              'make --continue.')
    else:
        print(f'[OMC Make] LISTO — {out} verificado (lint+build+audit+contraste).')
    return rc

# ===================== JSON LINT & SCAFFOLDING =====================
_ERR_RE = _re.compile(r'^slide (\d+) \[(\w+)\](?:\.([^:]+))?: (.*)$', _re.S)

def errs_to_json(errs, slides=None, profile=None, lang='es-ES'):
    """Machine-readable lint report for self-correcting agents."""
    items = []
    for e in errs:
        m = _ERR_RE.match(e)
        if m:
            items.append({'scope': 'slide', 'slide': int(m.group(1)), 'module': m.group(2),
                          'field': (m.group(3) or '').strip() or None, 'message': m.group(4).strip(),
                          'raw': e})
        else:
            head = e.split(':', 1)[0].strip()
            items.append({'scope': 'ledger' if head.startswith('ledger') else 'deck',
                          'slide': None, 'module': None, 'field': None,
                          'message': e.split(':', 1)[-1].strip(), 'raw': e})
    by_slide = {}
    for it in items:
        if it['slide']:
            by_slide[it['slide']] = by_slide.get(it['slide'], 0) + 1
    return {'kit': KIT_VERSION, 'status': 'PASS' if not errs else 'FAIL',
            'lang': lang, 'profile': profile,
            'slides': len(slides) if slides is not None else None,
            'error_count': len(errs), 'errors': items,
            'slides_with_errors': sorted(by_slide),
            'hint': 'Corrija sólo los campos listados; ejecute `schema <module>` para el contrato.'}

_SCAFFOLD_PLAN = {
 'lecture': ['title', 'learning_objectives', 'section_divider', 'definition', 'figure',
             'comparison_table', 'flow_diagram', 'taxonomy_tree', 'section_divider',
             'algorithm', 'side_by_side', 'stat_card', 'timeline', 'case_block',
             'viva_question', 'glossary', 'further_reading'],
 'seminar': ['title', 'learning_objectives', 'section_divider', 'definition', 'figure',
             'comparison_table', 'flow_diagram', 'section_divider', 'case_block',
             'checklist', 'glossary', 'further_reading'],
 'short':   ['title', 'section_divider', 'definition', 'figure', 'flow_diagram',
             'comparison_table', 'checklist', 'case_block', 'further_reading'],
 'custom':  ['title', 'section_divider', 'section_divider'],
}

def _anchor_for(module, used):
    base = {'title': 'portada', 'section_divider': 'seccion', 'definition': 'definicion',
            'figure': 'figura', 'case_block': 'caso', 'glossary': 'glosario',
            'further_reading': 'lecturas'}.get(module, module.replace('_', '-'))
    a, k = base, 2
    while a in used:
        a, k = f'{base}-{k}', k + 1
    used.add(a)
    return a

def cmd_new(profile=None, out='manifest.py', lang='es-ES', pal_key=None):
    """Emit a contract-valid scaffold: manifest skeleton + matching ATU ledger."""
    import pprint as _pp
    pname, prof = resolve_profile(None, profile)
    pk = pal_key if pal_key in PALETTES else 'oxford'
    if os.path.exists(out):
        print(f'[OMC New] FAIL — {out} ya existe (no se sobrescribe). Indique otra ruta.')
        return 1
    plan = _SCAFFOLD_PLAN[pname]
    used, lines = set(), []
    lines.append('# -*- coding: utf-8 -*-')
    lines.append(f'"""Scaffold generado por {KIT_VERSION} — perfil {pname} ({prof["desc"]}).')
    lines.append('Sustituya TODOS los marcadores <= N car.>; añada o elimine diapositivas')
    lines.append(f'hasta {prof["slides"][0]}-{prof["slides"][1]} y >= {prof["distinct"]} módulos distintos.')
    lines.append(f'Contrato por módulo: python3 uploads/omc_kit.py schema <módulo>"""')
    lines.append('')
    lines.append("COURSE_INFO = {'course': '<asignatura>', 'institution': '<institución>', 'author': '<autor opcional>'}")
    lines.append(f"CONFIG = {{'PALETTE': '{pk}', 'MODE': 'declarative', 'LANG': '{lang}', "
                 f"'PROFILE': '{pname}', 'SHOW_FOOTER': True, 'SHOW_SLIDE_NUMBER': True}}")
    lines.append('')
    lines.append('SLIDES = [')
    ledger_rows = []
    for i, mod in enumerate(plan, start=1):
        d = _module_skeleton(mod)
        anc = _anchor_for(mod, used)
        d = {'module': d.pop('module'), 'anchor': anc, **d}
        lines.append(f'# ---------------- {i:>2} · {mod}')
        lines.append(_pp.pformat(d, width=96, sort_dicts=False) + ',')
        lines.append('')
        if mod not in _NO_HEADER_MODULES:
            ledger_rows.append((mod, anc))
    lines.append(']')
    open(out, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

    ledger = 'work/atu_ledger.md'
    made_ledger = False
    if not os.path.exists(ledger):
        os.makedirs('work', exist_ok=True)
        n_div = sum(1 for m in plan if m == 'section_divider')
        per = max(1, -(-len(ledger_rows) // max(n_div, 1)))
        L = [f'# LEDGER DE UNIDADES DE ASEVERACIÓN (ATU) — <tema>', '',
             f'Idioma: {lang} · Perfil: {pname} · Referencias por ANCLA (#slug), '
             f'inmunes a la renumeración de diapositivas.', '',
             'REGLA: una sección `##` por cada section_divider del manifest, en el mismo orden.',
             'COLUMNA 4 (opcional, v8.1): source_quote — fragmento verbatim del source que',
             'respalda la aseveración. Activa el chequeo de fidelidad en el audit.',
             'Vincule cada slide con "atu": <N> en el manifest (cobertura bidirecional).',
             '']
        k = 0
        for sec in range(1, max(n_div, 1) + 1):
            L += [f'## Sección {sec} — <título>', '',
                  '| ATU | Aseveración | Slide | Source quote |', '|---|---|---|---|']
            for _ in range(per):
                if k >= len(ledger_rows):
                    break
                mod, anc = ledger_rows[k]; k += 1
                L.append(f'| {k} | <aseveración verificable extraída de la fuente> | #{anc} |')
            L.append('')
        open(ledger, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        made_ledger = True

    print(f'[OMC New] Scaffold escrito: {out} ({len(plan)} diapositivas, perfil {pname})')
    print(f'[OMC New] Ledger: {ledger}' + ('  (creado)' if made_ledger else '  (ya existía, intacto)'))
    print('[OMC New] Siguiente: 1) fijar CONFIG["PALETTE"]="ucp" si procede  2) redactar el ledger  '
          '3) imgprep work/imgs  4) schema <módulo>  5) lint  6) all')
    return 0

def cli():
    argv = sys.argv[1:]
    # Flags globales, independientes de la posición.
    as_json = '--json' in argv
    argv = [x for x in argv if x != '--json']
    force = '--force' in argv
    argv = [x for x in argv if x != '--force']
    profile = None
    if '--profile' in argv:
        i = argv.index('--profile')
        if i + 1 < len(argv):
            profile = argv[i + 1]
            del argv[i:i + 2]
        else:
            print('[OMC CLI] FAIL — --profile requiere un valor (' + ' | '.join(PROFILES) + ').')
            return 2
    a = argv
    if '--help' in a or '-h' in a:
        a = []  # v9.5.1/F1: --help muestra el uso
    if not a:
        print(f"{KIT_VERSION}\n"
              f"Uso:\n"
              f"  preflight [HASH] [--force]       deps + hash + self-test + matriz de contraste\n"
              f"  new [perfil] [manifest.py] [paleta] scaffold de manifest + ledger con anclas\n"
              f"  schema [módulo]                  contrato de autoría + esqueleto + tabla de tokens\n"
              f"  imgprep [ruta]                   valida y normaliza figuras (jpg/png, 20KB-4MB, >=300px)\n"
              f"  ingest <source> [dir]            source pdf/txt/md -> outline + ledger stub con citas verbatim\n"
              f"  imggen [--count N] [--palette P] [--out D]   placeholders ilustrativos (marcar image_role=illustrative)\n"
              f"  make <source> [deck.pptx]        pipeline completo: ingest->new->(autoría)->all\n"
              f"  make --continue                  reanuda make tras la autoría (lint->build->audit)\n"
              f"  lint <manifest.py> [--json]      contrato + ledger (salida legible o JSON)\n"
              f"  build <manifest.py> [out.pptx]   lint fail-fast + render\n"
              f"  audit <manifest.py> <deck.pptx>  completitud + contraste (sección 5 del reporte)\n"
              f"  all <manifest.py> [out.pptx]     lint -> build -> audit(+contraste) en un proceso\n"
              f"  contrast [manifest.py]           gate WCAG: sin argumento = matriz 5 temas;\n"
              f"                                   con manifest = escaneo del deck (--json soportado)\n"
              f"  check                            depuración del motor\n"
              f"Flags globales: --json (lint y contrast) · --profile "
              f"{'|'.join(PROFILES)} (anula CONFIG['PROFILE'])")
        return 0
    c = a[0]
    if c in ('lint', 'build', 'all') and len(a) < 2:
        print(f"[OMC CLI] FAIL — '{c}' requiere la ruta del manifest.")
        return 2
    if c == 'audit' and len(a) < 3:
        print("[OMC CLI] FAIL — 'audit' requiere <manifest.py> <deck.pptx>.")
        return 2
    if c == 'check': return cmd_check()
    if c == 'preflight':
        exp_hash = a[1] if len(a) > 1 and not a[1].startswith('--') else None
        return cmd_preflight(exp_hash, force=force, as_json=as_json)
    if c == 'new': return cmd_new(a[1] if len(a) > 1 else profile,
                                  a[2] if len(a) > 2 else 'manifest.py',
                                  pal_key=a[3] if len(a) > 3 else None)
    if c == 'schema': return cmd_schema(a[1] if len(a) > 1 else None)
    if c == 'imgprep': return cmd_imgprep(a[1] if len(a) > 1 else 'work/imgs', as_json=as_json)
    if c == 'make':
        if len(a) < 2:
            print("[OMC CLI] FAIL — 'make' requiere la ruta del source.")
            return 2
        src = a[1]
        out = a[2] if len(a) > 2 else 'deck.pptx'
        if '--continue' in src or (len(a) > 1 and a[1] == '--continue'):
            return _make_continue(out)
        return cmd_make(src, out, profile=profile)
    if c == 'imggen':
        count = 1
        pal = 'ucp'
        out_dir = 'work/imgs'
        kind_ = 'abstracto'
        i = 1
        while i < len(a):
            if a[i] == '--count' and i + 1 < len(a):
                try: count = max(1, int(a[i+1]))
                except ValueError:
                    print('[OMC CLI] FAIL — --count requiere un entero.')
                    return 2
                i += 2
            elif a[i] == '--palette' and i + 1 < len(a):
                pal = a[i+1]; i += 2
            elif a[i] == '--kind' and i + 1 < len(a):
                kind_ = a[i+1]; i += 2
            elif a[i] == '--out' and i + 1 < len(a):
                out_dir = a[i+1]; i += 2
            else:
                out_dir = a[i]; i += 1
        return cmd_imggen(count, out_dir, pal, kind_)
    if c == 'ingest':
        args_ = [x for x in a[1:] if x != '--json']
        if not args_:
            print("[OMC CLI] FAIL — 'ingest' requiere la ruta del source (pdf/txt/md).")
            return 2
        return cmd_ingest(args_[0], args_[1] if len(args_) > 1 else 'work', as_json=as_json)
    if c == 'lint': return cmd_lint(a[1], as_json=as_json, profile=profile)
    if c == 'build': return cmd_build(a[1], a[2] if len(a) > 2 else 'deck.pptx', profile=profile)
    if c == 'audit': return cmd_audit(a[1], a[2], profile=profile)
    if c == 'all': return cmd_all(a[1], a[2] if len(a) > 2 else 'deck.pptx', profile=profile)
    if c == 'contrast':
        return cmd_contrast(a[1] if len(a) > 1 else None, as_json=as_json, profile=profile)
    print(f"[OMC CLI] FAIL — comando desconocido: {c}")
    return 2

if __name__ == '__main__':
    sys.exit(cli() or 0)