-- BLOQUEANTE: os códigos assumidos em dbt_project.yml (vars codigo_*) precisam significar o que
-- o pipeline assume, segundo o dicionário oficial. Se a fonte mudar a codificação, a camada para
-- em vez de calcular o denominador errado em silêncio.
WITH esperado AS (
  SELECT 'presenca' AS coluna, '{{ var("codigo_presente") }}' AS codigo, r'presen' AS padrao
  UNION ALL SELECT 'preenchimento_caderno', '{{ var("codigo_caderno_preenchido") }}', r'preench|sim|valid'
  UNION ALL SELECT 'alfabetizado', '{{ var("codigo_alfabetizado") }}', r'alfabetizad|sim'
),
encontrado AS (
  SELECT e.coluna, e.codigo, e.padrao, d.valor, {{ normalize_text('d.valor') }} AS valor_norm
  FROM esperado e
  LEFT JOIN {{ ref('dicionario') }} d
    ON d.nome_coluna = e.coluna AND d.chave = e.codigo
)
SELECT coluna, codigo, valor
FROM encontrado
WHERE valor IS NULL
   OR NOT REGEXP_CONTAINS(valor_norm, padrao)
   OR REGEXP_CONTAINS(valor_norm, r'^(nao|ausente|sem)\b')
