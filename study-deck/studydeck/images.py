# -*- coding: utf-8 -*-
"""Politica de imagenes del deck UCP.

Regla de oro: la imagen APOYA el mensaje, no lo sustituye. Por eso
- `figure` y `authority_card` exigen imagen (la imagen ES el contenido) pero
  exigen pie ANALITICO: que diga que se aprende, no que exista;
- los modulos de apoyo (definition, case_block, stat_card, checklist) la
  aceptan como apoyo opcional y nunca reemplazan el texto;
- el presupuesto `auto` se lee del source (perfil + tamano), con tope duro y
  override explicito del autor.

Esquemas de fuente: ruta local (.jpg/.png), https:// (web), ai: (generativa),
placeholder: (marco reservado). Ningun modulo descarga nada en silencio: la
resolucion es responsabilidad del autor y del pipeline.
"""

import re
import unicodedata

from .palette import BRAND

IMAGE_MODULES = ('figure', 'definition', 'case_block', 'stat_card', 'checklist',
                 'authority_card')
REQUIRED_IMAGE_MODULES = ('figure', 'authority_card')
MODES = ('web-only', 'mixed', 'ai-only', 'none')
HARD_CAP = 10
CAPTION_MIN = 15
CREDIT_MAX = 130
EXTENSIONS = ('.jpg', '.jpeg', '.png')

_PROFILE_BASE = {'short': 2, 'lecture': 4, 'custom': 3}

# Vocabulario de EXISTENCIA: un pie hecho solo de estas palabras describe que hay
# una imagen, no que se ensena con ella.
_GENERIC_WORDS = {
    'imagem', 'imagen', 'imagenes', 'foto', 'fotos', 'diagrama', 'diagramas', 'exemplo',
    'exemplos', 'ejemplo', 'ejemplos', 'tema', 'temas', 'ilustrativa', 'ilustrativo', 'demostrativa', 'generico',
    'picture', 'image', 'images', 'photo', 'photos', 'diagram', 'diagrams',
    'sample', 'example', 'examples', 'topic', 'illustrative', 'generic', 'of',
    'the', 'de', 'do', 'da', 'del', 'sobre', 'para', 'a', 'o',
}

MARKERS = ('ai:', 'placeholder:')


def _plain_words(text):
    norm = unicodedata.normalize('NFKD', str(text).lower())
    return set(re.findall(r'[a-z]{2,}', norm.encode('ascii', 'ignore').decode('ascii')))


def is_generic_caption(caption):
    """True quando o pie nao diz nada ensinavel: so descreve que existe figura."""
    words = _plain_words(caption)
    return bool(words) and words.issubset(_GENERIC_WORDS)


def classify(source):
    """(esquema, valor) de una fuente de imagen: web | local | ai | placeholder."""
    s = str(source or '').strip()
    if not s:
        return ('empty', s)
    low = s.lower()
    if low.startswith('https://'):
        return ('web', s)
    if low.startswith('http://'):
        return ('insecure-web', s)
    if low.startswith('ai:'):
        return ('ai', s[3:].strip())
    if low.startswith('placeholder:'):
        return ('placeholder', s[len('placeholder:'):].strip())
    if '://' in low:
        return ('unsupported', s)
    if low.endswith(EXTENSIONS):
        return ('local', s)
    return ('unsupported', s)


class ImagePolicy:
    """Configurable por manifest y unico juez de las reglas de imagen."""

    def __init__(self, mode='web-only', max_n='auto', allow_ai=False,
                 allow_placeholder=False, cap=HARD_CAP):
        if mode not in MODES:
            raise ValueError(f'modo de imagen desconocido {mode!r}; use uno de {", ".join(MODES)}')
        if max_n != 'auto':
            if isinstance(max_n, bool) or not isinstance(max_n, int):
                raise ValueError(f'max_n debe ser "auto" o un entero, no {max_n!r}')
            if max_n < 0 or max_n > cap:
                raise ValueError(f'max_n={max_n} fuera de rango 0..{cap}')
        self.mode = mode
        self.max_n = max_n
        self.allow_ai = bool(allow_ai)
        self.allow_placeholder = bool(allow_placeholder)
        self.cap = cap

    @classmethod
    def from_config(cls, config):
        cfg = (config or {}).get('IMAGES') or {}
        return cls(mode=cfg.get('mode', 'web-only'),
                   max_n=cfg.get('max_n', 'auto'),
                   allow_ai=cfg.get('allow_ai', False),
                   allow_placeholder=cfg.get('allow_placeholder', False))

    def budget(self, n_slides=0, profile='short'):
        """Presupuesto de imagenes sensible al source; tope duro siempre."""
        if self.max_n != 'auto':
            return self.max_n
        n = max(int(n_slides or 0), 0)
        base = _PROFILE_BASE.get(profile, _PROFILE_BASE['short'])
        extra = max(n - 12, 0) // 6
        return min(base + extra, self.cap)

    def validate(self, slides):
        errs = []
        used = 0
        for i, d in enumerate(slides, 1):
            module = str(d.get('module', ''))
            image = d.get('image')
            if not image:
                if module in REQUIRED_IMAGE_MODULES:
                    errs.append(f'slide {i} [{module}] [IMG_REQUIRED]: modulo exige imagem real')
                continue
            used += 1
            if module not in IMAGE_MODULES:
                errs.append(f'slide {i} [IMG_MODULE_UNSUPPORTED]: modulo {module} no admite imagen '
                            f'(soportan: {", ".join(IMAGE_MODULES)})')
            if self.mode == 'none':
                errs.append(f'slide {i} [IMG_MODE_NONE]: IMAGES.mode="none" prohibio a imagen')
                continue
            scheme, value = classify(image)
            if scheme == 'empty':
                errs.append(f'slide {i} [IMG_SOURCE_EMPTY]: campo image vacio')
            elif scheme == 'insecure-web':
                errs.append(f'slide {i} [IMG_SOURCE_INSECURE]: a fonte web deve ser https, no http')
            elif scheme == 'unsupported':
                errs.append(f'slide {i} [IMG_SOURCE_SCHEME]: fonte de imagen sin esquema soportado: {image!r}')
            elif scheme == 'ai':
                if not self.allow_ai:
                    errs.append(f'slide {i} [IMG_AI_NOT_ALLOWED]: fonte AI exige IMAGES.allow_ai=True')
                elif self.mode in ('web-only',):
                    errs.append(f'slide {i} [IMG_AI_MODE]: modo "web-only" no admite fonte AI')
            elif scheme == 'placeholder':
                if not self.allow_placeholder:
                    errs.append(f'slide {i} [IMG_PLACEHOLDER_NOT_ALLOWED]: placeholder exige IMAGES.allow_placeholder=True')
            elif scheme == 'local':
                if self.mode == 'ai-only':
                    errs.append(f'slide {i} [IMG_LOCAL_MODE]: modo "ai-only" no admite arquivo local')
            caption = str(d.get('caption', '')).strip()
            credit = str(d.get('credit', '')).strip()
            if len(caption) < CAPTION_MIN:
                errs.append(f'slide {i}.caption [IMG_CAPTION_SHORT]: pie analitico obrigatorio con imagen '
                            f'(>={CAPTION_MIN} car.; describe que se ensena, no que existe)')
            elif is_generic_caption(caption):
                errs.append(f'slide {i}.caption [IMG_CAPTION_GENERIC]: pie nao analitico {caption!r} — '
                            f'describa que se aprende de la figura')
            if not credit:
                errs.append(f'slide {i}.credit [IMG_CREDIT_MISSING]: credito obrigatorio con imagen')
            elif len(credit) > CREDIT_MAX:
                errs.append(f'slide {i}.credit [IMG_CREDIT_LONG]: {len(credit)} > {CREDIT_MAX} caracteres')
            if not value and scheme in ('ai', 'placeholder'):
                errs.append(f'slide {i} [IMG_MARKER_EMPTY]: o marcador {image!r} nao diz o que representar')
            if used > self.budget(len(slides), 'custom'):
                errs.append(f'slide {i} [IMG_BUDGET_SLIDE]: imagen {used} sobre o presupuesto '
                            f'{self.budget(len(slides), "custom")} (IMAGES.max_n)')
        limit = self.budget(len(slides), 'custom')
        if used > limit:
            errs.append(f'deck [IMG_BUDGET_DECK]: {used} diapositivas con imagen sobre o presupuesto '
                        f'{limit} (IMAGES.max_n / auto segun source)')
        return errs


def textbook_prompt(subject, lang='pt-BR', role='suporte'):
    """Prompt de diagrama de libro de texto: ensena, no decora."""
    b = BRAND
    return (
        f'Diagrama de livro didatico sobre "{subject}". '
        f'Funcao: {role} a exposicao oral; a figura NAO substitui o texto do slide. '
        f'Estilo UCP: paleta #{b["primary"]} (primaria), #{b["accent"]} (acento), '
        f'#{b["text"]} (tinta), #{b["soft"]} (fundo suave); Montserrat; '
        f'linhas finas, sem degrade, sem gradiente. '
        f"Texto integral da figura em {lang}; rotulos curtos, sem marca d'água, "
        f'sem banco de imagens genérico, sem rosto humano, sem conteudo decorativo. '
        f'Uma mensagem visual unica; se o slide nao pedir duas comparacoes, '
        f'desenhe uma so.'
    )