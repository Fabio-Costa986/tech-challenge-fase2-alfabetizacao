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
from alfab.ops.adr_validation import check_run_id, validate


def _md_table(rows: list, cols: list[str]) -> str:
    if not rows:
        return "_(sem linhas)_\n"
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + " |")
    return "\n".join(out) + "\n"


def _q(sql: str) -> list[dict]:
    return [dict(r.items()) for r in client().query(sql).result()]


def collect(aceite_run_id: str | None = None) -> str:
    if aceite_run_id:
        check_run_id(aceite_run_id)
        validate(aceite_run_id)  # Garante evidencias da Gold realmente publicada.
    s = settings()
    p = s.project_id
    parts = [f"# Evidências de execução\n\nColetado em {datetime.now(UTC):%Y-%m-%d %H:%M} UTC "
             f"por `python -m alfab evidencias` no projeto `{p}`.\n"]
    if aceite_run_id:
        parts.append(f"**Aceite ADR-008/009 verificado no GCP:** run_id `{aceite_run_id}`; "
                     "etapas de Silver, Gold e publicação concluídas, testes bloqueantes aprovados "
                     "e Gold publicada sem meta futura.\n")
    else:
        parts.append("**Atenção:** relatório não ancorado em um run_id de aceite. "
                     "Resultados históricos não comprovam os ADRs 008/009.\n")

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

    if aceite_run_id:
        parts += [f"## Etapas efetivas do run_id de aceite `{aceite_run_id}`\n", _md_table(_q(f"""
            SELECT run_id, started_at, step, status, ROUND(duration_s, 2) AS duration_s,
                   SUBSTR(error, 1, 160) AS error
            FROM `{s.table('ops', 'pipeline_runs')}`
            WHERE run_id = '{aceite_run_id}' ORDER BY started_at"""),
            ["run_id", "started_at", "step", "status", "duration_s", "error"])]

    parts += ["## Qualidade por execução (inclui reprovações)\n", _md_table(_q(f"""
        SELECT run_id, fault_injection, executado_em, aprovados, bloqueantes_reprovados,
               informativos_alertados, erros
        FROM `{p}.{s.datasets['ops']}.vw_resumo_qualidade` ORDER BY executado_em DESC LIMIT 20"""),
        ["run_id", "fault_injection", "executado_em", "aprovados", "bloqueantes_reprovados",
         "informativos_alertados", "erros"])]

    # Nomes, status e IDs efetivos dos testes; os totais da view nao sao prova individual.
    filtro_run = f"AND run_id = '{aceite_run_id}'" if aceite_run_id else ""
    parts += ["## ADR-008/009 — testes registrados em ops.dq_results\n", _md_table(_q(f"""
        SELECT run_id, executed_at, test_name, severidade, status, failures, fault_injection
        FROM `{s.table('ops', 'dq_results')}`
        WHERE test_name IN ('assert_avaliados_completos', 'assert_ml_sem_vazamento')
          {filtro_run}
        ORDER BY executed_at DESC LIMIT 30"""),
        ["run_id", "executed_at", "test_name", "severidade", "status", "failures", "fault_injection"])]

    # Preserva a prova antiga de duplicate_keys e acrescenta evidencia negativa da ADR-008
    # SOMENTE se houve uma execucao negativa real em ops.dq_results.
    parts += ["## ADR-008 — reprovacoes controladas efetivamente registradas\n", _md_table(_q(f"""
        WITH negativas AS (
          SELECT run_id, MAX(executed_at) AS executado_em, MAX(failures) AS falhas
          FROM `{s.table('ops', 'dq_results')}`
          WHERE test_name = 'assert_avaliados_completos'
            AND status IN ('fail', 'error') AND severidade = 'bloqueante'
          GROUP BY run_id
        )
        SELECT n.run_id, n.executado_em, n.falhas,
               COUNTIF(p.step = 'dbt.silver' AND p.status = 'FAILED') AS silver_failed,
               COUNTIF(p.step = 'dbt.gold') AS gold_executada,
               COUNTIF(p.step = 'publish.gold') AS publicacao_executada
        FROM negativas n
        LEFT JOIN `{s.table('ops', 'pipeline_runs')}` p ON p.run_id = n.run_id
        GROUP BY n.run_id, n.executado_em, n.falhas
        ORDER BY n.executado_em DESC LIMIT 10"""),
        ["run_id", "executado_em", "falhas", "silver_failed", "gold_executada",
         "publicacao_executada"])]

    parts += ["## ADR-009 — schema real da Gold ML publicada\n", _md_table(_q(f"""
        SELECT table_name AS tabela, ordinal_position AS pos, column_name AS coluna, data_type AS tipo
        FROM `{p}.{s.datasets['gold']}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'ml_features_municipio'
        ORDER BY ordinal_position"""), ["tabela", "pos", "coluna", "tipo"])]

    # Proveniencia do export de Fase 3: URI, versao e snapshot registrados
    # pelo job GCP, nunca fornecidos manualmente no relatorio.
    parts += ["## Fase 3 — exports de ML realmente executados\n", _md_table(_q(f"""
        SELECT run_id, started_at, status,
               JSON_VALUE(details, '$.snapshot') AS snapshot,
               JSON_VALUE(details, '$.version') AS versao,
               JSON_VALUE(details, '$.published_run_id') AS gold_published_run_id,
               JSON_VALUE(details, '$.uri') AS parquet_gcs,
               SUBSTR(error, 1, 120) AS erro
        FROM `{s.table('ops', 'pipeline_runs')}`
        WHERE step = 'export.ml_fase3'
        ORDER BY started_at DESC LIMIT 10"""),
        ["run_id", "started_at", "status", "snapshot", "versao", "gold_published_run_id",
         "parquet_gcs", "erro"])]

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
