{#
  Persiste o resultado de TODOS os testes da invocação em ops.dq_results (append).
  Roda em on-run-end, portanto também quando a execução falha: o registro da reprovação sobrevive.
#}
{% macro _sql_str(value) -%}
  {%- if value is none -%}NULL{%- else -%}
  '{{ (value | string) | replace("\\", "\\\\") | replace("'", "\\'") | replace("\n", " ") | truncate(4000, True, "...") }}'
  {%- endif -%}
{%- endmacro %}

{% macro log_dq_results(results) %}
  {% if not execute %}{{ return('') }}{% endif %}
  {% set rows = [] %}
  {% for r in results if r.node.resource_type == 'test' %}
    {% set attached = r.node.attached_node if r.node.attached_node is defined else none %}
    {% do rows.append(
      "(" ~ _sql_str(var('run_id')) ~ ", " ~ _sql_str(invocation_id) ~ ", CURRENT_TIMESTAMP(), "
      ~ _sql_str(r.node.name) ~ ", " ~ _sql_str(r.node.unique_id) ~ ", " ~ _sql_str(attached) ~ ", "
      ~ _sql_str('bloqueante' if r.node.config.severity | lower == 'error' else 'informativa') ~ ", "
      ~ _sql_str(r.status) ~ ", "
      ~ (r.failures if r.failures is not none else 'NULL') ~ ", "
      ~ _sql_str(r.message) ~ ", "
      ~ (r.execution_time | round(3)) ~ ", "
      ~ _sql_str(var('fault_injection')) ~ ")"
    ) %}
  {% endfor %}
  {% if rows | length == 0 %}{{ return('') }}{% endif %}
  {% set sql %}
    INSERT INTO `{{ target.project }}.{{ var('ops_dataset') }}.dq_results`
      (run_id, invocation_id, executed_at, test_name, unique_id, attached_node, severidade, status,
       failures, message, execution_time_s, fault_injection)
    VALUES {{ rows | join(",\n") }}
  {% endset %}
  {{ return(sql) }}
{% endmacro %}
