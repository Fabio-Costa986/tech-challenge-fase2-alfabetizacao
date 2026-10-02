-- Tradução oficial de códigos. Uma linha por (tabela, coluna, chave).
-- Se a mesma chave tiver descrições diferentes em coberturas temporais distintas, fica a de cobertura
-- mais recente e o teste informativo de unicidade da fonte registra o caso.
SELECT
  id_tabela,
  nome_coluna,
  TRIM(chave) AS chave,
  ARRAY_AGG(valor ORDER BY cobertura_temporal DESC LIMIT 1)[OFFSET(0)] AS valor,
  {{ normalize_text("ARRAY_AGG(valor ORDER BY cobertura_temporal DESC LIMIT 1)[OFFSET(0)]") }} AS valor_normalizado,
  COUNT(DISTINCT valor) AS n_descricoes_na_fonte,
  {{ lineage_columns() }}
FROM {{ bronze('dicionario') }}
WHERE chave IS NOT NULL
GROUP BY id_tabela, nome_coluna, TRIM(chave)
