"""Aceite de ADR-008/009 somente leitura: consulta a execucao e a Gold reais no GCP.

Nao altera dados nem cria tabelas. Falha fechada caso falte qualquer comprovacao.
O CI local nao substitui esta validacao integrada em um ambiente autorizado.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from google.cloud import bigquery

from alfab.bq import _label, client, job_config
from alfab.config import Settings, settings

_REQUIRED_STEPS = ("dbt.silver", "dbt.gold", "publish.gold")
_REQUIRED_TESTS = ("assert_avaliados_completos", "assert_ml_sem_vazamento")
_FORBIDDEN = "feat_meta_pactuada_t_mais_1"


class AcceptanceError(RuntimeError):
    """Ausencia de prova suficiente para renovar as evidencias da ADR."""


@dataclass(frozen=True)
class Acceptance:
    run_id: str
    project: str
    gold_table: str
    gold_rows: int | None
    published_run_id: str
    tests: tuple[str, ...]


def check_run_id(run_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,63}", run_id):
        raise AcceptanceError("run_id invalido; informe exatamente o ID retornado pelo Workflow")
    return run_id


def check_ml_schema(columns: list[str] | tuple[str, ...], table: str) -> None:
    names = {c.lower() for c in columns}
    if _FORBIDDEN in names:
        raise AcceptanceError(f"{table} ainda tem a feature proibida {_FORBIDDEN}; nao gere evidencia/export")
    if "alvo_taxa_t_mais_1" not in names:
        raise AcceptanceError(f"{table} sem o alvo esperado alvo_taxa_t_mais_1")
    targets = [n for n in names if n.startswith("alvo_")]
    if len(targets) != 1:
        raise AcceptanceError(f"{table} tem {len(targets)} alvos (esperado: 1)")
    for field in ("id_municipio", "rede_canonica", "ano_referencia"):
        if field not in names:
            raise AcceptanceError(f"{table} sem a chave de grao {field}")


def validate(run_id: str, *, bq_client=None, cfg: Settings | None = None) -> Acceptance:
    """Exige steps SUCCEEDED, testes pass e schema/label da Gold publicada da mesma execucao."""
    check_run_id(run_id)
    s = cfg or settings()
    bq = bq_client or client()
    query_params = [bigquery.ScalarQueryParameter("run_id", "STRING", run_id)]
    rows = [dict(r.items()) for r in bq.query(
        f"SELECT step, status FROM `{s.table('ops', 'pipeline_runs')}` "
        "WHERE run_id = @run_id AND step IN ('dbt.silver', 'dbt.gold', 'publish.gold')",
        job_config=job_config(run_id, "ops", "aceite_etapas", params=query_params),
    ).result()]
    for step in _REQUIRED_STEPS:
        statuses = [r["status"] for r in rows if r["step"] == step]
        if not statuses or any(status != "SUCCEEDED" for status in statuses):
            raise AcceptanceError(f"{run_id}: etapa {step} sem comprovacao de sucesso: {statuses}")

    tests = [dict(r.items()) for r in bq.query(
        f"SELECT test_name, status, severidade FROM `{s.table('ops', 'dq_results')}` "
        "WHERE run_id = @run_id AND test_name IN "
        "('assert_avaliados_completos', 'assert_ml_sem_vazamento')",
        job_config=job_config(run_id, "ops", "aceite_testes", params=query_params),
    ).result()]
    for name in _REQUIRED_TESTS:
        matched = [r for r in tests if r["test_name"] == name]
        if not matched or any(r["status"] != "pass" or r["severidade"] != "bloqueante"
                              for r in matched):
            raise AcceptanceError(f"{run_id}: teste {name} nao comprovado como pass/bloqueante: {matched}")

    published = s.table("gold", "ml_features_municipio")
    ml_table = bq.get_table(published)
    check_ml_schema([c.name for c in ml_table.schema], published)
    meta_name = s.table("gold", "meta_vs_resultado")
    meta_table = bq.get_table(meta_name)
    if "meta_pactuada_pct" not in {c.name.lower() for c in meta_table.schema}:
        raise AcceptanceError("gold.meta_vs_resultado perdeu meta_pactuada_pct")
    expected = _label(run_id)
    for table_name, table in ((published, ml_table), (meta_name, meta_table)):
        label = (table.labels or {}).get("published_run_id")
        if label != expected:
            raise AcceptanceError(f"{table_name}: published_run_id={label!r}; esperado {expected!r}")
    return Acceptance(run_id, s.project_id, published, ml_table.num_rows, expected, _REQUIRED_TESTS)
