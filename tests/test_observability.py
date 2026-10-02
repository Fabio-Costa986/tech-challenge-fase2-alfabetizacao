import re

import pytest

from alfab.observability import new_run_id, track_step


def test_sucesso_registra_metricas():
    rows = []
    with track_step("r1", "batch", "etapa", rows.append) as m:
        m.rows_in, m.rows_out = 10, 8
    assert rows[0]["status"] == "SUCCEEDED"
    assert rows[0]["rows_in"] == 10 and rows[0]["rows_out"] == 8
    assert rows[0]["duration_s"] >= 0


def test_falha_registra_e_RELANCA():
    """O padrão proibido pelo enunciado: exceção capturada e processo termina com sucesso."""
    rows = []
    with pytest.raises(ValueError, match="dado ruim"):
        with track_step("r1", "batch", "etapa", rows.append):
            raise ValueError("dado ruim")
    assert rows[0]["status"] == "FAILED"
    assert "dado ruim" in rows[0]["error"]


def test_falha_ao_gravar_metrica_nao_mascara_erro_original():
    def writer(_row):
        raise RuntimeError("bq fora")

    with pytest.raises(ValueError):
        with track_step("r1", "batch", "etapa", writer):
            raise ValueError("original")


def test_falha_ao_gravar_metrica_em_sucesso_falha_a_etapa():
    def writer(_row):
        raise RuntimeError("bq fora")

    with pytest.raises(RuntimeError, match="bq fora"):
        with track_step("r1", "batch", "etapa", writer):
            pass


def test_run_id_ordenavel():
    a, b = new_run_id(), new_run_id()
    assert re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{6}", a)
    assert a[:16] <= b[:16]
