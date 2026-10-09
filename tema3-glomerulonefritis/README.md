# Tema 3 — Glomerulonefritis Crónica (deck UCP)

Deck de 10 diapositivas en español (es-ES) elaborado con el motor **StudyDeck**
(motor v3, `study-deck 3.zip` del repositorio) siguiendo el `SYSTEM_PROMPT.md`
del motor y la identidad visual **UCP** (paleta `#3854CC` / `#D92A2B` /
`#2B2C4A`, Montserrat, WCAG AA verificado en tiempo de build).

**Caso:** varón de 52 años con glomerulonefritis crónica terminal (riñón
contraído, esclerosis glomerular global y fibrosis intersticial) — Anatomía
Patológica, Grupo 3, Pregrado Médico.

## Archivos

| Archivo | Descripción |
|---|---|
| `tema3_glomerulonefritis_cronica.pptx` | **Deck generado (10 diapositivas, 16:9)** |
| `manifest.py` | Fuente del deck (COURSE_INFO + CONFIG + SLIDES) |
| `GUION_DEL_ORADOR.md` | Guion del orador por diapositiva (~14 min) |
| `imgs/` | Apoyo visual: esquemas didácticos (ecografía, macro, panel micro 2×2) |
| `source/` | Materiales fuente recibidos (guía visual + caso clínico) |

## Estructura del deck

1. **Portada** (`title`) — título, subtítulo, curso e integrantes.
2. **Caso clínico** (`timeline`) — 26 años / 47 años / 52 años (actual).
3. **Estudios complementarios** (`stat_card`) — TFGe 11 mL/min/1,73 m² (ERC 5) + bioquímica, hemograma/orina y ecografía (con esquema).
4. **Estudio macroscópico** (`figure`) — corte coronal del riñón contraído (con esquema anotado).
5. **Estudio microscópico** (`figure`) — panel 2×2: obsolescencia glomerular, fibrosis intersticial (Masson), tiroidización tubular, arterioloesclerosis hialina.
6. **Patogenia** (`flow_diagram`) — hiperfiltración de Brenner en 4 pasos.
7. **Correlación clínico-patológica** (`side_by_side`) — sustrato tisular vs. expresión clínica.
8. **Diagnóstico diferencial** (`comparison_table`) — 4 entidades × 4 criterios.
9. **Diagnóstico final y manejo** (`pyramid`) — diálisis → control integral → trasplante (con contraindicación de inmunosupresión en nota).
10. **Conclusiones** (`concept_map`) — 4 lecciones alrededor del riñón contraído terminal.

## Cómo reconstruir

```bash
# 1. instalar el motor v3 (desde el zip del repositorio)
python3 -m venv /tmp/sdvenv
/tmp/sdvenv/bin/pip install -e "<ruta>/study-deck"   # extraído de study-deck 3.zip

# 2. verificar el motor (35/35 módulos + contraste)
/tmp/sdvenv/bin/studydeck check

# 3. verificar imágenes y contrato del manifest
cd tema3-glomerulonefritis
/tmp/sdvenv/bin/studydeck imgprep imgs
/tmp/sdvenv/bin/studydeck lint manifest.py --json

# 4. generar el .pptx (lint fail-fast + render; el contraste bloquea la entrega)
/tmp/sdvenv/bin/studydeck all manifest.py tema3_glomerulonefritis_cronica.pptx
```

## Notas del borrador

- Las imágenes de `imgs/` son **esquemas didácticos generados** coherentes con la
  guía visual (apoyo visual permitido). Para la versión final, sustituir por
  fotografías reales (macro/micro) con `caption` analítico y `credit`.
- El contrato de imágenes exige: jpg/jpeg/png, 20 KB–4 MB, lado menor ≥ 300 px.
- El motor no descarga ni genera imágenes: las figuras reales deben incorporarse
  como archivo local.
