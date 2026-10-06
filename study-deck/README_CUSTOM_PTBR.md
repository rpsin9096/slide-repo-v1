# Caso Clínico 09 — versões pt-BR e es-ES

Entrega construída sobre o motor **StudyDeck v2 / deck v-1**, em 16:9, com a paleta institucional UCP e tipografia Montserrat.

## Arquivos

- `caso09_pancreatitis_biliar_es.pptx` — **versão em espanhol para entrega**.
- `manifest_es.py` — conteúdo e configuração da versão em espanhol.
- `caso09_pancreatite_biliar_ptbr.pptx` — versão em português brasileiro, mantida como material de estudo.
- `manifest_ptbr.py` — conteúdo e configuração da versão pt-BR.
- `assets/ai_obstrucao_biliar.png` — ilustração de apoio gerada por IA para o mecanismo biliar.

## Imagens reservadas

Os slides 7 e 8 mantêm deliberadamente os marcadores `placeholder:` para receber as duas imagens obrigatórias do PPTX original:

1. macroscopia da peça;
2. microfotografia H&E.

Ao receber o arquivo original, substituir os dois marcadores nos manifests por `.png`/`.jpg` locais e atualizar os créditos. O orçamento de imagens está em `max_n: 'auto'`: três slots são usados em cada versão, sendo duas reservas oficiais e uma imagem de apoio gerada por IA.

## Validação

- 12 slides em cada idioma;
- versão de entrega em `es-ES`;
- versão de estudo em `pt-BR`;
- sem rótulos de disciplinas nos títulos;
- lint de contrato aprovado;
- contraste WCAG aprovado em 0 violações.

Para reconstruir a versão de entrega com o motor, instale as dependências de `pyproject.toml` e execute:

```bash
PYTHONPATH=study-deck python -m studydeck.cli all \
  study-deck/manifest_es.py \
  study-deck/caso09_pancreatitis_biliar_es.pptx
```
