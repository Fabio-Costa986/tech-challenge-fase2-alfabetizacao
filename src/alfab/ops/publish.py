"""Write-Audit-Publish da Gold.

O dbt constrói e testa a Gold em `gold_staging`. Só depois de TODOS os testes bloqueantes
passarem este passo copia as tabelas para `gold` (o dataset que dashboards e a Fase 3 consomem).
Copy jobs do BigQuery não cobram processamento. Se a etapa gold do dbt falhar, este passo
nem é chamado pelo Workflow, e a Gold publicada permanece a da última execução boa.
"""

from __future__ import annotations

from datetime import UTC, datetime

from google.cloud import bigquery

from alfab.bq import _label, client, run_query
from alfab.config import ROOT, settings
from alfab.observability import bq_run_writer, track_step

VIEWS_DIR = ROOT / "sql" / "gold_views"


def render_view(sql: str, s) -> str:
    return sql.format(project=s.project_id, **s.datasets)


def publish(run_id: str) -> dict:
    s = settings()
    bq = client()
    writer = bq_run_writer(s.table("ops", "pipeline_runs"))
    with track_step(run_id, "batch", "publish.gold", writer) as m:
        staging = f"{s.project_id}.{s.datasets['gold_staging']}"
        tables = [t for t in bq.list_tables(staging) if t.table_type == "TABLE"]
        if not tables:
            raise RuntimeError(f"nenhuma tabela em {staging}: a etapa gold do dbt rodou?")

        copied = {}
        for t in tables:
            dest = s.table("gold", t.table_id)
            job = bq.copy_table(
                f"{staging}.{t.table_id}", dest,
                job_config=bigquery.CopyJobConfig(
                    write_disposition="WRITE_TRUNCATE",
                    labels={"run_id": _label(run_id), "camada": "gold", "etapa": "publish",
                            "app": "alfab"}))
            job.result()
            published = bq.get_table(dest)
            published.labels = {**(published.labels or {}), "published_run_id": _label(run_id)}
            bq.update_table(published, ["labels"])
            copied[t.table_id] = published.num_rows

        for view_file in sorted(VIEWS_DIR.glob("*.sql")):
            run_query(render_view(view_file.read_text(encoding="utf-8"), s), run_id, "gold", "views")

        m.rows_out = sum(copied.values())
        m.details.update(tabelas=copied, publicado_em=datetime.now(UTC))
        return copied

