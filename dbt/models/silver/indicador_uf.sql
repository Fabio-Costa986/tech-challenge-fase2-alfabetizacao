-- Indicador oficial por UF (grão da fonte: ano x UF x rede).
WITH base AS (
  SELECT
    CAST(ano AS INT64) AS ano,
    UPPER(TRIM(sigla_uf)) AS sigla_uf,
    TRIM(CAST(serie AS STRING)) AS serie_codigo,
    TRIM(CAST(rede AS STRING)) AS rede_codigo,
    CAST(taxa_alfabetizacao AS FLOAT64) AS taxa_alfabetizacao,
    CAST(media_portugues AS FLOAT64) AS media_portugues,
    {% for i in range(9) -%}
    CAST(proporcao_aluno_nivel_{{ i }} AS FLOAT64) AS proporcao_aluno_nivel_{{ i }},
    {% endfor -%}
    _bronze_run_id
  FROM {{ bronze('uf') }}
),
serie AS (
  SELECT * FROM {{ dict_lookup('serie', 'uf') }}
)
SELECT
  b.ano,
  b.sigla_uf,
  u.regiao,
  b.serie_codigo,
  CASE WHEN b.serie_codigo IS NULL THEN NULL ELSE COALESCE(s.valor, 'DESCONHECIDO') END AS serie,
  b.rede_codigo,
  r.descricao_dicionario AS rede,
  CASE WHEN b.rede_codigo IS NULL THEN NULL ELSE COALESCE(r.rede_canonica, 'DESCONHECIDO') END AS rede_canonica,
  b.taxa_alfabetizacao,
  b.media_portugues,
  {% for i in range(9) -%}
  b.proporcao_aluno_nivel_{{ i }},
  {% endfor -%}
  b._bronze_run_id,
  {{ lineage_columns() }}
FROM base b
LEFT JOIN serie s ON s.chave = b.serie_codigo
LEFT JOIN {{ ref('rede_map') }} r ON r.tabela = 'uf' AND r.valor_origem = b.rede_codigo
LEFT JOIN {{ ref('uf_ibge') }} u ON u.sigla_uf = b.sigla_uf
