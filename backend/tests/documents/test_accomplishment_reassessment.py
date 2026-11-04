"""Authorized reassessment workflow for approved accomplishments."""

from __future__ import annotations

from documents.accomplishment_reassessment import (
    open_reassessment_session,
    process_reassessment_action,
    reassessment_capabilities_for_viewer,
)
from documents.kra3_evidence.reviewer_assessment import apply_reviewer_accomplishment_decision


def _settings():
    return {
        "criteria": {"kra3-b": {"maxPoints": 50}},
        "indicators": {"kra3-b-train-local": {"points": 0.5}},
    }


class _User:
    def __init__(self, *, role: str, uid: int = 1):
        self.role = role
        self.id = uid
        self.public_id = f"usr_{uid}"


class _Doc:
    faculty_profile_id = 1

    def __init__(self, reviewer_user_id: int = 1):
        self.faculty_profile = type("P", (), {"reviewer_user_id": reviewer_user_id})()


def test_assigned_reviewer_can_request_not_finalize_by_default(monkeypatch):
    import config

    monkeypatch.setattr(config.Config, "ACCOMPLISHMENT_REASSESSMENT_ALLOW_REVIEWER", False, raising=False)

    class Reviewer(_User):
        role = "reviewer"

    caps = reassessment_capabilities_for_viewer(Reviewer(role="reviewer", uid=1), _Doc(reviewer_user_id=1))
    assert caps["canRequestReassessment"] is True
    assert caps["canFinalizeReassessment"] is False
    assert caps["actionLabel"] == "Request Reassessment"


def test_open_and_finalize_reassessment_preserves_history(monkeypatch):
    import config

    monkeypatch.setattr(config.Config, "ACCOMPLISHMENT_REASSESSMENT_ALLOW_REVIEWER", True, raising=False)

    bundle = {
        "deliveryHours": 4.0,
        "reviewStatus": "approved",
        "submittedForReviewAt": "2026-01-01",
        "reviewerRemarks": "Approved training QA test run",
    }
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status="approved",
        reviewer_user_id=1,
        reviewer_display_name="Reviewer A",
        remarks="Approved training QA test run",
        indicator_id="kra3-b-train-local",
        settings=_settings(),
    )
    prior_pts = bundle["reviewerAssessment"]["assessedPoints"]
    process_reassessment_action(
        bundle,
        action="open",
        reopen_reason="Attendance records show only two eligible hours were verified.",
        actor_user_id=2,
        actor_display_name="Reviewer B",
        is_administrator=False,
        is_assigned_reviewer=True,
        indicator_id="kra3-b-train-local",
        settings=_settings(),
        kra="kra3",
    )
    assert bundle["reassessmentSession"]["active"] is True
    assert bundle["reviewerAssessment"]["assessedPoints"] == prior_pts
    process_reassessment_action(
        bundle,
        action="finalize",
        confirm=True,
        remarks="Corrected to two hours after attendance audit.",
        assessed_points=1.0,
        score_adjustment_reason="Only two delivery hours were documented in signed attendance.",
        actor_user_id=2,
        actor_display_name="Reviewer B",
        is_administrator=False,
        is_assigned_reviewer=True,
        indicator_id="kra3-b-train-local",
        settings=_settings(),
        kra="kra3",
    )
    assert bundle["reviewStatus"] == "approved"
    assert bundle["reviewerAssessment"]["assessedPoints"] == 1.0
    assert isinstance(bundle.get("reassessmentHistory"), list)
    assert len(bundle["reassessmentHistory"]) >= 1


def test_reviewer_finalize_blocked_without_admin(monkeypatch):
    import config
    import pytest

    monkeypatch.setattr(config.Config, "ACCOMPLISHMENT_REASSESSMENT_ALLOW_REVIEWER", False, raising=False)
    bundle = {
        "deliveryHours": 2.0,
        "reviewStatus": "approved",
        "reassessmentSession": {
            "active": True,
            "openReason": "Legacy flat score must be corrected for hourly training.",
            "priorApproval": {"approvedPoints": 2.0},
            "draftAssessedPoints": 4.0,
        },
        "reviewerAssessment": {"assessedPoints": 2.0, "reviewStatus": "approved"},
    }
    with pytest.raises(ValueError, match="reassessment_finalize_requires_administrator"):
        process_reassessment_action(
            bundle,
            action="finalize",
            confirm=True,
            remarks="Attempt finalize as reviewer only.",
            actor_user_id=2,
            actor_display_name="Reviewer",
            is_administrator=False,
            is_assigned_reviewer=True,
            indicator_id="kra3-b-train-local",
            settings=_settings(),
            kra="kra3",
        )


def test_open_reassessment_requires_reason():
    bundle = {"reviewStatus": "approved", "reviewerAssessment": {"assessedPoints": 2}}
    import pytest

    with pytest.raises(ValueError, match="reassessment_reason_required"):
        open_reassessment_session(
            bundle,
            reopen_reason="too short",
            actor_user_id=1,
            actor_display_name="Admin",
        )
