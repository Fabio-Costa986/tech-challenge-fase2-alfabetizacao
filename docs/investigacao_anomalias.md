# Investigação de anomalias

> **Estado: roteiro.** Ainda não há achados registrados aqui, porque o pipeline ainda não foi executado
> na nuvem. Cada hipótese abaixo vem com a evidência que a confirma ou descarta. Ao investigar, preencher
> **Observado**, **Causa** e **Decisão** com números e `job_id`. Não registrar conclusão sem número.

## H1: o flag `alfabetizado` corresponde a proficiência ≥ 743?
- **Por que importa:** o indicador é definido pelo corte de 743 pontos. Se o flag divergir da
  proficiência, a validação cruzada falha por definição, não por erro do pipeline.
- **Evidência:** `evidencias/profiling/06_alfabetizado_vs_corte_743.csv`.
- Observado: _a preencher_ · Causa: _a preencher_ · Decisão: _a preencher_

## H2: a validação cruzada converge?
- **Evidência:** `gold.validacao_cruzada_microdado`, colunas `diff_pp`, `diff_pp_sem_peso_ERRADA`,
  `diff_pp_com_ausentes_ERRADA`.
- Se `diff_pp` estiver perto de 0 e as colunas `*_ERRADA` estiverem longe, o pipeline está certo e as
  armadilhas têm tamanho mensurável. Registrar esses tamanhos: é um resultado.
- Se `diff_pp` estiver longe de 0, testar nesta ordem: definição de avaliado (presença × preenchimento),
  recorte de rede (`rede_recortes.csv`), peso (`peso_aluno` nulo ou zero) e cobertura (`tem_microdado`).
- Observado: _a preencher_

## H3: as redes falam a mesma língua?
- **Evidência:** `evidencias/profiling/02_rede_por_tabela.csv` e `silver.rede_map` (`metodo_traducao`,
  `n_significados`).
- Esperado pela documentação da fonte: códigos nas tabelas de indicador e representação própria nas
  tabelas de meta.
- Observado: _a preencher_ · Mapeamento adicionado em `rede_sinonimos.csv`: _a preencher_

## H4: municípios com indicador e sem meta pactuada
- **Evidência:** `gold.meta_vs_resultado` com `status_meta = 'SEM_META'` no nível MUN, e
  `ops.join_match_rate` (`indicador_municipio__meta_municipio`).
- Pergunta: é falta de adesão (esperado) ou chave que não casa (erro)? Comparar com a cobertura de
  `meta_alfabetizacao_municipio` por UF.
- Observado: _a preencher_

## H5: consistência entre a tabela de meta e a tabela de indicador
- **Evidência:** testes `assert_consistencia_meta_vs_indicador_*` em `ops.dq_results`.
- Observado: _a preencher_

## H6: média simples × indicador nacional
- **Evidência:** `gold.fct_alfabetizacao_brasil` (`taxa_oficial`, `taxa_ponderada_ufs`,
  `media_simples_ufs`).
- Registrar a diferença em p.p. É o argumento numérico para nunca usar média simples.
- Observado: _a preencher_
