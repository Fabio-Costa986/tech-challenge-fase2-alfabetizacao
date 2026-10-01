"""Observabilidade: log estruturado + métricas de execução persistidas.

- Logs saem em JSON no stdout. No Cloud Run, o Cloud Logging indexa cada campo em jsonPayload,
  e as log-based metrics do Terraform (infra/monitoring.tf) contam `event=step_finished`.
- Cada etapa grava uma linha em ops.pipeline_runs (append, nunca sobrescreve).
- `track_step` NUNCA engole exceções: registra FAILED e relança. O processo termina com
  código != 0, o Cloud Run Job fica FAILED, e o alerta dispara.
"""

from __future__ import annotations

import json
import logging
import secrets
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

_LOGGER = logging.getLogger("alfab")


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": datetime.now(UTC).isoformat(),
        }
        payload.update(getattr(record, "fields", {}))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)


def log(message: str, level: int = logging.INFO, **fields: Any) -> None:
    _LOGGER.log(level, message, extra={"fields": fields})


def new_run_id(now: datetime | None = None) -> str:
    """ID ordenável lexicograficamente: 20260930T120000Z-a1b2c3."""
    now = now or datetime.now(UTC)
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(3)}"


@dataclass
class StepMetrics:
    run_id: str
    pipeline: str
    step: str
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    rows_in: int | None = None
    rows_out: int | None = None
    bytes_billed: int | None = None
    details: dict[str, Any] = field(default_factory=dict)


RunWriter = Callable[[dict[str, Any]], None]


@contextmanager
def track_step(run_id: str, pipeline: str, step: str, writer: RunWriter) -> Iterator[StepMetrics]:
    metrics = StepMetrics(run_id=run_id, pipeline=pipeline, step=step)
    t0 = time.perf_counter()
    log("step_started", event="step_started", run_id=run_id, pipeline=pipeline, step=step)
    status, error = "SUCCEEDED", None
    try:
        yield metrics
    except BaseException as exc:  # registra e relança: nunca engolir
        status, error = "FAILED", f"{type(exc).__name__}: {exc}"[:2000]
        raise
    finally:
        row = {
            "run_id": run_id,
            "pipeline": pipeline,
            "step": step,
            "started_at": metrics.started_at.isoformat(),
            "ended_at": datetime.now(UTC).isoformat(),
            "duration_s": round(time.perf_counter() - t0, 3),
            "rows_in": metrics.rows_in,
            "rows_out": metrics.rows_out,
            "bytes_billed": metrics.bytes_billed,
            "status": status,
            "error": error,
            "details": json.dumps(metrics.details, default=str),
        }
        log(
            "step_finished",
            level=logging.ERROR if status == "FAILED" else logging.INFO,
            event="step_finished",
            **row,
        )
        try:
            writer(row)
        except Exception as write_exc:  # noqa: BLE001 - falha de telemetria não pode mascarar a original
            log("falha ao persistir métrica", level=logging.ERROR, event="metrics_write_failed",
                run_id=run_id, step=step, error=str(write_exc))
            if status == "SUCCEEDED":
                raise


def bq_run_writer(table_fqn: str) -> RunWriter:
    from alfab.bq import client

    def _write(row: dict[str, Any]) -> None:
        errors = client().insert_rows_json(table_fqn, [row])
        if errors:
            raise RuntimeError(f"insert em {table_fqn} falhou: {errors}")

    return _write
