# -*- coding: utf-8 -*-
"""Carga de um manifest Python: COURSE_INFO + CONFIG + SLIDES.

CONFIG ausente nao quebra nada: entra a paleta UCP, o idioma padrao (pt-BR),
el perfil 'short' y la politica de imagenes por defecto (web-only, presupuesto
auto). Una paleta distinta de 'ucp' no rompe el build: se avisa.
"""

import importlib.util
import os

from . import i18n, images
from .palette import load_palette
from .version import VERSION

_PALETTE = 'ucp'


class Deck:
    """Manifesto ya normalizado: lo que el linter y el render necesitan."""

    def __init__(self, path, slides, course_info, config):
        self.path = path
        self.slides = slides
        self.course_info = course_info or {}
        self.config = config or {}
        self.warnings = []

    @property
    def course(self):
        return str(self.course_info.get('course', '') or '')

    @property
    def institution(self):
        return str(self.course_info.get('institution', '') or '')

    @property
    def author(self):
        return str(self.course_info.get('author', '') or '')

    @property
    def lang(self):
        return str(self.config.get('LANG', i18n.DEFAULT_LANG))

    @property
    def profile(self):
        return str(self.config.get('PROFILE', 'short'))

    @property
    def palette_key(self):
        return _PALETTE

    @property
    def palette(self):
        return load_palette(self.palette_key)

    @property
    def images(self):
        return images.ImagePolicy.from_config(self.config)

    @property
    def allow_terms(self):
        return tuple(self.config.get('ALLOW_TERMS', ()) or ())

    @property
    def version(self):
        return VERSION


def load(path):
    """Deck desde la ruta de un manifest; levanta erro claro si falta SLIDES."""
    if not os.path.exists(path):
        raise FileNotFoundError(f'manifest nao encontrado: {path}')
    if not str(path).lower().endswith('.py'):
        raise ValueError(
            f'{path}: StudyDeck lee MANIFESTS Python (.py), no archivos de salida. '
            f'Pase o manifest que gerou o deck.')
    spec = importlib.util.spec_from_file_location('sd_manifest', os.path.abspath(path))
    if spec is None or spec.loader is None:
        raise ValueError(f'{path}: no es un manifest Python legible.')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    slides = getattr(mod, 'SLIDES', None)
    if not isinstance(slides, list) or not slides:
        raise ValueError('SLIDES vazio ou ausente no manifest')
    config = getattr(mod, 'CONFIG', {}) or {}
    deck = Deck(path, slides, getattr(mod, 'COURSE_INFO', {}), config)
    declared = str(config.get('PALETTE', _PALETTE)).lower()
    if declared != _PALETTE:
        deck.warnings.append(
            f'CONFIG["PALETTE"]="{declared}" no existe: StudyDeck v2 e UCP-only. '
            f'Usando {_PALETTE}.')
    return deck