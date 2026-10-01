-- Dado territorial (br_bd_diretorios_brasil.municipio): referência para validar id_municipio.
SELECT
  LPAD(TRIM(CAST(id_municipio AS STRING)), 7, '0') AS id_municipio,
  nome AS nome_municipio,
  sigla_uf,
  nome_regiao AS regiao,
  CAST(capital_uf AS INT64) = 1 AS capital_uf,
  {{ lineage_columns() }}
FROM {{ bronze('diretorio_municipio') }}
