# ADR-002: Bronze em Parquet imutável no GCS (lakehouse)

**Status:** aceita

## Contexto
O enunciado exige que uma execução não apague a anterior e avisa sobre `WRITE_TRUNCATE`,
`CREATE OR REPLACE` e sobrescrita de partição.

## Decisão
- Cada execução que encontra a fonte alterada escreve em um caminho novo:
  `bronze/<entidade>/ingestion_date=<d>/run_id=<id>/`.
- `EXPORT DATA ... overwrite = false`: se o caminho existir, o BigQuery **falha** em vez de sobrescrever.
- Bucket com retention policy (`bronze_retention_days`): nenhum objeto pode ser apagado antes do prazo.
- External tables hive-particionadas (`bronze.<entidade>`). A Silver lê só o `run_id` mais recente, como
  literal, o que permite partition pruning.
- Formato Parquet + ZSTD; lifecycle Standard → Nearline (30 d) → Coldline (90 d).
- Streaming: `bronze.eventos_raw` é somente INSERT.

## Consequências
- Histórico auditável e barato; qualquer snapshot pode ser relido.
- Silver e Gold usam `CREATE OR REPLACE` (materialização `table` do dbt) **de propósito**: são derivadas
  e reconstruíveis a partir da Bronze.
- A retention policy não está travada (`is_locked=false`) para o ambiente acadêmico poder ser desmontado.
  Em produção, travar.
