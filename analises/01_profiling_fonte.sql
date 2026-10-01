-- Profiling da fonte, executado por `python -m alfab profile`.
-- Cada bloco começa com "-- name: <arquivo>" e o resultado vai para evidencias/profiling/<arquivo>.csv.
-- Objetivo: confirmar ANTES do dbt as premissas que, se erradas, não quebram nada e geram número errado.

-- name: 01_volume_por_tabela
SELECT table_id, row_count, ROUND(size_bytes / POW(1024, 2), 1) AS size_mib,
       TIMESTAMP_MILLIS(last_modified_time) AS last_modified
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.__TABLES__`
ORDER BY size_bytes DESC;

-- name: 02_rede_por_tabela
-- As chaves falam a mesma língua? Compara a representação de `rede` em cada tabela.
SELECT 'municipio' AS tabela, CAST(rede AS STRING) AS rede, COUNT(*) AS n FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio` GROUP BY 1, 2
UNION ALL SELECT 'uf', CAST(rede AS STRING), COUNT(*) FROM `basedosdados.br_inep_avaliacao_alfabetizacao.uf` GROUP BY 1, 2
UNION ALL SELECT 'alunos', CAST(rede AS STRING), COUNT(*) FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos` GROUP BY 1, 2
UNION ALL SELECT 'meta_alfabetizacao_brasil', CAST(rede AS STRING), COUNT(*) FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil` GROUP BY 1, 2
UNION ALL SELECT 'meta_alfabetizacao_uf', CAST(rede AS STRING), COUNT(*) FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf` GROUP BY 1, 2
UNION ALL SELECT 'meta_alfabetizacao_municipio', CAST(rede AS STRING), COUNT(*) FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio` GROUP BY 1, 2
ORDER BY tabela, rede;

-- name: 03_dicionario_completo
SELECT * FROM `basedosdados.br_inep_avaliacao_alfabetizacao.dicionario`
ORDER BY id_tabela, nome_coluna, chave;

-- name: 04_ano_serie_por_tabela
SELECT 'municipio' AS tabela, ano, CAST(serie AS STRING) AS serie, COUNT(*) AS n FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio` GROUP BY 1, 2, 3
UNION ALL SELECT 'uf', ano, CAST(serie AS STRING), COUNT(*) FROM `basedosdados.br_inep_avaliacao_alfabetizacao.uf` GROUP BY 1, 2, 3
UNION ALL SELECT 'alunos', ano, CAST(serie AS STRING), COUNT(*) FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos` GROUP BY 1, 2, 3
UNION ALL SELECT 'meta_alfabetizacao_brasil', ano, NULL, COUNT(*) FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil` GROUP BY 1, 2, 3
UNION ALL SELECT 'meta_alfabetizacao_uf', ano, NULL, COUNT(*) FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf` GROUP BY 1, 2, 3
UNION ALL SELECT 'meta_alfabetizacao_municipio', ano, NULL, COUNT(*) FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio` GROUP BY 1, 2, 3
ORDER BY tabela, ano;

-- name: 05_codigos_alunos
-- Confirma os códigos de presença/preenchimento/alfabetizado e o comportamento de proficiência e peso.
SELECT presenca, preenchimento_caderno, alfabetizado,
       COUNT(*) AS n,
       COUNTIF(proficiencia IS NULL) AS proficiencia_nula,
       COUNTIF(proficiencia <= 0) AS proficiencia_nao_positiva,
       MIN(proficiencia) AS prof_min, MAX(proficiencia) AS prof_max,
       COUNTIF(peso_aluno IS NULL) AS peso_nulo, MIN(peso_aluno) AS peso_min, MAX(peso_aluno) AS peso_max
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
GROUP BY 1, 2, 3
ORDER BY n DESC;

-- name: 06_alfabetizado_vs_corte_743
-- O flag `alfabetizado` corresponde a proficiência >= 743? Divergência = anomalia a investigar.
SELECT alfabetizado,
       COUNTIF(proficiencia >= 743) AS prof_ge_743,
       COUNTIF(proficiencia < 743) AS prof_lt_743,
       COUNTIF(proficiencia IS NULL) AS prof_nula
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
GROUP BY 1;

-- name: 07_metas_amostra
SELECT 'brasil' AS nivel, CAST(rede AS STRING) AS rede, ano, taxa_alfabetizacao, meta_alfabetizacao_2024, meta_alfabetizacao_2030
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil`
UNION ALL
SELECT CONCAT('uf:', sigla_uf), CAST(rede AS STRING), ano, taxa_alfabetizacao, meta_alfabetizacao_2024, meta_alfabetizacao_2030
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf`
ORDER BY nivel, ano;

-- name: 08_nulos_e_chaves_municipio
SELECT ano, CAST(rede AS STRING) AS rede, COUNT(*) AS n,
       COUNTIF(taxa_alfabetizacao IS NULL) AS taxa_nula,
       COUNTIF(LENGTH(CAST(id_municipio AS STRING)) != 7) AS id_fora_de_7_digitos,
       COUNT(DISTINCT id_municipio) AS municipios
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
GROUP BY 1, 2
ORDER BY 1, 2;
