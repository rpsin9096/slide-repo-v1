# Semiotecnia del tórax y aparato respiratorio

Deck de 33 diapositivas construido con el motor StudyDeck v2 (paleta UCP,
Montserrat, contraste WCAG AA) a partir del capítulo 3 del PDF adjunto.

## Archivos

| Archivo | Qué es |
|---|---|
| `semiotecnia_del_torax.pptx` | **Entrega.** Editable en PowerPoint / Keynote / LibreOffice. |
| `semiotecnia_del_torax.pdf` | Vista previa paginada (render del motor, no de Office). |
| `manifest.py` | Fuente de autoria: `COURSE_INFO`, `CONFIG` y los 33 módulos. |
| `imgs/*.png` | Ocho láminas recortadas del PDF original. |
| `imgs/_partes/` | Recortes sueltos de trabajo; no los usa el deck. |

## Cómo se regenera

```bash
pip install -e .                              # motor (python-pptx, Pillow)
python3 tools/extract_figures.py "semiotecnia del torax.pdf" decks/semiotecnia-torax/imgs
python3 -m studydeck lint decks/semiotecnia-torax/manifest.py     # contrato por slide
python3 -m studydeck all  decks/semiotecnia-torax/manifest.py \
        decks/semiotecnia-torax/semiotecnia_del_torax.pptx
python3 tools/preview_pptx.py decks/semiotecnia-torax/semiotecnia_del_torax.pptx \
        decks/semiotecnia-torax/semiotecnia_del_torax.pdf
```

`studydeck all` no escribe nada si alguna diapositiva rompe el contrato o si algún
par texto/fondo baja de 4.5:1.

## Recorte de las figuras

El PDF trae cada página como un escaneo 1-bit de ~397 dpi sin recortes. El script
`tools/extract_figures.py`:

1. extrae el PNG embebido **tal cual** (sin volver a rasterizar, que metería ruido);
2. enmascara las cajas de la capa OCR para quedarse solo con la tinta del dibujo
   (conserva los rótulos A/B de la fig. 3-8, que son parte de la figura);
3. recorta por tinta real, con 7 pt de margen;
4. publica los dibujos verticales en parejas sobre una misma lámina, para que dos
   maniobras quepan a la altura de un solo dibujo.

| Lámina | Figuras del capítulo | Página |
|---|---|---|
| `fig_3_1_3_3.png` | 3-1 tórax en tonel · 3-3 tórax excavado | 11-12 |
| `fig_3_8.png` | 3-8 escoliosis A y B | 13 |
| `fig_3_9.png` | 3-9 mano de escultor | 14 |
| `fig_3_12_3_13.png` | 3-12 grupos axilares · 3-13 supraclaviculares | 14-15 |
| `fig_3_18_3_19.png` | 3-18 resistencia torácica · 3-19 Ruault | 16 |
| `fig_3_21_3_22.png` | 3-21 bases por delante · 3-22 por detrás | 17 |
| `fig_3_27_3_32.png` | 3-27 campos de Krönig · 3-32 excursión basal | 19-20 |
| `fig_3_34_3_35.png` | 3-34 y 3-35 mapas de auscultación | 21 |

## Estructura del deck

```
Portada · Objetivos · La secuencia semiológica
├── Bloque 1 · Inspección         (6) pasos, deformidades, simetría, figuras, cifosis,
│                                     dinámica y signos extratorácicos
├── Bloque 2 · Palpación          (7) seis maniobras, pared, ganglios, expansión,
│                                     resistencia/Ruault, bases, frémito y vibraciones
├── Bloque 3 · Percusión          (5) timbres del aire, grados de amortiguación,
│                                     vértices y bases, protocolo de mapeo
└── Bloque 4 · Auscultación       (6) ruidos normales, mapa, soplos, adventicios,
                                      voz y tos, caso oral
Glosario · Referencias
```

Cada bloque abre con su divisor y las figuras del capítulo aparecen en el bloque
que las usa, con pie analítico (qué enseña la imagen) y crédito a la figura de
origen.

## Ajustes de fondo

- `CONFIG['LANG'] = 'es-ES'`: el texto del capítulo está en español y el motor
  bloquea calcos de otro idioma; los epónimos (`Krönig`, `Ruault`, `Traube`,
  `pectus excavatum`) van exentos en `ALLOW_TERMS`.
- `IMAGES.max_n = 8`: ocho láminas reales, no marcadores; el modo sigue siendo
  `web-only`, sin `ai:` ni `placeholder:`.
