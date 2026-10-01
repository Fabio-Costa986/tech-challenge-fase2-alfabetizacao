-- LEITURA ASPIRACIONAL: universalização da alfabetização (100%) até 2030.
-- Fica isolada nesta tabela, com nome próprio, para nunca se misturar à meta PACTUADA da fonte
-- (meta_alfabetizacao_2030 = 80 na rede pública), usada em meta_vs_resultado.
-- A meta pactuada aparece aqui só como coluna de contraste, nomeada explicitamente.
WITH ultimo AS (
  SELECT nivel, id_local, sigla_uf, rede_canonica, ano, taxa_alfabetizacao
  FROM {{ ref('evolucao_temporal') }}
  WHERE taxa_alfabetizacao IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY nivel, id_local, rede_canonica ORDER BY ano DESC) = 1
),
meta_2030 AS (
  SELECT nivel, id_local, rede_canonica, meta_pct AS meta_pactuada_2030_pct
  FROM {{ ref('meta_trajetoria') }}
  WHERE ano_meta = 2030
  QUALIFY ROW_NUMBER() OVER (PARTITION BY nivel, id_local, rede_canonica ORDER BY ano_referencia DESC) = 1
)
SELECT
  u.nivel, u.id_local, u.sigla_uf, u.rede_canonica,
  u.ano AS ano_ultimo_resultado,
  u.taxa_alfabetizacao AS taxa_ultimo_resultado,
  100.0 AS alvo_aspiracional_pct,
  100.0 - u.taxa_alfabetizacao AS distancia_universalizacao_pp,
  m.meta_pactuada_2030_pct,
  m.meta_pactuada_2030_pct - u.taxa_alfabetizacao AS distancia_meta_pactuada_2030_pp,
  'ASPIRACIONAL (universalização). Não é a meta pactuada.' AS leitura,
  {{ lineage_columns() }}
FROM ultimo u
LEFT JOIN meta_2030 m USING (nivel, id_local, rede_canonica)
