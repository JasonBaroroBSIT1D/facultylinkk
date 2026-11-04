"""End-to-end Criterion B flows per indicator family (bundle validation + scoring)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from documents.kra2_evidence.bundle import REVIEW_APPROVED, SLOT_STATUS_VERIFIED, build_initial_bundle, ensure_checklist_slots
from documents.kra2_evidence.patent_deduplication import apply_patent_highest_stage_only
from documents.kra2_evidence.scoring import aggregate_kra2_criterion_from_documents
from documents.kra2_evidence.slots import required_slots
from documents.kra2_evidence.validation import validate_kra2_bundle
from documents.kra2_evidence.reviewer_assessment import apply_reviewer_accomplishment_decision
from kra_configuration.kra2_indicator_pdf_verification import indicator_verification_status
from kra_configuration.kra2_indicator_registry import metadata_field_ids

FAMILY_REPRESENTATIVES = [
    "kra2-b-patent-g-sole",
    "kra2-b-patent-g-co",
    "kra2-b-comm-local",
    "kra2-b-um-sole",
    "kra2-b-sw-new-sole",
    "kra2-b-sw-new-co",
    "kra2-b-variety-co",
]


def _settings() -> dict:
    ind = {}
    for iid in FAMILY_REPRESENTATIVES + ["kra2-b-patent-a-sole", "kra2-b-patent-p-sole"]:
        v = indicator_verification_status(iid)
        ind[iid] = {"points": v["catalogPoints"], "maxPoints": v["catalogMaxPoints"]}
    ind["kra2-b-comm-local"]["group"] = "kra2-b-comm-local"
    ind["kra2-b-comm-local"]["groupMax"] = 20
    return {
        "version": "criterion-b-e2e",
        "kras": {"kra2": {"maxPoints": 100}},
        "criteria": {"kra2-b": {"maxPoints": 100}},
        "indicators": ind,
    }


def _fill_metadata(bundle: dict, indicator_id: str) -> None:
    values = {
        "outputTitle": "Test Output",
        "registrationNumber": "PH-E2E-001",
        "registrationDate": "2025-01-01",
        "authorsLine": "Faculty Member",
        "outputVenue": "Local market",
        "publicationDate": "2025-06-01",
        "declaredContributionPercent": 50,
    }
    confirmed: dict[str, bool] = {}
    for field_id in metadata_field_ids(indicator_id):
        if field_id in values:
            bundle[field_id] = values[field_id]
            confirmed[field_id] = True
    bundle["metadataConfirmed"] = confirmed


def _verify_all_slots(bundle: dict, indicator_id: str) -> None:
    for slot in required_slots(indicator_id=indicator_id):
        entry = bundle.setdefault("checklist", {}).setdefault(slot, {})
        if not entry.get("documentId"):
            entry["documentId"] = f"doc-{slot}"
        entry["status"] = SLOT_STATUS_VERIFIED


@pytest.mark.parametrize("indicator_id", FAMILY_REPRESENTATIVES)
def test_family_upload_validate_approve_aggregate(indicator_id: str):
    bundle = build_initial_bundle(
        primary_document_id="doc-primary",
        primary_file_hash="hash-primary",
        indicator_id=indicator_id,
    )
    _fill_metadata(bundle, indicator_id)
    bundle["submittedForReviewAt"] = "2026-01-01T00:00:00+00:00"

    v0 = validate_kra2_bundle(bundle, indicator_id=indicator_id)
    assert v0["readyForApproval"] is False

    _verify_all_slots(bundle, indicator_id)
    v1 = validate_kra2_bundle(bundle, indicator_id=indicator_id)
    assert v1["readyForApproval"] is True

    apply_reviewer_accomplishment_decision(
        bundle,
        review_status=REVIEW_APPROVED,
        reviewer_user_id=1,
        reviewer_display_name="Reviewer",
        remarks="E2E family test approval.",
        indicator_id=indicator_id,
        settings=_settings(),
    )
    doc = SimpleNamespace(
        public_id="doc-primary",
        criterion_id="kra2-b",
        indicator_id=indicator_id,
        extracted_info={"kra2EvidenceBundle": bundle},
        deleted_at=None,
        status="approved",
    )
    block = aggregate_kra2_criterion_from_documents(
        [doc],
        criterion_id="kra2-b",
        settings=_settings(),
        applicable_config_present=True,
    )
    assert block["validatedPoints"] > 0


def test_duplicate_patent_stages_keep_highest_only():
    bundle_by_key = {
        "a": {"registrationNumber": "PH-DEDUP", "outputTitle": "Same Device"},
        "p": {"registrationNumber": "PH-DEDUP", "outputTitle": "Same Device"},
        "g": {"registrationNumber": "PH-DEDUP", "outputTitle": "Same Device"},
    }
    indicator_by_key = {
        "a": "kra2-b-patent-a-sole",
        "p": "kra2-b-patent-p-sole",
        "g": "kra2-b-patent-g-sole",
    }
    out = apply_patent_highest_stage_only(
        {"a": 10.0, "p": 20.0, "g": 80.0},
        bundle_by_key=bundle_by_key,
        indicator_by_key=indicator_by_key,
    )
    assert out["g"] == 80.0
    assert out["a"] == 0.0
    assert out["p"] == 0.0


def test_rejected_slot_blocks_approval():
    bundle = build_initial_bundle(
        primary_document_id="doc1",
        primary_file_hash="h1",
        indicator_id="kra2-b-patent-a-sole",
    )
    _fill_metadata(bundle, "kra2-b-patent-a-sole")
    bundle["submittedForReviewAt"] = "2026-01-01T00:00:00+00:00"
    _verify_all_slots(bundle, "kra2-b-patent-a-sole")
    bundle["checklist"]["invention_photo"]["status"] = "rejected"
    v = validate_kra2_bundle(bundle, indicator_id="kra2-b-patent-a-sole")
    assert v["readyForApproval"] is False


def test_legacy_primary_only_bundle_expands_checklist_non_destructively():
    legacy = {
        "version": 1,
        "accomplishmentId": "acc-legacy",
        "indicatorId": "kra2-b-patent-g-sole",
        "primaryDocumentId": "doc-old",
        "primaryFileHash": "h-old",
        "checklist": {
            "primary_output": {
                "documentId": "doc-old",
                "fileHash": "h-old",
                "status": SLOT_STATUS_VERIFIED,
            }
        },
    }
    assert ensure_checklist_slots(legacy, indicator_id="kra2-b-patent-g-sole") is True
    for slot in required_slots(indicator_id="kra2-b-patent-g-sole"):
        assert slot in legacy["checklist"]
    assert legacy["checklist"]["primary_output"]["documentId"] == "doc-old"


def test_comm_local_initial_primary_lands_on_product_photo():
    bundle = build_initial_bundle(
        primary_document_id="doc-photo",
        primary_file_hash="hp",
        indicator_id="kra2-b-comm-local",
    )
    assert bundle["checklist"]["product_photo"]["documentId"] == "doc-photo"
