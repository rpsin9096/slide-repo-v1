# StudyDeck v2 — motor de slides UCP-only

Editorial, WCAG AA, 35 módulos verificados. Paleta UCP e Montserrat 100%: não
existe outra paleta nem outra fonte.

```bash
pip install -e .            # ou: uv pip install -e .
studydeck check             # 35/35 módulos + veredicto de contraste
```

## Comandos

```bash
studydeck ingest fonte.pdf work        # outline do source
studydeck new lecture manifest.py     # esqueleto editável (4 exemplos reais)
studydeck schema flow_diagram         # contrato + quando usar + esqueleto
studydeck imgprep work/imgs           # contrato de imagens
studydeck lint manifest.py --json     # veredicto por slide (agente)
studydeck all manifest.py aula.pptx   # lint -> render; contraste bloqueia
studydeck contrast manifest.py        # escane de contraste isolado
```

## Invariantes (o motor bloqueia, não avisa)

1. **Contraste WCAG AA em todo texto** — 4.5:1 (3.0:1 em display). Par que
   falha impede a gravação do `.pptx`.
2. **Deriva de idioma** bloqueia calço do idioma errado para o `LANG`
   configurado; termo legítimo de outro idioma vai em `ALLOW_TERMS`.
3. **Contrato por slide** — requeridos não vazios, orçamentos de caracteres,
   ajuste tipográfico e `caption`+`credit` com imagem. Nada é fabricado.

## Imagens: apoio, não conteúdo

`IMAGES.mode` = `web-only` (padrão) | `mixed` | `ai-only` | `none`.
`max_n` = `auto` (lê o source: 2 em deck curto, 4 em aula, +1 por 6 slides
acima de 12, **teto 10**) ou um inteiro. `allow_ai` / `allow_placeholder`
habilitam os marcadores `ai:` e `placeholder:`.

O motor **não baixa nem gera** imagem: fonte local é paintada; `https://`,
`ai:` e `placeholder:` viram painel rotulado. Figura com `caption` analítico
("o que se ensina") e `credit` — preenchimento decorativo é violação.

## Autoração

- `prompt.md` — prompt de restrições para enviar junto com o source (idioma,
  perfil, modo de imagem, orçamento).
- `SYSTEM_PROMPT.md` — prompt de sistema do agente autor (35 módulos, `when`,
  pegadinhas, fluxo).
- `examples/ejemplo_inflamacao.py` — deck de exemplo completo em pt-BR.

## Estrutura

```text
studydeck/
  contrast.py    WCAG: matiz, ratios, instrumentação que bloqueia a entrega
  palette.py     paleta UCP + tokens de texto derivados
  typography.py  Montserrat + estimador de ajuste
  geometry.py    lienzo 16:9, zona segura, reparto de cartões
  i18n.py        pt-BR (padrão) · es-ES · en-US + guard de deriva
  primitives.py  desenho: caixa, texto, pill, imagem
  images.py      política de imagem: modos, orçamento, propósito
  imagedata.py   contrato de arquivo (20 KB–4 MB, ≥ 300 px)
  contracts.py   orçamentos, requeridos, cardinalidades, pegadinhas  ← escritor único
  authoring.py   `when`, contrato legível, esqueleto pegável
  scaffold.py    guias e deck-mínimo de `new`
  registry.py    registro único de 35 módulos                    ← escritor único
  fixtures.py    self-test: um slide por módulo
  lint.py        contrato por slide
  render.py      montagem do .pptx, falha fechado
  manifest.py    carga de manifest + defaults
  cli.py         linha de comando
  ingest.py      outline de fonte
```

Regras estruturais como teste (`tests/test_fitness.py`): nenhum
`utils.py`, orçamentos escritos uma única vez, tetos de tamanho, imports só
para dentro, docstring em todo símbolo público, `except Exception` sem
justificativa.

## Testes

```bash
python -m pytest -q          # 237 testes
studydeck check              # 35/35 + contraste
studydeck pytest -q           # oraculo visual: tokens, piso, limites, composicao
```