-- BLOQUEANTE: a base de features nao pode conter colunas derivadas do alvo
-- (gap, status, atingiu...) nem meta_t+1 sem data de publicacao historica
-- comprovada (ADR-009). Deve ter exatamente UM alvo. Le o schema real.
{% set proibidas = [] %}
{% set alvos = [] %}
{% if execute %}
  {% for c in adapter.get_columns_in_relation(ref('ml_features_municipio')) %}
    {% set n = c.name | lower %}
    {% if 'gap' in n or 'status' in n or 'atingiu' in n or 'diff' in n or n == 'feat_meta_pactuada_t_mais_1' %}{% do proibidas.append(n) %}{% endif %}
    {% if n.startswith('alvo_') %}{% do alvos.append(n) %}{% endif %}
  {% endfor %}
{% endif %}
SELECT
  '{{ proibidas | join(",") }}' AS colunas_proibidas,
  {{ alvos | length }} AS n_alvos
FROM UNNEST([1])
WHERE {{ 'TRUE' if (execute and (proibidas | length > 0 or alvos | length != 1)) else 'FALSE' }}
-- depends_on: {{ ref('ml_features_municipio') }}
