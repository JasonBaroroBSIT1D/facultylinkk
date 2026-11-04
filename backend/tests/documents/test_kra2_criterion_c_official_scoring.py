"""Criterion C official scoring (JC 01 s. 2026 Annex A pp. 84–92, Sections 25–27)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from documents.kra2_evidence.bundle import REVIEW_APPROVED, SLOT_STATUS_VERIFIED, build_initial_bundle
from documents.kra2_evidence.kra2_c_evidence_slots import criterion_c_required_slots, is_criterion_c_indicator
from documents.kra2_evidence.reviewer_assessment import apply_reviewer_accomplishment_decision
from documents.kra2_evidence.scoring import (
    aggregate_kra2_criterion_from_documents,
    aggregate_kra2_kra_from_documents,
    estimated_points_for_bundle,
)
from documents.kra2_evidence.slots import required_slots
from documents.kra2_evidence.validation import validate_kra2_bundle
from kra_configuration.kra2_annex import CRITERION_C_ID, published_kra2_indicator_base_points
from kra_configuration.kra2_indicator_pdf_verification import indicator_verification_status
from kra_configuration.kra2_indicator_registry import indicators_for_criterion

CRITERION_C_IDS = [r["id"] for r in indicators_for_criterion(CRITERION_C_ID)]

OFFICIAL_BASE: dict[str, float] = {
    "kra2-c-music-comp-sole": 20,
    "kra2-c-music-perf": 10,
    "kra2-c-poetry": 2,
    "kra2-c-story-sole": 10,
    "kra2-c-novel-sole": 20,
}


def _settings() -> dict:
    ind = {}
    for iid in CRITERION_C_IDS:
        v = indicator_verification_status(iid)
        ind[iid] = {
            "points": v["catalogPoints"],
            "maxPoints": v["catalogMaxPoints"],
        }
    return {
        "version": "criterion-c-audit-test",
        "kras": {"kra2": {"maxPoints": 100}},
        "criteria": {
            "kra2-a": {"maxPoints": 100},
            "kra2-b": {"maxPoints": 100},
            "kra2-c": {"maxPoints": 100},
        },
        "indicators": ind,
    }


def _verify_all_slots(bundle: dict, indicator_id: str) -> None:
    for slot in required_slots(indicator_id=indicator_id):
        bundle.setdefault("checklist", {})[slot] = {
            "status": SLOT_STATUS_VERIFIED,
            "documentId": f"doc_{slot}",
        }


@pytest.mark.parametrize("indicator_id", CRITERION_C_IDS)
def test_catalog_points_match_annex(indicator_id: str):
    v = indicator_verification_status(indicator_id)
    assert v["status"] != "MISMATCH", v


@pytest.mark.parametrize("indicator_id", CRITERION_C_IDS)
def test_criterion_c_evidence_slots_annex_driven(indicator_id: str):
    slots = criterion_c_required_slots(indicator_id)
    assert slots
    assert slots[0] == "primary_output"
    assert list(required_slots(indicator_id=indicator_id)) == list(slots)


@pytest.mark.parametrize("indicator_id,base", list(OFFICIAL_BASE.items()))
def test_published_base_points(indicator_id: str, base: float):
    settings = _settings()
    got = published_kra2_indicator_base_points(indicator_id, settings, allow_annex_fallback=False)
    assert got == base


def test_co_author_estimated_points_use_contribution_percent():
    settings = _settings()
    bundle = build_initial_bundle(
        primary_document_id="doc1",
        primary_file_hash="h",
        indicator_id="kra2-c-music-comp-co",
        output_title="Suite",
    )
    bundle["contribution"] = "declared"
    bundle["declaredContributionPercent"] = 40
    est = estimated_points_for_bundle(
        bundle,
        indicator_id="kra2-c-music-comp-co",
        settings=settings,
        applicable_config_present=True,
    )
    assert est == 8.0


def test_criterion_c_aggregate_caps_at_100():
    settings = _settings()

    def _approved_doc(iid: str, pts_key: str) -> SimpleNamespace:
        bundle = build_initial_bundle(
            primary_document_id=f"doc_{pts_key}",
            primary_file_hash=pts_key,
            indicator_id=iid,
            output_title=f"Work {pts_key}",
        )
        bundle["accomplishmentId"] = f"acc_{pts_key}"
        bundle["outputVenue"] = "National gallery"
        bundle["authorsLine"] = "Faculty Author"
        bundle["publicationDate"] = "2025-01-01"
        bundle["metadataConfirmed"] = {
            "outputTitle": True,
            "outputVenue": True,
            "authorsLine": True,
            "publicationDate": True,
        }
        bundle["submittedForReviewAt"] = "2025-06-01T00:00:00+00:00"
        _verify_all_slots(bundle, iid)
        apply_reviewer_accomplishment_decision(
            bundle,
            review_status=REVIEW_APPROVED,
            reviewer_user_id=1,
            reviewer_display_name="Reviewer",
            remarks="Approved for unit test scoring cap.",
            indicator_id=iid,
            settings=settings,
        )
        return SimpleNamespace(
            public_id=f"doc_{pts_key}",
            indicator_id=iid,
            criterion_id=CRITERION_C_ID,
            extracted_info={"kra2EvidenceBundle": bundle},
            deleted_at=None,
            status="approved",
        )

    docs = [
        _approved_doc("kra2-c-novel-sole", "n1"),
        _approved_doc("kra2-c-novel-sole", "n2"),
        _approved_doc("kra2-c-novel-sole", "n3"),
        _approved_doc("kra2-c-novel-sole", "n4"),
        _approved_doc("kra2-c-novel-sole", "n5"),
        _approved_doc("kra2-c-novel-sole", "n6"),
    ]
    block = aggregate_kra2_criterion_from_documents(
        docs,
        criterion_id=CRITERION_C_ID,
        settings=settings,
        applicable_config_present=True,
    )
    assert block["validatedPoints"] == 100.0

    kra = aggregate_kra2_kra_from_documents(docs, settings=settings, applicable_config_present=True)
    assert kra["validatedPoints"] <= 100.0


def test_upload_alone_not_ready_for_scoring():
    bundle = build_initial_bundle(
        primary_document_id="doc_draft",
        primary_file_hash="x",
        indicator_id="kra2-c-poetry",
        output_title="Poem",
    )
    val = validate_kra2_bundle(bundle, indicator_id="kra2-c-poetry")
    assert not val.get("readyForScoring")
    assert is_criterion_c_indicator("kra2-c-poetry")
