"""Executa analises/01_profiling_fonte.sql e salva cada resultado em evidencias/profiling/<nome>.csv.

Cada query passa por dry run antes (bytes estimados no log) e respeita maximum_bytes_billed.
"""

from __future__ import annotations

import csv
import re

from alfab.bq import dry_run_bytes, run_query
from alfab.config import ROOT
from alfab.observability import log

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


def run(run_id: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, sql in split_named_queries(SQL_FILE.read_text(encoding="utf-8")):
        estimated = dry_run_bytes(sql, run_id, "profiling", name)
        job = run_query(sql, run_id, "profiling", name)
        rows = list(job.result())
        target = OUT_DIR / f"{name}.csv"
        with target.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if rows:
                writer.writerow(rows[0].keys())
                writer.writerows([list(r.values()) for r in rows])
        log("profiling salvo", event="profiling", query=name, rows=len(rows),
            bytes_estimados=estimated, bytes_faturados=job.total_bytes_billed, job_id=job.job_id,
            arquivo=str(target.relative_to(ROOT)))
