{{ config(severity='warn') }}
-- INFORMATIVA: mesma checagem no nível municipal (mais casos de borda; investigar, não bloquear).
SELECT m.id_local AS id_municipio, m.ano, m.rede_canonica,
       m.taxa_alfabetizacao AS taxa_tabela_meta, i.taxa_alfabetizacao AS taxa_tabela_indicador
FROM {{ ref('meta_linha_base') }} m
JOIN {{ ref('indicador_municipio') }} i
  ON i.id_municipio = m.id_local AND i.ano = m.ano AND i.rede_canonica = m.rede_canonica
WHERE m.nivel = 'MUN'
  AND m.taxa_alfabetizacao IS NOT NULL AND i.taxa_alfabetizacao IS NOT NULL
  AND ABS(m.taxa_alfabetizacao - i.taxa_alfabetizacao) > {{ var('tolerancia_consistencia_tabelas_pp') }}
