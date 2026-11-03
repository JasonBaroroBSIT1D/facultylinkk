"""
Criterion C rank simulation adapter (Phase C1).

Per-service accumulation with criterion cap 10; legacy documents without bundles
retain best-per-indicator aggregation for historical records.
"""

from __future__ import annotations

import os
from typing import Any

from documents.criterion_c_evidence.scoring import aggregate_criterion_c_from_documents


def _env_adapter_enabled() -> bool:
    raw = (os.environ.get("CRITERION_C_SIMULATION_ADAPTER_ENABLED") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    return True


CRITERION_C_SIMULATION_ADAPTER_ENABLED: bool = _env_adapter_enabled()


def aggregate_criterion_c_simulation_from_documents(
    docs: list[Any],
    *,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> dict[str, Any]:
    block = aggregate_criterion_c_from_documents(
        docs,
        settings=settings,
        applicable_config_present=applicable_config_present,
    )
    block["simulationAdapterEnabled"] = CRITERION_C_SIMULATION_ADAPTER_ENABLED
    return block
