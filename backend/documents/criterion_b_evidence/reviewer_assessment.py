"""Reviewer-proposed assessment scores (separate from official verified points)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from kra_configuration.criterion_b_annex import indicator_requires_contribution_percent
from kra_configuration.criterion_b_scoring import (
    published_base_points_for_annex_row,
    validate_contribution_percent,
)

BUNDLE_KEY = "reviewerProposedAssessment"
HISTORY_LIMIT = 20
MIN_JUSTIFICATION_LEN = 10


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def assessment_from_bundle(bundle: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(bundle, dict):
        return None
    raw = bundle.get(BUNDLE_KEY)
    return raw if isinstance(raw, dict) else None


def allowed_assessment_max_points(
    indicator_id: str,
    bundle: dict[str, Any] | None,
    *,
    settings: dict[str, Any] | None = None,
) -> float | None:
    base = published_base_points_for_annex_row(indicator_id, settings)
    if base is None:
        return None
    if indicator_requires_contribution_percent(indicator_id):
        pct, _err = validate_contribution_percent(
            (bundle or {}).get("contributionPercent"),
        )
        if pct is None:
            return round(base, 2)
        return round(base * (pct / 100.0), 2)
    return round(base, 2)


def apply_reviewer_proposed_assessment(
    bundle: dict[str, Any],
    *,
    points: float | int | str,
    justification: str,
    reviewer_user_id: int,
    reviewer_display_name: str,
    indicator_id: str,
) -> dict[str, Any]:
    text = (justification or "").strip()
    if len(text) < MIN_JUSTIFICATION_LEN:
        raise ValueError("reviewer_assessment_justification_required")

    try:
        score = round(float(points), 2)
    except (TypeError, ValueError) as error:
        raise ValueError("reviewer_assessment_points_invalid") from error
    if score < 0:
        raise ValueError("reviewer_assessment_points_invalid")

    from documents.criterion_b_evidence.contribution_confirmation import (
        assert_can_save_reviewer_assessment,
    )

    assert_can_save_reviewer_assessment(
        bundle,
        indicator_id=indicator_id,
        points=score,
        justification=text,
    )

    max_allowed = allowed_assessment_max_points(indicator_id, bundle)
    if max_allowed is not None and score > max_allowed + 1e-6:
        raise ValueError("reviewer_assessment_points_exceeds_published_max")

    existing = assessment_from_bundle(bundle) or {}
    history = existing.get("history")
    if not isinstance(history, list):
        history = []
    if existing.get("points") is not None or existing.get("justification"):
        history.append(
            {
                "points": existing.get("points"),
                "justification": existing.get("justification"),
                "updatedAt": existing.get("updatedAt"),
                "reviewerUserId": existing.get("reviewerUserId"),
                "reviewerDisplayName": existing.get("reviewerDisplayName"),
            }
        )
    history = history[-HISTORY_LIMIT:]

    record = {
        "points": score,
        "justification": text,
        "updatedAt": _utc_iso(),
        "reviewerUserId": reviewer_user_id,
        "reviewerDisplayName": (reviewer_display_name or "").strip() or None,
        "history": history,
    }
    bundle[BUNDLE_KEY] = record
    return record
