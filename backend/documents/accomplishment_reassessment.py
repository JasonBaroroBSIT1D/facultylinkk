"""Authorized reassessment of previously approved KRA II/III accomplishments."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from auth.permissions import ROLE_ADMINISTRATOR
from config import Config

REASSESSMENT_SESSION_KEY = "reassessmentSession"
REASSESSMENT_HISTORY_KEY = "reassessmentHistory"

MIN_REOPEN_REASON_LEN = 20
MIN_FINAL_REMARKS_LEN = 10


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def reassessment_server_flags() -> dict[str, Any]:
    """Non-user-specific server toggles (finalize delegation only)."""
    allow_reviewer_finalize = bool(
        getattr(Config, "ACCOMPLISHMENT_REASSESSMENT_ALLOW_REVIEWER", False)
    )
    return {"allowReviewerFinalize": allow_reviewer_finalize}


def reassessment_capabilities_for_viewer(viewer_user, doc) -> dict[str, Any]:
    """Per-viewer reassessment permissions (assigned reviewer or administrator)."""
    from documents.service import reviewer_can_access

    if viewer_user is None:
        return {
            "canRequestReassessment": False,
            "canFinalizeReassessment": False,
            "actionLabel": "",
            "requiresAdministratorToFinalize": False,
        }
    is_admin = getattr(viewer_user, "role", "") == ROLE_ADMINISTRATOR
    is_assigned = bool(reviewer_can_access(viewer_user, doc))
    allow_reviewer_finalize = bool(
        getattr(Config, "ACCOMPLISHMENT_REASSESSMENT_ALLOW_REVIEWER", False)
    )
    can_request = is_assigned or is_admin
    can_finalize = is_admin or (allow_reviewer_finalize and is_assigned)
    action_label = ""
    if can_request:
        action_label = "Reassess Score" if can_finalize else "Request Reassessment"
    return {
        "canRequestReassessment": can_request,
        "canFinalizeReassessment": can_finalize,
        "actionLabel": action_label,
        "requiresAdministratorToFinalize": bool(can_request and not can_finalize),
    }


def _assert_can_request_reassessment(*, is_administrator: bool, is_assigned_reviewer: bool) -> None:
    if not (is_assigned_reviewer or is_administrator):
        raise ValueError("reassessment_not_authorized")


def _assert_can_finalize_reassessment(*, is_administrator: bool, is_assigned_reviewer: bool) -> None:
    if is_administrator:
        return
    if getattr(Config, "ACCOMPLISHMENT_REASSESSMENT_ALLOW_REVIEWER", False) and is_assigned_reviewer:
        return
    raise ValueError("reassessment_finalize_requires_administrator")


def _active_session(bundle: dict[str, Any]) -> dict[str, Any]:
    raw = bundle.get(REASSESSMENT_SESSION_KEY)
    if not isinstance(raw, dict) or not raw.get("active"):
        raise ValueError("reassessment_not_active")
    return raw


def _prior_approval_snapshot(bundle: dict[str, Any]) -> dict[str, Any]:
    ra = bundle.get("reviewerAssessment") if isinstance(bundle.get("reviewerAssessment"), dict) else {}
    return {
        "reviewStatus": "approved",
        "approvedPoints": ra.get("approvedPoints") if ra.get("approvedPoints") is not None else ra.get("assessedPoints"),
        "assessedPoints": ra.get("assessedPoints"),
        "remarks": ra.get("remarks") or bundle.get("reviewerRemarks"),
        "scoreAdjustmentReason": ra.get("scoreAdjustmentReason"),
        "assessedAt": ra.get("assessedAt"),
        "reviewerUserId": ra.get("reviewerUserId"),
        "reviewerDisplayName": ra.get("reviewerDisplayName"),
        "systemCalculatedPoints": ra.get("systemCalculatedPoints"),
        "scoringConfigurationVersion": ra.get("scoringConfigurationVersion"),
        "eligiblePoints": ra.get("eligiblePoints"),
    }


def open_reassessment_session(
    bundle: dict[str, Any],
    *,
    reopen_reason: str,
    actor_user_id: int,
    actor_display_name: str,
) -> None:
    status = (bundle.get("reviewStatus") or "").strip().lower()
    if status != "approved":
        raise ValueError("reassessment_requires_approved")
    reason = (reopen_reason or "").strip()
    if len(reason) < MIN_REOPEN_REASON_LEN:
        raise ValueError("reassessment_reason_required")
    existing = bundle.get(REASSESSMENT_SESSION_KEY)
    if isinstance(existing, dict) and existing.get("active"):
        raise ValueError("reassessment_already_open")

    prior = _prior_approval_snapshot(bundle)
    bundle[REASSESSMENT_SESSION_KEY] = {
        "active": True,
        "openReason": reason,
        "openedAt": _utc_iso(),
        "openedByUserId": int(actor_user_id),
        "openedByDisplayName": (actor_display_name or "").strip() or None,
        "priorApproval": prior,
        "draftAssessedPoints": prior.get("approvedPoints"),
        "draftRemarks": prior.get("remarks"),
        "draftScoreAdjustmentReason": prior.get("scoreAdjustmentReason"),
    }


def save_reassessment_draft(
    bundle: dict[str, Any],
    *,
    assessed_points: float | int | str | None = None,
    remarks: str = "",
    score_adjustment_reason: str = "",
    validate_points_fn,
) -> None:
    session = _active_session(bundle)
    points, adjustment_reason = validate_points_fn(
        bundle,
        assessed_points=assessed_points,
        score_adjustment_reason=score_adjustment_reason,
        default_points=session.get("draftAssessedPoints"),
    )
    remark_text = (remarks or "").strip()
    if not remark_text:
        remark_text = (session.get("draftRemarks") or "").strip()
    session["draftAssessedPoints"] = points
    session["draftRemarks"] = remark_text or None
    session["draftScoreAdjustmentReason"] = adjustment_reason or None
    session["draftSavedAt"] = _utc_iso()
    bundle[REASSESSMENT_SESSION_KEY] = session


def cancel_reassessment_session(bundle: dict[str, Any]) -> None:
    session = bundle.get(REASSESSMENT_SESSION_KEY)
    if not isinstance(session, dict) or not session.get("active"):
        raise ValueError("reassessment_not_active")
    session["active"] = False
    session["cancelledAt"] = _utc_iso()
    bundle[REASSESSMENT_SESSION_KEY] = session


def finalize_reassessment(
    bundle: dict[str, Any],
    *,
    confirm: bool,
    actor_user_id: int,
    actor_display_name: str,
    remarks: str = "",
    assessed_points: float | int | str | None = None,
    score_adjustment_reason: str = "",
    validate_points_fn,
    indicator_id: str,
    settings: dict[str, Any] | None,
    apply_approved_fn,
) -> None:
    if not confirm:
        raise ValueError("reassessment_confirmation_required")
    session = _active_session(bundle)
    prior = dict(session.get("priorApproval") or _prior_approval_snapshot(bundle))

    points, adjustment_reason = validate_points_fn(
        bundle,
        assessed_points=assessed_points if assessed_points is not None else session.get("draftAssessedPoints"),
        score_adjustment_reason=score_adjustment_reason or (session.get("draftScoreAdjustmentReason") or ""),
        default_points=prior.get("approvedPoints"),
    )
    remark_text = (remarks or session.get("draftRemarks") or "").strip()
    if len(remark_text) < MIN_FINAL_REMARKS_LEN:
        raise ValueError("review_approval_remarks_required")

    apply_approved_fn(
        bundle,
        review_status="approved",
        reviewer_user_id=int(actor_user_id),
        reviewer_display_name=actor_display_name,
        remarks=remark_text,
        assessed_points=points,
        score_adjustment_reason=adjustment_reason,
        indicator_id=indicator_id,
        settings=settings,
    )

    ra = bundle.get("reviewerAssessment") if isinstance(bundle.get("reviewerAssessment"), dict) else {}
    closed = {
        "active": False,
        "finalizedAt": _utc_iso(),
        "finalizedByUserId": int(actor_user_id),
        "finalizedByDisplayName": (actor_display_name or "").strip() or None,
        "openReason": session.get("openReason"),
        "openedAt": session.get("openedAt"),
        "openedByUserId": session.get("openedByUserId"),
        "openedByDisplayName": session.get("openedByDisplayName"),
        "priorApproval": prior,
        "originalApprovedPoints": prior.get("approvedPoints"),
        "originalReviewerUserId": prior.get("reviewerUserId"),
        "originalReviewerDisplayName": prior.get("reviewerDisplayName"),
        "originalApprovedAt": prior.get("assessedAt"),
        "originalScoringConfigurationVersion": prior.get("scoringConfigurationVersion"),
        "correctedAssessedPoints": points,
        "correctedRemarks": remark_text,
        "correctedScoreAdjustmentReason": adjustment_reason or None,
        "correctedScoringConfigurationVersion": ra.get("scoringConfigurationVersion"),
        "correctedReviewerUserId": ra.get("reviewerUserId"),
        "correctedReviewerDisplayName": ra.get("reviewerDisplayName"),
        "correctedApprovedAt": ra.get("assessedAt"),
    }
    bundle[REASSESSMENT_SESSION_KEY] = closed
    hist = bundle.get(REASSESSMENT_HISTORY_KEY)
    if not isinstance(hist, list):
        hist = []
    hist.append(closed)
    bundle[REASSESSMENT_HISTORY_KEY] = hist[-20:]


def process_reassessment_action(
    bundle: dict[str, Any],
    *,
    action: str,
    reopen_reason: str = "",
    confirm: bool = False,
    remarks: str = "",
    assessed_points: float | int | str | None = None,
    score_adjustment_reason: str = "",
    actor_user_id: int,
    actor_display_name: str,
    is_administrator: bool,
    is_assigned_reviewer: bool,
    indicator_id: str,
    settings: dict[str, Any] | None,
    kra: str,
) -> None:
    act = (action or "").strip().lower()
    if act == "finalize":
        _assert_can_finalize_reassessment(
            is_administrator=is_administrator, is_assigned_reviewer=is_assigned_reviewer
        )
    else:
        _assert_can_request_reassessment(
            is_administrator=is_administrator, is_assigned_reviewer=is_assigned_reviewer
        )

    if act == "open":
        open_reassessment_session(
            bundle,
            reopen_reason=reopen_reason,
            actor_user_id=actor_user_id,
            actor_display_name=actor_display_name,
        )
        return

    if kra == "kra3":
        from documents.kra3_evidence.reviewer_assessment import (
            apply_reviewer_accomplishment_decision,
            propose_assessed_points,
        )
    else:
        from documents.kra2_evidence.reviewer_assessment import (
            apply_reviewer_accomplishment_decision,
            propose_assessed_points,
        )

    def _validate(
        bundle: dict[str, Any],
        *,
        assessed_points: float | int | str | None = None,
        score_adjustment_reason: str = "",
        default_points: float | None = None,
    ) -> tuple[float, str]:
        session = bundle.get(REASSESSMENT_SESSION_KEY)
        fallback = session if isinstance(session, dict) else {}
        return propose_assessed_points(
            bundle,
            assessed_points=assessed_points,
            score_adjustment_reason=score_adjustment_reason,
            default_points=default_points,
            fallback_assessed_from=fallback,
            indicator_id=indicator_id,
            settings=settings,
        )

    if act == "save_draft":
        save_reassessment_draft(
            bundle,
            assessed_points=assessed_points,
            remarks=remarks,
            score_adjustment_reason=score_adjustment_reason,
            validate_points_fn=_validate,
        )
        return
    if act == "cancel":
        cancel_reassessment_session(bundle)
        return
    if act == "finalize":
        finalize_reassessment(
            bundle,
            confirm=confirm,
            actor_user_id=actor_user_id,
            actor_display_name=actor_display_name,
            remarks=remarks,
            assessed_points=assessed_points,
            score_adjustment_reason=score_adjustment_reason,
            validate_points_fn=_validate,
            indicator_id=indicator_id,
            settings=settings,
            apply_approved_fn=apply_reviewer_accomplishment_decision,
        )
        return
    raise ValueError("invalid_reassessment_action")
