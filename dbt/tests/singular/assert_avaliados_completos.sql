-- ADR-008 (BLOQUEANTE): qualquer aluno efetivamente avaliado precisa ter
-- classificacao de alfabetizacao e peso amostral finito e positivo.
-- Nao transforma NULL em 0 nem reprova ausentes que nao integram o denominador.
-- tag:silver garante que o portao dbt-silver execute este teste.
{{ config(severity='error', tags=['silver']) }}

WITH inconsistencias AS (
  SELECT
    ano,
    id_municipio,
    rede_canonica,
    COUNTIF(alfabetizado IS NULL) AS n_sem_classificacao,
    COUNTIF(
      peso_aluno IS NULL OR peso_aluno <= 0
      OR IS_NAN(peso_aluno) OR IS_INF(peso_aluno)
    ) AS n_peso_invalido
  FROM {{ ref('alunos') }}
  WHERE avaliado
  GROUP BY ano, id_municipio, rede_canonica
)
SELECT *
FROM inconsistencias
WHERE n_sem_classificacao > 0 OR n_peso_invalido > 0
