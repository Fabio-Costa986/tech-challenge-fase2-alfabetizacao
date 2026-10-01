# ADR-007: Meta pactuada x leitura de universalização

**Status:** aceita

- Toda distância até a meta usa a **meta pactuada da fonte** (`meta_alfabetizacao_<ano>`; na rede
  pública, 2030 = 80). Ela está em `gold.meta_vs_resultado`, com `tipo_meta = 'PACTUADA'`.
- A leitura de universalização (100% até 2030) existe **somente** em `gold.cenario_universalizacao`, com a
  coluna `leitura = 'ASPIRACIONAL ...'`. A meta pactuada de 2030 aparece lá apenas como coluna de
  contraste, com nome explícito (`meta_pactuada_2030_pct`).
- A projeção linear até 2030 (`gold.evolucao_temporal`) é rotulada como **cenário**, com
  `n_pontos_serie` visível, porque 2 ou 3 anos de série não sustentam uma previsão.
