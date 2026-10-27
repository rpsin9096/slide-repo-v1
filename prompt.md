# PROMPT DE RESTRIÇÕES — StudyDeck v2 (UCP-only)

Preencha os campos abaixo e envie o bloco `TAREFA` junto com o source. O motor
aplica o resto; você escolhe o essencial.

```text
## RESTRIÇÕES (preencher; sem isso valem os padrões entre colchetes)
DISCIPLINA: [ex. Fisiopatologia]              # vai em COURSE_INFO.course
INSTITUIÇÃO: [ex. UCP]                        # COURSE_INFO.institution
AUTOR: [ex. Cátedra de Fisiopatologia]        # opcional
IDIOMA: [pt-BR | es-ES | en-US]               # padrão: pt-BR
PERFIL: [short | lecture | custom]            # ritmo sugerido, não obediência
IMAGENS:
  modo: [web-only | mixed | ai-only | none]   # padrão: web-only
  max_n: [auto | 0..10]                       # padrão: auto (lê o source)
  allow_ai: [false | true]                    # padrão: false
  allow_placeholder: [false | true]           # padrão: false
RODAPÉ: [sim | não]                            # curso no rodapé
NUMERAÇÃO: [sim | não]
TERMOS EM OUTRO IDIOMA: [lista]               # latim médico, nomes próprios, títulos

## TAREFA
[cole aqui o material: notas, transcrição, capítulo, lista de imagens]
```

## O que cada escolha muda (e o que não muda)

| Campo | Efeito observável | Padrão |
|---|---|---|
| `IDIOMA` | rótulos do motor + guard de deriva (bloqueia calco do idioma errado) | `pt-BR` |
| `PERFIL` | só o guia *advisory* do `new`; nunca limita slides | `short` |
| `IMAGES.modo` | `web-only` aceita arquivo local + `https://`; `ai:` e `placeholder:` exigem `allow_*` | `web-only` |
| `IMAGES.max_n` | `auto` = 2 (`short`) / 4 (`lecture`), +1 a cada 6 slides acima de 12, teto **10** | `auto` |
| `allow_ai` / `allow_placeholder` | habilitam marcadores `ai:` e `placeholder:`; o motor **não baixa nem inventa** imagem | `false` |
| `TERMOS EM OUTRO IDIOMA` | isenta esses termos do guard de deriva (ex.: nome de droga em inglês num deck pt-BR) | `[]` |
| `RODAPÉ` / `NUMERAÇÃO` | liga/desliga o pé editorial e a numeração `NN` | ligados |

## Imagens: apoio, nunca conteúdo

1. **Toda imagem com `caption` analítico** (≥ 15 caracteres) que diga **o que se
   ensina**, não o que se vê. O lint rejeita píes vazios ("imagem de exemplo",
   "diagrama do tema").
2. **`credit` é obrigatório** com imagem. Sem crédito não há entrega.
3. **`figure` e `authority_card` exigem imagem** (a figura *é* o conteúdo, com
   pie analítico). Os demais aceitam imagem como apoio e nunca substituem texto.
4. **O motor não baixa nada.** Fonte local → paintada; `https://`, `ai:` e
   `placeholder:` → painel rotulado, sem pixels inventados. Se você quer a figura
   real, baixe você e aponte o caminho.
5. **Arquivos locais**: jpg/jpeg/png, 20 KB–4 MB, lado menor ≥ 300 px
   (`studydeck imgprep work/imgs` verifica antes do lint).

### Diagramas de livro didático (quando usar `ai:`)

`studydeck.images.textbook_prompt(assunto, 'pt-BR')` gera o prompt com a marca
UCP (`#3854CC`, `#D92A2B`, `#2B2C4A`), texto no idioma-alvo, uma mensagem visual
única e proibição de preenchimento decorativo. Cole o resultado em
`image: "ai:<descrição>"` com `allow_ai: true`.

## Sequência de trabalho

```bash
studydeck ingest fonte.md work        # 1. outline do source
studydeck new lecture manifest.py     # 2. esqueleto editável (4 exemplos reais)
studydeck schema <módulo>             # 3. contrato do módulo que for usar
studydeck lint manifest.py --json     # 4. veredicto por slide, para agente
studydeck all  manifest.py aula.pptx  # 5. lint -> render (contraste bloqueia)
```

## Três invariantes (o motor bloqueia, não avisa)

1. **Contraste WCAG AA em todo texto** — qualquer par texto/fundo abaixo de 4.5:1
   (3.0:1 em display) impede a entrega: o `.pptx` **não é salvo**.
2. **Deriva de idioma** bloqueia calço do idioma errado (`developimento` em
   deck es-ES, `the` em deck pt-BR). Isente o que for legítimo em
   `TERMOS EM OUTRO IDIOMA`.
3. **Contrato por slide** — requeridos não vazios, orçamentos de caracteres,
   ajuste tipográfico (Montserrat 100%) e pie/credito com imagem. Nada é
   fabricado para cumprir regra: o texto que falta, o autor escreve.