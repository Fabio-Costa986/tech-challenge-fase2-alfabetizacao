"""Guarda o dataset analítico para a Fase 3 (exigência do enunciado, pág. 7).

Gera duas cópias imutáveis e versionadas por data:
- table snapshot no BigQuery: gold.ml_features_municipio_fase3_<AAAAMMDD> (custo só do delta);
- Parquet no GCS: gs://<bucket>/gold/ml/fase3/versao=<AAAA-MM-DD>/ (portável, sem depender do BQ).
"""

from __future__ import annotations

from datetime import UTC, datetime

from alfab.bq import run_query
from alfab.config import settings
from alfab.observability import bq_run_writer, track_step

SOURCE_TABLE = "ml_features_municipio"


def export(run_id: str) -> str:
    s = settings()
    today = datetime.now(UTC).date()
    src = s.table("gold", SOURCE_TABLE)
    snapshot = s.table("gold", f"{SOURCE_TABLE}_fase3_{today:%Y%m%d}")
    uri = f"gs://{s.bronze_bucket}/gold/ml/fase3/versao={today.isoformat()}/part-*.parquet"

    writer = bq_run_writer(s.table("ops", "pipeline_runs"))
    with track_step(run_id, "batch", "export.ml_fase3", writer) as m:
        run_query(f"CREATE SNAPSHOT TABLE IF NOT EXISTS `{snapshot}` CLONE `{src}`",
                  run_id, "gold", "snapshot_ml")
        job = run_query(
            "EXPORT DATA OPTIONS (uri = '" + uri + "', format = 'PARQUET', compression = 'ZSTD', "
            f"overwrite = false) AS SELECT * FROM `{src}`",
            run_id, "gold", "export_ml")
        m.bytes_billed = int(job.total_bytes_billed or 0)
        m.details.update(snapshot=snapshot, uri=uri)
        return uri
