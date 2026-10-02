import base64
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from alfab.streaming import simulator
from alfab.streaming.ingestor import app, get_sink
from alfab.streaming.schema import parse_event, to_bronze_row


def evento(**over):
    base = {
        "event_id": str(uuid.uuid4()),
        "event_type": "indicador_atualizado",
        "produced_at": datetime.now(UTC).isoformat(),
        "origem_dado": "SIMULADO",
        "payload": {"ano": 2025, "id_municipio": "3550308", "rede": "3", "taxa_alfabetizacao": 61.5},
    }
    base.update(over)
    return base


# ------------------------------------------------------------------ contrato
def test_evento_valido_dos_tres_tipos():
    parse_event(json.dumps(evento()))
    parse_event(json.dumps(evento(event_type="meta_revisada", payload={
        "id_municipio": "3550308", "rede": "3", "ano_meta": 2027, "meta_pct": 70})))
    parse_event(json.dumps(evento(event_type="medicao_desempenho", payload={
        "ano": 2025, "id_municipio": "3550308", "rede": "3", "n_avaliados": 100,
        "n_alfabetizados": 60, "proficiencia_media": 750.0})))


@pytest.mark.parametrize("mutacao", [
    {"payload": {"ano": 2025, "id_municipio": "3550308", "rede": "3", "taxa_alfabetizacao": 150}},
    {"payload": {"ano": 2025, "id_municipio": "123", "rede": "3", "taxa_alfabetizacao": 50}},
    {"origem_dado": "OFICIAL"},          # simulador não pode se passar por dado oficial
    {"event_type": "desconhecido"},
    {"campo_extra": 1},
])
def test_evento_invalido(mutacao):
    with pytest.raises(ValidationError):
        parse_event(json.dumps(evento(**mutacao)))


def test_alfabetizados_maior_que_avaliados_e_invalido():
    with pytest.raises(ValidationError):
        parse_event(json.dumps(evento(event_type="medicao_desempenho", payload={
            "ano": 2025, "id_municipio": "3550308", "rede": "3", "n_avaliados": 10,
            "n_alfabetizados": 11, "proficiencia_media": 700.0})))


def test_json_quebrado_e_invalido():
    with pytest.raises(ValueError):
        parse_event(b'{"event_id": ')


def test_linha_bronze_tem_dois_relogios():
    produced = datetime.now(UTC) - timedelta(seconds=3)
    evt = parse_event(json.dumps(evento(produced_at=produced.isoformat())))
    row = to_bronze_row(evt, datetime.now(UTC), "m1", None, 1)
    assert row["produced_at"] != row["ingested_at"]
    assert row["origem_dado"] == "SIMULADO" and row["ano"] == 2025


# ------------------------------------------------------------------ simulador
def test_simulador_gera_duplicatas_identicas_e_invalidos():
    msgs = list(simulator.generate(2000, simulator.FALLBACK_MUNICIPIOS, 0.05, 0.03, seed=7))
    categorias = [c.split(":")[0] for _, c in msgs]
    validos = {m for m, c in msgs if c == "valido"}
    duplicatas = [m for m, c in msgs if c == "duplicata"]
    assert 50 < len(duplicatas) < 150 and 30 < categorias.count("invalido") < 100
    assert all(d in validos for d in duplicatas), "duplicata = mesma mensagem (mesmo event_id)"


def test_simulador_deterministico_com_seed():
    a = [c for _, c in simulator.generate(200, simulator.FALLBACK_MUNICIPIOS, 0.05, 0.03, seed=1)]
    b = [c for _, c in simulator.generate(200, simulator.FALLBACK_MUNICIPIOS, 0.05, 0.03, seed=1)]
    assert a == b


def test_atraso_artificial_retem_antes_de_publicar(monkeypatch):
    dormidas = []
    monkeypatch.setattr(simulator.time, "sleep", dormidas.append)
    simulator.run(3, lambda d: None, simulator.FALLBACK_MUNICIPIOS, 0, 0, rate_per_s=0, atraso_s=2.0, seed=1)
    assert dormidas == [2.0, 2.0, 2.0]


# ------------------------------------------------------------------ ingestor
class FakeSink:
    def __init__(self, falhar=False):
        self.validos, self.quarentena, self.falhar = [], [], falhar

    def write_valid(self, row):
        if self.falhar:
            raise RuntimeError("bigquery indisponível")
        self.validos.append(row)

    def write_quarantine(self, row):
        self.quarentena.append(row)


def push(data: bytes, attempt=1):
    return {"message": {"data": base64.b64encode(data).decode(), "messageId": "m-1",
                        "publishTime": datetime.now(UTC).isoformat()},
            "subscription": "s", "deliveryAttempt": attempt}


@pytest.fixture
def cliente():
    sink = FakeSink()
    app.dependency_overrides[get_sink] = lambda: sink
    yield TestClient(app, raise_server_exceptions=False), sink
    app.dependency_overrides.clear()


def test_ingestor_aceita_valido(cliente):
    client, sink = cliente
    r = client.post("/pubsub/push", json=push(json.dumps(evento()).encode()))
    assert r.status_code == 204
    assert len(sink.validos) == 1 and not sink.quarentena
    assert sink.validos[0]["ingested_at"] != sink.validos[0]["produced_at"]


def test_ingestor_quarentena_invalido_e_da_ack(cliente):
    client, sink = cliente
    r = client.post("/pubsub/push", json=push(b'{"quebrado": '))
    assert r.status_code == 204, "inválido recebe ACK: reenviar não o tornaria válido"
    assert len(sink.quarentena) == 1 and not sink.validos
    assert sink.quarentena[0]["motivo_rejeicao"]


def test_ingestor_aceita_duplicata_na_bronze(cliente):
    """Dedup é responsabilidade do micro-lote (MERGE por event_id), não do ingestor."""
    client, sink = cliente
    data = json.dumps(evento()).encode()
    client.post("/pubsub/push", json=push(data))
    client.post("/pubsub/push", json=push(data, attempt=2))
    assert len(sink.validos) == 2
    assert sink.validos[0]["event_id"] == sink.validos[1]["event_id"]


def test_ingestor_falha_de_escrita_retorna_5xx_para_retry():
    app.dependency_overrides[get_sink] = lambda: FakeSink(falhar=True)
    try:
        r = TestClient(app, raise_server_exceptions=False).post(
            "/pubsub/push", json=push(json.dumps(evento()).encode()))
        assert r.status_code >= 500
    finally:
        app.dependency_overrides.clear()


def test_ingestor_rejeita_envelope_que_nao_e_pubsub(cliente):
    client, _ = cliente
    assert client.post("/pubsub/push", json={"foo": 1}).status_code == 400
