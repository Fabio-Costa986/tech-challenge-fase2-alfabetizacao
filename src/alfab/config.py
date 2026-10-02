"""Fonte única de configuração.

IDs de projeto, bucket, região e e-mail vêm SOMENTE de variáveis de ambiente (ou do .env local).
O que ingerir e como vem de config/settings.yaml. Nenhum outro módulo lê os.environ diretamente.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(os.environ.get("ALFAB_ROOT", Path(__file__).resolve().parents[2]))
SETTINGS_FILE = Path(os.environ.get("ALFAB_SETTINGS", ROOT / "config" / "settings.yaml"))


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Entity:
    name: str
    project: str
    dataset: str
    table: str
    columns: tuple[str, ...]

    @property
    def fqn(self) -> str:
        return f"{self.project}.{self.dataset}.{self.table}"


@dataclass(frozen=True)
class Settings:
    project_id: str
    bq_location: str
    region: str
    bronze_bucket: str
    pubsub_topic: str
    max_bytes_billed: int
    datasets: dict[str, str]
    entities: dict[str, Entity]
    streaming: dict = field(default_factory=dict)

    def table(self, layer: str, name: str) -> str:
        return f"{self.project_id}.{self.datasets[layer]}.{name}"


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"Variável de ambiente obrigatória ausente: {name} (veja .env.example)")
    return value


def load_settings(settings_file: Path | None = None) -> Settings:
    load_dotenv(ROOT / ".env", override=False)
    raw = yaml.safe_load(Path(settings_file or SETTINGS_FILE).read_text(encoding="utf-8"))

    src = raw["source"]
    entities = {
        name: Entity(
            name=name,
            project=spec.get("project", src["project"]),
            dataset=spec.get("dataset", src["dataset"]),
            table=spec["table"],
            columns=tuple(spec["columns"]),
        )
        for name, spec in raw["entities"].items()
    }

    return Settings(
        project_id=_required("GCP_PROJECT_ID"),
        bq_location=os.environ.get("BQ_LOCATION", "US"),
        region=os.environ.get("GCP_REGION", "us-central1"),
        bronze_bucket=_required("BRONZE_BUCKET"),
        pubsub_topic=os.environ.get("PUBSUB_TOPIC", "alfab-eventos"),
        max_bytes_billed=int(os.environ.get("MAX_BYTES_BILLED", str(50 * 1024**3))),
        datasets=raw["datasets"],
        entities=entities,
        streaming=raw.get("streaming", {}),
    )


@lru_cache(maxsize=1)
def settings() -> Settings:
    return load_settings()
