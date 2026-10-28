import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
if (!process.argv[2]) throw new Error('Usage: node scripts/build_bauhaus.mjs /path/to/compilador-handoff-v3-updated/pdf-generator.js');
// Use the supplied v3 compiler directly; no legacy formatter patches.
const compilerPath = path.resolve(process.argv[2]);
const { generatePdf, TEMPLATES } = await import(pathToFileURL(compilerPath).href);
const tmpl = TEMPLATES.bauhaus;
const columnWidth = (595.28 - tmpl.margins.left - tmpl.margins.right - tmpl.columnsep) / 2;
const maxCompilerHeight = (841.89 - tmpl.margins.top - tmpl.margins.bottom) * 0.45;
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const names = JSON.parse(fs.readFileSync(path.join(root, 'deliverables/figuras/manifest.json'), 'utf8'));
let md = fs.readFileSync(path.join(root, 'deliverables/semiotecnia-del-torax.md'), 'utf8');
md = md.replace(/^@fig (.+)$/gm, (_, ns) => ns.split(',').map(n => {
  const fig = names.find(x => x.figure === `3-${Number(n)}`);
  if (!fig) throw new Error(`Missing figure ${n}`);
  const image = path.join(root, `deliverables/figuras/fig-3-${String(Number(n)).padStart(2, '0')}.png`);
  const bytes = fs.readFileSync(image);
  const width = bytes.readUInt32BE(16), height = bytes.readUInt32BE(20);
  const baseScale = Math.min(columnWidth / width, maxCompilerHeight / height, 1);
  const desiredScale = Math.min((columnWidth - 12) / width, 164 / height, 1);
  const userScale = Math.min(1, desiredScale / baseScale);
  const uri = `data:image/png;base64,${bytes.toString('base64')}`;
  return `![Fig. 3-${Number(n)}. ${fig.caption}](${uri}) {width=${userScale.toFixed(6)} ratio=${(width/height).toFixed(6)}}`;
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
const options = {
  template: 'bauhaus', markdown: md, lang: 'es', geometry: 'v3',
  flush_columns: true, balance_columns: false,
  header_text: 'Material de Raul de Oliveira Pasin',
  header_date: { enabled: false }, alignment: 'justify',
  image_captions_enabled: true, chapters_toc: false, table_layout_mode: 'compact',
};
const pdf = await generatePdf(options);
const target = path.join(root, 'deliverables/semiotecnia-del-torax-bauhaus.pdf');
fs.writeFileSync(target, pdf);
console.log(`Generated ${target}: ${pdf.length} bytes`);
