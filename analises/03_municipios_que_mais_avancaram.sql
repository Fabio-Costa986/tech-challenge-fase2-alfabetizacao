-- Municípios que mais avançaram na alfabetização de 2023 para 2024 (rede municipal)
-- e se o avanço foi suficiente para atingir a meta pactuada de 2024.
-- Rode no console do BigQuery com o projeto do pipeline selecionado (lê só a Gold publicada).

WITH serie AS (
  SELECT
    id_municipio,
    nome_municipio,
    sigla_uf,
    regiao,
    MAX(IF(ano = 2023, taxa_alfabetizacao, NULL)) AS taxa_2023,
    MAX(IF(ano = 2024, taxa_alfabetizacao, NULL)) AS taxa_2024,
    MAX(IF(ano = 2024, alunos_avaliados, NULL)) AS avaliados_2024
  FROM gold.fct_alfabetizacao_municipio
  WHERE rede_canonica = 'municipal'
  GROUP BY id_municipio, nome_municipio, sigla_uf, regiao
),
meta AS (
  SELECT id_local AS id_municipio, meta_pactuada_pct AS meta_2024, status_meta
  FROM gold.meta_vs_resultado
  WHERE nivel = 'MUN' AND rede_canonica = 'municipal' AND ano = 2024
)
SELECT
  s.nome_municipio,
  s.sigla_uf,
  s.regiao,
  ROUND(s.taxa_2023, 1) AS taxa_2023,
  ROUND(s.taxa_2024, 1) AS taxa_2024,
  ROUND(s.taxa_2024 - s.taxa_2023, 1) AS avanco_pp,
  ROUND(m.meta_2024, 1) AS meta_pactuada_2024,
  COALESCE(m.status_meta, 'SEM_META') AS situacao_2024,
  s.avaliados_2024
FROM serie s
LEFT JOIN meta m USING (id_municipio)
WHERE s.taxa_2023 IS NOT NULL
  AND s.taxa_2024 IS NOT NULL
  AND s.avaliados_2024 >= 100          -- evita municípios muito pequenos, onde a taxa oscila por acaso
ORDER BY avanco_pp DESC
LIMIT 20;
