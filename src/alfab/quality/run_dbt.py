"""Executa uma camada do dbt (`dbt build` = modelos + testes) como portão de qualidade.

Códigos de saída (propagados ao Cloud Run Job e, por consequência, ao Workflow):
  0 = sucesso (testes `warn` podem ter falhado: são informativos)
  3 = regra BLOQUEANTE reprovou (teste severity=error) -> camada seguinte NÃO é publicada; sem retry
  1 = erro de execução (SQL, permissão, rede) -> elegível a retry

Os resultados de cada teste são persistidos em ops.dq_results pelo hook on-run-end
(dbt/macros/log_dq_results.sql), inclusive quando a execução falha.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from alfab.config import ROOT

DBT_DIR = ROOT / "dbt"

EXIT_OK, EXIT_ERROR, EXIT_DQ_FAILED = 0, 1, 3

LAYER_SELECTORS = {
    "silver": ["tag:seeds", "tag:silver", "tag:quality"],
    "gold": ["tag:gold"],
}


class QualityGateFailed(RuntimeError):
    exit_code = EXIT_DQ_FAILED


class DbtExecutionError(RuntimeError):
    exit_code = EXIT_ERROR


@dataclass
class Outcome:
    model_errors: list[str] = field(default_factory=list)
    blocking_failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passed: int = 0

    @property
    def exit_code(self) -> int:
        if self.model_errors:
            return EXIT_ERROR
        if self.blocking_failures:
            return EXIT_DQ_FAILED
        return EXIT_OK


def classify(results: list[tuple[str, str, str]]) -> Outcome:
    """results: (resource_type, name, status) — status do dbt: pass|fail|warn|error|skipped|success."""
    out = Outcome()
    for resource_type, name, status in results:
        if resource_type == "test":
            if status == "fail":
                out.blocking_failures.append(name)
            elif status == "warn":
                out.warnings.append(name)
            elif status == "error":
                out.model_errors.append(name)
            elif status == "pass":
                out.passed += 1
        elif status == "error":
            out.model_errors.append(name)
    return out


def build_args(layer: str, run_id: str, fault_injection: str | None) -> list[str]:
    if layer not in LAYER_SELECTORS:
        raise ValueError(f"camada inválida: {layer}")
    vars_ = {"run_id": run_id, "fault_injection": fault_injection or "none"}
    return [
        "build",
        "--select", *LAYER_SELECTORS[layer],
        "--vars", json.dumps(vars_),
        "--project-dir", str(DBT_DIR),
        "--profiles-dir", str(DBT_DIR),
    ]


def run(layer: str, run_id: str, fault_injection: str | None = None) -> Outcome:
    from dbt.cli.main import dbtRunner

    res = dbtRunner().invoke(build_args(layer, run_id, fault_injection))
    if res.exception is not None:
        raise DbtExecutionError(f"dbt falhou antes de executar: {res.exception}")

    rows = [(r.node.resource_type, r.node.name, str(r.status)) for r in (res.result or [])]
    outcome = classify(rows)
    if outcome.exit_code == EXIT_ERROR:
        raise DbtExecutionError(f"erros de execução: {outcome.model_errors}")
    if outcome.exit_code == EXIT_DQ_FAILED:
        raise QualityGateFailed(
            f"{len(outcome.blocking_failures)} regra(s) bloqueante(s) reprovada(s) em {layer}: "
            f"{outcome.blocking_failures}")
    return outcome


def manifest_path() -> Path:
    return DBT_DIR / "target" / "manifest.json"
