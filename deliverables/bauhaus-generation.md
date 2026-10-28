# Bauhaus edition — supplied v3 compiler

The current PDF is generated with the user's **compilador-handoff-v3-updated 2.zip**, found at `deliverables/compilador-handoff-v3-updated 2.zip` on `main` in `rpsin9096/slide-repo-v1`.

## Compiler provenance

- Source commit inspected: `1c8f02be4c2810ffa19eac2bf29ca99e377afb0d`.
- Git blob: `3bf8aba443f802752e0ce04fcf4aa105f203aa7f`.
- Archive SHA-256: `135074951fa5c35ed2260449e6c5343c93fd41cbf4833c5fd1ac19f71757c2f9`.
- Archive extracted into ignored `work/compiler-v3/`; dependencies installed with `npm ci`.
- Uses the supplied `pdf-generator.js` facade and v3 PDFKit pipeline directly. **No compiler source patches.** This supersedes the previous locally patched legacy formatter rendering.

## Settings and assets

- `template: 'bauhaus'`, `geometry: 'v3'`, `lang: 'es'`.
- **“Encaixar pé da página”: enabled** (`flush_columns: true`). “Quebrar colunas para acomodar” disabled (`balance_columns: false`). Flush fitting follows the compiler's bounded-glue rules; enabling it is not a claim that every column reaches the page foot.
- Two-column layout, justified alignment, captions enabled, date and TOC disabled.
- Running header: **Material de Raul de Oliveira Pasin**.
- Retains the 34 visually corrected crops, original figure numbering and complete study text.
- Images are embedded as data URIs to respect the new compiler's filesystem restrictions. Native figure-width attributes keep their intrinsic proportions with maximum height 164 pt. This does not require the old image-sizing patch.

## Rebuild

Extract the supplied ZIP under ignored `work/`, then:

```sh
cd work/compiler-v3/compilador-handoff-v3-updated
npm ci
cd ../../..
node scripts/build_bauhaus.mjs work/compiler-v3/compilador-handoff-v3-updated/pdf-generator.js
```

Existing Markdown, manifest and PNG assets are reused. To redo the crops from the original PDF, install `pymupdf` and `Pillow`, then run:

```sh
python scripts/recrop_figures.py '/path/to/semiotecnia del torax.pdf'
```

## Validation

```sh
python scripts/validate_bauhaus.py
```

Requires `pymupdf`. Current result: **7 pages, 34 images and captions**, aspect ratios preserved, no oversized/off-page images, credit on every page, final text present. Reviewed the complete rendered-page overview and enlarged percussion-table/final-page renders. The small gutter arrows are native compiler reading-flow indicators, not clipping warnings. Temporary renders remain under ignored `work/`.

## History

This PR replaces the original non-Bauhaus PDF/Word edition from PR #7. Earlier revisions used an older formatter that did not expose the flush-bottom control. That limitation no longer applies to this v3-generated PDF.
