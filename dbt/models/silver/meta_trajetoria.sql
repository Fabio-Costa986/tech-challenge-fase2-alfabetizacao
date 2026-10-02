-- Trajetória PACTUADA, em formato longo: uma linha por (nível, local, rede, ano da meta).
-- A fonte é larga (meta_alfabetizacao_2024 ... _2030). UNPIVOT descarta metas nulas por padrão:
-- ausência de meta vira ausência de linha e, na Gold, o estado explícito SEM_META (nunca zero).
{% set cols = [] %}{% for a in var('anos_meta') %}{% do cols.append('meta_alfabetizacao_' ~ a) %}{% endfor %}

WITH br AS (
  SELECT 'BR' AS nivel, 'BR' AS id_local, 'meta_alfabetizacao_brasil' AS tabela,
         TRIM(CAST(rede AS STRING)) AS rede_origem, CAST(ano AS INT64) AS ano_referencia,
         {{ cols | join(', ') }}
  FROM {{ bronze('meta_alfabetizacao_brasil') }}
),
uf AS (
  SELECT 'UF', UPPER(TRIM(sigla_uf)), 'meta_alfabetizacao_uf',
         TRIM(CAST(rede AS STRING)), CAST(ano AS INT64), {{ cols | join(', ') }}
  FROM {{ bronze('meta_alfabetizacao_uf') }}
),
mun AS (
  SELECT 'MUN', LPAD(TRIM(CAST(id_municipio AS STRING)), 7, '0'), 'meta_alfabetizacao_municipio',
         TRIM(CAST(rede AS STRING)), CAST(ano AS INT64), {{ cols | join(', ') }}
  FROM {{ bronze('meta_alfabetizacao_municipio') }}
),
longo AS (
  SELECT nivel, id_local, tabela, rede_origem, ano_referencia,
         CAST(SUBSTR(coluna_meta, -4) AS INT64) AS ano_meta,
         CAST(meta_pct AS FLOAT64) AS meta_pct
  FROM (SELECT * FROM br UNION ALL SELECT * FROM uf UNION ALL SELECT * FROM mun)
  UNPIVOT (meta_pct FOR coluna_meta IN ({{ cols | join(', ') }}))
)
SELECT
  l.nivel, l.id_local, l.tabela, l.rede_origem,
  CASE WHEN l.rede_origem IS NULL THEN NULL ELSE COALESCE(r.rede_canonica, 'DESCONHECIDO') END AS rede_canonica,
  l.ano_referencia, l.ano_meta, l.meta_pct,
  'PACTUADA' AS tipo_meta,
  {{ lineage_columns() }}
FROM longo l
LEFT JOIN {{ ref('rede_map') }} r ON r.tabela = l.tabela AND r.valor_origem = l.rede_origem
