"""ADR-008/009: testes offline, sem credenciais, consultas ou mutacoes no GCP."""

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

# Permite rodar apenas estes testes unitarios offline em ambientes de QA sem
# SDK do Google; no ambiente real usa os pacotes declarados em pyproject.toml.
try:
    from google.cloud import bigquery  # noqa: F401
except ImportError:
    import google.cloud

    bq_module = ModuleType("google.cloud.bigquery")
    class ScalarQueryParameter:
        def __init__(self, name, type_, value):
            self.name, self.type_, self.value = name, type_, value

    class QueryJobConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    bq_module.ScalarQueryParameter = ScalarQueryParameter
    bq_module.QueryJobConfig = QueryJobConfig
    bq_module.Client = object
    bq_module.QueryJob = object
    sys.modules["google.cloud.bigquery"] = bq_module
    google.cloud.bigquery = bq_module
    storage_module = ModuleType("google.cloud.storage")
    storage_module.Client = object
    sys.modules["google.cloud.storage"] = storage_module
    google.cloud.storage = storage_module
    api_module = ModuleType("google.api_core")
    exc_module = ModuleType("google.api_core.exceptions")
    class NotFound(Exception):
        pass
    exc_module.NotFound = NotFound
    api_module.exceptions = exc_module
    sys.modules["google.api_core"] = api_module
    sys.modules["google.api_core.exceptions"] = exc_module

from alfab import cli
from alfab.config import settings
from alfab.ops import adr_validation, evidence, export_ml, gold_snapshot, profile


class FakeBigQuery:
    def __init__(self):
        self.steps = [
            {"step": "dbt.silver", "status": "SUCCEEDED"},
            {"step": "dbt.gold", "status": "SUCCEEDED"},
            {"step": "publish.gold", "status": "SUCCEEDED"},
        ]
        self.tests = [
            {"test_name": "assert_avaliados_completos", "status": "pass", "severidade": "bloqueante"},
            {"test_name": "assert_ml_sem_vazamento", "status": "pass", "severidade": "bloqueante"},
        ]
        self.ml_columns = ["id_municipio", "rede_canonica", "ano_referencia", "alvo_taxa_t_mais_1"]
        self.labels = {"published_run_id": "r-1"}

    def query(self, sql, job_config=None):
        assert job_config is not None
        assert job_config.query_parameters[0].value == "r-1"
        if "pipeline_runs" in sql:
            return SimpleNamespace(result=lambda: self.steps)
        if "dq_results" in sql:
            return SimpleNamespace(result=lambda: self.tests)
        raise AssertionError(sql)

    def get_table(self, name):
        columns = self.ml_columns if name.endswith("ml_features_municipio") else ["meta_pactuada_pct"]
        return SimpleNamespace(schema=[SimpleNamespace(name=x) for x in columns],
                               labels=self.labels, num_rows=77)


def test_aceite_positive_cobre_etapas_testes_schema_e_versao():
    bq = FakeBigQuery()
    result = adr_validation.validate("r-1", bq_client=bq, cfg=settings())
    assert result.gold_rows == 77
    assert result.published_run_id == "r-1"
    assert len(result.tests) == 2


@pytest.mark.parametrize("scenario", ["no_silver", "missing_test", "bad_schema", "wrong_version"])
def test_aceite_reprova_provas_insuficientes(scenario):
    bq = FakeBigQuery()
    if scenario == "no_silver":
        bq.steps = bq.steps[1:]
    if scenario == "missing_test":
        bq.tests = bq.tests[1:]
    if scenario == "bad_schema":
        bq.ml_columns.append("feat_meta_pactuada_t_mais_1")
    if scenario == "wrong_version":
        bq.labels = {"published_run_id": "antigo"}
    with pytest.raises(adr_validation.AcceptanceError):
        adr_validation.validate("r-1", bq_client=bq, cfg=settings())


def test_run_id_e_schema_nao_aceitam_injecao_ou_vazamento():
    with pytest.raises(adr_validation.AcceptanceError):
        adr_validation.check_run_id("abc' OR 1=1")
    with pytest.raises(adr_validation.AcceptanceError):
        adr_validation.check_ml_schema(["alvo_1", "alvo_2"], "x")


def test_evidencia_tem_testes_individuais_e_preserva_historico(monkeypatch, tmp_path):
    (tmp_path / "evidencias").mkdir()
    monkeypatch.setattr(evidence, "ROOT", tmp_path)
    monkeypatch.setattr(evidence, "validate", lambda run_id: None)
    monkeypatch.setattr(evidence, "client", lambda: SimpleNamespace(list_tables=lambda ds: []))
    sqls = []

    def query(sql):
        sqls.append(sql)
        if "dq_results" in sql and "test_name IN" in sql:
            return [{"run_id": "r-1", "test_name": "assert_avaliados_completos", "status": "pass"}]
        return []

    monkeypatch.setattr(evidence, "_q", query)
    md = evidence.collect("r-1")
    assert "run_id `r-1`" in md
    assert "assert_avaliados_completos" in md
    assert "reprovacoes controladas" in md
    assert "INFORMATION_SCHEMA.COLUMNS" in "\n".join(sqls)
    assert "export.ml_fase3" in "\n".join(sqls)
    assert (tmp_path / "evidencias" / "execucao.md").read_text(encoding="utf-8") == md


def test_profile_so_substitui_csv_depois_de_todas_consultas_ok(monkeypatch, tmp_path):
    sql = tmp_path / "queries.sql"
    sql.write_text("-- name: 01_x\nSELECT 1;\n-- name: 02_y\nSELECT 2;\n", encoding="utf-8")
    pasta = tmp_path / "saida"
    pasta.mkdir()
    original = pasta / "01_x.csv"
    original.write_text("antigo\n", encoding="utf-8")
    monkeypatch.setattr(profile, "ROOT", tmp_path)
    monkeypatch.setattr(profile, "dry_run_bytes", lambda *_: 0)
    calls = []

    def run_query(sql, *_):
        calls.append(sql)
        if len(calls) == 2:
            raise RuntimeError("BigQuery indisponivel")
        return SimpleNamespace(result=lambda: [{"a": 1}], total_bytes_billed=0, job_id="j-1")

    monkeypatch.setattr(profile, "run_query", run_query)
    with pytest.raises(RuntimeError, match="BigQuery"):
        profile.run("r-1", "queries.sql", "saida")
    assert original.read_text(encoding="utf-8") == "antigo\n"
    assert not (pasta / "02_y.csv").exists()


def test_export_rejeita_versao_duplicada_ou_antiga():
    assert export_ml.version_suffix("2026-11-02") == "20261102"
    assert export_ml.version_suffix("2026-11-02-21d8d75") == "20261102_21d8d75"
    for version in ("2026-10-01", "2026-02-31", "2026/11/02", "2026-11-02-SQL"):
        with pytest.raises(ValueError):
            export_ml.version_suffix(version)


def test_export_nunca_consulta_gcs_com_schema_antigo(monkeypatch):
    bq = FakeBigQuery()
    bq.ml_columns.append("feat_meta_pactuada_t_mais_1")
    monkeypatch.setattr(export_ml, "client", lambda: bq)
    monkeypatch.setattr(export_ml.storage, "Client", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("GCS nao deveria ser chamado")))
    with pytest.raises(adr_validation.AcceptanceError):
        export_ml.export("r-2", "2026-11-02")


def test_foto_gold_persiste_antes_depois_somente_se_igual(monkeypatch, tmp_path):
    info = {"ml_features_municipio": {"published_run_id": "r-1", "num_rows": 7}}
    monkeypatch.setattr(gold_snapshot, "inspect_gold", lambda: info.copy())
    monkeypatch.setattr(gold_snapshot, "check_negative_run", lambda run_id: None)
    before = gold_snapshot.capture("antes", directory=tmp_path)
    after = gold_snapshot.capture("depois", "falha-1", directory=tmp_path)
    assert before.exists() and after.exists()
    with pytest.raises(FileExistsError):
        gold_snapshot.capture("antes", directory=tmp_path)


def test_cli_oferece_comandos_sem_ativar_gcp():
    parsed = cli.parser().parse_args(["validar-adrs", "--run-id", "r-1"])
    assert parsed.run_id == "r-1"
    parsed = cli.parser().parse_args(["export-ml", "--versao", "2026-11-02-21d8d75"])
    assert parsed.versao == "2026-11-02-21d8d75"
    parsed = cli.parser().parse_args(["dbt", "--layer", "silver", "--fault-injection", "avaliado_incompleto"])
    assert parsed.fault_injection == "avaliado_incompleto"


def test_fixture_negativa_so_existe_no_teste_e_com_guard_de_homologacao():
    root = Path(__file__).resolve().parents[1]
    sql = (root / "dbt/tests/singular/assert_avaliados_completos.sql").read_text(encoding="utf-8")
    assert "ALFAB_HML_PROJECT_ID" in sql
    assert "target.project" in sql
    assert "UNION ALL" in sql
    assert "FROM {{ ref('alunos') }}" in sql
    assert "peso_aluno" in sql


def test_foto_gold_negativa_exige_falha_e_nenhuma_publicacao(monkeypatch):
    bq = FakeBigQuery()
    bq.steps = [{"step": "dbt.silver", "status": "FAILED"}]
    bq.tests = [{"test_name": "assert_avaliados_completos", "status": "fail",
                 "severidade": "bloqueante", "failures": 1}]
    monkeypatch.setattr(gold_snapshot, "client", lambda: bq)
    gold_snapshot.check_negative_run("r-1")
    bq.steps.append({"step": "publish.gold", "status": "SUCCEEDED"})
    with pytest.raises(adr_validation.AcceptanceError, match="nao comprovado"):
        gold_snapshot.check_negative_run("r-1")


def test_export_nao_substitui_snapshot_existente(monkeypatch):
    bq = FakeBigQuery()  # get_table(snapshot) simula existencia
    monkeypatch.setattr(export_ml, "client", lambda: bq)
    monkeypatch.setattr(export_ml.storage, "Client", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("nao deveria tocar GCS com snapshot existente")))
    with pytest.raises(FileExistsError, match="snapshot ja existe"):
        export_ml.export("r-2", "2026-11-02")


def test_export_nao_mistura_parquets_se_prefixo_ja_existe(monkeypatch):
    bq = FakeBigQuery()
    original_get = bq.get_table

    def get_table(name):
        if "_fase3_" in name:
            raise export_ml.NotFound("snapshot ausente")
        return original_get(name)

    bq.get_table = get_table
    monkeypatch.setattr(export_ml, "client", lambda: bq)
    monkeypatch.setattr(export_ml.storage, "Client", lambda *a, **k: SimpleNamespace(
        list_blobs=lambda *a, **k: [object()]))
    with pytest.raises(FileExistsError, match="ja contem Parquet"):
        export_ml.export("r-2", "2026-11-02")
