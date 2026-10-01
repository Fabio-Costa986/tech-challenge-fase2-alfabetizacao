-- Resultado x meta PACTUADA (fonte oficial), nos níveis Brasil, UF e município.
-- Regras:
--  * compara apenas o MESMO recorte: mesma rede canônica e ano do resultado = ano da meta;
--  * estados explícitos: ATINGIU | NAO_ATINGIU | SEM_META | SEM_RESULTADO | AGUARDANDO_RESULTADO
--    (ausência de meta nunca é "não atingiu"; nulo nunca vira zero);
--  * a leitura de universalização (100%) NÃO aparece aqui: ver cenario_universalizacao.
WITH meta AS (
  -- se a fonte republicar a trajetória com outra linha de base, vale a mais recente
  SELECT nivel, id_local, rede_canonica, ano_meta AS ano, meta_pct, ano_referencia
  FROM {{ ref('meta_trajetoria') }}
  QUALIFY ROW_NUMBER() OVER (PARTITION BY nivel, id_local, rede_canonica, ano_meta
                             ORDER BY ano_referencia DESC) = 1
),
resultado AS (
  SELECT nivel, id_local, nome_local, sigla_uf, rede_canonica, ano, taxa_alfabetizacao, fonte_resultado
  FROM {{ ref('resultado_oficial') }}
),
-- só o universo comparável: níveis/redes que TÊM trajetória pactuada, nos anos da trajetória
resultado_comparavel AS (
  SELECT r.* FROM resultado r
  WHERE r.ano IN UNNEST({{ var('anos_meta') }})
    AND EXISTS (SELECT 1 FROM meta m WHERE m.nivel = r.nivel AND m.rede_canonica = r.rede_canonica)
),
ultimo_ano_resultado AS (
  SELECT nivel, MAX(ano) AS ano_max FROM resultado GROUP BY nivel
),
juntos AS (
  SELECT
    COALESCE(r.nivel, m.nivel) AS nivel,
    COALESCE(r.id_local, m.id_local) AS id_local,
    r.nome_local,
    r.sigla_uf,
    COALESCE(r.rede_canonica, m.rede_canonica) AS rede_canonica,
    COALESCE(r.ano, m.ano) AS ano,
    r.taxa_alfabetizacao,
    r.fonte_resultado,
    m.meta_pct AS meta_pactuada_pct,
    m.ano_referencia AS ano_referencia_meta
  FROM resultado_comparavel r
  FULL OUTER JOIN meta m
    ON m.nivel = r.nivel AND m.id_local = r.id_local AND m.rede_canonica = r.rede_canonica AND m.ano = r.ano
)
SELECT
  j.nivel,
  j.id_local,
  COALESCE(j.nome_local, dm.nome_municipio, IF(j.nivel = 'UF', j.id_local, NULL)) AS nome_local,
  COALESCE(j.sigla_uf, dm.sigla_uf, IF(j.nivel = 'UF', j.id_local, NULL)) AS sigla_uf,
  j.rede_canonica,
  j.ano,
  j.taxa_alfabetizacao,
  j.fonte_resultado,
  j.meta_pactuada_pct,
  j.taxa_alfabetizacao - j.meta_pactuada_pct AS gap_pp,
  CASE
    WHEN j.meta_pactuada_pct IS NULL THEN 'SEM_META'
    WHEN j.taxa_alfabetizacao IS NULL AND j.ano > u.ano_max THEN 'AGUARDANDO_RESULTADO'
    WHEN j.taxa_alfabetizacao IS NULL THEN 'SEM_RESULTADO'
    WHEN j.taxa_alfabetizacao >= j.meta_pactuada_pct THEN 'ATINGIU'
    ELSE 'NAO_ATINGIU'
  END AS status_meta,
  'PACTUADA' AS tipo_meta,
  j.ano_referencia_meta,
  {{ lineage_columns() }}
FROM juntos j
LEFT JOIN ultimo_ano_resultado u ON u.nivel = j.nivel
LEFT JOIN {{ ref('diretorio_municipio') }} dm ON j.nivel = 'MUN' AND dm.id_municipio = j.id_local
