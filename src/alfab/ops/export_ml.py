"""Snapshot Fase 3 imutavel, validado e sem sobrepor versoes anteriores.

A exportacao e uma operacao no GCP. O preflight e somente leitura e verifica
schema da Gold, run_id aceito (quando informado), snapshot e prefixo GCS.
Nunca use os artefatos da versao 2026-10-01 para treino apos ADR-009.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime

from google.api_core.exceptions import NotFound
from google.cloud import storage

from alfab.bq import client, run_query
from alfab.config import settings
from alfab.observability import bq_run_writer, track_step
from alfab.ops.adr_validation import AcceptanceError, check_ml_schema, validate

SOURCE_TABLE = "ml_features_municipio"


def version_suffix(version: str) -> str:
    """2026-11-02 ou 2026-11-02-<id>; prefixos e nomes de snapshots sem colisao."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:-[a-z0-9]{6,20})?", version):
        raise ValueError("versao invalida; use AAAA-MM-DD ou AAAA-MM-DD-identificador")
    date.fromisoformat(version[:10])  # rejeita datas inexistentes
    if version[:10] <= "2026-10-01":
        raise ValueError("nao reutilize o snapshot da Fase 3 de 2026-10-01 ou anterior")
    return version[:10].replace("-", "") + ("_" + version[11:] if len(version) > 10 else "")


def export(run_id: str, version: str | None = None, aceite_run_id: str | None = None) -> str:
    s = settings()
    version = version or datetime.now(UTC).date().isoformat()
    suffix = version_suffix(version)
    src = s.table("gold", SOURCE_TABLE)
    snapshot = s.table("gold", f"{SOURCE_TABLE}_fase3_{suffix}")
    prefix = f"gold/ml/fase3/versao={version}/"
    uri = f"gs://{s.bronze_bucket}/{prefix}part-*.parquet"

    # A execucao do Workflow tem run_id diferente do job de export. O aceite
    # ancora esta exportacao ao run_id de publicacao, se fornecido explicitamente.
    if aceite_run_id:
        validate(aceite_run_id)

    bq = client()
    table = bq.get_table(src)
    check_ml_schema([col.name for col in table.schema], src)
    if not (table.labels or {}).get("published_run_id"):
        raise AcceptanceError("Gold ML sem published_run_id; nao exportar ate validar a publicacao")
    try:
        bq.get_table(snapshot)
    except NotFound:
        pass
    else:
        raise FileExistsError(f"snapshot ja existe: {snapshot}; escolha versao nova")

    # Falha fechado se a credencial nao pode listar objetos: nao vamos assumir
    # que o prefixo esta vazio e arriscar mistura de Parquets de execucoes.
    objects = storage.Client(project=s.project_id).list_blobs(s.bronze_bucket, prefix=prefix, max_results=1)
    if next(iter(objects), None) is not None:
        raise FileExistsError(f"versao ja contem Parquet no GCS: gs://{s.bronze_bucket}/{prefix}")

    writer = bq_run_writer(s.table("ops", "pipeline_runs"))
    with track_step(run_id, "batch", "export.ml_fase3", writer) as m:
        run_query(f"CREATE SNAPSHOT TABLE `{snapshot}` CLONE `{src}`",
                  run_id, "gold", "snapshot_ml")
        job = run_query(
            "EXPORT DATA OPTIONS (uri = '" + uri + "', format = 'PARQUET', compression = 'ZSTD', "
            f"overwrite = false) AS SELECT * FROM `{src}`",
            run_id, "gold", "export_ml")
        m.bytes_billed = int(job.total_bytes_billed or 0)
        m.details.update(snapshot=snapshot, uri=uri, version=version,
                         published_run_id=(table.labels or {}).get("published_run_id"))
        return uri
