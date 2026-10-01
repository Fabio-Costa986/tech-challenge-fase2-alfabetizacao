-- Resultado OFICIAL unificado por (nível, local, rede, ano).
-- Fonte principal: tabelas de indicador (municipio, uf). As tabelas de meta também publicam a taxa
-- observada (`taxa_alfabetizacao`) e, no profiling, trazem um ano a mais (2025) que as tabelas de
-- indicador (até 2024). Elas completam SOMENTE as combinações ausentes; `fonte_resultado` registra
-- de onde veio cada número. O nível Brasil existe apenas na tabela de meta.
-- A concordância entre as duas fontes nos anos em comum é testada por
-- assert_consistencia_meta_vs_indicador_* (Silver).
WITH indicador AS (
  SELECT 'MUN' AS nivel, id_municipio AS id_local, nome_municipio AS nome_local, sigla_uf,
         rede_canonica, ano, taxa_alfabetizacao, 'tabela_indicador' AS fonte_resultado
  FROM {{ ref('fct_alfabetizacao_municipio') }}
  UNION ALL
  SELECT 'UF', sigla_uf, sigla_uf, sigla_uf, rede_canonica, ano, taxa_alfabetizacao, 'tabela_indicador'
  FROM {{ ref('fct_alfabetizacao_uf') }}
),
complemento AS (
  SELECT
    m.nivel,
    m.id_local,
    CASE m.nivel WHEN 'BR' THEN 'Brasil' WHEN 'UF' THEN m.id_local ELSE d.nome_municipio END AS nome_local,
    m.sigla_uf,
    m.rede_canonica,
    m.ano,
    m.taxa_alfabetizacao,
    'tabela_meta' AS fonte_resultado
  FROM {{ ref('meta_linha_base') }} m
  LEFT JOIN {{ ref('diretorio_municipio') }} d ON m.nivel = 'MUN' AND d.id_municipio = m.id_local
  WHERE m.taxa_alfabetizacao IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM indicador i
      WHERE i.nivel = m.nivel AND i.id_local = m.id_local
        AND i.rede_canonica = m.rede_canonica AND i.ano = m.ano)
)
SELECT *, {{ lineage_columns() }} FROM indicador
UNION ALL
SELECT *, {{ lineage_columns() }} FROM complemento
