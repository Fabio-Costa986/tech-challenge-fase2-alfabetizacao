-- BLOQUEANTE: a base de features não pode conter colunas derivadas do alvo
-- (gap, status, atingiu...) e deve ter exatamente UM alvo. Lê o schema real da tabela construída.
{% set proibidas = [] %}
{% set alvos = [] %}
{% if execute %}
  {% for c in adapter.get_columns_in_relation(ref('ml_features_municipio')) %}
    {% set n = c.name | lower %}
    {% if 'gap' in n or 'status' in n or 'atingiu' in n or 'diff' in n %}{% do proibidas.append(n) %}{% endif %}
    {% if n.startswith('alvo_') %}{% do alvos.append(n) %}{% endif %}
  {% endfor %}
{% endif %}
SELECT
  '{{ proibidas | join(",") }}' AS colunas_proibidas,
  {{ alvos | length }} AS n_alvos
FROM UNNEST([1])
WHERE {{ 'TRUE' if (execute and (proibidas | length > 0 or alvos | length != 1)) else 'FALSE' }}
-- depends_on: {{ ref('ml_features_municipio') }}
