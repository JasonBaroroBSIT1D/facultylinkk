"""Publish validation and automatic verified SET/SEF activation (no database)."""

from __future__ import annotations

import pytest

from documents.scoring.config_loader import SET_INDICATOR, SEF_INDICATOR
from documents.scoring.section10 import CIRCULAR_AGGREGATION_METHOD
from kra_configuration.verified_scoring import (
    apply_verified_scoring_to_settings,
    assess_publish_readiness,
    verified_set_sef_metadata,
)


def _set_sef_draft(set_pts=36.0, sef_pts=24.0) -> dict:
    return {
        "indicators": {
            SET_INDICATOR: {"maxPoints": set_pts, "multiplier": set_pts},
            SEF_INDICATOR: {"maxPoints": sef_pts, "multiplier": sef_pts},
        },
        "criteria": {"kra1-a": {"maxPoints": 60}},
        "evaluationCoverage": {"standardRequiredSemesters": 6},
    }


def test_assess_publish_ready_when_set_sef_configured():
    result = assess_publish_readiness(_set_sef_draft(), effective_from="2023-08-01")
    assert result["ready"] is True
    assert result["errors"] == []
    assert result["summary"]["aggregationMethod"] == CIRCULAR_AGGREGATION_METHOD


def test_assess_publish_blocks_missing_set():
    draft = _set_sef_draft()
    draft["indicators"][SET_INDICATOR] = {}
    result = assess_publish_readiness(draft, effective_from="2023-08-01")
    assert result["ready"] is False
    assert "set_indicator_incomplete" in result["errors"]


def test_apply_verified_scoring_stamps_metadata():
    merged = apply_verified_scoring_to_settings(_set_sef_draft(), effective_from="2024-01-01")
    set_sef = merged["setSefScoring"]
    assert set_sef["officialFormulaVerified"] is True
    assert set_sef["aggregationMethod"] == CIRCULAR_AGGREGATION_METHOD
    assert set_sef["formulaReference"]
    assert merged["setSefAggregationMethod"] == CIRCULAR_AGGREGATION_METHOD
    assert merged["effectiveFrom"] == "2024-01-01"


def test_apply_verified_scoring_does_not_silently_verify_incomplete_draft():
    draft = _set_sef_draft()
    draft["indicators"][SEF_INDICATOR] = {}
    with pytest.raises(ValueError, match="sef_indicator_incomplete"):
        apply_verified_scoring_to_settings(draft, effective_from="2024-01-01")


def test_verified_metadata_matches_config_loader_expectations():
    meta = verified_set_sef_metadata()
    assert meta["officialFormulaVerified"] is True
    assert meta["aggregationMethod"] == CIRCULAR_AGGREGATION_METHOD
