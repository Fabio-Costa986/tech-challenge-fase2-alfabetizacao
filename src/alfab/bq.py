"""Helpers de BigQuery com guarda-corpos de FinOps.

Toda query passa por `run_query`, que aplica:
- `maximum_bytes_billed` (a query falha em vez de custar caro);
- labels `run_id`, `camada`, `etapa` para atribuir custo por execução via INFORMATION_SCHEMA.JOBS.
"""

from __future__ import annotations

import re
from functools import lru_cache

from google.cloud import bigquery

from alfab.config import settings


@lru_cache(maxsize=1)
def client() -> bigquery.Client:
    s = settings()
    return bigquery.Client(project=s.project_id, location=s.bq_location)


def _label(value: str) -> str:
    # labels: minúsculas, dígitos, _ e -; até 63 chars
    return re.sub(r"[^a-z0-9_-]", "_", value.lower())[:63]


def job_config(run_id: str, camada: str, etapa: str, dry_run: bool = False,
               params: list | None = None) -> bigquery.QueryJobConfig:
    return bigquery.QueryJobConfig(
        dry_run=dry_run,
        use_query_cache=not dry_run,
        maximum_bytes_billed=settings().max_bytes_billed,
        labels={"run_id": _label(run_id), "camada": _label(camada), "etapa": _label(etapa),
                "app": "alfab"},
        query_parameters=params or [],
    )


def dry_run_bytes(sql: str, run_id: str, camada: str, etapa: str) -> int:
    job = client().query(sql, job_config=job_config(run_id, camada, etapa, dry_run=True))
    return int(job.total_bytes_processed or 0)


def run_query(sql: str, run_id: str, camada: str, etapa: str,
              params: list | None = None) -> bigquery.QueryJob:
    job = client().query(sql, job_config=job_config(run_id, camada, etapa, params=params))
    job.result()
    return job
