"""Gera evidencias/monitoramento/incidentes.md a partir da API de alertas do Cloud Monitoring.

Uso:  python scripts/incidentes_alerta.py
Cruza cada etapa FAILED de ops.pipeline_runs com o primeiro incidente da política
"alfab: etapa do pipeline FALHOU" aberto para o mesmo job, e mede o tempo até o alerta.
Autenticação: Application Default Credentials (gcloud auth application-default login).
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import google.auth
from google.auth.transport.requests import AuthorizedSession

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alfab.bq import client  # noqa: E402
from alfab.config import settings  # noqa: E402

OUT = ROOT / "evidencias" / "monitoramento" / "incidentes.md"
POLITICA = "alfab: etapa do pipeline FALHOU"


def incidentes(projeto: str) -> list[dict]:
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    sess = AuthorizedSession(creds)
    url = f"https://monitoring.googleapis.com/v3/projects/{projeto}/alerts"
    alertas, token = [], None
    while True:
        params = {"pageSize": 100, **({"pageToken": token} if token else {})}
        resp = sess.get(url, params=params, headers={"x-goog-user-project": projeto}, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        alertas += body.get("alerts", [])
        token = body.get("nextPageToken")
        if not token:
            return alertas


def _ts(valor: str) -> datetime:
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def main() -> None:
    s = settings()
    alertas = incidentes(s.project_id)
    falhas = list(client().query(f"""
        SELECT run_id, step, ended_at FROM `{s.table('ops', 'pipeline_runs')}`
        WHERE status = 'FAILED' ORDER BY ended_at""").result())

    linhas = []
    for f in falhas:
        job = "alfab-" + f.step.replace(".", "-")
        candidatos = [a for a in alertas
                      if a.get("policy", {}).get("displayName") == POLITICA
                      and a.get("resource", {}).get("labels", {}).get("job_name") == job
                      and _ts(a["openTime"]) >= f.ended_at]
        if not candidatos:
            linhas.append((f.run_id, f.step, f.ended_at, None, None))
            continue
        a = min(candidatos, key=lambda x: x["openTime"])
        segundos = (_ts(a["openTime"]) - f.ended_at).total_seconds()
        linhas.append((f.run_id, f.step, f.ended_at, _ts(a["openTime"]), segundos))

    md = [
        "# Alertas disparados (Cloud Monitoring)",
        "",
        f"Gerado em {datetime.now(UTC):%Y-%m-%d %H:%M} UTC por `python scripts/incidentes_alerta.py`, "
        "a partir da API `monitoring.googleapis.com/v3/projects/<projeto>/alerts`. Canal: e-mail do grupo.",
        "",
        "## Tempo entre a falha e a abertura do incidente",
        "",
        f"Política `{POLITICA}` (log-based metric `alfab/step_failed`). Horários em UTC.",
        "",
        "| run_id | etapa | data | falha registrada (ops.pipeline_runs) | incidente aberto "
        "| tempo até o alerta |",
        "|---|---|---|---|---|---|",
    ]
    for run_id, step, falha, aberto, seg in linhas:
        tempo = f"**{int(seg // 60)} min {int(seg % 60)} s**" if seg is not None else "sem incidente"
        hora_alerta = f"{aberto:%H:%M:%S}" if aberto else "—"
        md.append(f"| `{run_id}` | {step} | {falha:%Y-%m-%d} | {falha:%H:%M:%S} | {hora_alerta} | {tempo} |")
    md += ["", "## Todos os incidentes", "",
           "| estado | aberto | fechado | política | job |", "|---|---|---|---|---|"]
    for a in sorted(alertas, key=lambda x: x["openTime"]):
        md.append(f"| {a.get('state')} | {a['openTime']} | {a.get('closeTime', '-')} | "
                  f"{a.get('policy', {}).get('displayName')} | "
                  f"{a.get('resource', {}).get('labels', {}).get('job_name', '')} |")
    OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[9:9 + len(linhas) + 2]))


if __name__ == "__main__":
    main()
