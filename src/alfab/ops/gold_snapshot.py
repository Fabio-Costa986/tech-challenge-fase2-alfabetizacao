"""Fotos reais da Gold para a falha controlada ADR-008 (somente leitura no BigQuery).

Antes: captura metadados publicados antes do Workflow de falha.
Depois: comprova em ops que Silver reprovou e Gold nao rodou/publicou;
compara estado da Gold e somente entao grava demo_adr008_gold_depois.json.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from google.cloud import bigquery

from alfab.bq import client, job_config
from alfab.config import ROOT, settings
from alfab.ops.adr_validation import AcceptanceError, check_run_id

EVIDENCE_DIR = ROOT / "evidencias" / "qualidade"


def inspect_gold() -> dict:
    s = settings()
    bq = client()
    tables = {}
    ds = f"{s.project_id}.{s.datasets['gold']}"
    for listed in bq.list_tables(ds):
        if listed.table_type != "TABLE":
            continue
        t = bq.get_table(listed.reference)
        tables[listed.table_id] = {
            "modified": t.modified.isoformat() if t.modified else None,
            "published_run_id": (t.labels or {}).get("published_run_id"),
            "num_rows": t.num_rows,
            "schema": [(c.name, c.field_type, c.mode) for c in t.schema],
        }
    if not tables or "ml_features_municipio" not in tables:
        raise AcceptanceError(f"dataset {ds} nao tem a Gold ML publicada")
    return tables


def check_negative_run(run_id: str) -> None:
    check_run_id(run_id)
    s = settings()
    bq = client()
    params = [bigquery.ScalarQueryParameter("run_id", "STRING", run_id)]
    rows = [dict(r.items()) for r in bq.query(
        f"SELECT step, status FROM `{s.table('ops', 'pipeline_runs')}` WHERE run_id = @run_id "
        "AND step IN ('dbt.silver', 'dbt.gold', 'publish.gold')",
        job_config=job_config(run_id, "ops", "falha_etapas", params=params),
    ).result()]
    silver_failed = any(r["step"] == "dbt.silver" and r["status"] == "FAILED" for r in rows)
    downstream = [r for r in rows if r["step"] in ("dbt.gold", "publish.gold")]
    if not silver_failed or downstream:
        raise AcceptanceError(f"workflow negativo nao comprovado: silver_failed={silver_failed}, "
                              f"downstream={downstream}")
    tests = [dict(r.items()) for r in bq.query(
        f"SELECT test_name, status, severidade, failures FROM `{s.table('ops', 'dq_results')}` "
        "WHERE run_id = @run_id AND test_name = 'assert_avaliados_completos'",
        job_config=job_config(run_id, "ops", "falha_teste", params=params),
    ).result()]
    if not any(t["status"] == "fail" and t["severidade"] == "bloqueante" and
               (t["failures"] or 0) > 0 for t in tests):
        raise AcceptanceError(f"assert_avaliados_completos nao reprovou com falhas reais: {tests}")


def capture(moment: str, negative_run_id: str | None = None, *, directory: Path | None = None) -> Path:
    if moment not in {"antes", "depois"}:
        raise ValueError("momento deve ser antes ou depois")
    directory = directory or EVIDENCE_DIR
    before = directory / "demo_adr008_gold_antes.json"
    target = directory / f"demo_adr008_gold_{moment}.json"
    if target.exists():
        raise FileExistsError(f"evidencia ja existe: {target}; preserve o historico")
    if moment == "depois":
        if not negative_run_id:
            raise ValueError("informe --run-id da execucao negativa para o snapshot depois")
        check_negative_run(negative_run_id)
        if not before.exists():
            raise FileNotFoundError(f"capture a Gold ANTES do teste: {before}")

    tables = inspect_gold()
    if moment == "depois":
        original = json.loads(before.read_text(encoding="utf-8"))
        if tables != original["gold_tables"]:
            raise AcceptanceError("Gold modificada entre antes/depois: nao gravar prova de preservacao")

    data = {
        "observado_em_utc": datetime.now(UTC).isoformat(),
        "projeto": settings().project_id,
        "momento": moment,
        "run_id_teste_negativo": negative_run_id if moment == "depois" else None,
        "gold_tables": tables,
    }
    directory.mkdir(parents=True, exist_ok=True)
    # Exclusividade: evita sobrescrever uma prova ja registrada.
    with target.open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return target
