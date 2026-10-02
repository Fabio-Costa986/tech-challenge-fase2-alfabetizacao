{{ config(
    partition_by={'field': 'ano', 'data_type': 'int64', 'range': {'start': 2020, 'end': 2036, 'interval': 1}},
    cluster_by=['sigla_uf', 'id_municipio'],
) }}

-- Microdado de alunos. A UF não existe na fonte: deriva dos 2 primeiros dígitos do código IBGE.
-- `avaliado` define o DENOMINADOR do indicador: presente E caderno preenchido. Ausentes não entram.
WITH base AS (
  SELECT
    CAST(ano AS INT64) AS ano,
    LPAD(TRIM(CAST(id_municipio AS STRING)), 7, '0') AS id_municipio,
    CAST(id_escola AS STRING) AS id_escola,
    CAST(id_aluno AS STRING) AS id_aluno,
    CAST(caderno AS STRING) AS caderno,
    TRIM(CAST(serie AS STRING)) AS serie_codigo,
    TRIM(CAST(rede AS STRING)) AS rede_codigo,
    TRIM(CAST(presenca AS STRING)) AS presenca_codigo,
    TRIM(CAST(preenchimento_caderno AS STRING)) AS preenchimento_caderno_codigo,
    TRIM(CAST(alfabetizado AS STRING)) AS alfabetizado_codigo,
    CAST(proficiencia AS FLOAT64) AS proficiencia,
    CAST(peso_aluno AS FLOAT64) AS peso_aluno,
    _bronze_run_id
  FROM {{ bronze('alunos') }}
)
SELECT
  b.ano,
  b.id_municipio,
  u.sigla_uf,
  b.id_escola,
  b.id_aluno,
  b.caderno,
  b.serie_codigo,
  IF(b.serie_codigo IS NULL, NULL, COALESCE(ds.valor, 'DESCONHECIDO')) AS serie,
  b.rede_codigo,
  IF(b.rede_codigo IS NULL, NULL, COALESCE(r.rede_canonica, 'DESCONHECIDO')) AS rede_canonica,
  b.presenca_codigo,
  IF(b.presenca_codigo IS NULL, NULL, COALESCE(dp.valor, 'DESCONHECIDO')) AS presenca,
  b.preenchimento_caderno_codigo,
  IF(b.preenchimento_caderno_codigo IS NULL, NULL, COALESCE(dc.valor, 'DESCONHECIDO')) AS preenchimento_caderno,
  b.alfabetizado_codigo,
  IF(b.alfabetizado_codigo IS NULL, NULL, COALESCE(da.valor, 'DESCONHECIDO')) AS alfabetizado_descricao,
  b.presenca_codigo = '{{ var("codigo_presente") }}' AS presente,
  b.preenchimento_caderno_codigo = '{{ var("codigo_caderno_preenchido") }}' AS caderno_preenchido,
  COALESCE(b.presenca_codigo = '{{ var("codigo_presente") }}', FALSE)
    AND COALESCE(b.preenchimento_caderno_codigo = '{{ var("codigo_caderno_preenchido") }}', FALSE) AS avaliado,
  IF(b.alfabetizado_codigo IS NULL, NULL, b.alfabetizado_codigo = '{{ var("codigo_alfabetizado") }}') AS alfabetizado,
  b.proficiencia,           -- nulo preservado: ausente não é proficiência zero
  b.peso_aluno,
  b._bronze_run_id,
  {{ lineage_columns() }}
FROM base b
LEFT JOIN {{ ref('uf_ibge') }} u ON u.codigo_uf = SUBSTR(b.id_municipio, 1, 2)
LEFT JOIN {{ ref('rede_map') }} r ON r.tabela = 'alunos' AND r.valor_origem = b.rede_codigo
LEFT JOIN {{ dict_lookup('serie', 'alunos') }} ds ON ds.chave = b.serie_codigo
LEFT JOIN {{ dict_lookup('presenca', 'alunos') }} dp ON dp.chave = b.presenca_codigo
LEFT JOIN {{ dict_lookup('preenchimento_caderno', 'alunos') }} dc ON dc.chave = b.preenchimento_caderno_codigo
LEFT JOIN {{ dict_lookup('alfabetizado', 'alunos') }} da ON da.chave = b.alfabetizado_codigo
