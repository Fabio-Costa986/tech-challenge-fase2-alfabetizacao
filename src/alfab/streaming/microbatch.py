"""Micro-lote Bronze -> Silver dos eventos (Cloud Scheduler a cada 5 min).

Janela: (watermark - lookback, upper], em que upper = MAX(ingested_at) no momento da execução.
O lookback cobre linhas que ainda estavam no buffer de streaming na execução anterior; reprocessar
é seguro porque tudo é idempotente:
- dedup dentro do lote: ROW_NUMBER() por event_id (primeira chegada vence);
- dedup entre lotes: MERGE ... WHEN NOT MATCHED na Silver (janela de 7 dias = retenção do Pub/Sub);
- validação referencial: município inexistente -> quarentena (também via MERGE por event_id).

Latência medida: ingested_at (carimbo do ingestor) - produced_at (carimbo do produtor), e
silver_processed_at - produced_at (ponta a ponta até a camada analítica).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from google.cloud import bigquery

from alfab.bq import client, run_query
from alfab.config import settings
from alfab.observability import bq_run_writer, log, track_step

LOOKBACK = timedelta(minutes=10)
DEDUP_HORIZON_DAYS = 7


def script(s) -> str:
    raw = s.table("bronze", "eventos_raw")
    quarantine = s.table("bronze", "eventos_quarentena")
    silver = s.table("silver", "eventos")
    directory = s.table("silver", "diretorio_municipio")
    return f"""
DECLARE inseridas INT64 DEFAULT 0;

CREATE TEMP TABLE janela AS
SELECT * FROM `{raw}`
WHERE ingested_at > @lower AND ingested_at <= @upper;

CREATE TEMP TABLE lote AS
SELECT * EXCEPT (rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ingested_at) AS rn FROM janela
) WHERE rn = 1;

CREATE TEMP TABLE lote_valido AS
SELECT l.* FROM lote l
WHERE EXISTS (SELECT 1 FROM `{directory}` d WHERE d.id_municipio = l.id_municipio);

MERGE `{quarantine}` T
USING (SELECT * FROM lote WHERE event_id NOT IN (SELECT event_id FROM lote_valido)) S
ON T.event_id = S.event_id
WHEN NOT MATCHED THEN INSERT
  (event_id, pubsub_message_id, pubsub_publish_time, received_at, raw_data, motivo_rejeicao, delivery_attempt)
VALUES
  (S.event_id, S.pubsub_message_id, S.pubsub_publish_time, S.ingested_at, S.payload,
   'municipio_inexistente: id_municipio sem correspondência no diretório', S.delivery_attempt);

MERGE `{silver}` T
USING lote_valido S
ON T.event_id = S.event_id
   AND T.ingested_at >= TIMESTAMP_SUB(@lower, INTERVAL {DEDUP_HORIZON_DAYS} DAY)
WHEN NOT MATCHED THEN INSERT
  (event_id, event_type, produced_at, ingested_at, silver_processed_at, origem_dado,
   id_municipio, rede, ano, payload, _run_id)
VALUES
  (S.event_id, S.event_type, S.produced_at, S.ingested_at, CURRENT_TIMESTAMP(), S.origem_dado,
   S.id_municipio, S.rede, S.ano, PARSE_JSON(S.payload), @run_id);
SET inseridas = @@row_count;

SELECT
  (SELECT COUNT(*) FROM janela) AS lidas,
  (SELECT COUNT(*) FROM lote) AS unicas,
  (SELECT COUNT(*) FROM lote_valido) AS validas,
  inseridas,
  (SELECT APPROX_QUANTILES(TIMESTAMP_DIFF(ingested_at, produced_at, MILLISECOND), 100)
     FROM lote_valido) AS lat_ingestao_ms,
  (SELECT APPROX_QUANTILES(TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), produced_at, MILLISECOND), 100)
     FROM lote_valido) AS lat_ponta_a_ponta_ms;
"""


def _pct(q: list | None, p: int) -> float | None:
    return round(q[p] / 1000.0, 3) if q else None


def run(run_id: str) -> dict:
    s = settings()
    writer = bq_run_writer(s.table("ops", "pipeline_runs"))
    with track_step(run_id, "stream", "microbatch.silver.eventos", writer) as m:
        wm_row = list(client().query(
            f"SELECT MAX(watermark) AS wm FROM `{s.table('ops', 'stream_watermark')}`").result())[0]
        watermark = wm_row.wm or datetime(1970, 1, 1, tzinfo=UTC)
        upper_row = list(client().query(
            f"SELECT MAX(ingested_at) AS up FROM `{s.table('bronze', 'eventos_raw')}` "
            f"WHERE ingested_at > @wm",
            job_config=bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("wm", "TIMESTAMP", watermark - LOOKBACK)]),
        ).result())[0]
        upper = upper_row.up
        if upper is None:
            m.rows_in = m.rows_out = 0
            m.details["acao"] = "SEM_EVENTOS_NOVOS"
            return {"lidas": 0}

        lower = watermark - LOOKBACK
        job = run_query(script(s), run_id, "silver", "microbatch_eventos", params=[
            bigquery.ScalarQueryParameter("lower", "TIMESTAMP", lower),
            bigquery.ScalarQueryParameter("upper", "TIMESTAMP", upper),
            bigquery.ScalarQueryParameter("run_id", "STRING", run_id),
        ])
        r = list(job.result())[0]
        stats = {
            "lidas": r.lidas, "unicas": r.unicas, "validas": r.validas, "inseridas": r.inseridas,
            "duplicatas_descartadas": r.lidas - r.unicas,
            "quarentena_referencial": r.unicas - r.validas,
            "latencia_ingestao_p50_s": _pct(r.lat_ingestao_ms, 50),
            "latencia_ingestao_p95_s": _pct(r.lat_ingestao_ms, 95),
            "latencia_ingestao_p99_s": _pct(r.lat_ingestao_ms, 99),
            "latencia_ponta_a_ponta_p95_s": _pct(r.lat_ponta_a_ponta_ms, 95),
            "janela_inicio": lower, "janela_fim": upper,
        }
        m.rows_in, m.rows_out = r.lidas, r.inseridas
        m.bytes_billed = int(job.total_bytes_billed or 0)
        m.details.update(stats)

        errors = client().insert_rows_json(s.table("ops", "stream_watermark"), [{
            "run_id": run_id, "watermark": upper.isoformat(),
            "processed_at": datetime.now(UTC).isoformat()}])
        if errors:
            raise RuntimeError(f"falha ao gravar watermark de streaming: {errors}")

        quarantine_rate = (r.unicas - r.validas) / r.unicas if r.unicas else 0.0
        level = logging.WARNING if quarantine_rate > s.streaming.get("quarantine_alert_rate", 0.1) \
            else logging.INFO
        log("micro-lote concluído", level=level, event="stream_microbatch",
            quarantine_rate=round(quarantine_rate, 4), **stats)
        return stats
