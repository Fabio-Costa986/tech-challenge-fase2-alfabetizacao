"""Ingestão batch: Base dos Dados (BigQuery público) -> Bronze (Parquet imutável no GCS).

Para cada entidade:
1. Lê `modified` da tabela de origem via API (sem custo de query) e compara com o último
   watermark em ops.source_watermarks. Se a fonte não mudou, a entidade é pulada (custo zero).
2. Faz dry run do SELECT e registra os bytes estimados.
3. Executa EXPORT DATA para gs://<bucket>/bronze/<entidade>/ingestion_date=<d>/run_id=<id>/,
   com overwrite=false: se o caminho já existir, o BigQuery FALHA em vez de sobrescrever.
4. Confere linhas exportadas == linhas da origem (regra bloqueante de completude).
5. Garante a external table hive-particionada bronze.<entidade> e grava o watermark.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from alfab.bq import client, dry_run_bytes, run_query
from alfab.config import Entity, Settings, settings
from alfab.observability import bq_run_writer, log, track_step


class BronzeCompletenessError(RuntimeError):
    """Linhas exportadas diferem das linhas da origem."""


@dataclass(frozen=True)
class SourceState:
    last_modified: datetime
    num_rows: int
    num_bytes: int


def bronze_prefix(bucket: str, entity: str) -> str:
    return f"gs://{bucket}/bronze/{entity}"


def bronze_uri(bucket: str, entity: str, run_id: str, ingestion_date: str) -> str:
    return f"{bronze_prefix(bucket, entity)}/ingestion_date={ingestion_date}/run_id={run_id}/part-*.parquet"


def select_sql(entity: Entity, source_modified: datetime) -> str:
    cols = ",\n  ".join(f"`{c}`" for c in entity.columns)
    return (
        f"SELECT\n  {cols},\n"
        f"  CURRENT_TIMESTAMP() AS _ingested_at,\n"
        f"  TIMESTAMP('{source_modified.isoformat()}') AS _source_last_modified\n"
        f"FROM `{entity.fqn}`"
    )


def export_sql(entity: Entity, uri: str, source_modified: datetime) -> str:
    return (
        "EXPORT DATA OPTIONS (\n"
        f"  uri = '{uri}',\n"
        "  format = 'PARQUET',\n"
        "  compression = 'ZSTD',\n"
        "  overwrite = false\n"
        ") AS\n" + select_sql(entity, source_modified)
    )


def external_table_ddl(table_fqn: str, prefix: str) -> str:
    return (
        f"CREATE EXTERNAL TABLE IF NOT EXISTS `{table_fqn}`\n"
        "WITH PARTITION COLUMNS (ingestion_date DATE, run_id STRING)\n"
        "OPTIONS (\n"
        "  format = 'PARQUET',\n"
        f"  uris = ['{prefix}/*'],\n"
        f"  hive_partition_uri_prefix = '{prefix}'\n"
        ")"
    )


def source_state(entity: Entity) -> SourceState:
    t = client().get_table(entity.fqn)
    return SourceState(last_modified=t.modified, num_rows=int(t.num_rows or 0),
                       num_bytes=int(t.num_bytes or 0))


def last_watermarks(s: Settings) -> dict[str, datetime]:
    sql = f"""
      SELECT entity, MAX(source_last_modified) AS source_last_modified
      FROM `{s.table('ops', 'source_watermarks')}`
      GROUP BY entity
    """
    rows = client().query(sql).result()
    return {r.entity: r.source_last_modified for r in rows}


def exported_rows(job) -> int | None:
    stats = job._properties.get("statistics", {}).get("query", {}).get("exportDataStatistics", {})
    return int(stats["rowCount"]) if "rowCount" in stats else None


def ingest_entity(s: Settings, entity: Entity, run_id: str, ingestion_date: str,
                  previous: datetime | None, force: bool) -> str:
    writer = bq_run_writer(s.table("ops", "pipeline_runs"))
    with track_step(run_id, "batch", f"bronze.{entity.name}", writer) as m:
        state = source_state(entity)
        m.rows_in = state.num_rows
        m.details.update(source=entity.fqn, source_last_modified=state.last_modified,
                         source_bytes=state.num_bytes)

        if previous is not None and state.last_modified <= previous and not force:
            m.rows_out = 0
            m.details["acao"] = "PULADA_FONTE_INALTERADA"
            log("fonte inalterada; ingestão pulada", event="bronze_skipped", entity=entity.name)
            return "skipped"

        estimated = dry_run_bytes(select_sql(entity, state.last_modified), run_id, "bronze", entity.name)
        m.details["bytes_estimados_dry_run"] = estimated

        uri = bronze_uri(s.bronze_bucket, entity.name, run_id, ingestion_date)
        job = run_query(export_sql(entity, uri, state.last_modified), run_id, "bronze", entity.name)
        m.bytes_billed = int(job.total_bytes_billed or 0)
        m.rows_out = exported_rows(job)
        m.details.update(job_id=job.job_id, uri=uri, acao="EXPORTADA")

        if m.rows_out is not None and m.rows_out != state.num_rows:
            raise BronzeCompletenessError(
                f"{entity.name}: origem={state.num_rows} exportadas={m.rows_out}")

        prefix = bronze_prefix(s.bronze_bucket, entity.name)
        run_query(external_table_ddl(s.table("bronze", entity.name), prefix), run_id, "bronze", "ddl")

        errors = client().insert_rows_json(s.table("ops", "source_watermarks"), [{
            "entity": entity.name,
            "source_table": entity.fqn,
            "source_last_modified": state.last_modified.isoformat(),
            "source_num_rows": state.num_rows,
            "run_id": run_id,
            "bronze_uri": uri,
            "exported_rows": m.rows_out,
            "ingested_at": datetime.now(UTC).isoformat(),
        }])
        if errors:
            raise RuntimeError(f"falha ao gravar watermark: {errors}")
        return "exported"


def run(run_id: str, entities: list[str] | None = None, force: bool = False) -> dict[str, str]:
    s = settings()
    ingestion_date = datetime.now(UTC).date().isoformat()
    previous = last_watermarks(s)
    selected = entities or list(s.entities)
    unknown = set(selected) - set(s.entities)
    if unknown:
        raise ValueError(f"entidades desconhecidas: {sorted(unknown)}")

    outcome = {}
    for name in selected:
        outcome[name] = ingest_entity(s, s.entities[name], run_id, ingestion_date,
                                      previous.get(name), force)
    log("bronze concluída", event="bronze_done", run_id=run_id, outcome=outcome)
    return outcome
