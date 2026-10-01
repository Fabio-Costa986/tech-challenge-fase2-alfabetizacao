-- Base de features para a Fase 3 (predição da taxa de alfabetização municipal em t+1).
-- Grão: município x rede x ano de referência t. Somente dado OFICIAL.
-- ANTI-VAZAMENTO:
--   * features usam apenas informação disponível em t (e a meta de t+1, pactuada antes do resultado);
--   * o alvo é a taxa em t+1; NENHUMA coluna derivada do alvo (gap, status, atingiu) existe aqui;
--   * teste assert_ml_sem_vazamento reprova se uma coluna proibida aparecer;
--   * particao: 'treino' quando o alvo é conhecido; 'inferencia' para o último ano.
WITH base AS (
  SELECT
    f.*,
    LAG(f.taxa_alfabetizacao) OVER w AS taxa_t_menos_1,
    LAG(f.ano) OVER w AS ano_t_menos_1,
    LEAD(f.taxa_alfabetizacao) OVER w AS taxa_t_mais_1,
    LEAD(f.ano) OVER w AS ano_t_mais_1
  FROM {{ ref('fct_alfabetizacao_municipio') }} f
  WHERE f.origem_dado = 'OFICIAL'
  WINDOW w AS (PARTITION BY f.id_municipio, f.rede_canonica ORDER BY f.ano)
),
meta AS (
  SELECT id_local, rede_canonica, ano_meta, meta_pct
  FROM {{ ref('meta_trajetoria') }}
  WHERE nivel = 'MUN'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY id_local, rede_canonica, ano_meta ORDER BY ano_referencia DESC) = 1
),
uf AS (
  SELECT ano, sigla_uf, rede_canonica, taxa_alfabetizacao AS taxa_uf
  FROM {{ ref('fct_alfabetizacao_uf') }}
)
SELECT
  b.id_municipio,
  b.rede_canonica,
  b.ano AS ano_referencia,
  b.sigla_uf,
  b.regiao,
  b.capital_uf,
  -- features (informação até t)
  b.taxa_alfabetizacao AS feat_taxa_t,
  IF(b.ano_t_menos_1 = b.ano - 1, b.taxa_alfabetizacao - b.taxa_t_menos_1, NULL) AS feat_variacao_pp_t,
  b.media_portugues AS feat_media_portugues_t,
  {% for n in range(9) -%}
  b.proporcao_aluno_nivel_{{ n }} AS feat_prop_nivel_{{ n }}_t,
  {% endfor -%}
  b.alunos_avaliados_ponderado AS feat_alunos_avaliados_ponderado_t,
  b.proficiencia_media_ponderada AS feat_proficiencia_media_t,
  u.taxa_uf - b.taxa_alfabetizacao AS feat_distancia_media_uf_pp_t,
  m.meta_pct AS feat_meta_pactuada_t_mais_1,
  -- alvo
  IF(b.ano_t_mais_1 = b.ano + 1, b.taxa_t_mais_1, NULL) AS alvo_taxa_t_mais_1,
  IF(b.ano_t_mais_1 = b.ano + 1, 'treino', 'inferencia') AS particao,
  {{ lineage_columns() }}
FROM base b
LEFT JOIN uf u ON u.ano = b.ano AND u.sigla_uf = b.sigla_uf AND u.rede_canonica = b.rede_canonica
LEFT JOIN meta m ON m.id_local = b.id_municipio AND m.rede_canonica = b.rede_canonica AND m.ano_meta = b.ano + 1
