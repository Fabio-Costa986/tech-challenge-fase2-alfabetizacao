-- Evolução do indicador oficial por local e rede, com variação ano a ano.
-- A projeção até 2030 é um CENÁRIO de tendência linear entre o primeiro e o último ponto observado,
-- não uma previsão: com 2-3 anos de série ela é frágil, e a coluna n_pontos_serie deixa isso visível.
WITH serie AS (
  SELECT 'MUN' AS nivel, id_municipio AS id_local, sigla_uf, rede_canonica, ano, taxa_alfabetizacao
  FROM {{ ref('fct_alfabetizacao_municipio') }}
  UNION ALL
  SELECT 'UF', sigla_uf, sigla_uf, rede_canonica, ano, taxa_alfabetizacao FROM {{ ref('fct_alfabetizacao_uf') }}
  UNION ALL
  SELECT 'BR', 'BR', NULL, rede_canonica, ano, taxa_oficial FROM {{ ref('fct_alfabetizacao_brasil') }}
),
com_janela AS (
  SELECT
    *,
    LAG(taxa_alfabetizacao) OVER w AS taxa_ano_anterior,
    LAG(ano) OVER w AS ano_anterior,
    COUNTIF(taxa_alfabetizacao IS NOT NULL) OVER p AS n_pontos_serie,
    FIRST_VALUE(IF(taxa_alfabetizacao IS NULL, NULL, ano) IGNORE NULLS) OVER pw AS ano_primeiro,
    FIRST_VALUE(taxa_alfabetizacao IGNORE NULLS) OVER pw AS taxa_primeira,
    LAST_VALUE(IF(taxa_alfabetizacao IS NULL, NULL, ano) IGNORE NULLS) OVER pw AS ano_ultimo,
    LAST_VALUE(taxa_alfabetizacao IGNORE NULLS) OVER pw AS taxa_ultima
  FROM serie
  WINDOW
    w AS (PARTITION BY nivel, id_local, rede_canonica ORDER BY ano),
    p AS (PARTITION BY nivel, id_local, rede_canonica),
    pw AS (PARTITION BY nivel, id_local, rede_canonica ORDER BY ano
           ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
)
SELECT
  nivel, id_local, sigla_uf, rede_canonica, ano, taxa_alfabetizacao,
  taxa_ano_anterior,
  IF(ano_anterior = ano - 1, taxa_alfabetizacao - taxa_ano_anterior, NULL) AS variacao_pp_ano_anterior,
  n_pontos_serie,
  IF(ano = ano_ultimo AND n_pontos_serie >= 2,
     SAFE_DIVIDE(taxa_ultima - taxa_primeira, ano_ultimo - ano_primeiro), NULL) AS tendencia_pp_por_ano,
  IF(ano = ano_ultimo AND n_pontos_serie >= 2,
     LEAST(100, GREATEST(0, taxa_ultima
       + SAFE_DIVIDE(taxa_ultima - taxa_primeira, ano_ultimo - ano_primeiro) * (2030 - ano_ultimo))),
     NULL) AS cenario_tendencia_linear_2030,
  'CENARIO: tendência linear com poucos pontos; não é previsão' AS nota_cenario,
  {{ lineage_columns() }}
FROM com_janela
