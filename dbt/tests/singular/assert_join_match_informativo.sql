{{ config(severity='warn') }}
-- INFORMATIVA: cobertura abaixo do esperado, sem parar o pipeline (ex.: municípios que não pactuaram meta).
SELECT join_name, total, matched, match_rate, min_rate, justificativa
FROM {{ ref('join_match_rate') }}
WHERE measured_at = (SELECT MAX(measured_at) FROM {{ ref('join_match_rate') }})
  AND severidade = 'informativa'
  AND reprovado
