import json
from types import SimpleNamespace

import pytest

from alfab import cli
from alfab.quality import run_dbt
from alfab.quality.run_dbt import EXIT_DQ_FAILED, EXIT_ERROR, EXIT_OK, classify


def test_warn_nao_bloqueia_fail_bloqueia_error_e_erro():
    assert classify([("test", "t1", "pass"), ("test", "t2", "warn")]).exit_code == EXIT_OK
    assert classify([("test", "t1", "fail")]).exit_code == EXIT_DQ_FAILED
    assert classify([("model", "m1", "error"), ("test", "t1", "fail")]).exit_code == EXIT_ERROR


def test_selecao_por_camada_e_vars():
    args = run_dbt.build_args("silver", "r-1", "duplicate_keys")
    assert args[0] == "build"
    assert {"tag:seeds", "tag:silver", "tag:quality"} <= set(args)
    vars_ = json.loads(args[args.index("--vars") + 1])
    assert vars_ == {"run_id": "r-1", "fault_injection": "duplicate_keys"}
    with pytest.raises(ValueError):
        run_dbt.build_args("bronze", "r", None)


def _fake_runner(results, success=None):
    if success is None:
        success = not any(s in {"fail", "error"} for _t, _n, s in results)

    class Runner:
        def invoke(self, _args):
            return SimpleNamespace(success=success, exception=None, result=[
                SimpleNamespace(node=SimpleNamespace(resource_type=t, name=n), status=s)
                for t, n, s in results])
    return Runner


def test_regra_bloqueante_reprovada_levanta_quality_gate(monkeypatch):
    monkeypatch.setattr("dbt.cli.main.dbtRunner", _fake_runner([("test", "unique_x", "fail")]))
    with pytest.raises(run_dbt.QualityGateFailed) as exc:
        run_dbt.run("silver", "r")
    assert exc.value.exit_code == 3


def test_dbt_sucesso_inconsistente_ou_sem_resultados_nao_libera_publicacao(monkeypatch):
    # Caso um dbtRunner reporte success=False sem registrar status=fail, falhar fechado.
    monkeypatch.setattr("dbt.cli.main.dbtRunner", _fake_runner([("model", "alunos", "success")], False))
    with pytest.raises(run_dbt.DbtExecutionError):
        run_dbt.run("silver", "r")

    monkeypatch.setattr("dbt.cli.main.dbtRunner", _fake_runner([]))
    with pytest.raises(run_dbt.DbtExecutionError):
        run_dbt.run("silver", "r")


def test_dbt_aviso_sem_bloqueio_continua_valido(monkeypatch):
    monkeypatch.setattr("dbt.cli.main.dbtRunner", _fake_runner([("test", "informativa", "warn")]))
    assert run_dbt.run("silver", "r").exit_code == EXIT_OK


def test_cli_propaga_codigo_de_saida(monkeypatch):
    """Nenhuma falha termina com código 0 (o Cloud Run Job e o Workflow precisam ver FAILED)."""
    for exc, esperado in [(run_dbt.QualityGateFailed("reprovou"), 3), (RuntimeError("erro técnico"), 1)]:
        def falha(_a, exc=exc):
            raise exc

        p = cli.parser()
        for action in p._subparsers._group_actions:
            action.choices["microbatch"].set_defaults(fn=falha)
        monkeypatch.setattr(cli, "parser", lambda p=p: p)
        assert cli.main(["microbatch"]) == esperado
