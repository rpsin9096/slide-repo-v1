import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
if (!process.argv[2]) throw new Error('Usage: node scripts/build_practica_ii.mjs /path/to/compilador-handoff-v3-updated/pdf-generator.js');
// Use the supplied v3 compiler directly; no legacy formatter patches.
const compilerPath = path.resolve(process.argv[2]);
const { generatePdf, TEMPLATES } = await import(pathToFileURL(compilerPath).href);
const tmpl = TEMPLATES.bauhaus;
const columnWidth = (595.28 - tmpl.margins.left - tmpl.margins.right - tmpl.columnsep) / 2;
const maxCompilerHeight = (841.89 - tmpl.margins.top - tmpl.margins.bottom) * 0.45;
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const captions = {9:'Mão de escultor',12:'Localização dos grupos ganglionares axilares (A–E)',13:'Palpação dos linfonodos supraclaviculares',14:'Palpação do grupo axilar externo',18:'Elasticidade torácica: compressão bimanual',19:'Expansibilidade dos ápices: manobra de Ruault',21:'Expansibilidade das bases anteriores',22:'Expansibilidade das bases posteriores',24:'Frêmito toracovocal: face anterior',25:'Frêmito toracovocal: face posterior',27:'Percussão dos campos de Krönig',30:'Percussão anterior: transição hepatopulmonar',31:'Percussão dorsal',34:'Ausculta: distribuição anterior dos ruídos normais',35:'Ausculta: distribuição posterior dos ruídos normais'};
const names = JSON.parse(fs.readFileSync(path.join(root, 'deliverables/figuras/manifest.json'), 'utf8'));
let md = fs.readFileSync(path.join(root, 'deliverables/practica-ii-respiratorio.md'), 'utf8');
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
  return `![Fig. 3-${Number(n)}. ${captions[Number(n)]}](${uri}) {width=${userScale.toFixed(6)} ratio=${(width/height).toFixed(6)}}`;
}).join('\n\n'));
const options = {
  template: 'bauhaus', lang: 'pt', geometry: 'v3',
  title: 'Semiología I',
  sections: [{
    markdown: md,
    masthead: { enabled: true, prefix: 'P2', course: 'Semiología I', topic: 'Práctica II:', header: true },
  }],
  flush_columns: true, balance_columns: false,
  header_text: 'Material de Raul de Oliveira Pasin',
  header_date: { enabled: false }, alignment: 'justify',
  image_captions_enabled: true, chapters_toc: false, table_layout_mode: 'auto',
};
const pdf = await generatePdf(options);
const target = path.join(root, 'deliverables/practica-ii-respiratorio-bauhaus.pdf');
fs.writeFileSync(target, pdf);
console.log(`Generated ${target}: ${pdf.length} bytes`);
