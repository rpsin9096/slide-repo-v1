import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
if (!process.argv[2]) throw new Error('Usage: node scripts/build_bauhaus.mjs /path/to/Newjs-main/pdf-generator.js');
// Apply a narrow, reproducible image-layout correction to the external formatter.
// Upstream caps height without reducing width, distorting tall illustrations.
const formatterPath = path.resolve(process.argv[2]);
let formatter = fs.readFileSync(formatterPath, 'utf8');
const originalSizing = `const targetW = Math.min(colW, origW);
    let targetH = (origH / origW) * targetW;

    // Cap maximum height to prevent single image from taking over entire page
    const maxAllowedH = (doc.page.height - tmpl.margins.top - tmpl.margins.bottom) * 0.45;
    if (targetH > maxAllowedH) {
      const scale = maxAllowedH / targetH;
      targetH = maxAllowedH;
    }`;
if (!formatter.includes(originalSizing)) throw new Error('Unrecognized formatter image-sizing implementation; review before patching.');
formatter = formatter.replace(originalSizing, `// Preserve aspect ratio and a restrained editorial figure scale.
    const imageScale = Math.min((colW - 12) / origW, 164 / origH, 1);
    const targetW = origW * imageScale;
    const targetH = origH * imageScale;`);
// Reserve enough width for complete percussion-sound names in the compact table.
const tableAnchor = '  // Calculate Header Height with dynamic text wrapping';
if (!formatter.includes(tableAnchor)) throw new Error('Unrecognized formatter table implementation.');
formatter = formatter.replace(tableAnchor, `  if (colCount === 4 && rawHeaders[0] === 'Sonido') {
    [0.24, 0.24, 0.27, 0.25].forEach((weight, i) => { colWidths[i] = tableW * weight; });
  }
${tableAnchor}`);
const patchedPath = path.join(path.dirname(formatterPath), '.bauhaus-editorial.generated.mjs');
let generatePdf;
try {
  fs.writeFileSync(patchedPath, formatter);
  ({ generatePdf } = await import(pathToFileURL(patchedPath).href));
} finally {
  fs.rmSync(patchedPath, { force: true });
}
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const names = JSON.parse(fs.readFileSync(path.join(root, 'deliverables/figuras/manifest.json'), 'utf8'));
let md = fs.readFileSync(path.join(root, 'deliverables/semiotecnia-del-torax.md'), 'utf8');
md = md.replace(/^@fig (.+)$/gm, (_, ns) => ns.split(',').map(n => {
  const fig = names.find(x => x.figure === `3-${Number(n)}`);
  if (!fig) throw new Error(`Missing figure ${n}`);
  const image = path.join(root, `deliverables/figuras/fig-3-${String(Number(n)).padStart(2, '0')}.png`);
  return `![Fig. 3-${Number(n)}. ${fig.caption}](${image})`;
}).join('\n\n'));
md = md.replace('@table', `| Sonido | Sustrato | Topografía | Hallazgo |
|---|---|---|---|
| Sonoridad | Resonancia del parénquima alveolar aireado. | Campos de Krönig; dorso hasta bases; derecho hasta 4.º EIC, izquierdo hasta 3.º EIC. | Atenuada en atelectasias o consolidaciones. |
| Hipersonoridad | Tono más grave e intensidad aumentada por exceso aéreo. | No existe en reposo fisiológico. | Enfisema, crisis asmática, neumotórax. |
| Timpanismo | Sonido musical agudo en cavidad aérea tensa cerrada. | Espacio semilunar de Traube (cámara gástrica). | Neumotórax a tensión, cavernas superficiales de pared lisa. |
| Matidez | Golpe sordo y breve sobre masa sólida sin gas. | Desde 5.º EIC derecho (hígado), área precordial cardíaca. | Consolidación neumónica masiva, derrame pleural. |
| Submatidez | Transición entre aire alveolar y solidez visceral. | 4.º a 5.º EIC derecho, área periprecordial. | Derrames laminares incipientes, condensaciones incompletas. |`);
// Separate clinical entries for clearer scanning instead of a single dense paragraph.
md = md.replace(/([^\n])\n(?=\*\*)/g, '$1\n\n');
// Keep a visible label/body separator across PDFKit continued font runs.
md = md.replace(/(\*\*[^*\n]+)\*\* +/g, '$1\u00a0**');
const options = {
  template: 'bauhaus', markdown: md,
  header_text: 'Material de Raul de Oliveira Pasin',
  header_date: { enabled: false }, alignment: 'justify',
  image_captions_enabled: true, chapters_toc: false, table_layout_mode: 'compact',
};
const pdf = await generatePdf(options);
const target = path.join(root, 'deliverables/semiotecnia-del-torax-bauhaus.pdf');
fs.writeFileSync(target, pdf);
console.log(`Generated ${target}: ${pdf.length} bytes`);
