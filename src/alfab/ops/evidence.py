"""Coleta evidências de execução para o repositório (exigência da pág. 9: contagens, IDs, status).

Gera evidencias/execucao.md com:
- contagem de linhas de cada tabela em bronze/silver/gold/ops (metadados, sem custo de scan);
- últimas execuções de ops.pipeline_runs (run_id, etapa, status, duração, linhas);
- resumo de qualidade por run_id (inclui as execuções reprovadas);
- taxas de correspondência de joins da última medição;
- latência do streaming.
"""

from __future__ import annotations

from datetime import UTC, datetime

from alfab.bq import client
from alfab.config import ROOT, settings


def _md_table(rows: list, cols: list[str]) -> str:
    if not rows:
        return "_(sem linhas)_\n"
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + " |")
    return "\n".join(out) + "\n"


def _q(sql: str) -> list[dict]:
    return [dict(r.items()) for r in client().query(sql).result()]


def collect() -> str:
    s = settings()
    p = s.project_id
    parts = [f"# Evidências de execução\n\nColetado em {datetime.now(UTC):%Y-%m-%d %H:%M} UTC "
             f"por `python -m alfab evidencias` no projeto `{p}`.\n"]

    counts = []
    for layer in ("bronze", "silver", "gold", "ops"):
        ds = s.datasets[layer]
        for t in client().list_tables(f"{p}.{ds}"):
            tbl = client().get_table(t.reference)
            counts.append({"tabela": f"{ds}.{t.table_id}", "tipo": tbl.table_type,
                           "linhas": tbl.num_rows, "MiB": round((tbl.num_bytes or 0) / 2**20, 2),
                           "modificada": tbl.modified})
    parts += ["## Contagem de linhas por tabela\n",
              "External tables da Bronze mostram linhas vazias: os dados estão no GCS (ver "
              "ops.source_watermarks.exported_rows).\n",
              _md_table(counts, ["tabela", "tipo", "linhas", "MiB", "modificada"])]

    parts += ["## Snapshots da Bronze (histórico preservado)\n", _md_table(_q(f"""
        SELECT entity, run_id, source_last_modified, exported_rows, bronze_uri
        FROM `{s.table('ops', 'source_watermarks')}` ORDER BY ingested_at DESC LIMIT 30"""),
        ["entity", "run_id", "source_last_modified", "exported_rows", "bronze_uri"])]

    parts += ["## Últimas execuções (ops.pipeline_runs)\n", _md_table(_q(f"""
        SELECT run_id, pipeline, step, status, ROUND(duration_s, 1) AS duration_s, rows_in, rows_out,
               bytes_billed, SUBSTR(error, 1, 120) AS error
        FROM `{s.table('ops', 'pipeline_runs')}`
        WHERE started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        ORDER BY started_at DESC LIMIT 60"""),
        ["run_id", "pipeline", "step", "status", "duration_s", "rows_in", "rows_out", "bytes_billed",
         "error"])]

    parts += ["## Qualidade por execução (inclui reprovações)\n", _md_table(_q(f"""
        SELECT run_id, fault_injection, executado_em, aprovados, bloqueantes_reprovados,
               informativos_alertados, erros
        FROM `{p}.{s.datasets['ops']}.vw_resumo_qualidade` ORDER BY executado_em DESC LIMIT 20"""),
        ["run_id", "fault_injection", "executado_em", "aprovados", "bloqueantes_reprovados",
         "informativos_alertados", "erros"])]

    parts += ["## Taxa de correspondência dos joins (última medição)\n", _md_table(_q(f"""
        SELECT join_name, severidade, total, matched, ROUND(match_rate, 4) AS match_rate, min_rate, reprovado
        FROM `{p}.{s.datasets['ops']}.join_match_rate`
        WHERE measured_at = (SELECT MAX(measured_at) FROM `{p}.{s.datasets['ops']}.join_match_rate`)
        ORDER BY join_name"""),
        ["join_name", "severidade", "total", "matched", "match_rate", "min_rate", "reprovado"])]

    parts += ["## Latência do streaming (últimas janelas)\n", _md_table(_q(f"""
        SELECT janela_5min, eventos, p50_ingestao_s, p95_ingestao_s, p99_ingestao_s, p95_ponta_a_ponta_s
        FROM `{p}.{s.datasets['ops']}.vw_latencia_streaming` ORDER BY janela_5min DESC LIMIT 20"""),
        ["janela_5min", "eventos", "p50_ingestao_s", "p95_ingestao_s", "p99_ingestao_s",
         "p95_ponta_a_ponta_s"])]

    md = "\n".join(parts)
    target = ROOT / "evidencias" / "execucao.md"
    target.write_text(md, encoding="utf-8")
    print(md)
    return md
