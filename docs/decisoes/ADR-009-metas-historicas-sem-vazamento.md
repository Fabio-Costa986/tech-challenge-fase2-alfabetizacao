# ADR-009: Sem meta de t+1 no treinamento sem data historica comprovada

**Status:** aceita pelo grupo em 28/10/2026; implementada em codigo, pendente de nova validacao em GCP.

## Contexto

A fonte `meta_alfabetizacao_municipio` guarda `ano` (ano de referencia do
indicador) e colunas `meta_alfabetizacao_2024...2030`. A Silver
`meta_trajetoria` publica `ano_referencia`, `ano_meta` e `meta_pct`, **mas nao
conta com a data de publicacao de cada revisao da meta**.

Antes, `gold.ml_features_municipio` escolhia a versao mais recente de cada
meta (`ORDER BY ano_referencia DESC`) para produzir a feature de `t+1`.
Uma versao mais recente pode ter se tornado publica somente depois do ano
historico t, o que constitui **risco de vazamento temporal**.
`ano_referencia` nao deve ser interpretado como `data_publicacao`.

## Decisao

1. Remover da base `gold.ml_features_municipio` a coluna
   `feat_meta_pactuada_t_mais_1`, o CTE `meta` e o join correspondente.
   **Nao foi localizada evidencia versionada de data de publicacao por versao**
   nas fontes ingeridas. Nenhuma data foi presumida ou fabricada.
2. Nao remover as metas de `silver.meta_trajetoria`, `gold.meta_vs_resultado`
   ou `gold.cenario_universalizacao`: elas continuam validas para analise
   descritiva de resultados/metas, mas esse uso e diferente de previsao as-of.
3. Tornar bloqueante a reintroducao acidental da feature sem validacao da
   proveniencia: `assert_ml_sem_vazamento` confere o schema da Gold staging.
4. Quando houver fonte primaria verificavel para cada publicacao, registrar
   **data e fonte da publicacao, versao, universo/rede/local, ano_meta e
   disponibilidade no corte t**, e implementar um as-of join (`data_publicacao
   <= data_corte_t`) em uma **nova alteracao e ADR**, com casos de revisao
   tardia e testes bloqueantes. Nao usar `ano_referencia <= t` como substituto.
5. Manter historico de snapshots antigos intacto como evidencia da execucao
   anterior, mas **nao usa-los para treinamento historico**: o snapshot
   `ml_features_municipio_fase3_20261001` e o Parquet de 01/10/2026 foram
   exportados antes desta decisao. Apos deploy e reexecucao aprovados, gerar
   um **novo export** e conferir o schema real antes de usa-lo na Fase 3.

## Justificativa e trade-off

Escolhemos menor quantidade de features com integridade temporal verificavel
em vez de uma variavel potencialmente vazada. Isso pode reduzir sinal
preditivo, mas evita validar artificialmente uma previsao que dispunha de
informacao indisponivel no periodo simulado.

## Codigo / testes / aceite

- [dbt/models/gold/ml_features_municipio.sql](../../dbt/models/gold/ml_features_municipio.sql): sem meta futura.
- [dbt/tests/singular/assert_ml_sem_vazamento.sql](../../dbt/tests/singular/assert_ml_sem_vazamento.sql): bloqueia nome proibido no schema.
- Confirmar no `gold_staging.ml_features_municipio` e depois na Gold publicada
  ausencia da coluna antiga; confirmar que `gold.meta_vs_resultado` preserva
  as metas historicas.
- Registrar novo `run_id` e identificador do novo export; nao sobrescrever
  evidencia historica. Antes de substituir um diretorio inteiro, conferir o
  historico de commits da equipe.

**Evidencia:** revisao estatica do schema disponivel no RAR recebido; sem
consulta remota ao historico de publicacoes. Ver
[roteiro de validacao](../validacao_ajustes_silver_gold.md).
