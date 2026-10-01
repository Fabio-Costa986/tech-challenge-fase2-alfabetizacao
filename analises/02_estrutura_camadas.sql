-- Estrutura do banco nas camadas bronze, silver, gold e ops.
-- Rode no console do BigQuery (projeto do pipeline selecionado, região US) ou com:
--   python -m alfab profile --sql analises/02_estrutura_camadas.sql --saida evidencias/estrutura
-- Cada bloco "-- name:" vira um CSV. As consultas leem só metadados (custo mínimo).

-- name: 01_tabelas_por_camada
-- Visão geral: o que existe em cada camada, tipo, linhas, tamanho, última modificação e descrição.
-- (External tables da Bronze mostram 0 linhas: os dados estão em Parquet no GCS; ver bloco 06.)
WITH tabelas AS (
  SELECT 'bronze' AS camada, 1 AS ordem, table_id, type, row_count, size_bytes, TIMESTAMP_MILLIS(last_modified_time) AS modificada FROM bronze.__TABLES__
  UNION ALL SELECT 'silver' AS camada, 2 AS ordem, table_id, type, row_count, size_bytes, TIMESTAMP_MILLIS(last_modified_time) AS modificada FROM silver.__TABLES__
  UNION ALL SELECT 'gold_staging' AS camada, 3 AS ordem, table_id, type, row_count, size_bytes, TIMESTAMP_MILLIS(last_modified_time) AS modificada FROM gold_staging.__TABLES__
  UNION ALL SELECT 'gold' AS camada, 4 AS ordem, table_id, type, row_count, size_bytes, TIMESTAMP_MILLIS(last_modified_time) AS modificada FROM gold.__TABLES__
  UNION ALL SELECT 'ops' AS camada, 5 AS ordem, table_id, type, row_count, size_bytes, TIMESTAMP_MILLIS(last_modified_time) AS modificada FROM ops.__TABLES__
),
descricoes AS (
  SELECT table_schema, table_name, option_value FROM bronze.INFORMATION_SCHEMA.TABLE_OPTIONS WHERE option_name = 'description'
  UNION ALL SELECT table_schema, table_name, option_value FROM silver.INFORMATION_SCHEMA.TABLE_OPTIONS WHERE option_name = 'description'
  UNION ALL SELECT table_schema, table_name, option_value FROM gold_staging.INFORMATION_SCHEMA.TABLE_OPTIONS WHERE option_name = 'description'
  UNION ALL SELECT table_schema, table_name, option_value FROM gold.INFORMATION_SCHEMA.TABLE_OPTIONS WHERE option_name = 'description'
  UNION ALL SELECT table_schema, table_name, option_value FROM ops.INFORMATION_SCHEMA.TABLE_OPTIONS WHERE option_name = 'description'
)
SELECT
  t.camada,
  t.table_id AS tabela,
  CASE t.type WHEN 1 THEN 'TABELA' WHEN 2 THEN 'VIEW' WHEN 3 THEN 'EXTERNA (Parquet no GCS)' ELSE CAST(t.type AS STRING) END AS tipo,
  t.row_count AS linhas,
  ROUND(t.size_bytes / POW(1024, 2), 2) AS tamanho_mib,
  t.modificada,
  d.option_value AS descricao
FROM tabelas t
LEFT JOIN descricoes d ON d.table_schema = t.camada AND d.table_name = t.table_id
ORDER BY t.ordem, t.table_id;

-- name: 02_colunas_bronze
SELECT table_name AS tabela, ordinal_position AS pos, column_name AS coluna, data_type AS tipo,
       is_partitioning_column AS particao
FROM bronze.INFORMATION_SCHEMA.COLUMNS
ORDER BY table_name, ordinal_position;

-- name: 03_colunas_silver
SELECT table_name AS tabela, ordinal_position AS pos, column_name AS coluna, data_type AS tipo,
       is_partitioning_column AS particao, clustering_ordinal_position AS cluster_pos
FROM silver.INFORMATION_SCHEMA.COLUMNS
ORDER BY table_name, ordinal_position;

-- name: 04_colunas_gold
SELECT table_name AS tabela, ordinal_position AS pos, column_name AS coluna, data_type AS tipo,
       is_partitioning_column AS particao, clustering_ordinal_position AS cluster_pos
FROM gold.INFORMATION_SCHEMA.COLUMNS
ORDER BY table_name, ordinal_position;

-- name: 05_colunas_ops
SELECT table_name AS tabela, ordinal_position AS pos, column_name AS coluna, data_type AS tipo,
       is_partitioning_column AS particao, clustering_ordinal_position AS cluster_pos
FROM ops.INFORMATION_SCHEMA.COLUMNS
ORDER BY table_name, ordinal_position;

-- name: 06_snapshots_bronze
-- Histórico da Bronze: cada linha é um snapshot imutável no GCS (um caminho por execução).
SELECT entity AS entidade, run_id, source_last_modified AS fonte_modificada_em,
       exported_rows AS linhas_exportadas, bronze_uri AS caminho_gcs, ingested_at AS ingerido_em
FROM ops.source_watermarks
ORDER BY entidade, ingerido_em;

-- name: 07_grao_das_tabelas_gold
-- Grão (chave) de cada tabela analítica, conferido contra a contagem real de linhas.
SELECT 'fct_alfabetizacao_municipio' AS tabela, 'ano, id_municipio, rede_codigo' AS grao, COUNT(*) AS linhas,
       COUNT(DISTINCT FORMAT('%d|%s|%s', ano, id_municipio, rede_codigo)) AS chaves_distintas
FROM gold.fct_alfabetizacao_municipio
UNION ALL
SELECT 'fct_alfabetizacao_uf', 'ano, sigla_uf, rede_codigo', COUNT(*),
       COUNT(DISTINCT FORMAT('%d|%s|%s', ano, sigla_uf, rede_codigo))
FROM gold.fct_alfabetizacao_uf
UNION ALL
SELECT 'fct_alfabetizacao_brasil', 'ano, rede_canonica', COUNT(*),
       COUNT(DISTINCT FORMAT('%d|%s', ano, rede_canonica))
FROM gold.fct_alfabetizacao_brasil
UNION ALL
SELECT 'resultado_oficial', 'nivel, id_local, rede_canonica, ano', COUNT(*),
       COUNT(DISTINCT FORMAT('%s|%s|%s|%d', nivel, id_local, rede_canonica, ano))
FROM gold.resultado_oficial
UNION ALL
SELECT 'meta_vs_resultado', 'nivel, id_local, rede_canonica, ano', COUNT(*),
       COUNT(DISTINCT FORMAT('%s|%s|%s|%d', nivel, id_local, rede_canonica, ano))
FROM gold.meta_vs_resultado
UNION ALL
SELECT 'ml_features_municipio', 'id_municipio, rede_canonica, ano_referencia', COUNT(*),
       COUNT(DISTINCT FORMAT('%s|%s|%d', id_municipio, rede_canonica, ano_referencia))
FROM gold.ml_features_municipio
ORDER BY tabela;
