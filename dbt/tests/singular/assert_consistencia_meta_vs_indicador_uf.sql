-- BLOQUEANTE (consistência entre tabelas): a taxa publicada na tabela de meta estadual precisa ser a
-- mesma da tabela de indicador por UF, no mesmo ano e recorte de rede.
SELECT m.id_local AS sigla_uf, m.ano, m.rede_canonica,
       m.taxa_alfabetizacao AS taxa_tabela_meta, i.taxa_alfabetizacao AS taxa_tabela_indicador
FROM {{ ref('meta_linha_base') }} m
JOIN {{ ref('indicador_uf') }} i
  ON i.sigla_uf = m.id_local AND i.ano = m.ano AND i.rede_canonica = m.rede_canonica
WHERE m.nivel = 'UF'
  AND m.taxa_alfabetizacao IS NOT NULL AND i.taxa_alfabetizacao IS NOT NULL
  AND ABS(m.taxa_alfabetizacao - i.taxa_alfabetizacao) > {{ var('tolerancia_consistencia_tabelas_pp') }}
