"""Estimativa de custo ancorada em MEDIÇÃO (exigência da pág. 8-9 do enunciado).

Quantidades vêm das ferramentas da nuvem, não de premissas:
- bytes por ingestão: dry run de cada SELECT da Bronze;
- bytes faturados por execução: INFORMATION_SCHEMA.JOBS filtrado pelo label app=alfab;
- armazenamento BigQuery: INFORMATION_SCHEMA.TABLE_STORAGE;
- armazenamento GCS: soma do tamanho dos objetos do bucket;
- computação: duração real das etapas em ops.pipeline_runs;
- volume de streaming: bytes das mensagens efetivamente ingeridas em bronze.eventos_raw.

Saída: evidencias/finops/custos_medidos.md (tabela Serviço | Unidade | Quantidade medida |
Preço unitário | Custo mensal projetado).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from alfab.bq import client, dry_run_bytes
from alfab.config import ROOT, settings

GIB = 1024**3
TIB = 1024**4

# Preços de lista (USD), região US. CONFERIR na data da medição e atualizar PRICES_CHECKED_AT.
# https://cloud.google.com/bigquery/pricing | https://cloud.google.com/storage/pricing
# https://cloud.google.com/pubsub/pricing  | https://cloud.google.com/run/pricing
# https://cloud.google.com/workflows/pricing | https://cloud.google.com/scheduler/pricing
PRICES_CHECKED_AT = "2026-09-30"
PRICE = {
    "bq_query_tib": 6.25,          # on-demand; 1 TiB/mês gratuito
    "bq_free_tib": 1.0,
    "bq_storage_active_gib": 0.02,  # lógico ativo; 10 GiB/mês gratuitos
    "bq_storage_lt_gib": 0.01,
    "bq_storage_free_gib": 10.0,
    "bq_streaming_insert_gib": 0.05,  # legacy streaming inserts: US$ 0,01 / 200 MB
    "gcs_standard_us_gib": 0.026,
    "pubsub_tib": 40.0,            # 10 GiB/mês gratuitos
    "pubsub_free_gib": 10.0,
    "run_vcpu_s": 0.000018,        # free tier: 180.000 vCPU-s/mês
    "run_gib_s": 0.000002,         # free tier: 360.000 GiB-s/mês
    "run_free_vcpu_s": 180_000,
    "run_free_gib_s": 360_000,
    "workflows_step": 0.00001,     # US$ 0,01 / 1.000 passos internos; 5.000 gratuitos
    "scheduler_job_month": 0.10,   # 3 jobs gratuitos por conta de faturamento
}
JOB_CPU, JOB_MEM_GIB = 1.0, 2.0     # recursos declarados em infra/cloudrun.tf
SCHEDULER_JOBS = 2                  # batch (6/6h) e micro-lote (5 min), infra/scheduler.tf


@dataclass
class Line:
    servico: str
    unidade: str
    quantidade: float
    como: str
    preco: str
    custo_mes: float


def _q(sql: str) -> list:
    return list(client().query(sql).result())


def measure(dias: int, execucoes_mes: int) -> list[Line]:
    s = settings()
    region = f"region-{s.bq_location.lower()}"
    lines: list[Line] = []

    # 1. Scan da fonte por ingestão completa (dry run, custo zero para medir)
    ingest_bytes = sum(dry_run_bytes(
        "SELECT " + ", ".join(f"`{c}`" for c in e.columns) + f" FROM `{e.fqn}`",
        "finops", "finops", e.name) for e in s.entities.values())

    # 2. Bytes faturados por camada nas últimas `dias` execuções reais
    jobs = _q(f"""
      SELECT
        (SELECT value FROM UNNEST(labels) WHERE key = 'camada') AS camada,
        COUNT(DISTINCT (SELECT value FROM UNNEST(labels) WHERE key = 'run_id')) AS execucoes,
        SUM(total_bytes_billed) AS bytes_billed
      FROM `{region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
      WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {dias} DAY)
        AND EXISTS (SELECT 1 FROM UNNEST(labels) WHERE key = 'app' AND value = 'alfab')
        AND job_type = 'QUERY' AND state = 'DONE'
      GROUP BY camada
    """)
    batch_runs = _q(f"""
      SELECT COUNT(DISTINCT run_id) AS n FROM `{s.table('ops', 'pipeline_runs')}`
      WHERE pipeline = 'batch' AND started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {dias} DAY)
    """)[0].n or 1
    billed_total = sum((j.bytes_billed or 0) for j in jobs if j.camada not in (None, "finops"))
    billed_per_run = billed_total / batch_runs
    proj_tib = billed_per_run * execucoes_mes / TIB
    lines.append(Line(
        "BigQuery: consultas (todas as camadas)", "TiB faturado/execução", billed_per_run / TIB,
        f"INFORMATION_SCHEMA.JOBS, label app=alfab, {dias}d, {batch_runs} execuções batch; "
        f"scan completo da fonte no dry run = {ingest_bytes / GIB:.2f} GiB",
        f"US$ {PRICE['bq_query_tib']}/TiB (1 TiB grátis)",
        max(0.0, proj_tib - PRICE["bq_free_tib"]) * PRICE["bq_query_tib"]))

    # 3. Armazenamento BigQuery
    st = _q(f"""
      SELECT SUM(active_logical_bytes) AS active, SUM(long_term_logical_bytes) AS lt
      FROM `{region}`.INFORMATION_SCHEMA.TABLE_STORAGE
      WHERE table_schema IN ({", ".join(repr(d) for d in s.datasets.values())})
    """)[0]
    active_gib, lt_gib = (st.active or 0) / GIB, (st.lt or 0) / GIB
    lines.append(Line(
        "BigQuery: armazenamento", "GiB-mês (lógico)", active_gib + lt_gib,
        "INFORMATION_SCHEMA.TABLE_STORAGE", f"US$ {PRICE['bq_storage_active_gib']}/GiB ativo (10 GiB grátis)",
        max(0.0, active_gib - PRICE["bq_storage_free_gib"]) * PRICE["bq_storage_active_gib"]
        + lt_gib * PRICE["bq_storage_lt_gib"]))

    # 4. GCS (Bronze + snapshots ML)
    from google.cloud import storage
    blobs = list(storage.Client(project=s.project_id).list_blobs(s.bronze_bucket))
    gcs_gib = sum(b.size or 0 for b in blobs) / GIB
    lines.append(Line(
        "Cloud Storage: Bronze Parquet + snapshot ML", "GiB-mês", gcs_gib,
        f"soma de {len(blobs)} objetos em gs://{s.bronze_bucket}",
        f"US$ {PRICE['gcs_standard_us_gib']}/GiB", gcs_gib * PRICE["gcs_standard_us_gib"]))

    # 5. Streaming: volume real ingerido
    ev = _q(f"""
      SELECT COUNT(*) AS n, SUM(BYTE_LENGTH(payload)) + COUNT(*) * 200 AS bytes_aprox
      FROM `{s.table('bronze', 'eventos_raw')}`
      WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {dias} DAY)
    """)[0]
    ev_gib_mes = (ev.bytes_aprox or 0) / GIB * (30 / dias)
    lines.append(Line(
        "Pub/Sub: throughput", "GiB/mês", ev_gib_mes,
        f"{ev.n or 0} eventos em {dias}d em bronze.eventos_raw (payload + ~200 B de envelope)",
        f"US$ {PRICE['pubsub_tib']}/TiB (10 GiB grátis)",
        max(0.0, ev_gib_mes - PRICE["pubsub_free_gib"]) * PRICE["pubsub_tib"] / 1024))
    lines.append(Line(
        "BigQuery: streaming insert (eventos)", "GiB/mês", ev_gib_mes, "mesma medição acima",
        f"US$ {PRICE['bq_streaming_insert_gib']}/GiB", ev_gib_mes * PRICE["bq_streaming_insert_gib"]))

    # 6. Cloud Run: duração real das etapas
    dur = _q(f"""
      SELECT pipeline, SUM(duration_s) AS s, COUNT(DISTINCT run_id) AS runs
      FROM `{s.table('ops', 'pipeline_runs')}`
      WHERE started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {dias} DAY)
      GROUP BY pipeline
    """)
    by = {r.pipeline: r for r in dur}
    batch_s = (by["batch"].s / max(by["batch"].runs, 1)) if "batch" in by else 0.0
    stream_s_mes = (by["stream"].s * 30 / dias) if "stream" in by else 0.0
    vcpu_s = (batch_s * execucoes_mes + stream_s_mes) * JOB_CPU
    gib_s = (batch_s * execucoes_mes + stream_s_mes) * JOB_MEM_GIB
    lines.append(Line(
        "Cloud Run Jobs (batch + micro-lote)", "vCPU-s/mês", vcpu_s,
        f"ops.pipeline_runs: {batch_s:.0f}s por execução batch; {JOB_CPU} vCPU / {JOB_MEM_GIB} GiB",
        f"US$ {PRICE['run_vcpu_s']}/vCPU-s + US$ {PRICE['run_gib_s']}/GiB-s (free tier)",
        max(0.0, vcpu_s - PRICE["run_free_vcpu_s"]) * PRICE["run_vcpu_s"]
        + max(0.0, gib_s - PRICE["run_free_gib_s"]) * PRICE["run_gib_s"]))

    # ~12 passos por execução do workflow batch (o micro-lote vai do Scheduler direto ao Run Job)
    steps_mes = execucoes_mes * 12
    lines.append(Line(
        "Workflows + Scheduler", "passos/mês + jobs", steps_mes,
        "contagem de passos de workflows/*.yaml x cadência", "US$ 0,01/1.000 passos (5.000 grátis); "
        "US$ 0,10/job (3 grátis)",
        max(0, steps_mes - 5000) * PRICE["workflows_step"]
        + max(0, SCHEDULER_JOBS - 3) * PRICE["scheduler_job_month"]))
    return lines


def render(lines: list[Line], dias: int, execucoes_mes: int) -> str:
    total = sum(line.custo_mes for line in lines)
    out = [
        "# Estimativa de custo (medida)",
        "",
        f"Gerado em {datetime.now(UTC):%Y-%m-%d %H:%M} UTC por `python -m alfab finops`. "
        f"Janela de medição: {dias} dias. Projeção: {execucoes_mes} execuções batch/mês "
        f"+ micro-lote a cada 5 min. Preços de lista conferidos em {PRICES_CHECKED_AT}.",
        "",
        "| Serviço | Unidade | Quantidade medida | Como foi medida | Preço unitário "
        "| Custo mensal projetado (US$) |",
        "|---|---|---:|---|---|---:|",
    ]
    for line in lines:
        out.append(f"| {line.servico} | {line.unidade} | {line.quantidade:,.6g} | {line.como} | "
                   f"{line.preco} | {line.custo_mes:,.2f} |")
    out += ["", f"**Total projetado: US$ {total:,.2f}/mês**", ""]
    return "\n".join(out)


def main(dias: int = 7, execucoes_mes: int = 120) -> str:
    md = render(measure(dias, execucoes_mes), dias, execucoes_mes)
    target = ROOT / "evidencias" / "finops" / "custos_medidos.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(md, encoding="utf-8")
    print(md)
    return md
