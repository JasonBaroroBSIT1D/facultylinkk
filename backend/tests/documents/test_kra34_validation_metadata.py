"""KRA III/IV validation must not block approval on metadata_not_confirmed alone."""

from __future__ import annotations

from documents.kra3_evidence.validation import validate_kra3_bundle
from documents.kra4_evidence.validation import validate_kra4_bundle


def _kra4_member_bundle(**extra):
    base = {
        "indicatorId": "kra4-a-member",
        "submittedForReviewAt": "2026-01-01T00:00:00Z",
        "activityTitle": "Professional membership",
        "organizationName": "QA Professional Society",
        "facultyRole": "Active member",
        "serviceStartDate": "2024-01-01",
        "serviceEndDate": "2026-12-31",
        "metadataConfirmed": {},
        "checklist": {
            "primary_document": {"documentId": "doc_x", "status": "verified"},
        },
    }
    base.update(extra)
    return base


def test_kra4_no_metadata_not_confirmed_flag_when_fields_present():
    result = validate_kra4_bundle(_kra4_member_bundle(), indicator_id="kra4-a-member")
    assert "metadata_not_confirmed" not in (result.get("flags") or [])
    blockers = result.get("approvalBlockers") or []
    assert not any("Confirm the information" in b for b in blockers)


def test_kra3_no_metadata_not_confirmed_flag_when_fields_present():
    bundle = {
        "indicatorId": "kra3-a-linkage",
        "submittedForReviewAt": "2026-01-01T00:00:00Z",
        "activityTitle": "MOA with partner",
        "organizationName": "Partner Org",
        "facultyRole": "Coordinator",
        "activityDate": "2025-06-01",
        "approvalReference": "MOA-2025-01",
        "metadataConfirmed": {},
        "checklist": {"primary_document": {"documentId": "doc_y", "status": "verified"}},
    }
    result = validate_kra3_bundle(bundle, indicator_id="kra3-a-linkage")
    assert "metadata_not_confirmed" not in (result.get("flags") or [])
