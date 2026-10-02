-- BLOQUEANTE: alguma junção da execução corrente ficou abaixo do limiar (ou casou zero linhas).
-- Falhar aqui impede a construção da Gold (o Workflow não avança para a etapa gold).
SELECT join_name, total, matched, match_rate, min_rate, justificativa
FROM {{ ref('join_match_rate') }}
WHERE measured_at = (SELECT MAX(measured_at) FROM {{ ref('join_match_rate') }})
  AND severidade = 'bloqueante'
  AND reprovado
