-- Visão consolidada: indicador OFICIAL (batch) + último valor SIMULADO (streaming) por município.
-- Os dois convivem na mesma view SEM se misturar: a coluna origem_dado separa um do outro,
-- e o simulado nunca substitui o oficial (são linhas distintas).
-- Placeholders {project}, {gold}, {silver} são preenchidos por src/alfab/ops/publish.py.
CREATE OR REPLACE VIEW `{project}.{gold}.vw_indicador_consolidado`
OPTIONS (description = 'Oficial (batch) + simulado (streaming), separados por origem_dado') AS
SELECT
  'OFICIAL' AS origem_dado,
  ano,
  id_municipio,
  nome_municipio,
  sigla_uf,
  rede_codigo,
  rede_canonica,
  taxa_alfabetizacao,
  CAST(NULL AS TIMESTAMP) AS evento_produzido_em,
  _processed_at AS atualizado_em
FROM `{project}.{gold}.fct_alfabetizacao_municipio`

UNION ALL

SELECT
  'SIMULADO' AS origem_dado,
  e.ano,
  e.id_municipio,
  d.nome_municipio,
  d.sigla_uf,
  e.rede AS rede_codigo,
  rm.rede_canonica,
  LAX_FLOAT64(e.payload.taxa_alfabetizacao) AS taxa_alfabetizacao,
  e.produced_at AS evento_produzido_em,
  e.silver_processed_at AS atualizado_em
FROM `{project}.{silver}.eventos` e
LEFT JOIN `{project}.{silver}.diretorio_municipio` d USING (id_municipio)
LEFT JOIN `{project}.{silver}.rede_map` rm ON rm.tabela = 'municipio' AND rm.valor_origem = e.rede
WHERE e.event_type = 'indicador_atualizado'
QUALIFY ROW_NUMBER() OVER (PARTITION BY e.id_municipio, e.rede, e.ano ORDER BY e.produced_at DESC) = 1
