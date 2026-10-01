-- Uma linha por (nível, local, rede, ano) das 3 tabelas de meta: a taxa de referência publicada junto
-- com a trajetória e a participação. Usada para (a) o resultado nacional oficial e (b) checar
-- consistência entre tabelas (taxa da tabela de meta x taxa da tabela de indicador).
WITH br AS (
  SELECT 'BR' AS nivel, 'BR' AS id_local, CAST(NULL AS STRING) AS sigla_uf,
         'meta_alfabetizacao_brasil' AS tabela, TRIM(CAST(rede AS STRING)) AS rede_origem,
         CAST(ano AS INT64) AS ano, CAST(taxa_alfabetizacao AS FLOAT64) AS taxa_alfabetizacao,
         CAST(percentual_participacao AS FLOAT64) AS percentual_participacao,
         CAST(NULL AS INT64) AS nivel_alfabetizacao, _bronze_run_id
  FROM {{ bronze('meta_alfabetizacao_brasil') }}
),
uf AS (
  SELECT 'UF', UPPER(TRIM(sigla_uf)), UPPER(TRIM(sigla_uf)),
         'meta_alfabetizacao_uf', TRIM(CAST(rede AS STRING)),
         CAST(ano AS INT64), CAST(taxa_alfabetizacao AS FLOAT64),
         CAST(percentual_participacao AS FLOAT64), CAST(NULL AS INT64), _bronze_run_id
  FROM {{ bronze('meta_alfabetizacao_uf') }}
),
mun AS (
  SELECT 'MUN', LPAD(TRIM(CAST(m.id_municipio AS STRING)), 7, '0'), d.sigla_uf,
         'meta_alfabetizacao_municipio', TRIM(CAST(m.rede AS STRING)),
         CAST(m.ano AS INT64), CAST(m.taxa_alfabetizacao AS FLOAT64),
         CAST(m.percentual_participacao AS FLOAT64), CAST(m.nivel_alfabetizacao AS INT64), m._bronze_run_id
  FROM {{ bronze('meta_alfabetizacao_municipio') }} m
  LEFT JOIN {{ ref('diretorio_municipio') }} d
    ON d.id_municipio = LPAD(TRIM(CAST(m.id_municipio AS STRING)), 7, '0')
),
todas AS (
  SELECT * FROM br UNION ALL SELECT * FROM uf UNION ALL SELECT * FROM mun
)
SELECT
  t.nivel, t.id_local, t.sigla_uf, t.tabela, t.rede_origem,
  CASE WHEN t.rede_origem IS NULL THEN NULL ELSE COALESCE(r.rede_canonica, 'DESCONHECIDO') END AS rede_canonica,
  t.ano, t.taxa_alfabetizacao, t.percentual_participacao, t.nivel_alfabetizacao, t._bronze_run_id,
  {{ lineage_columns() }}
FROM todas t
LEFT JOIN {{ ref('rede_map') }} r ON r.tabela = t.tabela AND r.valor_origem = t.rede_origem
