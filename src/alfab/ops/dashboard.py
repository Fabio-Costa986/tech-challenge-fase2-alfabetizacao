"""Gera o dashboard de resultados a partir da Gold publicada (e do ops) - `python -m alfab dashboard`.

Todo número do dashboard sai das consultas abaixo; nada é digitado à mão. O HTML final
(evidencias/dashboard/index.html) é o template dashboard/template.html com os dados embutidos
em JSON, de modo que a página abre sem acesso ao BigQuery.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal

from alfab.bq import client
from alfab.config import ROOT, settings
from alfab.observability import log

TEMPLATE = ROOT / "dashboard" / "template.html"
OUT_DIR = ROOT / "evidencias" / "dashboard"


def _q(sql: str) -> list[dict]:
    return [dict(r.items()) for r in client().query(sql).result()]


def _json_default(v):
    if isinstance(v, datetime | date):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    raise TypeError(type(v))


def collect(dataset: str | None = None) -> dict:
    s = settings()
    p = s.project_id
    gold = dataset or s.datasets["gold"]
    tables = {t.table_id for t in client().list_tables(f"{p}.{gold}")}
    if "meta_vs_resultado" not in tables:
        raise RuntimeError(f"{p}.{gold} ainda não tem a Gold publicada (rode o pipeline batch)")
    G, OPS = f"`{p}.{gold}", f"`{p}.{s.datasets['ops']}"

    data = {
        "gerado_em": datetime.now(UTC).isoformat(timespec="seconds"),
        "projeto": p,
        "dataset_gold": gold,
        "brasil": _q(f"""
            SELECT ano, ROUND(taxa_alfabetizacao, 2) AS taxa, ROUND(meta_pactuada_pct, 2) AS meta,
                   status_meta, fonte_resultado
            FROM {G}.meta_vs_resultado` WHERE nivel = 'BR' AND rede_canonica = 'publica' ORDER BY ano"""),
        "brasil_serie": _q(f"""
            SELECT ano, ROUND(taxa_alfabetizacao, 2) AS taxa, fonte_resultado
            FROM {G}.resultado_oficial` WHERE nivel = 'BR' AND rede_canonica = 'publica' ORDER BY ano"""),
        "uf": _q(f"""
            SELECT ano, id_local AS uf, ROUND(taxa_alfabetizacao, 2) AS taxa,
                   ROUND(meta_pactuada_pct, 2) AS meta, ROUND(gap_pp, 2) AS gap, status_meta, fonte_resultado
            FROM {G}.meta_vs_resultado`
            WHERE nivel = 'UF' AND rede_canonica = 'publica' AND taxa_alfabetizacao IS NOT NULL
            ORDER BY ano, uf"""),
        "mun_status": _q(f"""
            SELECT ano, status_meta, COUNT(*) AS n
            FROM {G}.meta_vs_resultado`
            WHERE nivel = 'MUN' AND rede_canonica = 'municipal'
              AND ano <= (SELECT MAX(ano) FROM {G}.resultado_oficial` WHERE nivel = 'MUN')
            GROUP BY 1, 2 ORDER BY 1, 2"""),
        "mun_distribuicao": _q(f"""
            SELECT ano, CAST(FLOOR(taxa_alfabetizacao / 5) * 5 AS INT64) AS faixa, COUNT(*) AS n
            FROM {G}.fct_alfabetizacao_municipio`
            WHERE rede_canonica = 'municipal' AND taxa_alfabetizacao IS NOT NULL
            GROUP BY 1, 2 ORDER BY 1, 2"""),
        "validacao_uf": _q(f"""
            SELECT ano, id_local AS uf, rede_canonica AS rede, ROUND(taxa_oficial, 2) AS oficial,
                   ROUND(taxa_microdado_ponderada, 2) AS micro, ROUND(diff_pp, 3) AS diff,
                   ROUND(diff_pp_sem_peso_ERRADA, 3) AS diff_sem_peso,
                   ROUND(diff_pp_com_ausentes_ERRADA, 3) AS diff_ausentes, n_avaliados
            FROM {G}.validacao_cruzada_microdado` WHERE nivel = 'UF' AND tem_microdado
            ORDER BY ano, uf, rede"""),
        "validacao_resumo": _q(f"""
            SELECT nivel, COUNT(*) AS grupos,
                   ROUND(APPROX_QUANTILES(ABS(diff_pp), 100)[OFFSET(50)], 3) AS mediana_correta,
                   ROUND(APPROX_QUANTILES(ABS(diff_pp_sem_peso_ERRADA), 100)[OFFSET(50)], 3)
                     AS med_sem_peso,
                   ROUND(APPROX_QUANTILES(ABS(diff_pp_com_ausentes_ERRADA), 100)[OFFSET(50)], 3)
                     AS med_ausentes,
                   COUNTIF(ABS(diff_pp) <= 0.5) AS dentro_05
            FROM {G}.validacao_cruzada_microdado` WHERE tem_microdado AND nivel IN ('UF', 'MUN')
            GROUP BY nivel"""),
        "universalizacao": _q(f"""
            SELECT ano_ultimo_resultado AS ano, ROUND(taxa_ultimo_resultado, 2) AS taxa,
                   ROUND(distancia_universalizacao_pp, 2) AS dist_100,
                   ROUND(meta_pactuada_2030_pct, 2) AS meta_2030,
                   ROUND(distancia_meta_pactuada_2030_pp, 2) AS dist_meta_2030
            FROM {G}.cenario_universalizacao` WHERE nivel = 'BR' AND rede_canonica = 'publica'"""),
        "execucoes": _q(f"""
            SELECT run_id, MIN(started_at) AS inicio,
                   LOGICAL_AND(status = 'SUCCEEDED') AS sucesso,
                   ROUND(SUM(duration_s), 1) AS duracao_s,
                   SUM(bytes_billed) AS bytes_faturados,
                   ARRAY_AGG(STRUCT(step, status, ROUND(duration_s, 1) AS duracao_s, rows_out,
                                    JSON_VALUE(details, '$.acao') AS acao, SUBSTR(error, 1, 160) AS erro)
                             ORDER BY started_at) AS etapas
            FROM {OPS}.pipeline_runs`
            WHERE pipeline = 'batch' AND run_id NOT LIKE 'debug%'
            GROUP BY run_id ORDER BY inicio DESC LIMIT 8"""),
        "qualidade": _q(f"""
            SELECT run_id, executado_em, aprovados, bloqueantes_reprovados, informativos_alertados, erros
            FROM {OPS}.vw_resumo_qualidade` WHERE run_id NOT LIKE 'debug%'
            ORDER BY executado_em DESC LIMIT 8"""),
        "joins": _q(f"""
            SELECT join_name, severidade, total, matched, ROUND(match_rate, 4) AS taxa, min_rate, reprovado
            FROM {OPS}.join_match_rate`
            WHERE measured_at = (SELECT MAX(measured_at) FROM {OPS}.join_match_rate`)
            ORDER BY join_name, severidade"""),
    }
    return data


def build(dataset: str | None = None) -> str:
    data = collect(dataset)
    payload = json.dumps(data, default=_json_default, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DADOS__*/null", payload)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "dados.json").write_text(json.dumps(data, default=_json_default, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    out = OUT_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    log("dashboard gerado", event="dashboard_built", arquivo=str(out.relative_to(ROOT)),
        dataset=data["dataset_gold"])
    return str(out)
