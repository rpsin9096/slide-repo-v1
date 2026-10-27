# -*- coding: utf-8 -*-
"""Ingesta de fonte: extrai o outline do .pdf/.txt/.md para que o autor case
cada secao com o `when` de um modulo. Convenience, nao contrato."""

import os
import re

_HEADING = re.compile(r'^\d{1,2}(\.\d{1,3})*[\.)]?\s+\S')


def extract_text(path):
    """Texto plano da fonte (.txt/.md direto; .pdf via pypdf)."""
    ext = str(path).lower().rsplit('.', 1)[-1]
    if ext in ('txt', 'md'):
        with open(path, encoding='utf-8', errors='replace') as fh:
            return fh.read()
    if ext == 'pdf':
        try:
            from pypdf import PdfReader
        except ImportError:
            raise SystemExit('[StudyDeck Ingest] Falta pypdf: pip install pypdf')
        return '\n'.join((page.extract_text() or '') for page in PdfReader(path).pages)
    raise SystemExit(f'[StudyDeck Ingest] Formato .{ext} nao suportado (pdf/txt/md)')


def is_heading(line):
    """Titulo numerado curto sem ponto final (exclui '2.345 pacientes')."""
    if len(line) > 80 or line.rstrip().endswith('.'):
        return False
    if re.match(r'^\d{1,2}\.\d{3}\s', line):
        return False
    return bool(_HEADING.match(line))


def ingest(source_path, out_dir='work'):
    """Escreve work/outline.md e devolve o numero de blocos de texto."""
    if not os.path.exists(source_path):
        raise FileNotFoundError(f'source nao encontrado: {source_path}')
    text = extract_text(source_path)
    os.makedirs(out_dir, exist_ok=True)
    lines = [f'# OUTLINE — {source_path}', '']
    blocks = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if is_heading(line):
            lines.append(f'\n## {line}')
        else:
            lines.append(f'- {line}')
            blocks += 1
    out_md = os.path.join(out_dir, 'outline.md')
    with open(out_md, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    return out_md, blocks