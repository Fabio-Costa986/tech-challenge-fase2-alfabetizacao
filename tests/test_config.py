import pytest

from alfab.config import ConfigError, load_settings, settings


def test_ids_vem_do_ambiente():
    s = settings()
    assert s.project_id == "proj-teste"
    assert s.bronze_bucket == "bucket-teste"
    assert s.table("ops", "pipeline_runs") == "proj-teste.ops.pipeline_runs"


def test_variavel_obrigatoria_ausente_falha(monkeypatch):
    monkeypatch.delenv("GCP_PROJECT_ID")
    monkeypatch.setattr("alfab.config.load_dotenv", lambda *a, **k: None)
    with pytest.raises(ConfigError, match="GCP_PROJECT_ID"):
        load_settings()


def test_seis_entidades_mais_dicionario_e_diretorio():
    ents = settings().entities
    for nome in ["alunos", "municipio", "uf", "meta_alfabetizacao_brasil", "meta_alfabetizacao_uf",
                 "meta_alfabetizacao_municipio", "dicionario"]:
        assert ents[nome].fqn == f"basedosdados.br_inep_avaliacao_alfabetizacao.{ents[nome].table}"
    assert ents["diretorio_municipio"].fqn == "basedosdados.br_bd_diretorios_brasil.municipio"


def test_colunas_explicitas_em_toda_entidade():
    for e in settings().entities.values():
        assert e.columns and "*" not in e.columns
