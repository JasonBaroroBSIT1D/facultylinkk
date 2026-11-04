"""KRA III — all 46 indicators vs independent official reference (not self-referential catalog)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from documents.kra3_evidence.scoring import aggregate_kra3_kra_from_documents, estimated_points_for_bundle
from kra_configuration.kra3_annex import published_kra3_indicator_base_points
from kra_configuration.kra3_indicator_registry import scoring_group_max
from kra_configuration.kra3_official_reference import (
    CRITERION_CAPS,
    DESIGNATION_INDICATORS_BLOCKED,
    FORMULA_INDICATORS,
    KRA3_CAP,
    VERIFIED_BASE_POINTS,
    VERIFIED_GROUP_MAX,
    reference_status,
    scoring_unit,
)

_DATA = Path(__file__).resolve().parents[2] / "kra_configuration" / "data" / "kra3_indicators.json"


def _indicators() -> list[dict]:
    payload = json.loads(_DATA.read_text(encoding="utf-8"))
    return list(payload["indicators"])


def _admin_settings_with_published_points() -> dict:
    indicators = {iid: {"points": pts} for iid, pts in VERIFIED_BASE_POINTS.items()}
    for iid in DESIGNATION_INDICATORS_BLOCKED:
        indicators[iid] = {"points": 1.0}
    return {
        "kras": {"kra3": {"maxPoints": KRA3_CAP}},
        "criteria": {
            **{cid: {"maxPoints": cap} for cid, cap in CRITERION_CAPS.items()},
            "kra3-d": {"maxPoints": CRITERION_CAPS["kra3-d"], "bonus": True},
        },
        "indicators": indicators,
    }


@pytest.mark.parametrize("row", _indicators(), ids=lambda r: r["id"])
def test_indicator_reference_coverage(row: dict):
    iid = row["id"]
    status = reference_status(iid)
    assert status in ("PASS", "FORMULA", "BLOCKED"), iid


@pytest.mark.parametrize("iid,expected", sorted(VERIFIED_BASE_POINTS.items()))
def test_verified_base_points_match_admin_publish(iid: str, expected: float):
    settings = _admin_settings_with_published_points()
    got = published_kra3_indicator_base_points(iid, settings, allow_annex_fallback=False)
    assert got == expected


@pytest.mark.parametrize("iid", sorted(DESIGNATION_INDICATORS_BLOCKED))
def test_designation_catalog_fallback_blocked_without_admin(iid: str):
    got = published_kra3_indicator_base_points(iid, None, allow_annex_fallback=True)
    assert got is None, f"Unsupported auto points for {iid}"


def test_csr_formula_independent_of_catalog_points():
    bundle = {"csrOverallRating": 80.0}
    pts = estimated_points_for_bundle(
        bundle,
        indicator_id="kra3-c-satisfaction",
        settings=_admin_settings_with_published_points(),
        applicable_config_present=True,
    )
    assert pts == 16.0


def test_hourly_train_independent():
    bundle = {"deliveryHours": 3.0}
    pts = estimated_points_for_bundle(
        bundle,
        indicator_id="kra3-b-train-local",
        settings=_admin_settings_with_published_points(),
        applicable_config_present=True,
    )
    assert pts == 6.0


def test_group_max_reference_matches_registry():
    for iid, cap in VERIFIED_GROUP_MAX.items():
        assert scoring_group_max(iid) == cap


def test_kra_final_cap_100():
    class Doc:
        def __init__(self, cid, iid, pts):
            self.criterion_id = cid
            self.indicator_id = iid
            self.public_id = f"d-{iid}"
            self.extracted_info = {
                "kra3EvidenceBundle": {
                    "accomplishmentId": iid,
                    "reviewStatus": "approved",
                    "submittedForReviewAt": "2026-01-01",
                    "activityTitle": "x",
                    "checklist": {"primary_output": {"status": "verified", "documentId": "d1"}},
                    "reviewerAssessment": {"assessedPoints": pts},
                    "metadataConfirmed": {"activityTitle": True},
                }
            }
            self.deleted_at = None

    settings = _admin_settings_with_published_points()
    docs = [
        Doc("kra3-a", "kra3-a-linkage", 5),
        Doc("kra3-b", "kra3-b-qa-local", 50),
        Doc("kra3-c", "kra3-c-satisfaction", 20),
        Doc("kra3-d", "kra3-d-president", 20),
    ]
    block = aggregate_kra3_kra_from_documents(docs, settings=settings, applicable_config_present=True)
    assert block["maxPoints"] == KRA3_CAP
    assert float(block.get("validatedPoints") or 0) <= KRA3_CAP


def test_scoring_units_documented():
    for row in _indicators():
        unit = scoring_unit(row["id"])
        assert unit


def test_host_six_month_validation_blocker():
    from documents.kra3_evidence.validation import validate_kra3_bundle

    bundle = {
        "indicatorId": "kra3-b-host",
        "submittedForReviewAt": "2026-01-01",
        "activityTitle": "Show",
        "serviceDurationMonths": 3,
        "metadataConfirmed": {"activityTitle": True, "serviceDurationMonths": True},
        "checklist": {"primary_output": {"documentId": "x", "status": "present_unverified"}},
    }
    v = validate_kra3_bundle(bundle, indicator_id="kra3-b-host")
    assert any("6 months" in b for b in v.get("submissionBlockers") or [])
