"""Gera docs/arquitetura.drawio (3 páginas) a partir de uma descrição em código.

Uso:  python scripts/gerar_drawio.py
O diagrama descreve SOMENTE o que está implementado e foi executado no GCP. Recursos criados mas
pausados (Cloud Scheduler) aparecem marcados como "pausado".

Exportar imagens (o índice de página do draw.io começa em 1):
  draw.io -x -f png -s 2 -b 20 -p 1 -o docs/img/arquitetura-1-visao-geral.png docs/arquitetura.drawio
"""

from __future__ import annotations

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "arquitetura.drawio"

FONT = "fontFamily=Helvetica;fontColor=#1A1A1A;"
BASE = "rounded=1;whiteSpace=wrap;html=1;arcSize=8;spacing=8;fontSize=12;" + FONT
S = {
    "title": "text;html=1;align=left;verticalAlign=middle;fontSize=20;fontStyle=1;" + FONT,
    "subtitle": "text;html=1;align=left;verticalAlign=middle;fontSize=12;fontColor=#52514E;fontFamily=Helvetica;",
    "compute": BASE + "fillColor=#FFFFFF;strokeColor=#4285F4;strokeWidth=1.5;",
    "orchestr": BASE + "fillColor=#F1F6FE;strokeColor=#4285F4;strokeWidth=1.5;",
    "source": BASE + "fillColor=#E8F0FE;strokeColor=#1A73E8;strokeWidth=1.5;",
    "bronze": BASE + "fillColor=#F6E6D6;strokeColor=#B87333;strokeWidth=1.5;",
    "silver": BASE + "fillColor=#ECEFF1;strokeColor=#78909C;strokeWidth=1.5;",
    "gold": BASE + "fillColor=#FFF3C4;strokeColor=#C9A227;strokeWidth=1.5;",
    "ops": BASE + "fillColor=#EDE7F6;strokeColor=#7E57C2;strokeWidth=1.5;",
    "consumer": BASE + "fillColor=#E6F4EA;strokeColor=#34A853;strokeWidth=1.5;",
    "gate": BASE + "fillColor=#FDECEA;strokeColor=#D93025;strokeWidth=2;",
    "fail": BASE + "fillColor=#FDECEA;strokeColor=#D93025;strokeWidth=1.5;dashed=1;",
    "sim": BASE + "fillColor=#FFFFFF;strokeColor=#9AA0A6;strokeWidth=1.5;dashed=1;",
    "group": "rounded=1;whiteSpace=wrap;html=1;arcSize=3;verticalAlign=top;align=left;spacingLeft=12;"
             "spacingTop=6;fontSize=13;fontStyle=1;fillColor=#FAFAF8;strokeColor=#C3C2B7;" + FONT,
    "note": "shape=note;whiteSpace=wrap;html=1;size=14;align=left;verticalAlign=top;spacing=10;fontSize=11;"
            "fillColor=#FFFDE7;strokeColor=#C9A227;" + FONT,
    "legend": "text;html=1;align=left;verticalAlign=middle;fontSize=11;fontColor=#52514E;fontFamily=Helvetica;",
}
EDGE = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#52514E;strokeWidth=1.5;fontSize=10;"
        "endArrow=block;endFill=1;labelBackgroundColor=#FFFFFF;fontFamily=Helvetica;fontColor=#1A1A1A;")
EDGE_FAIL = EDGE.replace("strokeColor=#52514E", "strokeColor=#D93025") + "dashed=1;"
EDGE_OPS = EDGE.replace("strokeColor=#52514E", "strokeColor=#7E57C2") + "dashed=1;"


class Page:
    def __init__(self, name: str, width: int, height: int) -> None:
        self.name, self.w, self.h = name, width, height
        self.cells: list[str] = []
        self._n = 1

    def _id(self) -> str:
        self._n += 1
        return f"c{self._n}"

    def box(self, label: str, x: int, y: int, w: int, h: int, style: str) -> str:
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value="{escape(label, quote=True)}" style="{S.get(style, style)}" '
            f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def edge(self, src: str, dst: str, label: str = "", style: str = EDGE, extra: str = "",
             points: list[tuple[int, int]] | None = None) -> str:
        """`extra`: pontos de saída/entrada (exitX...). `points`: pontos de passagem (evita cruzar caixas)."""
        cid = self._id()
        pts = ""
        if points:
            pts = '<Array as="points">' + "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points) + "</Array>"
        self.cells.append(
            f'<mxCell id="{cid}" value="{escape(label, quote=True)}" style="{style}{extra}" edge="1" '
            f'parent="1" source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry">{pts}'
            f"</mxGeometry></mxCell>")
        return cid

    def xml(self, idx: int) -> str:
        return (
            f'<diagram id="pagina{idx}" name="{escape(self.name, quote=True)}">'
            f'<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
            f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.w}" pageHeight="{self.h}" '
            f'math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
            + "".join(self.cells) + "</root></mxGraphModel></diagram>")


def svc(tipo: str, nome: str, detalhe: str = "") -> str:
    """Rótulo padrão de um recurso: tipo do serviço, nome real e detalhe."""
    txt = f'<font color="#52514E" style="font-size:10px">{tipo}</font><br><b>{nome}</b>'
    return txt + (f'<br><font style="font-size:11px">{detalhe}</font>' if detalhe else "")


# ------------------------------------------------------------------ página 1: visão geral (executiva)
def pagina_visao_geral() -> Page:
    p = Page("1. Visão geral", 1680, 800)
    p.box("Pipeline híbrido do Indicador Criança Alfabetizada", 30, 20, 900, 34, "title")
    p.box("Google Cloud · arquitetura medalhão · batch + streaming · todos os componentes abaixo estão "
          "implementados e foram executados", 30, 54, 1100, 22, "subtitle")

    fonte = p.box("<b>Fonte oficial</b><br>Base dos Dados (Inep)<br><br>alunos (3,9 milhões)<br>município · UF<br>"
                  "metas Brasil, UF e município<br>dicionário de códigos", 30, 130, 190, 210, "source")
    sim = p.box("<b>Simulador de eventos</b><br>atualizações de indicador,<br>medições e metas<br>"
                "(dado marcado como SIMULADO)", 30, 400, 190, 110, "sim")

    batch = p.box("<b>Ingestão batch</b><br>a cada 6 h<br>lê direto do BigQuery público<br>"
                  "pula a fonte que não mudou", 300, 180, 190, 110, "orchestr")
    stream = p.box("<b>Ingestão streaming</b><br>mensageria Pub/Sub<br>eventos em segundos<br>"
                   "inválidos vão para quarentena", 300, 400, 190, 110, "orchestr")

    p.box("Arquitetura medalhão (BigQuery + Cloud Storage)", 540, 110, 930, 430, "group")
    bronze = p.box("<b>BRONZE</b><br>dado bruto<br><br>cópia fiel da fonte<br>Parquet imutável<br>"
                   "1 pasta por execução<br>histórico preservado", 560, 170, 170, 340, "bronze")
    g1 = p.box("<b>Portão de qualidade</b><br><br>só avança<br>se aprovado", 770, 280, 110, 120, "gate")
    silver = p.box("<b>SILVER</b><br>dado tratado<br><br>tipos e chaves<br>padronizados<br>códigos traduzidos<br>"
                   "pelo dicionário<br>6 entidades integradas", 920, 170, 170, 340, "silver")
    g2 = p.box("<b>Portão de qualidade</b><br><br>só publica<br>se aprovado", 1130, 280, 110, 120, "gate")
    gold = p.box("<b>GOLD</b><br>dado analítico<br><br>resultado ×<br>meta pactuada<br>evolução temporal<br>"
                 "validação cruzada<br>base para IA", 1280, 170, 170, 340, "gold")

    dash = p.box("<b>Painel de resultados</b><br>Brasil, UFs e municípios<br>contra a meta", 1520, 140, 130, 100, "consumer")
    ml = p.box("<b>Base para IA</b><br>(Fase 3)<br>sem vazamento de alvo", 1520, 290, 130, 100, "consumer")
    sql = p.box("<b>Consultas SQL</b><br>e análises", 1520, 440, 130, 70, "consumer")

    obs = p.box("Observabilidade e FinOps", 300, 600, 1350, 170, "group")
    p.box("<b>Registro de execuções</b><br>duração, linhas e status de cada etapa,<br>acumulados a cada execução",
          320, 640, 312, 110, "ops")
    p.box("<b>Resultado dos testes</b><br>regras bloqueantes e informativas,<br>taxa de correspondência de cada join",
          652, 640, 312, 110, "ops")
    p.box("<b>Alertas por e-mail</b><br>falha detectada em ~4 minutos<br>(medido em 4 falhas)", 984, 640, 312, 110, "ops")
    p.box("<b>Custo medido</b><br>US$ 5,15/mês a preço de lista<br>US$ 0,00 dentro do nível gratuito",
          1316, 640, 312, 110, "ops")

    p.edge(fonte, batch)
    p.edge(sim, stream, "eventos")
    p.edge(batch, bronze, "", EDGE, "entryX=0;entryY=0.25;")
    p.edge(stream, bronze, "", EDGE, "entryX=0;entryY=0.75;")
    p.edge(bronze, g1)
    p.edge(g1, silver)
    p.edge(silver, g2)
    p.edge(g2, gold)
    p.edge(gold, dash)
    p.edge(gold, ml)
    p.edge(gold, sql)
    p.edge(silver, obs, "métricas de cada etapa e resultados dos testes", EDGE_OPS,
           "exitX=0.5;exitY=1;entryX=0.522;entryY=0;")

    p.box("<b>Como ler</b><br>Dado ruim não avança: se uma regra bloqueante reprova, a camada seguinte "
          "não é construída e a Gold publicada continua a da última execução boa.<br><br>"
          "Dado oficial e dado simulado nunca se misturam: toda linha carrega a origem.",
          30, 600, 240, 170, "note")
    return p


# ------------------------------------------------------------------ página 2: batch (técnica)
def pagina_batch() -> Page:
    p = Page("2. Fluxo batch", 1760, 1040)
    p.box("Fluxo batch: orquestração, portões de qualidade e publicação", 30, 20, 1000, 34, "title")
    p.box("Projeto GCP · região us-central1 (computação) e US (dados) · infraestrutura em Terraform (82 recursos)",
          30, 54, 1100, 22, "subtitle")

    sched = p.box(svc("Cloud Scheduler", "alfab-batch", "0 */6 * * * · <b>pausado</b>"), 30, 135, 180, 90, "orchestr")
    wf = p.box(svc("Cloud Workflows", "alfab-pipeline-batch", "encadeia as etapas, injeta o run_id,<br>repete erros transitórios"),
               240, 135, 220, 90, "orchestr")

    p.box("Cloud Run Jobs · imagem única (Artifact Registry: alfab/pipeline) · executados em sequência: "
          "cada um só roda se o anterior teve sucesso", 540, 100, 1190, 145, "group")
    xs, w = [560, 860, 1160, 1460], 240
    j1 = p.box(svc("Cloud Run Job", "alfab-ingest-bronze", "watermark + dry run + EXPORT DATA"), xs[0], 145, w, 80, "compute")
    j2 = p.box(svc("Cloud Run Job", "alfab-dbt-silver", "dbt build: modelos + testes"), xs[1], 145, w, 80, "compute")
    j3 = p.box(svc("Cloud Run Job", "alfab-dbt-gold", "dbt build em gold_staging"), xs[2], 145, w, 80, "compute")
    j4 = p.box(svc("Cloud Run Job", "alfab-publish-gold", "copy jobs (sem custo de consulta)"), xs[3], 145, w, 80, "compute")

    g1 = p.box("<b>Completude</b><br>linhas exportadas = linhas da origem", xs[0], 300, w, 64, "gate")
    g2 = p.box("<b>Portão Silver</b><br>duplicidade, nulos, domínio, códigos,<br>taxa de match de cada join", xs[1], 300, w, 64, "gate")
    g3 = p.box("<b>Portão Gold</b><br>validação cruzada microdado × oficial,<br>vazamento de alvo, testes unitários", xs[2], 300, w, 64, "gate")

    src = p.box(svc("BigQuery público (US)", "basedosdados.br_inep_avaliacao_alfabetizacao",
                    "alunos, municipio, uf, 3 tabelas de meta,<br>dicionario + diretório de municípios"),
                30, 430, 430, 140, "source")
    bz = p.box(svc("Cloud Storage + tabelas externas", "BRONZE",
                   "gs://…-alfab-lake/bronze/&lt;entidade&gt;/<br>ingestion_date=/run_id=/ · Parquet ZSTD<br>"
                   "overwrite=false · retenção 30 dias<br>a Silver lê só o run_id mais recente"), xs[0], 430, w, 140, "bronze")
    sv = p.box(svc("BigQuery", "SILVER", "silver.* · 9 modelos + 4 seeds<br>rede canônica (rede_map)<br>"
                   "metas em formato longo<br>alunos: 3.867.999 linhas"), xs[1], 430, w, 140, "silver")
    gs = p.box(svc("BigQuery", "GOLD em auditoria", "gold_staging.* · 10 tabelas<br>construída e testada aqui,<br>"
                   "ainda invisível para consumo"), xs[2], 430, w, 140, "gold")
    gd = p.box(svc("BigQuery", "GOLD publicada", "gold.* · 10 tabelas + 2 views<br>rótulo published_run_id<br>"
                   "lida por painel, SQL e IA"), xs[3], 430, w, 140, "gold")

    fail = p.box("<b>Regra bloqueante reprovou</b><br>job termina com código 3 → workflow FAILED → as etapas seguintes "
                 "não executam → a Gold publicada permanece a da última execução boa",
                 860, 640, 500, 90, "fail")
    ml = p.box(svc("Cloud Run Job", "alfab-export-ml", "snapshot para a Fase 3:<br>tabela snapshot no BigQuery<br>"
                   "+ Parquet em gs://…/gold/ml/fase3/"), xs[3], 635, w, 100, "compute")

    p.box("Observabilidade · dataset ops (somente acréscimo, nunca sobrescreve)", 30, 790, 1700, 220, "group")
    runs = p.box(svc("BigQuery", "ops.pipeline_runs", "etapa, duração, linhas, bytes, status, erro"), 50, 835, 250, 90, "ops")
    wm = p.box(svc("BigQuery", "ops.source_watermarks", "data de modificação da fonte<br>por entidade e execução"), 320, 835, 250, 90, "ops")
    dq = p.box(svc("BigQuery", "ops.dq_results", "cada teste, a cada execução,<br>inclusive reprovações"), 590, 835, 250, 90, "ops")
    p.box(svc("BigQuery", "ops.join_match_rate", "taxa de match de 7 junções<br>com limiar e severidade"), 860, 835, 250, 90, "ops")
    log = p.box(svc("Cloud Logging", "métricas baseadas em log", "alfab/step_failed,<br>alfab/batch_pipeline_succeeded"), 1130, 835, 270, 90, "ops")
    mon = p.box(svc("Cloud Monitoring", "políticas de alerta → e-mail", "etapa falhou · job falhou ·<br>13 h sem sucesso · orçamento"), 1420, 835, 290, 90, "ops")
    p.box("Cada job grava sua etapa em ops.pipeline_runs e emite log estruturado; o dbt grava ops.dq_results e "
          "ops.join_match_rate.", 50, 940, 900, 24, "legend")
    p.box("Tempo medido entre a falha e a abertura do incidente: de 3 min 38 s a 4 min 31 s (4 falhas).",
          50, 966, 900, 24, "legend")

    p.edge(sched, wf, "dispara")
    p.edge(wf, j1, "1")
    p.edge(j1, j2, "2")
    p.edge(j2, j3, "3")
    p.edge(j3, j4, "4")
    p.edge(src, j1, "SELECT (colunas explícitas)", EDGE, "exitX=0.5;exitY=0;entryX=0.15;entryY=1;",
           points=[(245, 270), (596, 270)])
    p.edge(j1, g1, "", EDGE, "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    p.edge(g1, bz, "EXPORT DATA")
    p.edge(bz, j2, "", EDGE, "exitX=1;exitY=0.3;entryX=0;entryY=0.75;", points=[(820, 472), (820, 205)])
    p.edge(j2, g2)
    p.edge(g2, sv, "aprovado")
    p.edge(sv, j3, "", EDGE, "exitX=1;exitY=0.3;entryX=0;entryY=0.75;", points=[(1120, 472), (1120, 205)])
    p.edge(j3, g3)
    p.edge(g3, gs, "aprovado")
    p.edge(gs, j4, "", EDGE, "exitX=1;exitY=0.3;entryX=0;entryY=0.75;", points=[(1420, 472), (1420, 205)])
    p.edge(j4, gd, "copia as tabelas<br>e recria as views")
    # reprovação: desce pelo corredor entre as colunas, sem cruzar as caixas de dados
    p.edge(g2, fail, "reprovado", EDGE_FAIL, "exitX=1;exitY=0.75;entryX=0.5;entryY=0;",
           points=[(1140, 348), (1140, 610), (1110, 610)])
    p.edge(g3, fail, "reprovado", EDGE_FAIL, "exitX=1;exitY=0.75;entryX=1;entryY=0.5;",
           points=[(1440, 348), (1440, 600), (1400, 600), (1400, 685)])
    p.edge(gd, ml, "sob demanda")
    p.edge(j1, wm, "watermark:<br>fonte igual<br>= pulada", EDGE_OPS,
           "exitX=0;exitY=0.75;entryX=0.76;entryY=0;", points=[(510, 205), (510, 835)])
    p.edge(fail, dq, "resultado persistido", EDGE_OPS, "exitX=0;exitY=0.5;entryX=0.5;entryY=0;")
    p.edge(runs, log, "", EDGE_OPS, "exitX=0.5;exitY=1;entryX=0.5;entryY=1;", points=[(175, 932), (1265, 932)])
    p.edge(log, mon, "", EDGE_OPS)
    return p


# ------------------------------------------------------------------ página 3: streaming (técnica)
def pagina_streaming() -> Page:
    p = Page("3. Fluxo streaming", 1780, 1000)
    p.box("Fluxo streaming: mensageria, quarentena, deduplicação e latência medida", 30, 20, 1100, 34, "title")
    p.box("Entrega at-least-once do Pub/Sub; unicidade garantida pelo MERGE do micro-lote; dado sempre marcado "
          "origem_dado = SIMULADO", 30, 54, 1200, 22, "subtitle")

    sim = p.box(svc("Cloud Run Job", "alfab-simulator", "gera eventos a partir de municípios reais<br>"
                    "~5% duplicatas · ~3% inválidos<br>carimba <b>produced_at</b>"), 30, 130, 250, 110, "sim")
    topic = p.box(svc("Pub/Sub · tópico", "alfab-eventos", "retenção de 7 dias"), 340, 140, 200, 90, "orchestr")
    sub = p.box(svc("Pub/Sub · subscription push", "alfab-eventos-push", "token OIDC · retry 10–600 s<br>até 5 tentativas"),
                590, 140, 230, 90, "orchestr")
    ing = p.box(svc("Cloud Run (serviço, escala a zero)", "alfab-event-ingestor",
                    "valida o contrato do evento<br>carimba <b>ingested_at</b>"), 890, 130, 260, 110, "compute")
    raw = p.box(svc("BigQuery", "bronze.eventos_raw", "toda entrega é gravada,<br>inclusive reentregas (duplicatas)"),
                1240, 140, 230, 90, "bronze")

    dlq = p.box(svc("Pub/Sub · fila de descarte", "alfab-eventos-dlq", "+ alfab-eventos-dlq-inspect<br>"
                    "mensagens que falharam 5 entregas"), 590, 310, 230, 100, "fail")
    quar = p.box(svc("BigQuery", "bronze.eventos_quarentena", "evento rejeitado + motivo<br>"
                     "(estrutura, domínio ou referência)"), 1370, 310, 230, 100, "fail")

    sched = p.box(svc("Cloud Scheduler", "alfab-microbatch", "*/5 * * * * · <b>pausado</b>"), 590, 520, 230, 90, "orchestr")
    mb = p.box(svc("Cloud Run Job", "alfab-microbatch",
                   "janela por watermark + 10 min de segurança<br>ROW_NUMBER por event_id (dentro do lote)<br>"
                   "valida município contra o diretório<br>MERGE idempotente (entre lotes, 7 dias)"),
               890, 500, 260, 130, "compute")
    sil = p.box(svc("BigQuery", "silver.eventos", "1 linha por event_id<br>carimba <b>silver_processed_at</b>"),
                1240, 520, 230, 90, "silver")
    gold = p.box(svc("BigQuery · views", "gold.vw_indicador_consolidado",
                     "OFICIAL (batch) + SIMULADO (streaming),<br>separados por origem_dado<br>+ gold.vw_eventos_tempo_real"),
                 1530, 510, 220, 110, "gold")

    p.box("Observabilidade do streaming", 30, 720, 1720, 240, "group")
    runs = p.box(svc("BigQuery", "ops.pipeline_runs", "por micro-lote: lidas, únicas, novas,<br>duplicatas descartadas, quarentena,<br>"
                     "latência p50/p95/p99"), 50, 770, 270, 110, "ops")
    p.box(svc("BigQuery", "ops.stream_watermark", "até onde o micro-lote já processou"), 340, 770, 240, 110, "ops")
    p.box(svc("BigQuery · view", "ops.vw_latencia_streaming", "ingested_at − produced_at<br>(dois relógios diferentes)"),
          600, 770, 250, 110, "ops")
    alert = p.box(svc("Cloud Monitoring", "4 políticas de alerta → e-mail",
                      "backlog &gt; 5 min · fila de descarte &gt; 0<br>latência p95 &gt; 60 s · quarentena &gt; 10%"),
                  870, 770, 300, 110, "ops")
    p.box("<b>Medido na nuvem (3 rodadas)</b><br>1.240 eventos publicados · 1.206 entregas na Bronze para 1.135 distintos<br>"
          "71 duplicatas: 39 do simulador e <b>32 reentregas reais do Pub/Sub</b><br>"
          "1.125 na Silver, sem duplicata · 50 na quarentena<br>"
          "latência de ingestão p50: 0,066 s (5,097 s com 5 s de atraso injetado)",
          1230, 760, 500, 130, "note")

    p.edge(sim, topic, "publica")
    p.edge(topic, sub)
    p.edge(sub, ing, "push")
    p.edge(ing, raw, "válido")
    p.edge(ing, quar, "inválido: gravado com o motivo", EDGE_FAIL, "exitX=0.7;exitY=1;entryX=0;entryY=0.5;",
           points=[(1072, 360)])
    p.edge(sub, dlq, "5 falhas", EDGE_FAIL)
    p.edge(sched, mb, "dispara")
    p.edge(raw, mb, "lê a janela", EDGE, "exitX=0.15;exitY=1;entryX=0.55;entryY=0;",
           points=[(1274, 450), (1033, 450)])
    p.edge(mb, sil, "MERGE")
    p.edge(mb, quar, "município inexistente", EDGE_FAIL, "exitX=0.92;exitY=0;entryX=0.5;entryY=1;",
           points=[(1129, 475), (1485, 475)])
    p.edge(sil, gold)
    p.edge(mb, runs, "métricas do lote", EDGE_OPS, "exitX=0.25;exitY=1;entryX=0.5;entryY=0;",
           points=[(955, 680), (185, 680)])
    p.edge(runs, alert, "", EDGE_OPS, "exitX=0.5;exitY=1;entryX=0.5;entryY=1;", points=[(185, 905), (1020, 905)])

    p.box("<b>Batch × streaming</b><br>Batch: snapshot da tabela, horas de latência, dado inválido para o pipeline.<br>"
          "Streaming: evento individual, segundos até a Bronze, dado inválido vai para a quarentena sem parar o fluxo.",
          30, 310, 480, 110, "note")
    return p


def main() -> None:
    pages = [pagina_visao_geral(), pagina_batch(), pagina_streaming()]
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<mxfile host="app.diagrams.net" type="device">'
           + "".join(pg.xml(i) for i, pg in enumerate(pages, 1)) + "</mxfile>\n")
    OUT.write_text(xml, encoding="utf-8")
    print(f"gerado {OUT.relative_to(ROOT)} ({len(pages)} páginas, {sum(len(pg.cells) for pg in pages)} elementos)")


if __name__ == "__main__":
    main()
