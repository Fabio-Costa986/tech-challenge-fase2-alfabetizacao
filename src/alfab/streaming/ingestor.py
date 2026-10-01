"""Cloud Run service que recebe eventos do Pub/Sub (push subscription).

Semântica de entrega:
- Evento válido   -> bronze.eventos_raw (toda entrega é gravada, inclusive reentregas) -> 204 (ACK)
- Evento inválido -> bronze.eventos_quarentena com o motivo -> 204 (ACK: reenviar não o tornaria válido)
- Falha ao gravar -> 500 -> o Pub/Sub reenvia com backoff; após N tentativas vai para a DLQ.

Como o Pub/Sub entrega pelo menos uma vez, duplicatas CHEGAM na Bronze. A garantia de unicidade
é do micro-lote (MERGE por event_id na Silver), não daqui.

`ingested_at` é carimbado AQUI, no recebimento, por um relógio diferente do produtor.
"""

from __future__ import annotations

import base64
import binascii
import json
from datetime import UTC, datetime
from typing import Annotated, Protocol

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import ValidationError

from alfab.observability import configure_logging, log
from alfab.streaming.schema import parse_event, to_bronze_row


class EventSink(Protocol):
    def write_valid(self, row: dict) -> None: ...
    def write_quarantine(self, row: dict) -> None: ...


class BigQuerySink:
    def __init__(self) -> None:
        from alfab.bq import client
        from alfab.config import settings

        s = settings()
        self._client = client()
        self._raw = s.table("bronze", "eventos_raw")
        self._quarantine = s.table("bronze", "eventos_quarentena")

    def write_valid(self, row: dict) -> None:
        # Sem insertId de propósito: o dedup best-effort do BigQuery esconderia as reentregas.
        # A Bronze registra TODA entrega; a unicidade é garantida só pelo MERGE do micro-lote.
        errors = self._client.insert_rows_json(self._raw, [row], row_ids=[None])
        if errors:
            raise RuntimeError(f"insert eventos_raw: {errors}")

    def write_quarantine(self, row: dict) -> None:
        errors = self._client.insert_rows_json(self._quarantine, [row])
        if errors:
            raise RuntimeError(f"insert eventos_quarentena: {errors}")


_sink: EventSink | None = None


def get_sink() -> EventSink:
    global _sink
    if _sink is None:
        _sink = BigQuerySink()
    return _sink


configure_logging()
app = FastAPI(title="alfab event-ingestor")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/pubsub/push", status_code=204)
async def pubsub_push(request: Request, sink: Annotated[EventSink, Depends(get_sink)]) -> Response:
    ingested_at = datetime.now(UTC)
    try:
        envelope = await request.json()
        message = envelope["message"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        # Não é um push do Pub/Sub: rejeita sem gravar
        raise HTTPException(status_code=400, detail="envelope Pub/Sub inválido") from exc

    message_id = message.get("messageId") or message.get("message_id")
    publish_time = message.get("publishTime") or message.get("publish_time")
    attempt = envelope.get("deliveryAttempt")

    try:
        raw = base64.b64decode(message.get("data", ""), validate=True)
    except (binascii.Error, ValueError):
        raw = b""

    try:
        evt = parse_event(raw)
    except (ValidationError, ValueError) as exc:
        reason = exc.errors(include_url=False) if isinstance(exc, ValidationError) else str(exc)
        sink.write_quarantine({
            "pubsub_message_id": message_id,
            "pubsub_publish_time": publish_time,
            "received_at": ingested_at.isoformat(),
            "raw_data": raw.decode("utf-8", errors="replace")[:100_000],
            "motivo_rejeicao": json.dumps(reason, default=str, ensure_ascii=False)[:10_000],
            "delivery_attempt": attempt,
        })
        log("evento em quarentena", event="event_quarantined", message_id=message_id)
        return Response(status_code=204)

    row = to_bronze_row(evt, ingested_at, message_id, publish_time, attempt)
    sink.write_valid(row)  # exceção -> 500 -> retry do Pub/Sub -> DLQ
    log("evento ingerido", event="event_ingested", event_id=row["event_id"],
        latency_s=(ingested_at - evt.produced_at).total_seconds())
    return Response(status_code=204)
