"""Check the Práctica II export; requires pymupdf."""
from pathlib import Path
import re
import pymupdf

root = Path(__file__).resolve().parents[1]
source = (root / 'deliverables/practica-ii-respiratorio.md').read_text()
selected = [int(n) for line in re.findall(r'^@fig (.+)$', source, re.M) for n in line.split(',')]
assert selected == [9, 12, 13, 14, 18, 19, 21, 22, 24, 25, 30, 27, 31, 34, 35]
pdf = pymupdf.open(root / 'deliverables/practica-ii-respiratorio-bauhaus.pdf')
text = '\n'.join(page.get_text() for page in pdf)
for token in ['P2', 'SEMIOLOGÍA I', 'Práctica II:']:
    assert token in pdf[0].get_text(), f'Masthead missing: {token}'
placements = []
for page in pdf:
    assert 'Material de Raul de Oliveira Pasin' in page.get_text()
    for im in page.get_image_info():
        box = pymupdf.Rect(im['bbox'])
        assert page.rect.contains(box)
        assert box.height <= 164.1
        assert abs(box.width / box.height - im['width'] / im['height']) < .001
        placements.append(im)
assert len(placements) == len(selected) == 15
captions = [int(n) for n in re.findall(r'Fig\. 3-(\d+)\.', text)]
assert sorted(captions) == sorted(selected), f'Wrong captions: {captions}'
text = re.sub(r'\s+', ' ', text)
for phrase in ['Sinal de Jobert', 'Espaço semilunar de Traube', 'Conduta de decisão clínica', 'Organização regional', 'pesquisa de atrito pleural']:
    assert phrase in text, f'Missing content: {phrase}'
print(f'PASS: {len(pdf)} pages, 15 pertinent figures/captions, requested masthead, credit, intrinsic proportions and image bounds.')
