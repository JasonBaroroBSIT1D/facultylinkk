"""Reviewer accomplishment assessment for KRA IV."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from kra_configuration.kra4_annex import published_kra4_indicator_points
from kra_configuration.kra4_indicator_registry import (
    allows_reviewer_partial_points,
    contribution_mode,
    official_indicator_max_points,
    reviewer_adjustment_governing_rule,
)
from documents.kra4_evidence.bundle import REVIEW_APPROVED, REVIEW_PENDING, REVIEW_REJECTED

SCORING_METHOD_FIXED = "fixed"
SCORING_METHOD_CONTRIBUTION = "contribution_based"
SCORING_METHOD_VARIABLE = "variable"


def reviewer_scoring_method(indicator_id: str) -> str:
    """Official KRA IV scoring UX method (no invented variable rules)."""
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
    from documents.kra4_evidence.scoring import estimated_points_for_bundle

    est = estimated_points_for_bundle(
        bundle,
        indicator_id=indicator_id,
        settings=settings,
        applicable_config_present=settings is not None and bool(settings.get("criteria")),
    )
    if est is None:
        raise ValueError("indicator_points_unknown")
    return round(float(est), 2)


def allows_reviewer_point_adjustment(*, indicator_id: str) -> bool:
    """True when official rules permit reviewer-assessed points below system-calculated eligible."""
    return allows_reviewer_partial_points(indicator_id)


def reviewer_scoring_controls(indicator_id: str, *, settings: dict[str, Any] | None = None) -> dict[str, Any]:
    """Reviewer-facing scoring control metadata (Admin rules unchanged)."""
    method = reviewer_scoring_method(indicator_id)
    partial = allows_reviewer_point_adjustment(indicator_id=indicator_id)
    official_max = official_indicator_max_points(indicator_id, settings)
    return {
        "scoringMethod": method,
        "scoringMethodLabel": reviewer_scoring_method_label(method),
        "allowsPointAdjustment": partial,
        "allowsContributionEdit": method == SCORING_METHOD_CONTRIBUTION,
        "officialIndicatorMaxPoints": official_max,
        "adjustmentGoverningRule": reviewer_adjustment_governing_rule(indicator_id),
    }


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


def _system_and_cap_for_bundle(
    bundle: dict[str, Any],
    *,
    indicator_id: str,
    settings: dict[str, Any] | None,
) -> tuple[float, float]:
    applicable = settings is not None and bool((settings or {}).get("criteria"))
    eligible = published_kra4_indicator_points(
        indicator_id,
        settings,
        allow_annex_fallback=not applicable,
    )
    system_calc: float | None = None
    try:
        system_calc = system_calculated_assessed_points(
            bundle,
            indicator_id=indicator_id,
            settings=settings,
        )
    except ValueError:
        system_calc = None
    if eligible is None:
        eligible = system_calc
    if eligible is None:
        raise ValueError("indicator_points_unknown")
    official_max = official_indicator_max_points(indicator_id, settings)
    indicator_cap = round(float(official_max if official_max is not None else eligible), 2)
    if system_calc is not None:
        system_points = round(float(system_calc), 2)
    else:
        system_points = round(float(_default_assessed_points(bundle, base_points=float(eligible))), 2)
    return system_points, indicator_cap


def propose_assessed_points(
    bundle: dict[str, Any],
    *,
    assessed_points: float | int | str | None = None,
    score_adjustment_reason: str = "",
    default_points: float | None = None,
    fallback_assessed_from: dict[str, Any] | None = None,
    indicator_id: str,
    settings: dict[str, Any] | None = None,
) -> tuple[float, str]:
    system_points, indicator_cap = _system_and_cap_for_bundle(
        bundle, indicator_id=indicator_id, settings=settings
    )
    eligible_for_review = round(min(float(system_points), float(indicator_cap)), 2)
    partial_ok = allows_reviewer_point_adjustment(indicator_id=indicator_id)
    prior_ra = fallback_assessed_from if isinstance(fallback_assessed_from, dict) else {}
    if not prior_ra:
        ra = bundle.get("reviewerAssessment")
        prior_ra = ra if isinstance(ra, dict) else {}

    if assessed_points is not None:
        try:
            points = round(float(assessed_points), 2)
        except (TypeError, ValueError) as exc:
            raise ValueError("assessed_points_invalid") from exc
    elif default_points is not None:
        points = round(float(default_points), 2)
    elif prior_ra.get("assessedPoints") is not None:
        points = round(float(prior_ra["assessedPoints"]), 2)
    else:
        points = eligible_for_review

    if points < 0 or points > indicator_cap:
        raise ValueError("assessed_points_exceeds_indicator_max")
    if points > system_points + 0.001:
        raise ValueError("assessed_points_exceeds_eligible")
    if not partial_ok and abs(points - eligible_for_review) > 0.001:
        raise ValueError("assessed_points_not_adjustable")

    adjustment_reason = (score_adjustment_reason or "").strip()
    if not adjustment_reason:
        adjustment_reason = (prior_ra.get("scoreAdjustmentReason") or "").strip()
    if abs(points - eligible_for_review) > 0.001:
        if not partial_ok:
            raise ValueError("assessed_points_not_adjustable")
        if len(adjustment_reason) < MIN_ADJUSTMENT_REASON_LEN:
            raise ValueError("score_adjustment_reason_required")
    elif adjustment_reason:
        adjustment_reason = ""
    return points, adjustment_reason


def _append_assessment_revision_history(
    prior_ra: dict[str, Any],
    *,
    draft_assessed_points: float,
    draft_remarks: str,
    draft_adjustment_reason: str,
    reviewer_user_id: int,
    reviewer_display_name: str,
) -> list[dict[str, Any]]:
    history = list(prior_ra.get("history") or []) if isinstance(prior_ra.get("history"), list) else []
    history.append(
        {
            "kind": "saved_assessment_revision",
            "draftAssessedPoints": draft_assessed_points,
            "draftRemarks": draft_remarks or None,
            "draftScoreAdjustmentReason": draft_adjustment_reason or None,
            "savedAt": _utc_iso(),
            "reviewerUserId": int(reviewer_user_id),
            "reviewerDisplayName": (reviewer_display_name or "").strip() or None,
        }
    )
    return history[-HISTORY_LIMIT:]


def _save_post_finalization_assessment_revision(
    bundle: dict[str, Any],
    *,
    reviewer_user_id: int,
    reviewer_display_name: str,
    remarks: str = "",
    assessed_points: float | int | str | None = None,
    score_adjustment_reason: str = "",
    indicator_id: str,
    settings: dict[str, Any] | None = None,
) -> None:
    """Save reviewer draft points/feedback without changing finalized reviewStatus or approvedPoints."""
    prior_ra = bundle.get("reviewerAssessment")
    prior_ra = dict(prior_ra) if isinstance(prior_ra, dict) else {}

    points, adjustment_reason = propose_assessed_points(
        bundle,
        assessed_points=assessed_points,
        score_adjustment_reason=score_adjustment_reason,
        fallback_assessed_from={
            **prior_ra,
            "assessedPoints": prior_ra.get("draftAssessedPoints")
            if prior_ra.get("draftAssessedPoints") is not None
            else prior_ra.get("approvedPoints")
            if prior_ra.get("approvedPoints") is not None
            else prior_ra.get("assessedPoints"),
            "scoreAdjustmentReason": prior_ra.get("draftScoreAdjustmentReason")
            or prior_ra.get("scoreAdjustmentReason"),
        },
        indicator_id=indicator_id,
        settings=settings,
    )

    remark_text = (remarks or "").strip()
    if not remark_text:
        remark_text = (prior_ra.get("draftRemarks") or prior_ra.get("remarks") or "").strip()

    prior_ra["draftAssessedPoints"] = points
    prior_ra["draftRemarks"] = remark_text or None
    prior_ra["draftScoreAdjustmentReason"] = adjustment_reason or None
    prior_ra["draftSavedAt"] = _utc_iso()
    prior_ra["draftReviewerUserId"] = int(reviewer_user_id)
    prior_ra["draftReviewerDisplayName"] = (reviewer_display_name or "").strip() or None
    prior_ra["history"] = _append_assessment_revision_history(
        prior_ra,
        draft_assessed_points=points,
        draft_remarks=remark_text,
        draft_adjustment_reason=adjustment_reason,
        reviewer_user_id=reviewer_user_id,
        reviewer_display_name=reviewer_display_name,
    )
    bundle["reviewerAssessment"] = prior_ra
    if remark_text:
        bundle["reviewerRemarks"] = remark_text


def save_reviewer_assessment_draft(
    bundle: dict[str, Any],
    *,
    reviewer_user_id: int,
    reviewer_display_name: str,
    remarks: str = "",
    assessed_points: float | int | str | None = None,
    score_adjustment_reason: str = "",
    indicator_id: str,
    settings: dict[str, Any] | None = None,
) -> None:
    """Persist reviewer points and feedback without finalizing reviewStatus."""
    prior_status = (bundle.get("reviewStatus") or "").strip().lower()
    if prior_status in (REVIEW_APPROVED, REVIEW_REJECTED):
        _save_post_finalization_assessment_revision(
            bundle,
            reviewer_user_id=reviewer_user_id,
            reviewer_display_name=reviewer_display_name,
            remarks=remarks,
            assessed_points=assessed_points,
            score_adjustment_reason=score_adjustment_reason,
            indicator_id=indicator_id,
            settings=settings,
        )
        return

    system_points, indicator_cap = _system_and_cap_for_bundle(
        bundle, indicator_id=indicator_id, settings=settings
    )
    applicable = settings is not None and bool((settings or {}).get("criteria"))
    eligible = published_kra4_indicator_points(
        indicator_id,
        settings,
        allow_annex_fallback=not applicable,
    )
    if eligible is None:
        eligible = system_points
    prior_ra = bundle.get("reviewerAssessment")
    prior_ra = prior_ra if isinstance(prior_ra, dict) else {}

    points, adjustment_reason = propose_assessed_points(
        bundle,
        assessed_points=assessed_points,
        score_adjustment_reason=score_adjustment_reason,
        indicator_id=indicator_id,
        settings=settings,
    )

    remark_text = (remarks or "").strip()
    if not remark_text:
        remark_text = (prior_ra.get("remarks") or bundle.get("reviewerRemarks") or "").strip()

    history = list(prior_ra["history"]) if isinstance(prior_ra.get("history"), list) else []

    bundle["reviewStatus"] = prior_status if prior_status == REVIEW_REJECTED else REVIEW_PENDING
    if remark_text:
        bundle["reviewerRemarks"] = remark_text
    bundle["reviewerAssessment"] = {
        "reviewStatus": REVIEW_PENDING,
        "eligiblePoints": round(float(eligible), 2),
        "officialIndicatorMaxPoints": indicator_cap,
        "systemCalculatedPoints": system_points,
        "assessedPoints": points,
        "approvedPoints": None,
        "scoreAdjustmentReason": adjustment_reason or None,
        "remarks": remark_text or None,
        "reviewerUserId": int(reviewer_user_id),
        "reviewerDisplayName": (reviewer_display_name or "").strip() or None,
        "draftSavedAt": _utc_iso(),
        "history": history,
    }


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

    applicable = settings is not None and bool((settings or {}).get("criteria"))
    eligible = published_kra4_indicator_points(
        indicator_id,
        settings,
        allow_annex_fallback=not applicable,
    )
    system_calc: float | None = None
    try:
        system_calc = system_calculated_assessed_points(
            bundle,
            indicator_id=indicator_id,
            settings=settings,
        )
    except ValueError:
        system_calc = None
    if eligible is None:
        eligible = system_calc
    if eligible is None:
        raise ValueError("indicator_points_unknown")
    official_max = official_indicator_max_points(indicator_id, settings)
    indicator_cap = round(float(official_max if official_max is not None else eligible), 2)

    remark_text = (remarks or "").strip()
    if status == REVIEW_REJECTED and len(remark_text) < MIN_REMARKS_LEN:
        raise ValueError("review_rejection_remarks_required")
    if status == REVIEW_APPROVED and len(remark_text) < MIN_REMARKS_LEN:
        raise ValueError("review_approval_remarks_required")

    points: float | None = None
    system_points: float | None = None
    adjustment_reason = (score_adjustment_reason or "").strip()
    if status == REVIEW_APPROVED:
        if system_calc is not None:
            system_points = round(float(system_calc), 2)
        else:
            system_points = _default_assessed_points(bundle, base_points=float(eligible))
            system_points = round(float(system_points), 2)
        partial_ok = allows_reviewer_point_adjustment(indicator_id=indicator_id)
        if assessed_points is not None:
            try:
                points = round(float(assessed_points), 2)
            except (TypeError, ValueError) as exc:
                raise ValueError("assessed_points_invalid") from exc
            if points < 0 or points > indicator_cap:
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
        "officialIndicatorMaxPoints": indicator_cap if status == REVIEW_APPROVED else None,
        "systemCalculatedPoints": round(float(system_points), 2) if status == REVIEW_APPROVED else None,
        "assessedPoints": points,
        "approvedPoints": points if status == REVIEW_APPROVED else None,
        "scoreAdjustmentReason": adjustment_reason or None,
        "remarks": remark_text,
        "reviewerUserId": int(reviewer_user_id),
        "reviewerDisplayName": (reviewer_display_name or "").strip() or None,
        "assessedAt": _utc_iso(),
        "history": history,
    }
