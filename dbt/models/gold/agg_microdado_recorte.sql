-- Agregação do microdado de alunos por (ano, nível territorial, local, recorte de rede).
-- Taxa oficial = alunos AVALIADOS alfabetizados / alunos AVALIADOS, ponderado por peso_aluno.
-- As variantes erradas (sem peso; denominador com ausentes) são calculadas DE PROPÓSITO, rotuladas,
-- para quantificar o tamanho de cada armadilha em docs/investigacao_anomalias.md.
WITH base AS (
  SELECT a.ano, a.id_municipio, a.sigla_uf, rr.recorte, a.avaliado, a.alfabetizado,
         a.proficiencia, a.peso_aluno
  FROM {{ ref('alunos') }} a
  JOIN {{ ref('rede_recortes') }} rr ON rr.componente = a.rede_canonica
),
niveis AS (
  SELECT 'MUN' AS nivel, id_municipio AS id_local, sigla_uf, * EXCEPT (id_municipio, sigla_uf) FROM base
  UNION ALL
  SELECT 'UF', sigla_uf, sigla_uf, * EXCEPT (id_municipio, sigla_uf) FROM base
  UNION ALL
  SELECT 'BR', 'BR', CAST(NULL AS STRING), * EXCEPT (id_municipio, sigla_uf) FROM base
)
SELECT
  ano, nivel, id_local, ANY_VALUE(sigla_uf) AS sigla_uf, recorte,
  COUNT(*) AS n_registros,
  COUNTIF(avaliado) AS n_avaliados,
  COUNTIF(avaliado AND alfabetizado) AS n_alfabetizados,
  SUM(IF(avaliado, peso_aluno, 0)) AS peso_avaliados,
  SUM(IF(avaliado AND alfabetizado, peso_aluno, 0)) AS peso_alfabetizados,
  100 * SAFE_DIVIDE(SUM(IF(avaliado AND alfabetizado, peso_aluno, 0)),
                    SUM(IF(avaliado AND alfabetizado IS NOT NULL, peso_aluno, 0))) AS taxa_microdado_ponderada,
  100 * SAFE_DIVIDE(COUNTIF(avaliado AND alfabetizado),
                    COUNTIF(avaliado AND alfabetizado IS NOT NULL)) AS taxa_microdado_sem_peso_ERRADA,
  -- ausentes têm peso_aluno NULO na fonte (profiling 05), então esta variante só existe por contagem
  100 * SAFE_DIVIDE(COUNTIF(avaliado AND alfabetizado), COUNT(*)) AS taxa_denominador_com_ausentes_ERRADA,
  SAFE_DIVIDE(SUM(IF(avaliado AND proficiencia IS NOT NULL, peso_aluno * proficiencia, 0)),
              SUM(IF(avaliado AND proficiencia IS NOT NULL, peso_aluno, 0))) AS proficiencia_media_ponderada,
  100 * SAFE_DIVIDE(SUM(IF(avaliado AND proficiencia < 743, peso_aluno, 0)),
                    SUM(IF(avaliado AND proficiencia IS NOT NULL, peso_aluno, 0))) AS pct_abaixo_corte_743,
  {{ lineage_columns() }}
FROM niveis
GROUP BY ano, nivel, id_local, recorte
