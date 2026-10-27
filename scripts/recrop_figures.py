"""Render the original PDF, then crop illustrations (not the scanned captions).
Usage: python scripts/recrop_figures.py '/path/to/semiotecnia del torax.pdf'
Requires pymupdf and Pillow. Rectangles are measured on 774 × 1095 page proofs.
"""
import io
import json
import sys
from pathlib import Path
import pymupdf
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/figuras'
# page, left, top, right, bottom; includes original drawing/labels, excludes captions.
BOXES = {
1:(3,52,704,379,968), 2:(3,389,729,703,978),
3:(4,74,145,390,384), 4:(4,408,108,724,383),
5:(4,79,632,400,880), 6:(4,443,518,704,886),
7:(5,258,195,496,548), 8:(5,118,616,649,948),
9:(6,87,110,373,440),10:(6,399,110,717,433),
11:(6,110,540,356,883),12:(6,420,510,713,897),
13:(7,67,193,353,524),14:(7,386,195,713,530),
15:(7,101,608,363,959),16:(7,393,631,716,966),
17:(8,60,112,372,529),18:(8,416,117,693,511),19:(8,86,672,387,939),
20:(9,350,194,700,544),21:(9,65,589,346,924),22:(9,411,581,645,909),
24:(10,405,119,727,415),25:(10,87,584,404,943),
26:(11,63,185,334,519),27:(11,397,186,683,480),28:(11,345,662,701,1028),
29:(12,65,117,381,373),30:(12,400,117,719,293),
31:(12,100,528,383,874),32:(12,433,478,709,809),
33:(13,55,190,356,558),34:(13,386,190,696,559),35:(13,423,658,705,1029),
}
manifest = json.loads((OUT / 'manifest.json').read_text())
pdf = pymupdf.open(sys.argv[1])
rendered = {}
for entry in manifest:
    n = int(entry['figure'].split('-')[1])
    page, x0, y0, x1, y1 = BOXES[n]
    if page not in rendered:
        pix = pdf[page-1].get_pixmap(matrix=pymupdf.Matrix(3, 3))
        rendered[page] = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
    im = rendered[page]
    fraction = [x0/774, y0/1095, x1/774, y1/1095]
    crop = im.crop(tuple(round(v*d) for v,d in zip(fraction,[im.width,im.height]*2)))
    ImageOps.expand(crop, border=12, fill='white').save(OUT / f'fig-3-{n:02}.png')
    entry['crop_fraction'] = [round(v,6) for v in fraction]
    entry['raster_padding_px'] = 12
    entry['render_scale'] = 3
    if n == 12:
        entry['caption'] = 'Localización de grupos ganglionares axilares (A–E)'
    if n == 14:
        entry['caption'] = 'Palpación del grupo axilar externo'
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
print(f'Recropped {len(manifest)} figures from full-page renders.')
