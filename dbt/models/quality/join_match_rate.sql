{{ config(
    materialized='incremental',
    on_schema_change='append_new_columns',
    partition_by={'field': 'measured_at', 'data_type': 'timestamp', 'granularity': 'day'},
) }}

-- Taxa de correspondência de CADA junção da pipeline, medida a cada execução e ACUMULADA (append).
-- Um join sem par não dá erro, devolve nulo. Aqui o nulo vira número, e o número tem limiar
-- (seeds/join_thresholds.csv). Os testes assert_join_match_* reprovam a execução corrente.
-- total = 0 também reprova: significa que as chaves não falam a mesma língua (ex.: rede).

WITH
anos_meta AS (SELECT ano FROM UNNEST({{ var('anos_meta') }}) AS ano),

m1 AS (
  SELECT 'indicador_municipio__diretorio' AS join_name, COUNT(*) AS total,
         COUNTIF(d.id_municipio IS NOT NULL) AS matched
  FROM {{ ref('indicador_municipio') }} i
  LEFT JOIN {{ ref('diretorio_municipio') }} d USING (id_municipio)
),
m2 AS (
  SELECT 'meta_municipio__diretorio', COUNT(*), COUNTIF(d.id_municipio IS NOT NULL)
  FROM {{ ref('meta_linha_base') }} m
  LEFT JOIN {{ ref('diretorio_municipio') }} d ON d.id_municipio = m.id_local
  WHERE m.nivel = 'MUN'
),
m3 AS (
  SELECT 'alunos__diretorio', COUNT(*), COUNTIF(d.id_municipio IS NOT NULL)
  FROM (SELECT DISTINCT ano, id_municipio FROM {{ ref('alunos') }}) a
  LEFT JOIN {{ ref('diretorio_municipio') }} d USING (id_municipio)
),
m4 AS (
  SELECT 'indicador_uf__uf', COUNT(*), COUNTIF(u.sigla_uf IS NOT NULL)
  FROM {{ ref('indicador_uf') }} i
  LEFT JOIN {{ ref('uf_ibge') }} u USING (sigla_uf)
),
m5 AS (
  -- resultado UF no recorte (rede) em que existe meta UF, nos anos da trajetória
  SELECT 'indicador_uf__meta_uf', COUNT(*), COUNTIF(m.id_local IS NOT NULL)
  FROM {{ ref('indicador_uf') }} i
  LEFT JOIN {{ ref('meta_trajetoria') }} m
    ON m.nivel = 'UF' AND m.id_local = i.sigla_uf AND m.rede_canonica = i.rede_canonica AND m.ano_meta = i.ano
  WHERE i.ano IN (SELECT ano FROM anos_meta)
    AND i.rede_canonica IN (SELECT DISTINCT rede_canonica FROM {{ ref('meta_trajetoria') }} WHERE nivel = 'UF')
),
m6 AS (
  SELECT 'indicador_municipio__meta_municipio', COUNT(*), COUNTIF(m.id_local IS NOT NULL)
  FROM {{ ref('indicador_municipio') }} i
  LEFT JOIN {{ ref('meta_trajetoria') }} m
    ON m.nivel = 'MUN' AND m.id_local = i.id_municipio AND m.rede_canonica = i.rede_canonica AND m.ano_meta = i.ano
  WHERE i.ano IN (SELECT ano FROM anos_meta)
    AND i.rede_canonica IN (SELECT DISTINCT rede_canonica FROM {{ ref('meta_trajetoria') }} WHERE nivel = 'MUN')
),
m7 AS (
  -- grupos do microdado (ano, UF, recorte) que encontram o indicador oficial do mesmo recorte
  SELECT 'alunos__indicador_uf', COUNT(*), COUNTIF(i.sigla_uf IS NOT NULL)
  FROM (
    SELECT DISTINCT a.ano, a.sigla_uf, rr.recorte
    FROM {{ ref('alunos') }} a
    JOIN {{ ref('rede_recortes') }} rr ON rr.componente = a.rede_canonica
    WHERE a.avaliado
      AND rr.recorte IN (SELECT DISTINCT rede_canonica FROM {{ ref('indicador_uf') }})
  ) g
  LEFT JOIN {{ ref('indicador_uf') }} i
    ON i.ano = g.ano AND i.sigla_uf = g.sigla_uf AND i.rede_canonica = g.recorte AND i.taxa_alfabetizacao IS NOT NULL
),
medidas AS (
  SELECT * FROM m1 UNION ALL SELECT * FROM m2 UNION ALL SELECT * FROM m3 UNION ALL SELECT * FROM m4
  UNION ALL SELECT * FROM m5 UNION ALL SELECT * FROM m6 UNION ALL SELECT * FROM m7
)
SELECT
  m.join_name,
  m.total,
  m.matched,
  SAFE_DIVIDE(m.matched, m.total) AS match_rate,
  t.min_rate,
  t.severidade,
  t.justificativa,
  (m.total = 0 OR SAFE_DIVIDE(m.matched, m.total) < t.min_rate) AS reprovado,
  '{{ var("run_id") }}' AS run_id,
  '{{ var("fault_injection") }}' AS fault_injection,
  CURRENT_TIMESTAMP() AS measured_at
FROM medidas m
JOIN {{ ref('join_thresholds') }} t USING (join_name)
