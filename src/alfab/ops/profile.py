"""Executa um arquivo de consultas nomeadas (padrão: analises/01_profiling_fonte.sql) e salva cada
resultado em CSV (padrão: evidencias/profiling/<nome>.csv).

Cada query passa por dry run antes (bytes estimados no log) e respeita maximum_bytes_billed.
"""

from __future__ import annotations

import csv
import re

from alfab.bq import dry_run_bytes, run_query
from alfab.config import ROOT
from alfab.observability import log
from alfab.ops.adr_validation import validate

SQL_FILE = ROOT / "analises" / "01_profiling_fonte.sql"
OUT_DIR = ROOT / "evidencias" / "profiling"


def split_named_queries(text: str) -> list[tuple[str, str]]:
    blocks = re.split(r"^-- name:\s*(\S+)\s*$", text, flags=re.M)
    pairs = []
    for name, body in zip(blocks[1::2], blocks[2::2], strict=True):
        sql = body.strip().rstrip(";").strip()
        if sql:
            pairs.append((name, sql))
    return pairs


def run(run_id: str, sql_file: str | None = None, out_dir: str | None = None,
        aceite_run_id: str | None = None) -> None:
    if aceite_run_id:
        validate(aceite_run_id)  # nao atualizar CSVs com a Gold anterior
    source = (ROOT / sql_file) if sql_file else SQL_FILE
    target_dir = (ROOT / out_dir) if out_dir else OUT_DIR
    queries = split_named_queries(source.read_text(encoding="utf-8"))
    if not queries:
        raise ValueError(f"arquivo sem consultas nomeadas: {source}")
    collected = []
    for name, sql in queries:
        estimated = dry_run_bytes(sql, run_id, "profiling", name)
        job = run_query(sql, run_id, "profiling", name)
        rows = list(job.result())
        collected.append((name, rows, estimated, job.total_bytes_billed, job.job_id))

    # So comeca a substituir os CSVs depois de TODAS as consultas terem sucesso.
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, rows, estimated, billed, job_id in collected:
        target = target_dir / f"{name}.csv"
        with target.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if rows:
                writer.writerow(rows[0].keys())
                writer.writerows([list(r.values()) for r in rows])
        log("profiling salvo", event="profiling", query=name, rows=len(rows),
            bytes_estimados=estimated, bytes_faturados=billed, job_id=job_id,
            arquivo=str(target.relative_to(ROOT)))
