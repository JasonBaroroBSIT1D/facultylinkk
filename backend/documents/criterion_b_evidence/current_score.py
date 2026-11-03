"""Canonical Criterion B current score (Estimated vs Reviewer Assessed) for API and KRA aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kra_configuration.criterion_b_scoring import (
    compute_criterion_b_indicator_automated_estimate,
    compute_criterion_b_indicator_points,
    published_base_points_for_annex_row,
)
from documents.criterion_b_evidence.reviewer_assessment import (
    assessment_from_bundle,
    allowed_assessment_max_points,
)
from documents.scoring.document_evidence_points import effective_document_points

from models import Document

_EXCLUDED_DOC_STATUSES = frozenset({"rejected", "needs_revision", "draft"})


@dataclass(frozen=True)
class CriterionBCurrentScore:
    points: float | None
    label: str
    source: str
    system_estimate_points: float | None
    allowed_reviewer_max_points: float | None


def _system_estimate_points(
    doc: Document,
    *,
    indicator_id: str,
    bundle: dict[str, Any],
    settings: dict[str, Any] | None,
    ignore_document_row_points: bool = False,
) -> float | None:
    if not ignore_document_row_points:
        if doc.estimated_points is not None and float(doc.estimated_points) > 0:
            return round(float(doc.estimated_points), 2)
        eff = effective_document_points(doc)
        if eff is not None:
            return eff
    contrib = bundle.get("contributionPercent")
    auto = compute_criterion_b_indicator_automated_estimate(
        indicator_id,
        contribution_percent=contrib,
        settings=settings,
    )
    if auto is not None:
        return auto
    return None


def _has_completed_reviewer_assessment(bundle: dict[str, Any]) -> tuple[float | None, bool]:
    proposed = assessment_from_bundle(bundle) or {}
    proposed_pts = proposed.get("points")
    proposed_just = (proposed.get("justification") or "").strip()
    if proposed_pts is None or not proposed_just:
        return None, False
    try:
        return round(float(proposed_pts), 2), True
    except (TypeError, ValueError):
        return None, False


def resolve_criterion_b_current_score(
    doc: Document,
    bundle: dict[str, Any] | None,
    validation: dict[str, Any] | None,
    *,
    settings: dict[str, Any] | None = None,
    ignore_document_row_points: bool = False,
) -> CriterionBCurrentScore:
    """
    One display/aggregation current score per primary Criterion B accomplishment.

    Reviewer Assessed replaces Estimated in the current score when a completed
    reviewer-proposed assessment exists (points + justification).
    """
    indicator_id = (doc.indicator_id or "").strip()
    bundle = bundle if isinstance(bundle, dict) else {}
    validation = validation if isinstance(validation, dict) else {}

    system_est = _system_estimate_points(
        doc,
        indicator_id=indicator_id,
        bundle=bundle,
        settings=settings,
        ignore_document_row_points=ignore_document_row_points,
    )
    max_assessment = allowed_assessment_max_points(indicator_id, bundle, settings=settings)

    assessment_pts, has_assessment = _has_completed_reviewer_assessment(bundle)
    if has_assessment and assessment_pts is not None:
        return CriterionBCurrentScore(
            points=assessment_pts,
            label="Reviewer Assessed",
            source="reviewer_assessment",
            system_estimate_points=system_est,
            allowed_reviewer_max_points=max_assessment,
        )

    return CriterionBCurrentScore(
        points=system_est,
        label="Estimated",
        source="automated_estimate",
        system_estimate_points=system_est,
        allowed_reviewer_max_points=max_assessment,
    )


def current_score_eligible_for_kra_aggregation(
    doc: Document,
    validation: dict[str, Any] | None,
    current: CriterionBCurrentScore,
) -> bool:
    """Whether this accomplishment's current score may count toward KRA / simulation totals."""
    if doc.deleted_at is not None:
        return False
    if (doc.status or "").strip() in _EXCLUDED_DOC_STATUSES:
        return False
    if current.points is None:
        return False
    if current.source == "reviewer_assessment":
        return True
    return validation.get("readyForScoring") is True


def guideline_verified_points_if_ready(
    indicator_id: str,
    bundle: dict[str, Any],
    validation: dict[str, Any] | None,
    *,
    settings: dict[str, Any] | None = None,
) -> float | None:
    """Rule-based points when evidence is reviewer-verified (audit; not the current score after assessment)."""
    validation = validation if isinstance(validation, dict) else {}
    ready = validation.get("readyForScoring") is True
    contrib = bundle.get("contributionPercent")
    guideline_result = compute_criterion_b_indicator_points(
        indicator_id,
        contribution_percent=contrib,
        evidence_verified=ready,
        settings=settings,
    )
    return guideline_result.points if guideline_result.eligible else None


def published_base_for_display(indicator_id: str, settings: dict[str, Any] | None = None) -> float | None:
    return published_base_points_for_annex_row(indicator_id, settings)
