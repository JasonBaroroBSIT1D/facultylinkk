"""Criterion A (Teaching Effectiveness) upload classification helpers."""

from __future__ import annotations

CRITERION_A_ID = "kra1-a"
CRITERION_A_AUTO_INDICATOR_ID = "kra1-a-teaching-evidence"

_LEGACY_SET_SEF_IDS = frozenset({"kra1-a-student", "kra1-a-supervisor"})


def is_auto_criterion_a_upload(indicator_id: str | None) -> bool:
    return (indicator_id or "").strip() == CRITERION_A_AUTO_INDICATOR_ID


def should_run_set_sef_pipeline(*, indicator_id: str | None, criterion_id: str | None) -> bool:
    if (criterion_id or "").strip() == CRITERION_A_ID:
        return True
    ind = (indicator_id or "").strip()
    return ind in _LEGACY_SET_SEF_IDS


def normalize_upload_classification(
    *,
    kra_id: str,
    criterion_id: str,
    indicator_id: str,
) -> tuple[str, str, str]:
    """
    Resolve KRA/criterion/indicator for upload.

    Criterion A accepts uploads without a manual SET/SEF indicator (OCR routes records).
    Legacy clients may still send ``kra1-a-student`` or ``kra1-a-supervisor``.
    """
    kra_id = (kra_id or "").strip()
    criterion_id = (criterion_id or "").strip()
    indicator_id = (indicator_id or "").strip()
    if not kra_id or not criterion_id:
        raise ValueError("classification_required")
    if criterion_id == CRITERION_A_ID:
        if not indicator_id or indicator_id == CRITERION_A_AUTO_INDICATOR_ID:
            return kra_id, criterion_id, CRITERION_A_AUTO_INDICATOR_ID
        if indicator_id in _LEGACY_SET_SEF_IDS:
            return kra_id, criterion_id, indicator_id
        raise ValueError("invalid_indicator")
    if not indicator_id:
        raise ValueError("classification_required")
    return kra_id, criterion_id, indicator_id


def classification_status_from_composition(composition: str, section_count: int) -> str:
    if section_count <= 0:
        return "needs_classification"
    if composition in ("Uncertain evaluation content", "No evaluation sections detected"):
        return "needs_classification"
    return "classified"
