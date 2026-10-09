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
| `imgs/` | Apoyo visual: esquema de ecografía generado + fotos macro/micro reales de web (con crédito) |
| `source/` | Materiales fuente recibidos (guía visual + caso clínico) |

## Estructura del deck

1. **Portada** (`title`) — título, subtítulo, curso e integrantes.
2. **Caso clínico** (`case_block`) — viñeta clínica: paciente de 52 años, motivo de consulta, evolución de 8 meses y antecedentes clave.
3. **Estudios complementarios** (`checklist`) — panel verificado: TFGe 11 (ERC 5), anemia, sedimento de orina y ecografía (con esquema).
4. **Estudio macroscópico** (`figure`) — foto macro real (Wikimedia Commons): superficie cortical finamente granular con regla métrica.
5. **Estudio microscópico** (`figure`) — foto micro real anotada (PathologyOutlines, PAS): glomérulo con esclerosis global, fibrosis intersticial y atrofia tubular señalados con elipse, flechas y rótulos.
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

## Revisión PME v1.0 (auditoría de prosa médica deliberativa)

Refinamientos aplicados desde la matriz de la auditoría:

- **Diapositiva 2:** el antecedente de HTA asigna agencia causal explícita
  («la sobrecarga presora aceleró el colapso hemodinámico») — preservado en
  la viñeta clínica como hallazgo clave.
- **Diapositiva 4:** el pie desempaqueta la atrofia hacia evidencia temporal
  («reducción simétrica que confirma la lesión crónica terminal»).
- **Diapositiva 7:** la lesión vascular se enuncia como proceso causal
  (estrecha la luz → isquemia posglomerular → liberación desregulada de renina).
- **Diapositiva 9:** clausura pragmática vinculante (> 85% de obsolescencia
  glomerular contraindica la inmunosupresión e impone terapia de sustitución
  renal inmediata).

### Verificación de solapamiento (slide 3)

El módulo `stat_card` **con imagen** solapa el panel del dato heroico con las
tarjetas narrativas en **0,80 in × 1,52 in** (medido sobre el `.pptx`; el
fixture del motor no cubre `stat_card` con imagen, por lo que `studydeck check`
no lo detecta). La diapositiva 3 se reestructuró como `checklist` con imagen —
el único módulo de apoyo visual sin solapamiento (ítems 0,65–8,15 in; imagen
8,35–12,65 in) — conservando los cuatro ejes de estudios y el esquema de
ecografía. Verificación: escaneo geométrico de los 10 slides → los 10 CLEAN (los
0,04 in que mostraba el slide 2 eran los nodos intencionales de la antigua
línea de tiempo; con la viñeta clínica no hay solapamientos).

## Versión 2 — fotos web en macro/micro + caso simplificado

Cambios solicitados tras la revisión PME:

- **Fotos reales de web** (el motor no descarga imágenes: se descargaron y se
  referencian como archivo local con `caption` analítico y `credit`):
  - Slide 4 (macro): `imgs/macro_rinon_contraido_web.jpg` — Wikimedia Commons,
    «Gross pathology of nephrosclerosis» (875×673 px). Riñón con superficie
    cortical finamente granular, regla métrica e inserto magnificado. Nota de
    transparencia: la foto corresponde a un caso de nefroesclerosis; la
    morfología (riñón contraído granular) es la misma que enseña el caso.
  - Slide 5 (micro): foto real de PathologyOutlines con anotación gráfica
    incorporada (ver «Versión 3» y «Versión 4»). **Reemplazada en la Versión 4**
    tras la auditoría de coherencia clínica: la foto v2 («Interstitial fibrosis
    and tubular atrophy», 1160×630 px) mostraba fibrosis intersticial y atrofia
    tubular, pero **ningún glomérulo** (ver el detalle morfométrico en
    «Versión 4»).
- **Esquema conservado donde es pertinente:** slide 3 mantiene el esquema de
  ecografía generado (la guía pide ecografía anotada con medidas; no hay foto
  real equivalente con esas anotaciones). Se eliminaron los esquemas macro y
  micro reemplazados.
- **Slide 2 simplificado:** de `timeline` (26/47/52 años) a `case_block`
  (viñeta clínica), más fiel al guion del caso: paciente, motivo de consulta,
  evolución de 8 meses, antecedentes clave, juicio diagnóstico, diagnóstico y
  perla clínica. Se conservó el refinamiento PME de agencia causal en el
  antecedente de HTA.

Verificación: `imgprep` 3/3 PASS · `lint` PASS (10 slides) · build OK con
**contraste 0 violaciones WCAG** · escaneo geométrico de solapamientos: los
10 slides CLEAN.

## Versión 3 — anotación del slide 5 (micrografía con marcadores)

Solicitud: sobreponer a la foto elementos que indiquen **dónde ocurre cada
proceso**. Como el motor no coloca formas sobre las diapositivas, la anotación
se hornea en la propia imagen; los píxeles de la histología no se alteran,
solo se añaden gráficos encima (chips blancos con borde azul UCP `#3854CC`,
texto `#2B2C4A`, flechas y elipse en rojo UCP `#D92A2B`). La primera
implementación sobre la foto «Interstitial fibrosis and tubular atrophy» fue
**superada por la Versión 4**: la auditoría de coherencia clínica demostró
que esa foto no contiene ningún glomérulo, por lo que el marcador de
esclerosis glomerular global era incorrecto (ver «Versión 4»).

## Versión 4 — coherencia clínica del slide 5 (reemplazo de la micrografía)

**Hallazgo de la auditoría (tamaño medido con la barra de escala).** La foto
v2/v3 (`micro_rinon_web.jpg`, «Interstitial fibrosis and tubular atrophy»,
1160×630 px) tiene una barra de 90 µm ≈ 190-220 px (~2,1 px/µm). A ese aumento,
un glomérulo (150-250 µm) mediría 315-550 px; la imagen **no contiene ninguna
estructura redonda de ese tamaño** (las mayores miden ~150 px ≈ 68 µm). La
estructura señalada con la elipse medía ~75-85 µm: corresponde a un
**arteríolo hialinizado (arteriolosclerosis hialina)**, no a un glomérulo.
Conclusión: el marcador «Esclerosis glomerular global» y la leyenda v2
(«...y glomérulo con esclerosis global») eran **clínicamente incorrectos**;
la foto solo acreditaba fibrosis intersticial y atrofia tubular.

**Corrección.** Nueva micrografía: `imgs/micro_rinon_esclerosis_web.jpg` —
PathologyOutlines, «**Global glomerulosclerosis**», tinción **PAS**
(1716×942 px, 602 KB), del mismo tema que la foto anterior
(`kidneyrenaldisease.html` — glomerulonefritis crónica / riñón terminal, el
propio caso). Barra de escala de 80 µm = 204 px (2,55 px/µm).

**Verificación morfométrica (clínica):**

- Glomérulo central: ~192×208 µm (de cápsula a cápsula), tuft entero
  sustituido por masa cicatricial con cápsula de Bowman engrosada (PAS) =
  **esclerosis glomerular global**; segundo glomérulo esclerosado (~176 µm)
  en la parte inferior-izquierda.
- Túbulos de 43-78 µm con membrana basal engrosada (PAS+) = **atrofia
  tubular**.
- Intersticio pálido expandido con fibroblastos = **fibrosis intersticial**.

**Anotación final** (`imgs/micro_rinon_esclerosis_web_anotada.jpg`): elipse
roja sobre el glomérulo central con esclerosis global; flechas hacia la
fibrosis intersticial (intersticio pálido) y hacia un túbulo atrófico (membrana
basal magenta engrosada). La barra de 80 µm queda visible y sin cubrir.
Diff de píxeles contra un re-encode de referencia (misma calidad): los
gráficos quedan confinados a las regiones de los rótulos/flechas/elipse —
**0 píxeles de histología alterados** fuera de ellos.

**Manifest corregido:** caption «Micrografía anotada (PAS): glomérulo con
esclerosis global, fibrosis intersticial y atrofia tubular.» (100 car.);
crédito «PathologyOutlines (pathologyoutlines.com) — Global
glomerulosclerosis, PAS + anotación gráfica del Grupo 3» (106 car.); pie
corregido a «Tinción PAS · > 85% de glomérulos con esclerosis global en la
biopsia: confirma el estadio terminal.» (100 car.) — la foto es una única
tinción PAS, no el tríptico H&E/PAS/tricrómico que decía el pie anterior.
Archivos v2 eliminados: `micro_rinon_web.jpg`, `micro_rinon_web_anotada.jpg`.

Verificación: `imgprep` 4/4 PASS · `lint` PASS (10 slides) · build OK con
**contraste 0 violaciones WCAG** · escaneo geométrico de solapamientos: los
10 slides CLEAN.

## Notas del borrador

- Las imágenes de `imgs/` son **fotos reales de web con crédito** (slides 4-5)
  y un **esquema didáctico generado** (slide 3, ecografía anotada). Toda imagen
  lleva `caption` analítico (qué se enseña) y `credit` (fuente).
- El contrato de imágenes exige: jpg/jpeg/png, 20 KB–4 MB, lado menor ≥ 300 px.
- El motor no descarga ni genera imágenes: las figuras reales deben incorporarse
  como archivo local.
