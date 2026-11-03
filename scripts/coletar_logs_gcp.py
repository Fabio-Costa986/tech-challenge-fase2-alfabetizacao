"""Exporta, pelas APIs do GCP, os registros que o console mostra: execuções e logs de batch e streaming.

Uso:  python scripts/coletar_logs_gcp.py [--desde 2026-11-02T00:00:00Z]
Saída:
  evidencias/batch/workflow_execucoes.md       execuções do Cloud Workflows (estado, horários, argumento)
  evidencias/batch/cloud_run_jobs_execucoes.md execuções dos Cloud Run Jobs (imagem, status, horários)
  evidencias/batch/logs_etapas.md              logs estruturados `step_finished` das etapas batch
  evidencias/streaming/logs_streaming.md       simulador, ingestor (eventos recebidos/quarentena) e micro-lote
Autenticação: Application Default Credentials. O Cloud Logging guarda os logs por 30 dias (bucket _Default).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import google.auth
from google.auth.transport.requests import AuthorizedSession

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alfab.config import settings  # noqa: E402

JOBS = [
    "alfab-ingest-bronze",
    "alfab-dbt-silver",
    "alfab-dbt-gold",
    "alfab-publish-gold",
    "alfab-export-ml",
    "alfab-simulator",
    "alfab-microbatch",
]
STREAM_JOBS = {"alfab-simulator", "alfab-microbatch"}


class Api:
    def __init__(self, projeto: str) -> None:
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        self.s, self.p = AuthorizedSession(creds), projeto
        self.h = {"x-goog-user-project": projeto}

    def get_all(self, url: str, chave: str, params: dict | None = None) -> list[dict]:
        itens, token = [], None
        while True:
            q = {**(params or {}), **({"pageToken": token} if token else {})}
            r = self.s.get(url, params=q, headers=self.h, timeout=120)
            r.raise_for_status()
            body = r.json()
            itens += body.get(chave, [])
            token = body.get("nextPageToken")
            if not token:
                return itens

    def logs(self, filtro: str, limite: int = 5000) -> list[dict]:
        itens, token = [], None
        while len(itens) < limite:
            body = {
                "resourceNames": [f"projects/{self.p}"],
                "filter": filtro,
                "orderBy": "timestamp asc",
                "pageSize": 1000,
                **({"pageToken": token} if token else {}),
            }
            r = self.s.post(
                "https://logging.googleapis.com/v2/entries:list", json=body, headers=self.h, timeout=120
            )
            r.raise_for_status()
            data = r.json()
            itens += data.get("entries", [])
            token = data.get("nextPageToken")
            if not token:
                break
        return itens


def _h(ts: str | None) -> str:
    return ts.replace("T", " ")[:19] if ts else "—"


def _cab(titulo: str, fonte: str, desde: str) -> list[str]:
    return [
        f"# {titulo}",
        "",
        f"Exportado em {datetime.now(UTC):%Y-%m-%d %H:%M} UTC por `python scripts/coletar_logs_gcp.py`, "
        f"a partir {fonte}. Período: desde {desde}. Horários em UTC.",
        "",
    ]


def workflows(api: Api, regiao: str, desde: str) -> str:
    url = (
        f"https://workflowexecutions.googleapis.com/v1/projects/{api.p}/locations/{regiao}/"
        "workflows/alfab-pipeline-batch/executions"
    )
    exs = [
        e
        for e in api.get_all(url, "executions", {"pageSize": 100, "view": "FULL"})
        if e.get("startTime", "") >= desde
    ]
    md = _cab(
        "Execuções do Cloud Workflows `alfab-pipeline-batch`",
        "da API `workflowexecutions.googleapis.com`",
        desde,
    )
    md += ["| execução | estado | início | fim | argumento | erro |", "|---|---|---|---|---|---|"]
    for e in sorted(exs, key=lambda x: x["startTime"]):
        erro = json.dumps(e.get("error", {}).get("payload", ""))[:120] if e.get("error") else ""
        md.append(
            f"| `{e['name'].split('/')[-1]}` | **{e.get('state')}** | {_h(e.get('startTime'))} | "
            f"{_h(e.get('endTime'))} | `{e.get('argument', '')}` | {erro.replace('|', '/')} |"
        )
    return "\n".join(md) + "\n"


def jobs(api: Api, regiao: str, desde: str) -> str:
    md = _cab("Execuções dos Cloud Run Jobs", "da API `run.googleapis.com/v2`", desde)
    md += [
        "| job | execução | imagem (digest) | criada | concluída | resultado |",
        "|---|---|---|---|---|---|",
    ]
    for job in JOBS:
        url = f"https://run.googleapis.com/v2/projects/{api.p}/locations/{regiao}/jobs/{job}/executions"
        for e in sorted(
            api.get_all(url, "executions", {"pageSize": 100}), key=lambda x: x.get("createTime", "")
        ):
            if e.get("createTime", "") < desde:
                continue
            img = (
                e.get("template", {})
                .get("containers", [{}])[0]
                .get("image", "")
                .split("@")[-1]
                .split(":")[-1][:12]
            )
            res = (
                "SUCEDEU"
                if e.get("succeededCount")
                else "FALHOU"
                if e.get("failedCount")
                else "CANCELADA"
                if e.get("cancelledCount")
                else "em andamento"
            )
            md.append(
                f"| {job} | `{e['name'].split('/')[-1]}` | `{img}` | {_h(e.get('createTime'))} | "
                f"{_h(e.get('completionTime'))} | **{res}** |"
            )
    return "\n".join(md) + "\n"


def etapas(api: Api, desde: str) -> tuple[str, list[dict]]:
    ents = api.logs(
        f'resource.type="cloud_run_job" AND jsonPayload.event="step_finished" ' f'AND timestamp>="{desde}"'
    )
    md = _cab(
        "Logs das etapas batch (Cloud Logging)",
        "da API `logging.googleapis.com`, filtro " '`jsonPayload.event="step_finished"`',
        desde,
    )
    md += [
        "| horário do log | job | run_id | etapa | status | duração (s) | linhas saída | erro |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for e in ents:
        job = e.get("resource", {}).get("labels", {}).get("job_name", "")
        if job in STREAM_JOBS:
            continue
        j = e.get("jsonPayload", {})
        md.append(
            f"| {_h(e.get('timestamp'))} | {job} | `{j.get('run_id')}` | {j.get('step')} | "
            f"**{j.get('status')}** | {j.get('duration_s')} | {j.get('rows_out') or ''} | "
            f"{(j.get('error') or '')[:110].replace('|', '/')} |"
        )
    return "\n".join(md) + "\n", ents


def streaming(api: Api, desde: str, etapas_ents: list[dict]) -> str:
    md = _cab("Logs do streaming (Cloud Logging)", "da API `logging.googleapis.com`", desde)
    md += [
        "## Simulador e micro-lote (`step_finished`)",
        "",
        "| horário do log | job | run_id | status | duração (s) | detalhes |",
        "|---|---|---|---|---|---|",
    ]
    for e in etapas_ents:
        job = e.get("resource", {}).get("labels", {}).get("job_name", "")
        if job not in STREAM_JOBS:
            continue
        j = e.get("jsonPayload", {})
        det = j.get("details", "")
        try:
            d = json.loads(det)
            det = (
                json.dumps(d.get("counts"), ensure_ascii=False)
                if job == "alfab-simulator"
                else "lidas={lidas} únicas={unicas} inseridas={inseridas} "
                "duplicatas={duplicatas_descartadas} "
                "quarentena={quarentena_referencial} p50={latencia_ingestao_p50_s}s "
                "p95={latencia_ingestao_p95_s}s".format(
                    **{
                        k: d.get(k)
                        for k in (
                            "lidas",
                            "unicas",
                            "inseridas",
                            "duplicatas_descartadas",
                            "quarentena_referencial",
                            "latencia_ingestao_p50_s",
                            "latencia_ingestao_p95_s",
                        )
                    }
                )
            )
        except (ValueError, TypeError, AttributeError):
            pass
        md.append(
            f"| {_h(e.get('timestamp'))} | {job} | `{j.get('run_id')}` | **{j.get('status')}** | "
            f"{j.get('duration_s')} | {str(det).replace('|', '/')} |"
        )

    ing = api.logs(
        'resource.type="cloud_run_revision" AND resource.labels.service_name="alfab-event-ingestor" '
        f'AND jsonPayload.event=("event_ingested" OR "event_quarantined") AND timestamp>="{desde}"',
        limite=20000,
    )
    cont = Counter((e["timestamp"][:10], e["jsonPayload"]["event"]) for e in ing)
    md += [
        "",
        "## Ingestor `alfab-event-ingestor`: eventos recebidos do Pub/Sub",
        "",
        "Cada evento entregue pelo push do Pub/Sub gera um log: `event_ingested` (gravado em "
        "`bronze.eventos_raw`) ou `event_quarantined` (gravado em `bronze.eventos_quarentena`).",
        "",
        "| dia | eventos ingeridos | eventos em quarentena |",
        "|---|---|---|",
    ]
    for dia in sorted({d for d, _ in cont}):
        md.append(f"| {dia} | {cont[(dia, 'event_ingested')]} | {cont[(dia, 'event_quarantined')]} |")
    amostra = [e for e in ing if e["jsonPayload"]["event"] == "event_ingested"][:5] + [
        e for e in ing if e["jsonPayload"]["event"] == "event_quarantined"
    ][:3]
    md += [
        "",
        "Amostra de entradas (primeiras do período):",
        "",
        "| horário do log | evento | event_id / message_id | latência de ingestão (s) |",
        "|---|---|---|---|",
    ]
    for e in amostra:
        j = e["jsonPayload"]
        md.append(
            f"| {_h(e.get('timestamp'))} | {j['event']} | `{j.get('event_id') or j.get('message_id')}` | "
            f"{round(j['latency_s'], 3) if j.get('latency_s') is not None else '—'} |"
        )

    req = api.logs(
        'resource.type="cloud_run_revision" AND resource.labels.service_name="alfab-event-ingestor" '
        f'AND httpRequest.requestUrl:"/pubsub/push" AND timestamp>="{desde}"',
        limite=20000,
    )
    st = Counter(str(e.get("httpRequest", {}).get("status")) for e in req)
    md += [
        "",
        "## Requisições HTTP de push recebidas pelo ingestor",
        "",
        "| status HTTP | requisições |",
        "|---|---|",
    ] + [f"| {k} | {v} |" for k, v in sorted(st.items())]
    md += [
        "",
        "204 = evento aceito (ingerido ou em quarentena, ambos com ACK). 403 = chamada sem a identidade "
        "OIDC do push, bloqueada. 5xx levaria o Pub/Sub a tentar de novo e, após 5 falhas, "
        "à fila de descarte.",
    ]
    return "\n".join(md) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2026-11-02T00:00:00Z")
    a = ap.parse_args()
    s = settings()
    api = Api(s.project_id)
    (ROOT / "evidencias" / "batch").mkdir(parents=True, exist_ok=True)
    (ROOT / "evidencias" / "streaming").mkdir(parents=True, exist_ok=True)
    (ROOT / "evidencias/batch/workflow_execucoes.md").write_text(
        workflows(api, s.region, a.desde), encoding="utf-8"
    )
    (ROOT / "evidencias/batch/cloud_run_jobs_execucoes.md").write_text(
        jobs(api, s.region, a.desde), encoding="utf-8"
    )
    md, ents = etapas(api, a.desde)
    (ROOT / "evidencias/batch/logs_etapas.md").write_text(md, encoding="utf-8")
    (ROOT / "evidencias/streaming/logs_streaming.md").write_text(
        streaming(api, a.desde, ents), encoding="utf-8"
    )
    print("ok")


if __name__ == "__main__":
    main()
