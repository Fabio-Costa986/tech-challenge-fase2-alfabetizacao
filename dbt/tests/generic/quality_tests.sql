{# Duplicidade: retorna as combinações repetidas. #}
{% test unique_combination(model, columns) %}
  SELECT {{ columns | join(', ') }}, COUNT(*) AS n
  FROM {{ model }}
  GROUP BY {{ columns | join(', ') }}
  HAVING COUNT(*) > 1
{% endtest %}


{# Faixa válida. Nulo NÃO reprova (ausência é tratada por null_rate_below). #}
{% test between(model, column_name, min_value=none, max_value=none, exclusive_min=false) %}
  SELECT {{ column_name }}
  FROM {{ model }}
  WHERE {{ column_name }} IS NOT NULL
    AND (
      FALSE
      {% if min_value is not none %} OR {{ column_name }} {{ '<=' if exclusive_min else '<' }} {{ min_value }} {% endif %}
      {% if max_value is not none %} OR {{ column_name }} > {{ max_value }} {% endif %}
    )
{% endtest %}


{# Fallback explícito: a categoria DESCONHECIDO precisa ter contagem zero. #}
{% test no_unknown_category(model, column_name, unknown='DESCONHECIDO') %}
  SELECT {{ column_name }}, COUNT(*) AS n
  FROM {{ model }}
  WHERE {{ column_name }} = '{{ unknown }}'
  GROUP BY 1
{% endtest %}


{# Detecção de ausentes: reprova se a proporção de nulos exceder max_rate. Retorna 1 linha com a taxa. #}
{% test null_rate_below(model, column_name, max_rate, where='TRUE') %}
  SELECT nulos, total, SAFE_DIVIDE(nulos, total) AS taxa_nulos
  FROM (
    SELECT COUNTIF({{ column_name }} IS NULL) AS nulos, COUNT(*) AS total
    FROM {{ model }} WHERE {{ where }}
  )
  WHERE total = 0 OR SAFE_DIVIDE(nulos, total) > {{ max_rate }}
{% endtest %}


{# Diferença absoluta entre duas colunas acima da tolerância (consistência entre fontes). #}
{% test abs_diff_within(model, column_name, other_column, tolerance, where='TRUE') %}
  SELECT *
  FROM {{ model }}
  WHERE {{ where }}
    AND {{ column_name }} IS NOT NULL AND {{ other_column }} IS NOT NULL
    AND ABS({{ column_name }} - {{ other_column }}) > {{ tolerance }}
{% endtest %}


{# Tabela não pode estar vazia (um join que zera tudo também é falha). #}
{% test not_empty(model) %}
  SELECT 1 AS vazio FROM (SELECT COUNT(*) AS n FROM {{ model }}) WHERE n = 0
{% endtest %}
