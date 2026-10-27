# Bauhaus edition

This replaces the earlier PDF/Word edition from PR #7. Only the Bauhaus PDF is a finished document; the Markdown, cropped figures and manifest are retained as its source assets.

## Generation

- Formatter: DOE Formatter, `rpsin9096/js15-09`, `Newjs-main.zip` (archive dated September 14, 2026).
- Template: `bauhaus`; justified alignment; captions enabled; date and table of contents disabled.
- Generated locally, not through the hosted worker. Direct requests to the hosted service were blocked in the execution environment.
- **“Encaixar pé da página” was not applied.** That control is absent from the available formatter source. This is not an exact hosted-service export with both requested settings.
- The PDF reuses all 34 figures cropped from the user's original PDF.

## Rebuild

Extract the formatter archive outside tracked files (e.g. under `work/`), install its npm dependencies if necessary, then run from this repository:

```sh
node scripts/build_bauhaus.mjs /path/to/Newjs-main/pdf-generator.js
```

The formatter and its dependencies are external and are not vendored in this repository.

## Editorial revision

- Visually compared all 11 illustrated source pages with a proof of all 34 crops. Replaced every crop, removing scanned captions/neighboring text while preserving the original drawing and labels (including A/B in figure 3-8 and A–E in figure 3-12).
- `scripts/recrop_figures.py` reproducibly renders the original PDF at 3×, applies the reviewed rectangles, adds a small white safety margin and updates the manifest. Run it with the original PDF path; requires `pymupdf` and `Pillow`.
- `scripts/build_bauhaus.mjs` applies a guarded local patch to the external formatter: image width and height now share the same scale factor, with a 164-point maximum height and a column-width inset. This corrects the upstream aspect-ratio bug and avoids oversized illustrations.
- Rebalanced compact percussion-table widths to keep sound names intact; shortened table headings without removing cell content. Added clear clinical-entry spacing and preserved the label/body separator across font changes.
- Running header on every page: **Material de Raul de Oliveira Pasin**.
- Final revision: **7 pages**, all **34 figures**, with captions kept with their illustrations. Inspected full-document render proofs and enlarged sample pages, including the percussion table and final page.
- Validation: `python scripts/validate_bauhaus.py` (requires `pymupdf`) checks figure and caption counts, undistorted image proportions, image size/page bounds, credit on each page and the final text. Render proofs are temporary under ignored `work/`.
