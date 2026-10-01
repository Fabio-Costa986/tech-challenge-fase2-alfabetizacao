from pathlib import Path

import yaml

from alfab.config import ROOT, settings
from alfab.ops.profile import split_named_queries
from alfab.ops.publish import VIEWS_DIR, render_view


def test_profiling_separa_queries_nomeadas():
    pares = split_named_queries((ROOT / "analises" / "01_profiling_fonte.sql").read_text(encoding="utf-8"))
    nomes = [n for n, _ in pares]
    assert "02_rede_por_tabela" in nomes and "03_dicionario_completo" in nomes
    assert all(sql and not sql.endswith(";") for _, sql in pares)


def test_views_gold_renderizam_sem_placeholder():
    for f in VIEWS_DIR.glob("*.sql"):
        sql = render_view(f.read_text(encoding="utf-8"), settings())
        assert "{" not in sql and "proj-teste.gold." in sql


def test_workflow_encadeia_camadas_na_ordem():
    text = (ROOT / "workflows" / "pipeline_batch.yaml").read_text(encoding="utf-8")
    wf = yaml.safe_load(text.replace("${project}", "p").replace("${region}", "r"))
    pipeline = next(s["pipeline"] for s in wf["main"]["steps"] if "pipeline" in s)
    ordem = [list(s)[0] for s in pipeline["try"]["steps"]]
    assert ordem == ["ingest_bronze", "dbt_silver", "dbt_gold", "publish_gold"]
    assert pipeline["except"]["steps"][-1]["reraise"]["raise"], "falha precisa encerrar o workflow"


def test_nenhuma_credencial_versionada():
    proibidos = ("BEGIN PRIVATE KEY", '"private_key"', "AIza")
    for p in ROOT.rglob("*"):
        if any(part in {".venv", ".git", "target", "__pycache__", "tests"} for part in p.parts):
            continue
        if p.is_file() and p.suffix in {".py", ".yaml", ".yml", ".tf", ".json", ".sql", ".md", ".env"}:
            texto = p.read_text(encoding="utf-8", errors="ignore")
            assert not any(x in texto for x in proibidos), p


def test_ids_de_projeto_nao_fixos_no_codigo():
    for p in list((ROOT / "src").rglob("*.py")) + list((ROOT / "dbt").rglob("*.sql")):
        assert "basedosdados-" not in p.read_text(encoding="utf-8")
    assert Path(ROOT / ".env.example").exists()
