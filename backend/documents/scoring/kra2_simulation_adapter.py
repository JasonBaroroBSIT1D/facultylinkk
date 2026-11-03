"""
KRA II rank simulation adapter — criterion-level accomplishment sums (Phase 2).
"""

from __future__ import annotations

import os
from typing import Any

from kra_configuration.kra2_annex import CRITERION_A_ID, CRITERION_B_ID, CRITERION_C_ID, is_kra2_criterion
from documents.kra2_evidence.scoring import aggregate_kra2_criterion_from_documents


def _env_adapter_enabled() -> bool:
    raw = (os.environ.get("KRA2_SIMULATION_ADAPTER_ENABLED") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    return True


KRA2_SIMULATION_ADAPTER_ENABLED: bool = _env_adapter_enabled()


def aggregate_kra2_criterion_simulation_from_documents(
    docs: list[Any],
    *,
    criterion_id: str,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> dict[str, Any]:
    block = aggregate_kra2_criterion_from_documents(
        docs,
        criterion_id=criterion_id,
        settings=settings,
        applicable_config_present=applicable_config_present,
    )
    block["simulationAdapterEnabled"] = KRA2_SIMULATION_ADAPTER_ENABLED
    return block


def aggregate_kra2_a_simulation_from_documents(
    docs: list[Any],
    *,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> dict[str, Any]:
    return aggregate_kra2_criterion_simulation_from_documents(
        docs,
        criterion_id=CRITERION_A_ID,
        settings=settings,
        applicable_config_present=applicable_config_present,
    )
