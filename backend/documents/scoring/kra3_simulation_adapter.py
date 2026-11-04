"""KRA III rank simulation adapter — bundle-based criterion totals."""

from __future__ import annotations

import os
from typing import Any

from kra_configuration.kra3_annex import (
    CRITERION_A_ID,
    CRITERION_B_ID,
    CRITERION_C_ID,
    CRITERION_D_ID,
    is_kra3_criterion,
)
from documents.kra3_evidence.scoring import (
    aggregate_kra3_criterion_from_documents,
    aggregate_kra3_kra_from_documents,
)


def _env_adapter_enabled() -> bool:
    raw = (os.environ.get("KRA3_SIMULATION_ADAPTER_ENABLED") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    return True


KRA3_SIMULATION_ADAPTER_ENABLED: bool = _env_adapter_enabled()


def aggregate_kra3_criterion_simulation_from_documents(
    docs: list[Any],
    *,
    criterion_id: str,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> dict[str, Any]:
    block = aggregate_kra3_criterion_from_documents(
        docs,
        criterion_id=criterion_id,
        settings=settings,
        applicable_config_present=applicable_config_present,
    )
    block["simulationAdapterEnabled"] = KRA3_SIMULATION_ADAPTER_ENABLED
    return block


def aggregate_kra3_simulation_from_documents(
    docs: list[Any],
    *,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> dict[str, Any]:
    block = aggregate_kra3_kra_from_documents(
        docs,
        settings=settings,
        applicable_config_present=applicable_config_present,
    )
    block["simulationAdapterEnabled"] = KRA3_SIMULATION_ADAPTER_ENABLED
    return block


__all__ = [
    "KRA3_SIMULATION_ADAPTER_ENABLED",
    "CRITERION_A_ID",
    "CRITERION_B_ID",
    "CRITERION_C_ID",
    "CRITERION_D_ID",
    "is_kra3_criterion",
    "aggregate_kra3_criterion_simulation_from_documents",
    "aggregate_kra3_simulation_from_documents",
]
