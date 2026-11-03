"""Criterion B simulation aggregation — distinct outputs vs duplicate credit (Phase 5A.1)."""

from __future__ import annotations

import re
from typing import Any

from kra_configuration.criterion_b_annex import annex_row_for_indicator
from documents.criterion_b_evidence.program_bundle import is_academic_program_bundle

_NORMALIZE_RE = re.compile(r"\s+")


def _normalize_label(value: str | None) -> str:
    return _NORMALIZE_RE.sub(" ", (value or "").strip().lower())


def deduplication_key_for_bundle(
    bundle: dict[str, Any] | None,
    *,
    document_public_id: str | None = None,
) -> str:
    """
    Stable identity for one scored Criterion B **output** (instructional material or program claim).

    Used to prevent double credit for the same material (e.g. sole + co paths, re-uploads)
    while allowing multiple distinct outputs that share an Annex A row or indicator ID.
    """
    if not bundle or not isinstance(bundle, dict):
        return f"unknown:{document_public_id or 'missing'}"

    if is_academic_program_bundle(bundle):
        program = _normalize_label(str(bundle.get("programName") or ""))
        indicator = (bundle.get("indicatorId") or "").strip()
        return f"program:{program}:{indicator}"

    checklist = bundle.get("checklist") if isinstance(bundle.get("checklist"), dict) else {}
    primary = checklist.get("primary_material")
    primary = primary if isinstance(primary, dict) else {}
    file_hash = (primary.get("fileHash") or "").strip()
    if file_hash:
        return f"im:hash:{file_hash}"

    title = _normalize_label(str(bundle.get("materialTitle") or ""))
    if title:
        return f"im:title:{title}"

    return f"im:doc:{document_public_id or 'unknown'}"


def aggregate_eligible_points_by_output(
    results: list[Any],
    *,
    dedupe_keys: list[str],
    settings: dict[str, Any] | None = None,
) -> tuple[float, float]:
    """
    Sum eligible points with one credit per deduplication key per Annex row.

    Within each (annex_row_id, dedupe_key) group, keep the **maximum** points
    (resolves sole vs co duplicate submissions for the same file).
    """
    from kra_configuration.criterion_b_scoring import cap_criterion_b_total

    if len(dedupe_keys) != len(results):
        raise ValueError("dedupe_keys must align one-to-one with results")

    best_by_output: dict[tuple[str, str], float] = {}
    for res, dedupe_key in zip(results, dedupe_keys, strict=True):
        if not getattr(res, "eligible", False) or getattr(res, "points", None) is None:
            continue
        annex_row = getattr(res, "annex_row_id", None) or (
            annex_row_for_indicator(getattr(res, "indicator_id", None)).row_id
            if annex_row_for_indicator(getattr(res, "indicator_id", None))
            else getattr(res, "indicator_id", "")
        )
        row_key = str(annex_row or "")
        group = (row_key, dedupe_key)
        pts = float(res.points)
        prev = best_by_output.get(group)
        if prev is None or pts > prev:
            best_by_output[group] = pts

    return cap_criterion_b_total(list(best_by_output.values()), settings)
