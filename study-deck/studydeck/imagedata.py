# -*- coding: utf-8 -*-
"""Inspeccion de archivos de imagen: existencia, peso y lado menor.

No descarga nada. `ai:`, `placeholder:` y `https://` se validan por politica
(marcador + credito), no por archivo.
"""

import os

from .images import (
    CAPTION_MIN, CREDIT_MAX, EXTENSIONS, HARD_CAP, ImagePolicy, classify,
)

MIN_BYTES = 20000
MAX_BYTES = 4000000
MIN_PX = 300


def inspect_file(path):
    """('PASS'|'FAIL', mensaje) de un archivo local."""
    if not os.path.exists(path):
        return ('FAIL', f'{path}: arquivo nao encontrado')
    size = os.path.getsize(path)
    if not str(path).lower().endswith(EXTENSIONS):
        return ('FAIL', f'{path}: extensao nao suportada (use jpg/jpeg/png)')
    if size < MIN_BYTES:
        return ('FAIL', f'{path}: {size} B abaixo do minimo {MIN_BYTES // 1000} KB')
    if size > MAX_BYTES:
        return ('FAIL', f'{path}: {size} B acima do maximo {MAX_BYTES // 1000 // 1000} MB')
    try:
        from PIL import Image as PILImage
        with PILImage.open(path) as im:
            w, h = im.size
    except Exception as exc:                          # noqa: BLE001 - Pillow many errors
        return ('FAIL', f'{path}: ilegivel por Pillow ({type(exc).__name__})')
    if min(w, h) < MIN_PX:
        return ('FAIL', f'{path}: {w}x{h} px, lado menor < {MIN_PX} px')
    return ('PASS', f'{path}: {w}x{h} px · {size // 1024} KB')


def inspect_sources(slides):
    """Errores de archivo de las imagenes locales declaradas en el deck."""
    errs = []
    for i, d in enumerate(slides, 1):
        source = d.get('image')
        if not source:
            continue
        scheme, _value = classify(source)
        if scheme != 'local':
            continue
        status, msg = inspect_file(source)
        if status == 'FAIL':
            errs.append(f'slide {i}: {msg}')
    return errs


def imgprep(target='work/imgs'):
    """Verifica el contrato de imagenes de una carpeta y explica las reglas."""
    policy = ImagePolicy()
    print(f'[StudyDeck Imgprep] {target}')
    print(f'  contrato: jpg/jpeg/png · {MIN_BYTES // 1000} KB-{MAX_BYTES // 1000 // 1000} MB'
          f' · lado menor >= {MIN_PX} px · pie analitico >= {CAPTION_MIN} car.'
          f' · credito <= {CREDIT_MAX} car.')
    print(f'  presupuesto: {policy.mode} · max {HARD_CAP} imagenes (auto por source)')
    if not os.path.isdir(target):
        print(f'  [INFO] {target} aun no existe: cree la carpeta y deposite las figuras.')
        return 0
    failures = 0
    names = sorted(n for n in os.listdir(target) if n.lower().endswith(EXTENSIONS))
    if not names:
        print('  [INFO] sin imagenes en la carpeta.')
    for name in names:
        status, msg = inspect_file(os.path.join(target, name))
        print(f'  [{status}] {msg}')
        failures += status == 'FAIL'
    print(f'[StudyDeck Imgprep] ' + ('PASS' if not failures
                                    else f'FAIL — {failures} imagen(es) fora do contrato'))
    return 0 if not failures else 1