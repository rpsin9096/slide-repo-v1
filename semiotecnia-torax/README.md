# Semiotecnia del Tórax y Aparato Respiratorio — documento ilustrado

Documento construido a partir del texto provisto, con **todas las figuras citadas
(3-1 a 3-35) adjuntas como láminas** en el punto donde el texto las menciona.
Cada imagen es un **recorte de un render a 300 dpi** del PDF adjunto
(`semiotecnia del torax.pdf`, 14 páginas; capítulo 3, pp. 9–21 del libro).
No se redibujó ni se generó ninguna imagen.

## Entregables

| Archivo | Descripción |
|---|---|
| `Semiotecnia-del-Torax-y-Aparato-Respiratorio.docx` | Documento editable (Word/Google Docs): portada, índice actualizable, 4 capítulos, tabla de timbres percutorios, apéndices. |
| `Semiotecnia-del-Torax-y-Aparato-Respiratorio.pdf` | Misma versión en PDF (17 págs., listo para imprimir/compartir). |
| `figures/fig-3-01.jpg` … `fig-3-35.jpg` | 36 recortes individuales a 300 dpi (la 3-8 va separada en `fig-3-08a/b`). |
| `figuras-manifiesto.csv` | Procedencia de cada recorte: página del PDF, página del libro, coordenadas de recorte y tamaño en px. |

> En el DOCX, si el índice aparece vacío: clic derecho → «Actualizar campos».

## Cobertura de figuras

- **35/35 figuras citadas en el texto tienen lámina** (verificado por script:
  ninguna cita `(Fig. …)` quedó sin imagen).
- La **Fig. 3-8** se separó en dos recortes (**3-8A** sinistroconvexa y
  **3-8B** dextroconvexa) porque el texto las cita por separado; en el libro
  es una sola figura con dos paneles (p. 13).
- La **Fig. 3-23** (ángulo de Louis) existe en la fuente pero **no es citada
  en el texto provisto**: se incluye en el **Apéndice B** para completar la serie.
- Correspondencia 3-2/3-4: el texto agrupa «en quilla (pectus carinatum /
  piriforme)»; en los epígrafes originales, la 3-2 es el *tórax de pollo*
  (en quilla) y la 3-4 el *tórax piriforme*. Las láminas conservan el título
  original de cada una.
- La Fig. 3-30 es en el original un detalle cercano de manos (percusión
  digito-digital), sin vista completa del tórax; se reproduce tal cual.

## Método de extracción

1. Render de control de las 14 páginas del PDF y mapeo visual de cada figura
   (página del PDF ↔ página del libro ↔ número de figura).
2. Render directo con clip por figura a **300 dpi** (PyMuPDF `get_pixmap(clip=…)`,
   sin JPEG intermedio).
3. Limpieza con Pillow: escala de grises, nivel de blancos del papel escaneado
   y recorte automático de márgenes con relleno. Control visual de los 36
   recortes en láminas de contacto (se corrigieron sangrados de encabezados
   de página y epígrafes vecinos).

## Reconstruir

```bash
pip install pymupdf pillow python-docx reportlab
python3 _build/extract_figures.py "/ruta/semiotecnia del torax.pdf" figures
python3 _build/build_docx.py
python3 _build/build_pdf.py
```

El texto vive en `_build/content.py` (fuente única para DOCX y PDF); las
coordenadas de recorte, en `_build/extract_figures.py`.
