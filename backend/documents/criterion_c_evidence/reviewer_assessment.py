"""Reviewer accomplishment assessment for Criterion C."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from kra_configuration.criterion_c_annex import published_points_for_indicator
from documents.criterion_c_evidence.bundle import REVIEW_APPROVED, REVIEW_PENDING, REVIEW_REJECTED

MIN_REMARKS_LEN = 10
HISTORY_LIMIT = 20


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_reviewer_accomplishment_decision(
    bundle: dict[str, Any],
    *,
    review_status: str,
    reviewer_user_id: int,
    reviewer_display_name: str,
    remarks: str = "",
    assessed_points: float | None = None,
    indicator_id: str,
    settings: dict[str, Any] | None = None,
) -> None:
    status = (review_status or "").strip().lower()
    if status not in (REVIEW_PENDING, REVIEW_APPROVED, REVIEW_REJECTED):
        raise ValueError("invalid_review_status")

    allow_fb = settings is None
    eligible = published_points_for_indicator(
        indicator_id,
        settings,
        allow_annex_fallback=allow_fb,
    )
    if eligible is None:
        raise ValueError("indicator_points_unknown")

    remark_text = (remarks or "").strip()
    if status == REVIEW_REJECTED and len(remark_text) < MIN_REMARKS_LEN:
        raise ValueError("review_rejection_remarks_required")
    if status == REVIEW_APPROVED and len(remark_text) < MIN_REMARKS_LEN:
        raise ValueError("review_approval_remarks_required")

    points: float | None = None
    if status == REVIEW_APPROVED:
        if assessed_points is not None:
            try:
                points = round(float(assessed_points), 2)
            except (TypeError, ValueError) as exc:
                raise ValueError("assessed_points_invalid") from exc
            if points < 0 or points > float(eligible):
                raise ValueError("assessed_points_exceeds_annex_max")
        else:
            points = round(float(eligible), 2)

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
        "assessedPoints": points,
        "remarks": remark_text,
        "reviewerUserId": int(reviewer_user_id),
        "reviewerDisplayName": (reviewer_display_name or "").strip() or None,
        "assessedAt": _utc_iso(),
        "history": history,
    }
