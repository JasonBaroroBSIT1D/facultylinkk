"""Reviewer accomplishment assessment for KRA II."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from kra_configuration.kra2_annex import published_kra2_indicator_points
from kra_configuration.kra2_indicator_registry import allows_reviewer_partial_points, contribution_mode
from documents.kra2_evidence.bundle import REVIEW_APPROVED, REVIEW_PENDING, REVIEW_REJECTED

SCORING_METHOD_FIXED = "fixed"
SCORING_METHOD_CONTRIBUTION = "contribution_based"
SCORING_METHOD_VARIABLE = "variable"


def reviewer_scoring_method(indicator_id: str) -> str:
    """Official KRA II scoring UX method (no invented variable rules)."""
    mode = contribution_mode(indicator_id)
    if mode == "declared":
        return SCORING_METHOD_CONTRIBUTION
    if allows_reviewer_partial_points(indicator_id):
        return SCORING_METHOD_VARIABLE
    return SCORING_METHOD_FIXED


def reviewer_scoring_method_label(method: str) -> str:
    if method == SCORING_METHOD_CONTRIBUTION:
        return "Contribution-Based"
    if method == SCORING_METHOD_VARIABLE:
        return "Variable"
    return "Fixed"

MIN_REMARKS_LEN = 10
MIN_ADJUSTMENT_REASON_LEN = 10
HISTORY_LIMIT = 20


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def system_calculated_assessed_points(
    bundle: dict[str, Any],
    *,
    indicator_id: str,
    settings: dict[str, Any] | None = None,
) -> float:
    eligible = published_kra2_indicator_points(
        indicator_id,
        settings,
        allow_annex_fallback=settings is None,
    )
    if eligible is None:
        raise ValueError("indicator_points_unknown")
    return _default_assessed_points(bundle, base_points=float(eligible))


def allows_reviewer_point_adjustment(*, indicator_id: str) -> bool:
    """True when official rules permit reviewer-assessed points below system-calculated eligible."""
    return allows_reviewer_partial_points(indicator_id)


def _default_assessed_points(
    bundle: dict[str, Any],
    *,
    base_points: float,
) -> float:
    contribution = (bundle.get("contribution") or "").strip().lower()
    if contribution != "declared":
        return round(float(base_points), 2)
    raw_pct = bundle.get("declaredContributionPercent")
    try:
        pct = float(raw_pct)
    except (TypeError, ValueError):
        pct = 100.0
    pct = max(0.0, min(100.0, pct))
    return round(float(base_points) * (pct / 100.0), 2)


def apply_reviewer_accomplishment_decision(
    bundle: dict[str, Any],
    *,
    review_status: str,
    reviewer_user_id: int,
    reviewer_display_name: str,
    remarks: str = "",
    assessed_points: float | None = None,
    score_adjustment_reason: str = "",
    indicator_id: str,
    settings: dict[str, Any] | None = None,
) -> None:
    status = (review_status or "").strip().lower()
    if status not in (REVIEW_PENDING, REVIEW_APPROVED, REVIEW_REJECTED):
        raise ValueError("invalid_review_status")

    eligible = published_kra2_indicator_points(
        indicator_id,
        settings,
        allow_annex_fallback=settings is None,
    )
    if eligible is None:
        raise ValueError("indicator_points_unknown")

    remark_text = (remarks or "").strip()
    if status == REVIEW_REJECTED and len(remark_text) < MIN_REMARKS_LEN:
        raise ValueError("review_rejection_remarks_required")
    if status == REVIEW_APPROVED and len(remark_text) < MIN_REMARKS_LEN:
        raise ValueError("review_approval_remarks_required")

    points: float | None = None
    system_points: float | None = None
    adjustment_reason = (score_adjustment_reason or "").strip()
    if status == REVIEW_APPROVED:
        system_points = _default_assessed_points(bundle, base_points=float(eligible))
        system_points = round(float(system_points), 2)
        indicator_max = round(float(eligible), 2)
        partial_ok = allows_reviewer_point_adjustment(indicator_id=indicator_id)
        if assessed_points is not None:
            try:
                points = round(float(assessed_points), 2)
            except (TypeError, ValueError) as exc:
                raise ValueError("assessed_points_invalid") from exc
            if points < 0 or points > indicator_max:
                raise ValueError("assessed_points_exceeds_indicator_max")
            if points > system_points + 0.001:
                raise ValueError("assessed_points_exceeds_eligible")
            if not partial_ok and abs(points - system_points) > 0.001:
                raise ValueError("assessed_points_not_adjustable")
        else:
            points = system_points
        if abs(points - system_points) > 0.001:
            if not partial_ok:
                raise ValueError("assessed_points_not_adjustable")
            if len(adjustment_reason) < MIN_ADJUSTMENT_REASON_LEN:
                raise ValueError("score_adjustment_reason_required")
        elif adjustment_reason:
            adjustment_reason = ""

    prior = bundle.get("reviewerAssessment")
    history: list[dict[str, Any]] = []
    if isinstance(prior, dict) and isinstance(prior.get("history"), list):
        history = list(prior["history"])
    if isinstance(prior, dict) and prior.get("reviewStatus"):
        history.append(
            {
                "reviewStatus": prior.get("reviewStatus"),
                "assessedPoints": prior.get("assessedPoints"),
                "remarks": prior.get("remarks"),
                "assessedAt": prior.get("assessedAt"),
                "reviewerUserId": prior.get("reviewerUserId"),
            }
        )
    history = history[-HISTORY_LIMIT:]

    bundle["reviewStatus"] = status
    bundle["reviewerRemarks"] = remark_text
    bundle["reviewerAssessment"] = {
        "reviewStatus": status,
        "eligiblePoints": round(float(eligible), 2),
        "systemCalculatedPoints": round(float(system_points), 2) if status == REVIEW_APPROVED else None,
        "assessedPoints": points,
        "scoreAdjustmentReason": adjustment_reason or None,
        "remarks": remark_text,
        "reviewerUserId": int(reviewer_user_id),
        "reviewerDisplayName": (reviewer_display_name or "").strip() or None,
        "assessedAt": _utc_iso(),
        "history": history,
    }
