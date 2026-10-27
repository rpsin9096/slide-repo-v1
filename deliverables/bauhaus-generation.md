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
