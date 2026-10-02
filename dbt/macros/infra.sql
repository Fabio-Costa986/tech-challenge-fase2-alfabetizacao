{# Usa o nome de schema configurado (silver, gold_staging, ops) sem o prefixo do target. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
  {{ custom_schema_name | trim if custom_schema_name else target.schema }}
{%- endmacro %}


{# Labels de job (job-label: true). Valores: minúsculas, [a-z0-9_-], até 63 chars. #}
{% macro alfab_job_labels() -%}
  {%- set clean = modules.re.compile('[^a-z0-9_-]') -%}
  {%- set labels = {
      'app': 'alfab',
      'run_id': clean.sub('_', var('run_id', 'local') | lower)[:63],
      'camada': clean.sub('_', (node.config.schema if node is defined and node is not none and node.config.schema else 'dbt') | lower)[:63],
      'etapa': clean.sub('_', (node.name if node is defined and node is not none else 'hook') | lower)[:63],
  } -%}
  {{ return(tojson(labels)) }}
{%- endmacro %}


{# run_id do snapshot Bronze mais recente da entidade (ordenável lexicograficamente). Vira literal na
   query, o que permite partition pruning na external table hive-particionada. #}
{% macro latest_bronze_run(entity) %}
  {% if not execute %}{{ return('compile_only') }}{% endif %}
  {% set q %}
    SELECT MAX(run_id) FROM `{{ target.project }}.{{ var('ops_dataset') }}.source_watermarks`
    WHERE entity = '{{ entity }}'
  {% endset %}
  {% set v = run_query(q).columns[0].values()[0] %}
  {% if not v %}
    {{ exceptions.raise_compiler_error("Sem snapshot Bronze para '" ~ entity ~ "'. Rode `python -m alfab ingest-bronze` antes.") }}
  {% endif %}
  {{ return(v) }}
{% endmacro %}


{# Lê o snapshot mais recente da Bronze (somente a partição run_id correspondente). #}
{% macro bronze(entity) -%}
  (
    SELECT * EXCEPT (ingestion_date), run_id AS _bronze_run_id
    FROM {{ source('bronze', entity) }}
    WHERE run_id = '{{ latest_bronze_run(entity) }}'
  )
{%- endmacro %}


{# minúsculas, sem acento, sem espaços nas pontas, sem o prefixo "rede ". #}
{% macro normalize_text(expr) -%}
  REGEXP_REPLACE(
    REGEXP_REPLACE(NORMALIZE(LOWER(TRIM(CAST({{ expr }} AS STRING))), NFD), r'\p{M}', ''),
    r'^rede\s+', '')
{%- endmacro %}


{# Metadados de linhagem presentes em toda tabela Silver/Gold. #}
{% macro lineage_columns(origem='OFICIAL') -%}
  '{{ origem }}' AS origem_dado,
  '{{ var("run_id") }}' AS _run_id,
  CURRENT_TIMESTAMP() AS _processed_at
{%- endmacro %}


{# (chave, valor) do dicionário para uma coluna: prioriza a própria tabela; senão, qualquer tabela.
   Uma linha por chave, para o LEFT JOIN nunca multiplicar linhas. #}
{% macro dict_lookup(nome_coluna, tabela) -%}
  (
    SELECT chave, ARRAY_AGG(valor ORDER BY prioridade, id_tabela LIMIT 1)[OFFSET(0)] AS valor
    FROM (
      SELECT chave, valor, id_tabela,
        IF(id_tabela = '{{ tabela }}' OR REGEXP_CONTAINS(id_tabela, r'(^|[._]){{ tabela }}$'), 0, 1) AS prioridade
      FROM {{ ref('dicionario') }}
      WHERE nome_coluna = '{{ nome_coluna }}'
        {% if tabela in ['uf', 'municipio'] %}AND NOT STARTS_WITH(id_tabela, 'meta_'){% endif %}
    )
    GROUP BY chave
  )
{%- endmacro %}
