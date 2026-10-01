-- Validação cruzada: taxa RECALCULADA do microdado (ponderada, denominador = avaliados) x taxa PUBLICADA.
-- Se convergem, ingestão, tipos, decodificação, chaves e agregação estão corretos por consequência.
-- As colunas *_ERRADA mostram quanto cada armadilha (sem peso / ausentes no denominador) desviaria.
WITH oficial AS (
  SELECT 'MUN' AS nivel, id_municipio AS id_local, sigla_uf, rede_canonica, ano, taxa_alfabetizacao AS taxa_oficial
  FROM {{ ref('indicador_municipio') }}
  UNION ALL
  SELECT 'UF', sigla_uf, sigla_uf, rede_canonica, ano, taxa_alfabetizacao FROM {{ ref('indicador_uf') }}
  UNION ALL
  SELECT 'BR', 'BR', NULL, rede_canonica, ano, taxa_alfabetizacao
  FROM {{ ref('meta_linha_base') }} WHERE nivel = 'BR'
)
SELECT
  o.nivel, o.id_local, o.sigla_uf, o.rede_canonica, o.ano,
  o.taxa_oficial,
  m.taxa_microdado_ponderada,
  m.taxa_microdado_ponderada - o.taxa_oficial AS diff_pp,
  m.taxa_microdado_sem_peso_ERRADA - o.taxa_oficial AS diff_pp_sem_peso_ERRADA,
  m.taxa_denominador_com_ausentes_ERRADA - o.taxa_oficial AS diff_pp_com_ausentes_ERRADA,
  m.n_registros, m.n_avaliados, m.peso_avaliados,
  m.n_avaliados IS NOT NULL AS tem_microdado,
  {{ lineage_columns() }}
FROM oficial o
LEFT JOIN {{ ref('agg_microdado_recorte') }} m
  ON m.nivel = o.nivel AND m.id_local = o.id_local AND m.ano = o.ano AND m.recorte = o.rede_canonica
WHERE o.taxa_oficial IS NOT NULL
