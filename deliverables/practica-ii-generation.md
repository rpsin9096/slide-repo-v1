# Práctica II — exame respiratório

New document, separate from the previous Spanish guide. Uses the Portuguese text supplied in chat, with figure insertion markers added in the Markdown source; wording and clinical claims are preserved, not independently validated.

## Compiler and settings

Same supplied archive and provenance as `bauhaus-generation.md`: `compilador-handoff-v3-updated 2.zip` (SHA-256 `135074951fa5c35ed2260449e6c5343c93fd41cbf4833c5fd1ac19f71757c2f9`). No compiler patches.

- Bauhaus; geometry v3; language Portuguese; two columns.
- **Encaixar pé da página ON** (`flush_columns: true`).
- **Quebrar colunas para acomodar OFF** (`balance_columns: false`).
- Masthead: prefix **P2**, course **Semiología I**, topic **Práctica II:**. Compiler displays the course in uppercase.
- Credit: **Material de Raul de Oliveira Pasin**.
- Captions in Portuguese, preserving the original figure numbers.
- Auto table layout: final five-column comparative table spans the full printable page width.
- Native image width attributes preserve proportions and limit drawing height to 164 pt.

## Pertinent figures only

| Original figure | Relationship to supplied text |
|---|---|
| 3-9 | Mão de escultor |
| 3-12, 3-13, 3-14 | Axillary groups, supraclavicular and axillary palpation |
| 3-18 | Bimanual thoracic elasticity |
| 3-19 | Ruault / apical expansion |
| 3-21, 3-22 | Anterior and posterior basal expansion |
| 3-24, 3-25 | Anterior and posterior vocal fremitus |
| 3-30 | Anterior percussion / hepatic transition |
| 3-27, 3-31 | Krönig fields and dorsal percussion |
| 3-34, 3-35 | Anterior/posterior distribution of normal auscultatory sounds |

No deformity, trophism, muscular-tone, direct clavicular/sternal/vertebral percussion, or diaphragmatic-excursion illustrations were inserted, since those specific techniques are not discussed. Existing PNGs are reused, not duplicated.

## Rebuild and validation

After extracting the supplied archive and running `npm ci` in its directory:

```sh
node scripts/build_practica_ii.mjs work/compiler-v3/compilador-handoff-v3-updated/pdf-generator.js
python scripts/validate_practica_ii.py
```

Validator requires `pymupdf`. Current output: **4 pages, 15 figures**. Reviewed the overview of all pages and enlarged first/final pages to check masthead, crops, captions and panoramic summary table. Validation checks exact figure selection, aspect ratios, height/page bounds, masthead/credit and key sections.
