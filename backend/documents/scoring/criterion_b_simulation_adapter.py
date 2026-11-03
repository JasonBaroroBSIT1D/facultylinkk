"""
Criterion B rank simulation adapter (Phase 5A).

Pure functions that map evidence bundles → simulation points using published Admin
config. Wired via ``faculty.kra_document_aggregate`` when the feature flag below
is enabled (default off).
"""

from __future__ import annotations

import os
from typing import Any

from kra_configuration.criterion_b_aggregation import deduplication_key_for_bundle
from kra_configuration.criterion_b_annex import CRITERION_B_ID
from kra_configuration.criterion_b_scoring import (
    CriterionBScoreResult,
    aggregate_criterion_b_from_results,
    published_base_points_for_annex_row,
    published_criterion_b_max,
)
from documents.criterion_b_evidence.current_score import (
    current_score_eligible_for_kra_aggregation,
    resolve_criterion_b_current_score,
)
from documents.criterion_b_evidence.bundle import (
    bundle_from_document,
    is_supporting_evidence_document,
)
from documents.criterion_b_evidence.program_bundle import is_academic_program_bundle
from documents.criterion_b_evidence.program_validation import validate_academic_program_bundle
from documents.criterion_b_evidence.validation import validate_instructional_material_bundle

def _env_adapter_enabled() -> bool:
    """Staging/production toggle via env; unset → off (safe default)."""
    raw = (os.environ.get("CRITERION_B_SIMULATION_ADAPTER_ENABLED") or "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return False


# Phase 5B: default off; staging sets CRITERION_B_SIMULATION_ADAPTER_ENABLED=1 on the host only.
CRITERION_B_SIMULATION_ADAPTER_ENABLED: bool = _env_adapter_enabled()

SIMULATION_SCORING_NOTE = (
    "Estimated Criterion B points use reviewer-verified evidence bundles only — "
    "not official DBM–CHED certification."
)


def _validate_bundle(bundle: dict[str, Any] | None) -> dict[str, Any]:
    if is_academic_program_bundle(bundle):
        return validate_academic_program_bundle(bundle)
    return validate_instructional_material_bundle(bundle)


def score_primary_document_for_simulation(
    doc: Any,
    *,
    settings: dict[str, Any] | None = None,
) -> CriterionBScoreResult | None:
    """
    Score one primary Criterion B document for rank simulation.

    Returns ``None`` when the row is not a Criterion B primary claim.
    Never uses legacy ``estimated_points`` / ``verified_points`` on the document row.
    """
    criterion_id = (getattr(doc, "criterion_id", None) or "").strip()
    if criterion_id != CRITERION_B_ID:
        return None
    if is_supporting_evidence_document(doc):
        return None

    indicator_id = (getattr(doc, "indicator_id", None) or "").strip()
    bundle = bundle_from_document(doc)
    if not bundle:
        return CriterionBScoreResult(
            indicator_id=indicator_id,
            annex_row_id=None,
            base_points=None,
            contribution_percent=None,
            raw_points=None,
            points=None,
            eligible=False,
            reasons=("bundle_not_initialized",),
        )

    validation = _validate_bundle(bundle)
    current = resolve_criterion_b_current_score(
        doc,
        bundle,
        validation,
        settings=settings,
        ignore_document_row_points=True,
    )
    if not current_score_eligible_for_kra_aggregation(doc, validation, current):
        reasons: tuple[str, ...] = ("current_score_not_eligible",)
        if current.points is None:
            reasons = ("current_score_unavailable",)
        elif current.source == "automated_estimate":
            reasons = ("evidence_not_ready_for_scoring",)
        base = published_base_points_for_annex_row(indicator_id, settings)
        return CriterionBScoreResult(
            indicator_id=indicator_id,
            annex_row_id=None,
            base_points=base,
            contribution_percent=bundle.get("contributionPercent"),
            raw_points=None,
            points=None,
            eligible=False,
            reasons=reasons,
        )

    pts = round(float(current.points), 2)
    base = published_base_points_for_annex_row(indicator_id, settings)
    return CriterionBScoreResult(
        indicator_id=indicator_id,
        annex_row_id=None,
        base_points=base,
        contribution_percent=bundle.get("contributionPercent"),
        raw_points=pts,
        points=pts,
        eligible=True,
        reasons=(f"current_score_{current.source}",),
    )


def aggregate_criterion_b_simulation_from_documents(
    documents: list[Any],
    *,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Aggregate eligible Criterion B simulation points from in-memory or ORM documents.

    Uses per-output deduplication keys + criterion B ceiling (published max, default 30).
    """
    results: list[CriterionBScoreResult] = []
    dedupe_keys: list[str] = []
    claim_summaries: list[dict[str, Any]] = []
    primary_count = 0

    for doc in documents:
        if (getattr(doc, "criterion_id", None) or "").strip() != CRITERION_B_ID:
            continue
        if is_supporting_evidence_document(doc):
            continue
        primary_count += 1
        res = score_primary_document_for_simulation(doc, settings=settings)
        if res is None:
            continue
        bundle = bundle_from_document(doc)
        results.append(res)
        dedupe_keys.append(
            deduplication_key_for_bundle(
                bundle,
                document_public_id=getattr(doc, "public_id", None),
            )
        )
        validation = _validate_bundle(bundle)
        claim_summaries.append(
            {
                "documentId": getattr(doc, "public_id", None),
                "indicatorId": res.indicator_id,
                "deduplicationKey": dedupe_keys[-1],
                "readyForScoring": validation.get("readyForScoring") is True,
                "validationStatus": validation.get("validationStatus"),
                "points": res.points,
                "eligible": res.eligible,
                "reasons": list(res.reasons),
            }
        )

    capped, raw_sum = aggregate_criterion_b_from_results(
        results,
        settings,
        dedupe_keys=dedupe_keys if results else None,
    )
    max_pts = published_criterion_b_max(settings)
    any_eligible = any(r.eligible and r.points is not None for r in results)
    assessed = primary_count > 0 and (any_eligible or capped > 0)

    return {
        "criterionId": CRITERION_B_ID,
        "estimatedPoints": capped if any_eligible and capped >= 0 else None,
        "maxPoints": max_pts,
        "assessed": assessed,
        "documentCount": primary_count,
        "rawSumBeforeCap": raw_sum,
        "cappedTotal": capped,
        "claimResults": claim_summaries,
        "scoringSource": "criterion_b_evidence_bundle",
        "adapterEnabled": CRITERION_B_SIMULATION_ADAPTER_ENABLED,
        "scoringNote": SIMULATION_SCORING_NOTE,
    }
