"""KRA III scoring — CSR formula, hourly train, caps, aggregation."""

from __future__ import annotations

from documents.kra3_evidence.reviewer_assessment import (
    apply_reviewer_accomplishment_decision,
    save_reviewer_assessment_draft,
)
from documents.kra3_evidence.scoring import aggregate_kra3_kra_from_documents, estimated_points_for_bundle


def _settings():
    return {
        "criteria": {
            "kra3-a": {"maxPoints": 30},
            "kra3-b": {"maxPoints": 50},
            "kra3-c": {"maxPoints": 20},
            "kra3-d": {"maxPoints": 20, "bonus": True},
        },
        "indicators": {
            "kra3-c-satisfaction": {"points": 20},
            "kra3-b-train-local": {"points": 0.5},
            "kra3-a-linkage": {"points": 5},
        },
    }


def test_csr_formula_estimated_points():
    bundle = {"csrOverallRating": 85.0}
    pts = estimated_points_for_bundle(
        bundle,
        indicator_id="kra3-c-satisfaction",
        settings=_settings(),
        applicable_config_present=True,
    )
    assert pts == 17.0


def test_reviewer_approval_csr_uses_formula_not_fixed_base():
    bundle = {"csrOverallRating": 85.0}
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status="approved",
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="Approved CSR QA test run",
        indicator_id="kra3-c-satisfaction",
        settings=_settings(),
    )
    assert bundle["reviewerAssessment"]["assessedPoints"] == 17.0


def test_reviewer_approval_train_uses_hourly_system_points():
    bundle = {"deliveryHours": 4.0}
    apply_reviewer_accomplishment_decision(
        bundle,
        review_status="approved",
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="Approved training QA test run",
        indicator_id="kra3-b-train-local",
        settings=_settings(),
    )
    assert bundle["reviewerAssessment"]["assessedPoints"] == 2.0


def test_train_hourly_multiplier():
    bundle = {"deliveryHours": 4.0}
    pts = estimated_points_for_bundle(
        bundle,
        indicator_id="kra3-b-train-local",
        settings=_settings(),
        applicable_config_present=True,
    )
    assert pts == 2.0


def test_reviewer_assessment_draft_does_not_finalize():
    bundle = {"deliveryHours": 4.0, "reviewStatus": "pending", "submittedForReviewAt": "2026-01-01"}
    save_reviewer_assessment_draft(
        bundle,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="Draft feedback for faculty",
        assessed_points=1.0,
        score_adjustment_reason="Only one hour was verified in attendance records.",
        indicator_id="kra3-b-train-local",
        settings=_settings(),
    )
    assert bundle["reviewStatus"] == "pending"
    assert bundle["reviewerAssessment"]["approvedPoints"] is None
    assert bundle["reviewerAssessment"]["assessedPoints"] == 1.0
    assert bundle["reviewerAssessment"]["systemCalculatedPoints"] == 2.0


def test_reviewer_assessment_revision_on_approved_preserves_approved_points():
    bundle = {
        "deliveryHours": 4.0,
        "reviewStatus": "approved",
        "submittedForReviewAt": "2026-01-01",
        "reviewerAssessment": {
            "reviewStatus": "approved",
            "approvedPoints": 2.0,
            "assessedPoints": 2.0,
            "remarks": "Original approval remarks here",
            "assessedAt": "2026-01-02T00:00:00+00:00",
            "reviewerUserId": 9,
        },
    }
    save_reviewer_assessment_draft(
        bundle,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="Updated assessment notes for audit only",
        assessed_points=1.5,
        score_adjustment_reason="Attendance records support a lower verified hour count.",
        indicator_id="kra3-b-train-local",
        settings=_settings(),
    )
    ra = bundle["reviewerAssessment"]
    assert bundle["reviewStatus"] == "approved"
    assert ra["approvedPoints"] == 2.0
    assert ra["assessedPoints"] == 2.0
    assert ra["draftAssessedPoints"] == 1.5
    assert any(h.get("kind") == "saved_assessment_revision" for h in ra.get("history") or [])


def test_reviewer_assessment_draft_requires_adjustment_reason():
    bundle = {"deliveryHours": 4.0, "reviewStatus": "pending"}
    import pytest

    with pytest.raises(ValueError, match="score_adjustment_reason_required"):
        save_reviewer_assessment_draft(
            bundle,
            reviewer_user_id=1,
            reviewer_display_name="Reviewer",
            assessed_points=1.0,
            indicator_id="kra3-b-train-local",
            settings=_settings(),
        )


def test_kra_total_caps_at_100():
    class Doc:
        def __init__(self, cid, iid, bundle):
            self.criterion_id = cid
            self.indicator_id = iid
            self.public_id = f"doc-{iid}"
            self.extracted_info = {"kra3EvidenceBundle": bundle}
            self.deleted_at = None

    docs = [
        Doc(
            "kra3-a",
            "kra3-a-linkage",
            {
                "accomplishmentId": "a1",
                "reviewStatus": "approved",
                "submittedForReviewAt": "2026-01-01",
                "checklist": {"primary_output": {"status": "verified", "documentId": "d1"}},
                "reviewerAssessment": {"assessedPoints": 5},
                "metadataConfirmed": {"activityTitle": True},
                "activityTitle": "Link",
            },
        ),
    ]
    block = aggregate_kra3_kra_from_documents(docs, settings=_settings(), applicable_config_present=True)
    assert block["kraId"] == "kra3"
    assert block["maxPoints"] == 100.0
