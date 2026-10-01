-- "As chaves falam a mesma língua?" Nas tabelas de indicador, `rede` é código coberto pelo dicionário;
-- nas tabelas de meta o dicionário NÃO cobre `rede`. Este modelo lista toda representação de rede
-- encontrada nas 6 entidades e a traduz para um vocabulário canônico único.
-- Valor sem tradução vira DESCONHECIDO (nunca uma categoria válida por fallback) e o teste
-- no_unknown_category reprova a camada.
WITH valores AS (
  SELECT DISTINCT 'municipio' AS tabela, TRIM(CAST(rede AS STRING)) AS valor_origem FROM {{ bronze('municipio') }}
  UNION DISTINCT
  SELECT DISTINCT 'uf', TRIM(CAST(rede AS STRING)) FROM {{ bronze('uf') }}
  UNION DISTINCT
  SELECT DISTINCT 'alunos', TRIM(CAST(rede AS STRING)) FROM {{ bronze('alunos') }}
  UNION DISTINCT
  SELECT DISTINCT 'meta_alfabetizacao_brasil', TRIM(CAST(rede AS STRING)) FROM {{ bronze('meta_alfabetizacao_brasil') }}
  UNION DISTINCT
  SELECT DISTINCT 'meta_alfabetizacao_uf', TRIM(CAST(rede AS STRING)) FROM {{ bronze('meta_alfabetizacao_uf') }}
  UNION DISTINCT
  SELECT DISTINCT 'meta_alfabetizacao_municipio', TRIM(CAST(rede AS STRING)) FROM {{ bronze('meta_alfabetizacao_municipio') }}
),
dic_mesma_tabela AS (
  SELECT id_tabela, chave, valor FROM {{ ref('dicionario') }} WHERE nome_coluna = 'rede'
),
dic_qualquer AS (
  SELECT chave, ANY_VALUE(valor) AS valor, COUNT(DISTINCT valor_normalizado) AS n_significados
  FROM {{ ref('dicionario') }} WHERE nome_coluna = 'rede' GROUP BY chave
),
traduzido AS (
  SELECT
    v.tabela,
    v.valor_origem,
    COALESCE(dm.valor, dq.valor) AS descricao_dicionario,
    CASE WHEN dm.valor IS NOT NULL THEN 'dicionario_mesma_tabela'
         WHEN dq.valor IS NOT NULL THEN 'dicionario_outra_tabela'
         ELSE 'texto_da_fonte' END AS metodo_traducao,
    dq.n_significados,
    {{ normalize_text('COALESCE(dm.valor, dq.valor, v.valor_origem)') }} AS valor_normalizado
  FROM valores v
  LEFT JOIN dic_mesma_tabela dm
    ON dm.chave = v.valor_origem
   AND (dm.id_tabela = v.tabela OR REGEXP_CONTAINS(dm.id_tabela, CONCAT(r'(^|[._])', v.tabela, r'$')))
   AND NOT (v.tabela IN ('uf', 'municipio') AND STARTS_WITH(dm.id_tabela, 'meta_'))
  LEFT JOIN dic_qualquer dq
    ON dq.chave = v.valor_origem
  WHERE v.valor_origem IS NOT NULL
)
SELECT
  t.*,
  {% if var('fault_injection') == 'unmapped_rede' -%}
  -- DEMONSTRAÇÃO DE FALHA: um valor de rede passa a não ter tradução
  IF(t.tabela = 'municipio' AND t.valor_origem = (SELECT MIN(valor_origem) FROM traduzido WHERE tabela = 'municipio'),
     'DESCONHECIDO', COALESCE(s.rede_canonica, 'DESCONHECIDO')) AS rede_canonica,
  {%- else -%}
  COALESCE(s.rede_canonica, 'DESCONHECIDO') AS rede_canonica,
  {%- endif %}
  {{ lineage_columns() }}
FROM traduzido t
LEFT JOIN {{ ref('rede_sinonimos') }} s USING (valor_normalizado)
