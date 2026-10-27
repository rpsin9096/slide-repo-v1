import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
if (!process.argv[2]) throw new Error('Usage: node scripts/build_bauhaus.mjs /path/to/Newjs-main/pdf-generator.js');
const { generatePdf } = await import(pathToFileURL(path.resolve(process.argv[2])).href);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const names = JSON.parse(fs.readFileSync(path.join(root, 'deliverables/figuras/manifest.json'), 'utf8'));
let md = fs.readFileSync(path.join(root, 'deliverables/semiotecnia-del-torax.md'), 'utf8');
md = md.replace(/^@fig (.+)$/gm, (_, ns) => ns.split(',').map(n => {
  const fig = names.find(x => x.figure === `3-${Number(n)}`);
  if (!fig) throw new Error(`Missing figure ${n}`);
  const image = path.join(root, `deliverables/figuras/fig-3-${String(Number(n)).padStart(2, '0')}.png`);
  return `![Fig. 3-${Number(n)}. ${fig.caption}](${image})`;
}).join('\n\n'));
md = md.replace('@table', `| Sonido | Sustrato biofísico | Topografía fisiológica | Hallazgo patológico |
|---|---|---|---|
| Sonoridad | Resonancia del parénquima alveolar aireado. | Campos de Krönig; dorso hasta bases; derecho hasta 4.º EIC, izquierdo hasta 3.º EIC. | Atenuada en atelectasias o consolidaciones. |
| Hipersonoridad | Tono más grave e intensidad aumentada por exceso aéreo. | No existe en reposo fisiológico. | Enfisema, crisis asmática, neumotórax. |
| Timpanismo | Sonido musical agudo en cavidad aérea tensa cerrada. | Espacio semilunar de Traube (cámara gástrica). | Neumotórax a tensión, cavernas superficiales de pared lisa. |
| Matidez | Golpe sordo y breve sobre masa sólida sin gas. | Desde 5.º EIC derecho (hígado), área precordial cardíaca. | Consolidación neumónica masiva, derrame pleural. |
| Submatidez | Transición entre aire alveolar y solidez visceral. | 4.º a 5.º EIC derecho, área periprecordial. | Derrames laminares incipientes, condensaciones incompletas. |`);
const options = {
  template: 'bauhaus', markdown: md,
  header_text: 'Semiotecnia del tórax y aparato respiratorio',
  header_date: { enabled: false }, alignment: 'justify',
  image_captions_enabled: true, chapters_toc: false,
};
const pdf = await generatePdf(options);
const target = path.join(root, 'deliverables/semiotecnia-del-torax-bauhaus.pdf');
fs.writeFileSync(target, pdf);
console.log(`Generated ${target}: ${pdf.length} bytes`);
