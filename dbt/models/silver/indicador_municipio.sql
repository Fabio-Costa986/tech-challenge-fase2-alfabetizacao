{{ config(cluster_by=['sigla_uf', 'id_municipio']) }}

-- Indicador oficial por município (grão da fonte: ano x município x rede).
WITH base AS (
  SELECT
    CAST(ano AS INT64) AS ano,
    LPAD(TRIM(CAST(id_municipio AS STRING)), 7, '0') AS id_municipio,
    TRIM(CAST(serie AS STRING)) AS serie_codigo,
    TRIM(CAST(rede AS STRING)) AS rede_codigo,
    -- nulo preservado: "não sei" não vira zero
    CAST(taxa_alfabetizacao AS FLOAT64) AS taxa_alfabetizacao,
    CAST(media_portugues AS FLOAT64) AS media_portugues,
    {% for i in range(9) -%}
    CAST(proporcao_aluno_nivel_{{ i }} AS FLOAT64) AS proporcao_aluno_nivel_{{ i }},
    {% endfor -%}
    _bronze_run_id
  FROM {{ bronze('municipio') }}
),
serie AS (
  SELECT * FROM {{ dict_lookup('serie', 'municipio') }}
),
final AS (
  SELECT
    b.ano,
    b.id_municipio,
    d.sigla_uf,
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
  LEFT JOIN {{ ref('rede_map') }} r ON r.tabela = 'municipio' AND r.valor_origem = b.rede_codigo
  LEFT JOIN {{ ref('diretorio_municipio') }} d ON d.id_municipio = b.id_municipio
)
SELECT * FROM final
{% if var('fault_injection') == 'duplicate_keys' -%}
-- DEMONSTRAÇÃO DE FALHA: duplica chaves de propósito; o teste unique_combination deve bloquear a Gold
UNION ALL
SELECT * FROM final WHERE MOD(ABS(FARM_FINGERPRINT(id_municipio)), 100) = 0
{%- endif %}
