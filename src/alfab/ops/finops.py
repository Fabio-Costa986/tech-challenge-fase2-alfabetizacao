"""Estimativa de custo ancorada em MEDIÇÃO (exigência da pág. 8-9 do enunciado).

Quantidades vêm das ferramentas da nuvem, não de premissas:
- bytes por ingestão: dry run de cada SELECT da Bronze e bytes faturados do EXPORT DATA;
- bytes faturados por execução: INFORMATION_SCHEMA.JOBS, pelo label run_id de cada job;
- armazenamento BigQuery: metatabela __TABLES__ de cada dataset;
- armazenamento GCS: soma do tamanho dos objetos do bucket;
- computação: duração real das etapas em ops.pipeline_runs;
- volume de streaming: bytes das mensagens efetivamente ingeridas em bronze.eventos_raw.

A projeção usa a CADÊNCIA PRETENDIDA em produção (batch a cada 6 h, micro-lote a cada 5 min), não
o número de execuções que aconteceram na janela de medição.

Saída: evidencias/finops/custos_medidos.md, com duas leituras: preço de lista e com nível gratuito.
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
JOB_CPU, JOB_MEM_GIB = 1.0, 2.0      # recursos declarados em infra/cloudrun.tf
SCHEDULER_JOBS = 2                   # batch (6/6 h) e micro-lote (5 min), infra/orchestration.tf
MICROBATCH_RUNS_MES = 30 * 24 * 12   # a cada 5 min (infra/variables.tf: microbatch_schedule)


@dataclass
class Line:
    servico: str
    unidade: str
    quantidade: float
    como: str
    preco: str
    custo_lista: float      # preço de lista, sem nenhum nível gratuito
    custo_free_tier: float  # após o nível gratuito mensal


def _q(sql: str) -> list:
    return list(client().query(sql).result())


def _median(values: list[float]) -> float:
    v = sorted(values)
    if not v:
        return 0.0
    mid = len(v) // 2
    return v[mid] if len(v) % 2 else (v[mid - 1] + v[mid]) / 2


def measure(dias: int, execucoes_mes: int, ingestoes_mes: int = 1) -> list[Line]:
    s = settings()
    region = f"region-{s.bq_location.lower()}"
    lines: list[Line] = []

    # 1. Scan da fonte por ingestão completa (dry run, custo zero para medir)
    dry_bytes = sum(dry_run_bytes(
        "SELECT " + ", ".join(f"`{c}`" for c in e.columns) + f" FROM `{e.fqn}`",
        "finops", "finops", e.name) for e in s.entities.values())

    # 2. Bytes FATURADOS por execução (label run_id), separados em ingestão (bronze) e transformação
    publicadas = {r.run_id.lower() for r in _q(f"""
      SELECT DISTINCT run_id FROM `{s.table('ops', 'pipeline_runs')}`
      WHERE step = 'publish.gold' AND status = 'SUCCEEDED'
        AND started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {dias} DAY)""")}
    jobs = _q(f"""
      SELECT (SELECT value FROM UNNEST(labels) WHERE key = 'run_id') AS run_id,
             (SELECT value FROM UNNEST(labels) WHERE key = 'camada') = 'bronze' AS ingestao,
             SUM(total_bytes_billed) AS b
      FROM `{region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
      WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {dias} DAY)
        AND EXISTS (SELECT 1 FROM UNNEST(labels) WHERE key = 'app' AND value = 'alfab')
        AND state = 'DONE'
      GROUP BY 1, 2""")
    ingest_b = max([j.b or 0 for j in jobs if j.ingestao], default=0)
    transf_b = _median([j.b or 0 for j in jobs if not j.ingestao and j.run_id in publicadas])
    bq_tib = (ingest_b * ingestoes_mes + transf_b * execucoes_mes) / TIB
    lines.append(Line(
        "BigQuery: ingestão da fonte (EXPORT DATA)", "GiB faturado por ingestão completa", ingest_b / GIB,
        f"INFORMATION_SCHEMA.JOBS, label camada=bronze (dry run das 8 entidades: {dry_bytes / GIB:.2f} GiB). "
        f"Só ocorre quando a fonte muda: {ingestoes_mes}/mês",
        f"US$ {PRICE['bq_query_tib']}/TiB", ingest_b * ingestoes_mes / TIB * PRICE["bq_query_tib"], 0.0))
    lines.append(Line(
        "BigQuery: Silver + Gold + testes (dbt)", "GiB faturado por execução", transf_b / GIB,
        f"INFORMATION_SCHEMA.JOBS por run_id, mediana de {len(publicadas)} execuções publicadas; "
        f"{execucoes_mes} execuções/mês",
        f"US$ {PRICE['bq_query_tib']}/TiB (1 TiB/mês grátis no total)",
        transf_b * execucoes_mes / TIB * PRICE["bq_query_tib"],
        max(0.0, bq_tib - PRICE["bq_free_tib"]) * PRICE["bq_query_tib"]))

    # 3. Armazenamento BigQuery (metatabela __TABLES__ de cada dataset: não exige permissão regional)
    union = " UNION ALL ".join(
        f"SELECT size_bytes FROM `{s.project_id}.{d}.__TABLES__`" for d in s.datasets.values())
    st_gib = (_q(f"SELECT SUM(size_bytes) AS b FROM ({union})")[0].b or 0) / GIB
    lines.append(Line(
        "BigQuery: armazenamento", "GiB-mês (lógico ativo)", st_gib,
        "soma de size_bytes em <dataset>.__TABLES__ (bronze, silver, gold_staging, gold, ops)",
        f"US$ {PRICE['bq_storage_active_gib']}/GiB (10 GiB grátis)",
        st_gib * PRICE["bq_storage_active_gib"],
        max(0.0, st_gib - PRICE["bq_storage_free_gib"]) * PRICE["bq_storage_active_gib"]))

    # 4. GCS (Bronze): cresce um snapshot por atualização da fonte
    from google.cloud import storage
    blobs = list(storage.Client(project=s.project_id).list_blobs(s.bronze_bucket))
    gcs_gib = sum(b.size or 0 for b in blobs) / GIB
    lines.append(Line(
        "Cloud Storage: Bronze Parquet ZSTD", "GiB-mês", gcs_gib,
        f"soma de {len(blobs)} objetos em gs://{s.bronze_bucket} (1 snapshot das 8 entidades)",
        f"US$ {PRICE['gcs_standard_us_gib']}/GiB", gcs_gib * PRICE["gcs_standard_us_gib"],
        gcs_gib * PRICE["gcs_standard_us_gib"]))

    # 5. Streaming: volume real ingerido, projetado para 30 dias no mesmo ritmo da janela medida
    ev = _q(f"""
      SELECT COUNT(*) AS n, SUM(BYTE_LENGTH(payload)) + COUNT(*) * 200 AS bytes_aprox
      FROM `{s.table('bronze', 'eventos_raw')}`
      WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {dias} DAY)""")[0]
    ev_gib_mes = (ev.bytes_aprox or 0) / GIB * (30 / dias)
    lines.append(Line(
        "Pub/Sub + streaming insert (eventos)", "GiB/mês", ev_gib_mes,
        f"{ev.n or 0} entregas em {dias}d em bronze.eventos_raw (payload + ~200 B de envelope), x 30/{dias}",
        f"US$ {PRICE['pubsub_tib']}/TiB (10 GiB grátis) + US$ {PRICE['bq_streaming_insert_gib']}/GiB",
        ev_gib_mes * (PRICE["pubsub_tib"] / 1024 + PRICE["bq_streaming_insert_gib"]),
        max(0.0, ev_gib_mes - PRICE["pubsub_free_gib"]) * PRICE["pubsub_tib"] / 1024
        + ev_gib_mes * PRICE["bq_streaming_insert_gib"]))

    # 6. Cloud Run Jobs: duração real das etapas (por execução publicada) x cadência pretendida
    batch = _q(f"""
      SELECT run_id, SUM(duration_s) AS s FROM `{s.table('ops', 'pipeline_runs')}`
      WHERE pipeline = 'batch' AND started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {dias} DAY)
      GROUP BY run_id""")
    batch_s = _median([r.s for r in batch if r.run_id.lower() in publicadas])
    mb = _q(f"""
      SELECT AVG(duration_s) AS s, COUNT(*) AS n FROM `{s.table('ops', 'pipeline_runs')}`
      WHERE step = 'microbatch.silver.eventos' AND status = 'SUCCEEDED'
        AND started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {dias} DAY)""")[0]
    mb_s = mb.s or 0.0
    total_s = batch_s * execucoes_mes + mb_s * MICROBATCH_RUNS_MES
    vcpu_s, gib_s = total_s * JOB_CPU, total_s * JOB_MEM_GIB
    lines.append(Line(
        "Cloud Run Jobs (batch + micro-lote)", "vCPU-s/mês", vcpu_s,
        f"ops.pipeline_runs: {batch_s:.0f} s por batch publicado x {execucoes_mes}/mês; "
        f"{mb_s:.1f} s por micro-lote (média de {mb.n}) x {MICROBATCH_RUNS_MES}/mês; "
        f"{JOB_CPU:g} vCPU, {JOB_MEM_GIB:g} GiB. Não inclui o tempo de inicialização do container",
        f"US$ {PRICE['run_vcpu_s']}/vCPU-s + US$ {PRICE['run_gib_s']}/GiB-s "
        f"({PRICE['run_free_vcpu_s']:,} vCPU-s grátis)",
        vcpu_s * PRICE["run_vcpu_s"] + gib_s * PRICE["run_gib_s"],
        max(0.0, vcpu_s - PRICE["run_free_vcpu_s"]) * PRICE["run_vcpu_s"]
        + max(0.0, gib_s - PRICE["run_free_gib_s"]) * PRICE["run_gib_s"]))

    # 7. Orquestração: ~12 passos por execução do workflow; o micro-lote vai do Scheduler direto ao job
    steps_mes = execucoes_mes * 12
    lines.append(Line(
        "Workflows + Cloud Scheduler", "passos/mês", steps_mes,
        f"12 passos (workflows/pipeline_batch.yaml) x {execucoes_mes}/mês; "
        f"{SCHEDULER_JOBS} jobs do Scheduler",
        "US$ 0,01/1.000 passos (5.000 grátis); US$ 0,10/job (3 grátis)",
        steps_mes * PRICE["workflows_step"] + SCHEDULER_JOBS * PRICE["scheduler_job_month"],
        max(0, steps_mes - 5000) * PRICE["workflows_step"]
        + max(0, SCHEDULER_JOBS - 3) * PRICE["scheduler_job_month"]))
    return lines


def _n(v: float) -> str:
    txt = f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.4g}"
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")


def render(lines: list[Line], dias: int, execucoes_mes: int) -> str:
    lista = sum(line.custo_lista for line in lines)
    free = sum(line.custo_free_tier for line in lines)
    out = [
        "# Estimativa de custo (medida)",
        "",
        f"Gerado em {datetime.now(UTC):%Y-%m-%d %H:%M} UTC por `python -m alfab finops`. "
        f"Janela de medição: {dias} dias. Cadência projetada (produção): {execucoes_mes} execuções batch/mês "
        f"(a cada 6 h) e micro-lote a cada 5 min. Preços de lista (US) conferidos em {PRICES_CHECKED_AT}.",
        "",
        "Duas leituras do mesmo desenho: **preço de lista** (sem nenhum nível gratuito: é o custo se a "
        "franquia já estiver consumida por outras cargas) e **com o nível gratuito mensal** do GCP.",
        "",
        "| Serviço | Unidade | Quantidade medida | Como foi medida | Preço unitário "
        "| Custo mensal de lista (US$) | Com nível gratuito (US$) |",
        "|---|---|---:|---|---|---:|---:|",
    ]
    for line in lines:
        out.append(f"| {line.servico} | {line.unidade} | {_n(line.quantidade)} | {line.como} | "
                   f"{line.preco} | {line.custo_lista:,.2f} | {line.custo_free_tier:,.2f} |")
    out += ["", f"**Total projetado: US$ {lista:,.2f}/mês a preço de lista; "
                f"US$ {free:,.2f}/mês com o nível gratuito.**", ""]
    return "\n".join(out)


def main(dias: int = 7, execucoes_mes: int = 120) -> str:
    md = render(measure(dias, execucoes_mes), dias, execucoes_mes)
    target = ROOT / "evidencias" / "finops" / "custos_medidos.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(md, encoding="utf-8")
    print(md)
    return md
