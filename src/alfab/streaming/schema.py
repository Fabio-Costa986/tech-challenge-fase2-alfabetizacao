"""Contrato do evento de streaming (validação estrutural e de domínio).

A validação referencial (o município existe?) acontece no micro-lote, contra a Silver,
porque o ingestor não deve consultar o warehouse a cada mensagem.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

IdMunicipio = Annotated[str, Field(pattern=r"^\d{7}$")]
Percentual = Annotated[float, Field(ge=0, le=100)]
AnoAvaliacao = Annotated[int, Field(ge=2023, le=2030)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IndicadorAtualizado(_Strict):
    ano: AnoAvaliacao
    id_municipio: IdMunicipio
    rede: str = Field(min_length=1, max_length=20)
    taxa_alfabetizacao: Percentual


class MetaRevisada(_Strict):
    id_municipio: IdMunicipio
    rede: str = Field(min_length=1, max_length=20)
    ano_meta: Annotated[int, Field(ge=2024, le=2030)]
    meta_pct: Percentual


class MedicaoDesempenho(_Strict):
    ano: AnoAvaliacao
    id_municipio: IdMunicipio
    rede: str = Field(min_length=1, max_length=20)
    n_avaliados: Annotated[int, Field(gt=0)]
    n_alfabetizados: Annotated[int, Field(ge=0)]
    proficiencia_media: Annotated[float, Field(gt=0, lt=1500)]

    @model_validator(mode="after")
    def _alfabetizados_ate_avaliados(self) -> MedicaoDesempenho:
        if self.n_alfabetizados > self.n_avaliados:
            raise ValueError("n_alfabetizados maior que n_avaliados")
        return self


class _Envelope(_Strict):
    event_id: UUID
    produced_at: datetime
    origem_dado: Literal["SIMULADO"]


class EventoIndicador(_Envelope):
    event_type: Literal["indicador_atualizado"]
    payload: IndicadorAtualizado


class EventoMeta(_Envelope):
    event_type: Literal["meta_revisada"]
    payload: MetaRevisada


class EventoMedicao(_Envelope):
    event_type: Literal["medicao_desempenho"]
    payload: MedicaoDesempenho


Evento = Annotated[EventoIndicador | EventoMeta | EventoMedicao, Field(discriminator="event_type")]
EVENTO = TypeAdapter(Evento)


def parse_event(raw: bytes | str) -> EventoIndicador | EventoMeta | EventoMedicao:
    """Lança pydantic.ValidationError ou ValueError (JSON malformado)."""
    return EVENTO.validate_python(json.loads(raw))


def to_bronze_row(evt, ingested_at: datetime, message_id: str | None,
                  publish_time: str | None, delivery_attempt: int | None) -> dict:
    p = evt.payload
    return {
        "event_id": str(evt.event_id),
        "event_type": evt.event_type,
        "produced_at": evt.produced_at.isoformat(),
        "ingested_at": ingested_at.isoformat(),
        "origem_dado": evt.origem_dado,
        "id_municipio": p.id_municipio,
        "rede": p.rede,
        "ano": getattr(p, "ano", None) or getattr(p, "ano_meta", None),
        "payload": p.model_dump_json(),
        "pubsub_message_id": message_id,
        "pubsub_publish_time": publish_time,
        "delivery_attempt": delivery_attempt,
    }
