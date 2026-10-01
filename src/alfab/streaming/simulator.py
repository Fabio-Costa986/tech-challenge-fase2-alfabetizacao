"""Simulador de eventos (produtor).

Gera eventos realistas a partir de pares (município, rede, taxa) REAIS da Silver e publica no Pub/Sub.
Propositalmente injeta:
- duplicatas (mesmo event_id republicado) -> exercita o dedup do micro-lote;
- inválidos estruturais/domínio (taxa > 100, id malformado, JSON quebrado) -> quarentena no ingestor;
- inválidos referenciais (município inexistente) -> quarentena no micro-lote.

`produced_at` é carimbado na CRIAÇÃO do evento. Com `atraso_s` > 0 o evento é retido antes de publicar,
o que deve aparecer na latência medida (prova de que a métrica mede algo).
"""

from __future__ import annotations

import json
import random
import time
import uuid
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

Publish = Callable[[bytes], None]


@dataclass(frozen=True)
class Municipio:
    id_municipio: str
    rede: str
    taxa: float


FALLBACK_MUNICIPIOS = [  # só para modo local/teste; em nuvem a amostra vem da Silver
    Municipio("3550308", "3", 55.0), Municipio("3304557", "3", 50.0),
    Municipio("5300108", "2", 60.0), Municipio("2304400", "3", 70.0),
    Municipio("4106902", "3", 65.0),
]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _valid_event(rng: random.Random, m: Municipio) -> dict:
    kind = rng.choices(["indicador_atualizado", "medicao_desempenho", "meta_revisada"],
                       weights=[6, 3, 1])[0]
    if kind == "indicador_atualizado":
        taxa = min(100.0, max(0.0, rng.gauss(m.taxa, 3.0)))
        payload = {"ano": 2025, "id_municipio": m.id_municipio, "rede": m.rede,
                   "taxa_alfabetizacao": round(taxa, 2)}
    elif kind == "medicao_desempenho":
        n = rng.randint(20, 2000)
        alf = int(n * min(1.0, max(0.0, rng.gauss(m.taxa / 100, 0.05))))
        payload = {"ano": 2025, "id_municipio": m.id_municipio, "rede": m.rede,
                   "n_avaliados": n, "n_alfabetizados": alf,
                   "proficiencia_media": round(rng.gauss(743, 40), 1)}
    else:
        payload = {"id_municipio": m.id_municipio, "rede": m.rede,
                   "ano_meta": rng.randint(2026, 2030),
                   "meta_pct": round(min(100.0, m.taxa + rng.uniform(2, 15)), 1)}
    return {"event_id": str(uuid.uuid4()), "event_type": kind, "produced_at": _now(),
            "origem_dado": "SIMULADO", "payload": payload}


def _invalid_event(rng: random.Random, m: Municipio) -> tuple[bytes, str]:
    base = _valid_event(rng, m)
    kind = rng.choice(["taxa_fora_faixa", "id_malformado", "campo_faltando", "json_quebrado",
                       "municipio_inexistente"])
    if kind == "taxa_fora_faixa":
        base.update(event_type="indicador_atualizado",
                    payload={"ano": 2025, "id_municipio": m.id_municipio, "rede": m.rede,
                             "taxa_alfabetizacao": 150.0})
    elif kind == "id_malformado":
        base["payload"]["id_municipio"] = "123"
    elif kind == "campo_faltando":
        base.pop("produced_at")
    elif kind == "json_quebrado":
        return b'{"event_id": "quebrado", ', kind
    elif kind == "municipio_inexistente":  # estruturalmente válido; reprovado no micro-lote
        base["payload"]["id_municipio"] = "9999999"
    return json.dumps(base).encode(), kind


def generate(n: int, municipios: list[Municipio], duplicate_rate: float, invalid_rate: float,
             seed: int | None = None) -> Iterable[tuple[bytes, str]]:
    """Gera (mensagem, categoria). Categoria: valido | duplicata | invalido:<tipo>."""
    rng = random.Random(seed)
    sent: list[bytes] = []
    for _ in range(n):
        m = rng.choice(municipios)
        r = rng.random()
        if sent and r < duplicate_rate:
            yield rng.choice(sent), "duplicata"
        elif r < duplicate_rate + invalid_rate:
            data, kind = _invalid_event(rng, m)
            yield data, f"invalido:{kind}"
        else:
            data = json.dumps(_valid_event(rng, m)).encode()
            sent.append(data)
            yield data, "valido"


def run(n: int, publish: Publish, municipios: list[Municipio], duplicate_rate: float,
        invalid_rate: float, rate_per_s: float = 20.0, atraso_s: float = 0.0,
        seed: int | None = None) -> Counter:
    counts: Counter = Counter()
    interval = 1.0 / rate_per_s if rate_per_s > 0 else 0.0
    for data, category in generate(n, municipios, duplicate_rate, invalid_rate, seed):
        if atraso_s > 0:
            time.sleep(atraso_s)
        publish(data)
        kind = category.split(":")[0]
        counts[kind] += 1
        if kind != category:
            counts[category] += 1
        if interval:
            time.sleep(interval)
    return counts


def pubsub_publisher(project_id: str, topic: str) -> tuple[Publish, Callable[[], None]]:
    from google.cloud import pubsub_v1

    client = pubsub_v1.PublisherClient()
    path = client.topic_path(project_id, topic)
    futures = []

    def publish(data: bytes) -> None:
        futures.append(client.publish(path, data))

    def flush() -> None:
        for f in futures:
            f.result(timeout=60)

    return publish, flush


def sample_municipios(limit: int = 300) -> list[Municipio]:
    from alfab.bq import client
    from alfab.config import settings

    s = settings()
    sql = f"""
      SELECT id_municipio, rede_codigo AS rede, AVG(taxa_alfabetizacao) AS taxa
      FROM `{s.table('silver', 'indicador_municipio')}`
      WHERE taxa_alfabetizacao IS NOT NULL
      GROUP BY 1, 2
      ORDER BY FARM_FINGERPRINT(id_municipio)
      LIMIT {int(limit)}
    """
    return [Municipio(r.id_municipio, r.rede, float(r.taxa)) for r in client().query(sql).result()]
