-- Resumo quase em tempo real do streaming (última hora), já na camada analítica.
CREATE OR REPLACE VIEW `{project}.{gold}.vw_eventos_tempo_real`
OPTIONS (description = 'Eventos SIMULADOS processados na última hora, por tipo e UF') AS
SELECT
  e.event_type,
  d.sigla_uf,
  COUNT(*) AS eventos,
  MAX(e.silver_processed_at) AS ultimo_processamento,
  APPROX_QUANTILES(TIMESTAMP_DIFF(e.silver_processed_at, e.produced_at, SECOND), 100)[OFFSET(95)]
    AS p95_produzido_ate_silver_s,
  'SIMULADO' AS origem_dado
FROM `{project}.{silver}.eventos` e
LEFT JOIN `{project}.{silver}.diretorio_municipio` d USING (id_municipio)
WHERE e.ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
GROUP BY e.event_type, d.sigla_uf
