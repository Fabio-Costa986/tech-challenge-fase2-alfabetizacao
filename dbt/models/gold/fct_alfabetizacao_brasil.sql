-- Indicador nacional. O número OFICIAL vem de meta_alfabetizacao_brasil.taxa_alfabetizacao.
-- Ao lado, duas agregações das UFs para mostrar por que média simples não é o indicador:
--   taxa_ponderada_ufs  : ponderada por alunos avaliados (peso amostral) -> deve bater com o oficial
--   media_simples_ufs   : cada UF pesa igual -> nomeada como tal, NÃO é o indicador nacional
WITH ufs AS (
  SELECT
    ano, rede_canonica,
    SAFE_DIVIDE(SUM(IF(alunos_avaliados_ponderado > 0, taxa_alfabetizacao * alunos_avaliados_ponderado, 0)),
                SUM(IF(taxa_alfabetizacao IS NOT NULL, alunos_avaliados_ponderado, 0))) AS taxa_ponderada_ufs,
    AVG(taxa_alfabetizacao) AS media_simples_ufs,
    COUNTIF(taxa_alfabetizacao IS NOT NULL) AS n_ufs_com_taxa,
    COUNTIF(taxa_alfabetizacao IS NOT NULL AND alunos_avaliados_ponderado IS NULL) AS n_ufs_sem_peso
  FROM {{ ref('fct_alfabetizacao_uf') }}
  GROUP BY ano, rede_canonica
),
oficial AS (
  SELECT ano, rede_canonica, taxa_alfabetizacao AS taxa_oficial, percentual_participacao
  FROM {{ ref('meta_linha_base') }}
  WHERE nivel = 'BR'
),
micro AS (
  SELECT ano, recorte AS rede_canonica, taxa_microdado_ponderada, n_avaliados, peso_avaliados
  FROM {{ ref('agg_microdado_recorte') }}
  WHERE nivel = 'BR'
)
SELECT
  COALESCE(o.ano, u.ano) AS ano,
  COALESCE(o.rede_canonica, u.rede_canonica) AS rede_canonica,
  o.taxa_oficial,
  o.percentual_participacao,
  u.taxa_ponderada_ufs,
  u.media_simples_ufs,
  u.n_ufs_com_taxa,
  u.n_ufs_sem_peso,
  m.taxa_microdado_ponderada,
  m.n_avaliados AS alunos_avaliados,
  m.peso_avaliados AS alunos_avaliados_ponderado,
  {{ lineage_columns() }}
FROM oficial o
FULL OUTER JOIN ufs u ON u.ano = o.ano AND u.rede_canonica = o.rede_canonica
LEFT JOIN micro m ON m.ano = COALESCE(o.ano, u.ano) AND m.rede_canonica = COALESCE(o.rede_canonica, u.rede_canonica)
