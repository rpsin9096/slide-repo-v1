"""Structural checks; visual review of page renders is still required."""
import json
from pathlib import Path
import pymupdf

root = Path(__file__).resolve().parents[1]
pdf = pymupdf.open(root / 'deliverables/semiotecnia-del-torax-bauhaus.pdf')
manifest = json.loads((root / 'deliverables/figuras/manifest.json').read_text())
images = []
text = ''
for number, page in enumerate(pdf, 1):
    page_text = page.get_text()
    assert 'Material de Raul de Oliveira Pasin' in page_text, f'Missing credit on {number}'
    assert len(page_text.strip()) > 80, f'Empty page {number}'
    text += page_text
    for image in page.get_image_info():
        rect = pymupdf.Rect(image['bbox'])
        assert page.rect.contains(rect), f'Image outside page {number}'
        assert rect.height <= 164.1, f'Oversized image on {number}'
        aspect = image['width'] / image['height']
        assert abs(rect.width/rect.height - aspect) < 0.001, f'Distorted image on {number}'
        images.append(image)
assert len(images) == len(manifest) == 34
for entry in manifest:
    assert f"Fig. {entry['figure']}." in text, f"Missing caption {entry['figure']}"
assert 'establecer un diagnóstico.' in text
print(f'PASS: {len(pdf)} pages; 34 figures/captions; proportions preserved; no oversized or off-page images; credit on every page; final text present.')
