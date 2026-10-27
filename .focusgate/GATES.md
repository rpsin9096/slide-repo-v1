# FocusGate Ledger: StudyDeck v2 — rebuild UCP-only
State: [Step 4 of 4] [gates] FocusGate v3.4-PROD

## 1. Domain Anchors (Micro-Glossary)
- **Deck**: manifest carregado (`COURSE_INFO` + `CONFIG` + `SLIDES`), com defaults UCP/pt-BR.
- **Contrato**: por slide — requeridos, orçamentos de caracteres, ajuste tipográfico, imagem.
- **Gate de contraste**: `ContrastGate`; par texto/superficie abaixo do limiar impede a gravação.
- **Política de imagem**: modo (`web-only|mixed|ai-only|none`), orçamento (`auto|N`), propósito analítico.
- **Registro**: índice único de 35 módulos (`registry.py`); `contracts.py` é o escritor único dos orçamentos.
- Avoid: `utils.py`, paleta ≠ UCP, download silencioso de imagem, marker `<= N car.>`.

## 2. Acceptance Gates — invariantes do rebuild

- [x] g-ucp-only: a paleta é UCP e a fonte é Montserrat, sem alternativa
  CHECK: .venv/bin/python -c "from studydeck.palette import PALETTES; from studydeck.typography import FONTS; print(sorted(PALETTES), sorted(set(FONTS.values())))"
  EXPECT: \['ucp'\] \['Montserrat'\]

- [x] g-cobertura-modulos: os 35 módulos renderizam sem violação de contraste
  CHECK: .venv/bin/studydeck check
  EXPECT: modulos 35/35 renderizados sem violacao de contraste

- [x] g-contraste-invariante: o fixture completo fecha com zero violações WCAG
  CHECK: .venv/bin/studydeck check
  EXPECT: contraste fixture: PASS — 0 violaciones

- [x] g-contrato-exemplo: o deck de exemplo cumpre o contrato em pt-BR
  CHECK: .venv/bin/studydeck lint examples/ejemplo_inflamacao.py
  EXPECT: PASS — 10 slides cumprem o contrato

- [x] g-entrega-deck: lint -> build produz .pptx com contraste limpo
  CHECK: .venv/bin/studydeck all examples/ejemplo_inflamacao.py /tmp/gate_deck.pptx
  EXPECT: contraste 0 violaciones

- [x] g-politica-imagem: modos, orçamento context-aware e propósito analítico
  CHECK: .venv/bin/python -m pytest tests/test_images.py -q
  EXPECT: 43 passed

- [x] g-fitness-ratchets: escritor único, sem caião de utilidades, imports para dentro
  CHECK: .venv/bin/python -m pytest tests/test_fitness.py -q
  EXPECT: 20 passed

- [x] g-suite-completa: a suite inteira verde
  CHECK: .venv/bin/python -m pytest -q
  EXPECT: 245 passed in

- [x] g-instalavel: o console script responde depois de `pip install -e .`
  CHECK: .venv/bin/studydeck --help
  EXPECT: Uso

- [x] g-sem-cliche-codigo: FocusGate não acha estrutura de máquina
  CHECK: python3 skills/focus-gate-v3.4/scripts/focus-gate.py --audit-code-cliche studydeck
  EXPECT: CODE_CLICHE_AUDIT_PASS

- [x] g-prompt-restricoes: o prompt de restrições expõe os controles de imagem
  CHECK: .venv/bin/python -c "import pathlib; t=pathlib.Path('prompt.md').read_text(); print('PROMPT_OK' if all(k in t for k in ('max_n','allow_ai','allow_placeholder','web-only','auto')) else 'PROMPT_INCOMPLETO')"
  EXPECT: PROMPT_OK

- [x] g-sem-paleta-legada: nenhuma palavra nem hex de paleta morta no código ou docs
  CHECK: .venv/bin/python -m pytest tests/test_fitness.py::TestNoLegacyPalette -q
  EXPECT: 2 passed

- [x] g-oraculo-visual: tokens, piso tipografico, limites y composicion probados sobre el .pptx
  CHECK: .venv/bin/python -m pytest tests/test_visual.py -q
  EXPECT: 16 passed

- [x] g-tokens-sem-hex: nenhum #hex solto em nenhum .py do pacote (oraculo real --audit-tokens)
  CHECK: for f in studydeck/*.py studydeck/modules/*.py; do python3 skills/focus-gate-v3.4/scripts/focus-gate.py --audit-tokens "$f" | grep -q AUDIT_TOKENS_PASS || { echo "TOKENS_FAIL $f"; exit 1; }; done && echo TOKENS_ALL_PASS
  EXPECT: TOKENS_ALL_PASS

- [x] g-sem-borrachice: nenhuma via de escape trivial nem marcador de stub (--unlazy-rigor)
  CHECK: python3 skills/focus-gate-v3.4/scripts/focus-gate.py --unlazy-rigor studydeck
  EXPECT: 0 total violation

- [x] g-lienzo-16x9: o pptx renderizado e 16:9 para cada slide, pelo oraculo real --audit-safe-zone
  CHECK: mkdir -p .focusgate/prototypes/deck_svg && rm -f .focusgate/prototypes/deck_svg/*.svg && .venv/bin/python tests/export_deck_svg.py examples/ejemplo_inflamacao.py .focusgate/prototypes/deck_svg && python3 skills/focus-gate-v3.4/scripts/focus-gate.py --audit-safe-zone .focusgate/prototypes/deck_svg --platform landscape-16x9
  EXPECT: SAFE_ZONE_PASS

## 3. Micro-ADR Ledger
- **UCP-only**: as 4 paletasrizes legadas foram removidas; `CONFIG['PALETTE']`
  diferente só avisa. Fonte única Montserrat (`typography.FONTS`).
- **Escritor único**: `contracts.B` e `REQUIRED_NONEMPTY` vivem só em
  `contracts.py`; `registry.MODULES` é o único índice de módulos.
- **Imagem apoia**: `figure`/`authority_card` exigem imagem com pie analítico;
  demais aceitam apoio. Nenhum download automático.
- **Log do gate por deck**: `new_slide()` limpa superfícies mas preserva o log
  — perder violações entre slides entregaria deck ilegível como legível.
- **Verde sem artefato**: `studydeck check` = 35/35 módulos + 0 violações.
- **Faceta banner-safe-zone (avaliação honesta)**: o que se APLICA foi
  verificado com o oráculo REAL — aspecto 16:9 de cada slide renderizado
  (g-lienzo-16x9, via export SVG + `--audit-safe-zone`). O envelope central
  de 70% (tolerância de crop de plataformas sociais) NÃO se aplica a .pptx:
  nenhuma plataforma corta as bordas; evidência `--box 650,1550,12033,5050`
  → SAFE_ZONE_FAIL documentado. A banda editorial (0.65in) é a zona segura
  correta do domínio pptx, provada por g-oraculo-visual. Inventário de
  formatos: exatamente UM (16:9) → uma superfície de auditoria, completa.
- **Rótulos sem floritura (decisão do autor)**: moção = DEBATE (não a fórmula
  da Oxford Union); exame oral = PROVA ORAL/EXAMEN ORAL/ORAL EXAM (não o
  latim 'viva voce'); `§` removido da numeração; defaults fabricados
  (curso/instituição/série de monografias) removidos — o motor não inventa
  conteúdo.