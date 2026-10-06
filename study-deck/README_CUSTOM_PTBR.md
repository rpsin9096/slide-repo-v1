# Caso Clínico 09 — deck customizado pt-BR

Entrega construída sobre o motor **StudyDeck v2 / deck v-1**, em 16:9, com a paleta institucional UCP e tipografia Montserrat.

## Arquivos

- `caso09_pancreatite_biliar_ptbr.pptx` — deck editável com 12 slides.
- `manifest_ptbr.py` — conteúdo e configuração do deck.
- `assets/ai_obstrucao_biliar.png` — ilustração de apoio gerada por IA para o mecanismo biliar.

## Imagens reservadas

Os slides 7 e 8 mantêm deliberadamente os marcadores `placeholder:` para receber as duas imagens obrigatórias do PPTX original:

1. macroscopia da peça;
2. microfotografia H&E.

Ao receber o arquivo original, substituir os dois marcadores por `.png`/`.jpg` locais e atualizar os créditos no manifest. O orçamento de imagens está em `max_n: 'auto'`: três slots são usados nesta versão, sendo duas reservas oficiais e uma imagem de apoio gerada por IA.

## Validação

- 12 slides;
- idioma `pt-BR`;
- sem rótulos de disciplinas nos títulos;
- lint de contrato aprovado;
- contraste WCAG aprovado em 0 violações.

Para reconstruir com o motor, instale as dependências de `pyproject.toml` e execute:

```bash
PYTHONPATH=study-deck python -m studydeck.cli all \
  study-deck/manifest_ptbr.py \
  study-deck/caso09_pancreatite_biliar_ptbr.pptx
```
