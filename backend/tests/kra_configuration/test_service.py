"""Unit tests for KRA configuration service (no database writes)."""

from __future__ import annotations

from kra_configuration import service as kra_svc
from kra_configuration.service import (
    default_set_sef_scoring,
    empty_kra_settings,
    kra_settings_from_json,
    validate_publish_payload,
)
from documents.scoring.section10 import CIRCULAR_AGGREGATION_METHOD


def test_kra_settings_from_json_roundtrip():
    root = {
        "kras": {"kra1": {"maxPoints": 100}},
        "criteria": {},
        "indicators": {"kra1-a-student": {"maxPoints": 36, "multiplier": 36}},
        "indicatorMeta": {},
        "rankWeights": {"Instructor": {"kra1": 60}},
    }
    blob = kra_settings_from_json(root)
    assert blob["indicators"]["kra1-a-student"]["multiplier"] == 36
    assert blob["rankWeights"]["Instructor"]["kra1"] == 60


def test_merge_settings_preserves_set_sef_incomplete():
    existing = {"kras": {}, "setSefScoring": default_set_sef_scoring()}
    merged = kra_svc._merge_settings_json(existing, {"kraSettings": empty_kra_settings()})
    assert merged["setSefScoring"]["officialFormulaVerified"] is False


def test_validate_publish_requires_effective_date():
    _, err = validate_publish_payload({"kras": {}}, {})
    assert err == "effective_from_required"


def test_validate_publish_auto_verifies_set_sef_when_complete():
    settings = {
        "indicators": {
            "kra1-a-student": {"maxPoints": 36, "multiplier": 36},
            "kra1-a-supervisor": {"maxPoints": 24, "multiplier": 24},
        },
        "criteria": {"kra1-a": {"maxPoints": 60}},
        "setSefScoring": default_set_sef_scoring(),
    }
    body = {"metadata": {"effectiveFrom": "2023-08-01"}}
    merged, err = validate_publish_payload(settings, body)
    assert err is None
    assert merged["setSefScoring"]["officialFormulaVerified"] is True
    assert merged["setSefScoring"]["aggregationMethod"] == CIRCULAR_AGGREGATION_METHOD
    assert merged["effectiveFrom"] == "2023-08-01"
    assert (merged["setSefScoring"].get("formulaReference") or "").strip()


def test_validate_publish_blocks_incomplete_set_sef():
    settings = {
        "indicators": {"kra1-a-student": {"maxPoints": 36, "multiplier": 36}},
        "setSefScoring": default_set_sef_scoring(),
    }
    body = {"effectiveFrom": "2023-08-01", "metadata": {"effectiveFrom": "2023-08-01"}}
    _, err = validate_publish_payload(settings, body)
    assert err == "sef_indicator_incomplete"


def test_validate_publish_ignores_client_false_verification_flag():
    """Admins cannot publish without passing server validation by toggling flags in the body."""
    settings = {
        "indicators": {
            "kra1-a-student": {"maxPoints": 36, "multiplier": 36},
            "kra1-a-supervisor": {"maxPoints": 24, "multiplier": 24},
        },
    }
    body = {
        "metadata": {
            "effectiveFrom": "2023-08-01",
            "setSefScoring": {
                "officialFormulaVerified": False,
                "aggregationMethod": "custom_unsupported",
            },
        }
    }
    merged, err = validate_publish_payload(settings, body)
    assert err is None
    assert merged["setSefScoring"]["officialFormulaVerified"] is True
    assert merged["setSefScoring"]["aggregationMethod"] == CIRCULAR_AGGREGATION_METHOD
