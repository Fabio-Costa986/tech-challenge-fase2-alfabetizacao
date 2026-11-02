-- ADR-008 (BLOQUEANTE): todo avaliado deve ter classificacao e peso finito positivo.
-- Nao reprova ausentes. A fixture de teste NAO altera silver.alunos: so amplia
-- a consulta deste teste para produzir falha controlada em HOMOLOGACAO.
{{ config(severity='error', tags=['silver']) }}

{% set inject = var('fault_injection', 'none') == 'avaliado_incompleto' %}
{% if inject %}
  {% set hml_project = env_var('ALFAB_HML_PROJECT_ID', '') %}
  {% if not hml_project or target.project != hml_project %}
    {{ exceptions.raise_compiler_error('ADR-008 fixture proibida fora do projeto de homologacao explicitamente configurado') }}
  {% endif %}
{% endif %}

WITH base AS (
  SELECT ano, id_municipio, rede_canonica, avaliado, alfabetizado, peso_aluno
  FROM {{ ref('alunos') }}
  {% if inject %}
  -- Somente teste em homologacao: nao persiste/insere na Silver real.
  UNION ALL SELECT 2099, 'HML_ADR008', 'municipal', TRUE, CAST(NULL AS BOOL), 1.0
  UNION ALL SELECT 2099, 'HML_ADR008', 'municipal', TRUE, TRUE, CAST(0 AS FLOAT64)
  {% endif %}
),
inconsistencias AS (
  SELECT ano, id_municipio, rede_canonica,
    COUNTIF(alfabetizado IS NULL) AS n_sem_classificacao,
    COUNTIF(peso_aluno IS NULL OR peso_aluno <= 0
            OR IS_NAN(peso_aluno) OR IS_INF(peso_aluno)) AS n_peso_invalido
  FROM base
  WHERE avaliado
  GROUP BY ano, id_municipio, rede_canonica
)
SELECT * FROM inconsistencias
WHERE n_sem_classificacao > 0 OR n_peso_invalido > 0
