"""CLI única: `python -m alfab <comando>`. É o entrypoint de todos os Cloud Run Jobs.

O run_id vem de ALFAB_RUN_ID (o Workflow injeta o mesmo id em todas as etapas de uma execução)
ou é gerado na hora para execuções locais.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from alfab.observability import configure_logging, log, new_run_id


def _run_id() -> str:
    return os.environ.get("ALFAB_RUN_ID") or new_run_id()


def cmd_ingest_bronze(a) -> None:
    from alfab.bronze import ingest_batch
    ingest_batch.run(_run_id(), a.entities, a.force)


def cmd_dbt(a) -> None:
    from alfab.config import settings
    from alfab.observability import bq_run_writer, track_step
    from alfab.quality import run_dbt

    run_id = _run_id()
    writer = bq_run_writer(settings().table("ops", "pipeline_runs"))
    with track_step(run_id, "batch", f"dbt.{a.layer}", writer) as m:
        m.details["fault_injection"] = a.fault_injection
        outcome = run_dbt.run(a.layer, run_id, a.fault_injection)
        m.details.update(testes_aprovados=outcome.passed, informativos_alertados=outcome.warnings)
    log("camada aprovada", event="quality_gate_passed", layer=a.layer, passed=outcome.passed,
        warnings=outcome.warnings)


def cmd_publish_gold(a) -> None:
    from alfab.ops import publish
    publish.publish(_run_id())


def cmd_pipeline(a) -> None:
    """Equivalente local do Workflow: cada etapa só roda se a anterior passou."""
    run_id = _run_id()
    os.environ["ALFAB_RUN_ID"] = run_id
    log("pipeline batch iniciado", event="pipeline_started", run_id=run_id)
    cmd_ingest_bronze(argparse.Namespace(entities=None, force=a.force))
    cmd_dbt(argparse.Namespace(layer="silver", fault_injection=a.fault_injection))
    cmd_dbt(argparse.Namespace(layer="gold", fault_injection=a.fault_injection))
    cmd_publish_gold(a)
    log("pipeline batch concluído", event="pipeline_succeeded", run_id=run_id)


def cmd_microbatch(a) -> None:
    from alfab.streaming import microbatch
    microbatch.run(_run_id())


def cmd_simulate(a) -> None:
    from alfab.config import settings
    from alfab.observability import bq_run_writer, track_step
    from alfab.streaming import simulator

    cfg = settings().streaming
    if a.local:
        municipios = simulator.FALLBACK_MUNICIPIOS
        publish, flush = (lambda d: print(d.decode("utf-8", "replace"))), (lambda: None)
        counts = simulator.run(a.n, publish, municipios, cfg["duplicate_rate"], cfg["invalid_rate"],
                               a.rate, a.atraso, a.seed)
        log("simulação local concluída", event="simulation_done", **counts)
        return

    s = settings()
    run_id = _run_id()
    with track_step(run_id, "stream", "simulator", bq_run_writer(s.table("ops", "pipeline_runs"))) as m:
        municipios = simulator.sample_municipios()
        publish, flush = simulator.pubsub_publisher(s.project_id, s.pubsub_topic)
        counts = simulator.run(a.n, publish, municipios, cfg["duplicate_rate"], cfg["invalid_rate"],
                               a.rate, a.atraso, a.seed)
        flush()
        m.rows_out = sum(v for k, v in counts.items() if ":" not in k)
        m.details.update(counts=dict(counts), atraso_artificial_s=a.atraso)


def cmd_export_ml(a) -> None:
    from alfab.ops import export_ml
    export_ml.export(_run_id())


def cmd_profile(a) -> None:
    from alfab.ops import profile
    profile.run(_run_id(), a.sql, a.saida)


def cmd_evidencias(a) -> None:
    from alfab.ops import evidence
    evidence.collect()


def cmd_dashboard(a) -> None:
    from alfab.ops import dashboard
    print(dashboard.build(a.dataset))


def cmd_serve(a) -> None:
    import uvicorn
    uvicorn.run("alfab.streaming.ingestor:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


def cmd_finops(a) -> None:
    from alfab.ops import finops
    finops.main(a.dias, a.execucoes_mes)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="alfab")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("ingest-bronze", help="Base dos Dados -> Bronze (Parquet no GCS)")
    sp.add_argument("--entities", nargs="*")
    sp.add_argument("--force", action="store_true", help="ingere mesmo se a fonte não mudou")
    sp.set_defaults(fn=cmd_ingest_bronze)

    sp = sub.add_parser("dbt", help="dbt build de uma camada (portão de qualidade)")
    sp.add_argument("--layer", choices=["silver", "gold"], required=True)
    sp.add_argument("--fault-injection", choices=["none", "duplicate_keys", "unmapped_rede"],
                    default=os.environ.get("ALFAB_FAULT_INJECTION", "none"))
    sp.set_defaults(fn=cmd_dbt)

    sp = sub.add_parser("publish-gold", help="gold_staging -> gold (após testes)")
    sp.set_defaults(fn=cmd_publish_gold)

    sp = sub.add_parser("pipeline", help="batch completo, sequencial (uso local)")
    sp.add_argument("--force", action="store_true")
    sp.add_argument("--fault-injection", choices=["none", "duplicate_keys", "unmapped_rede"],
                    default="none")
    sp.set_defaults(fn=cmd_pipeline)

    sp = sub.add_parser("microbatch", help="Bronze -> Silver dos eventos")
    sp.set_defaults(fn=cmd_microbatch)

    sp = sub.add_parser("simulate", help="publica eventos simulados")
    sp.add_argument("--n", type=int, default=500)
    sp.add_argument("--rate", type=float, default=20.0, help="eventos por segundo")
    sp.add_argument("--atraso", type=float, default=0.0, help="retenção artificial por evento (s)")
    sp.add_argument("--seed", type=int)
    sp.add_argument("--local", action="store_true", help="imprime no stdout em vez de publicar")
    sp.set_defaults(fn=cmd_simulate)

    sp = sub.add_parser("export-ml", help="snapshot da base de features para a Fase 3")
    sp.set_defaults(fn=cmd_export_ml)

    sp = sub.add_parser("profile", help="profiling da fonte -> evidencias/profiling/*.csv")
    sp.add_argument("--sql", help="arquivo .sql com blocos '-- name:' (relativo à raiz)")
    sp.add_argument("--saida", help="pasta de saída dos CSVs (relativa à raiz)")
    sp.set_defaults(fn=cmd_profile)

    sp = sub.add_parser("evidencias", help="contagens e execuções -> evidencias/execucao.md")
    sp.set_defaults(fn=cmd_evidencias)

    sp = sub.add_parser("dashboard", help="dashboard de resultados -> evidencias/dashboard/index.html")
    sp.add_argument("--dataset", help="dataset da Gold (padrão: gold publicada)")
    sp.set_defaults(fn=cmd_dashboard)

    sp = sub.add_parser("serve", help="sobe o event-ingestor (Cloud Run service)")
    sp.set_defaults(fn=cmd_serve)

    sp = sub.add_parser("finops", help="mede custos e gera a tabela de estimativa")
    sp.add_argument("--dias", type=int, default=7)
    sp.add_argument("--execucoes-mes", type=int, default=120, help="batch a cada 6h = 120/mês")
    sp.set_defaults(fn=cmd_finops)
    return p


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = parser().parse_args(argv)
    try:
        args.fn(args)
    except Exception as exc:  # noqa: BLE001 - não engole: converte em código de saída != 0
        code = getattr(exc, "exit_code", 1)
        log(f"comando falhou: {exc}", level=logging.ERROR, event="command_failed", cmd=args.cmd,
            exit_code=code, error_type=type(exc).__name__)
        return code
    return 0


if __name__ == "__main__":
    sys.exit(main())
