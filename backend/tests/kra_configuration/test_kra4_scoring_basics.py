"""KRA IV catalog and scoring smoke tests."""

from __future__ import annotations

from documents.kra4_evidence.scoring import estimated_points_for_bundle
from kra_configuration.kra4_annex import (
    CRITERION_A_MAX,
    CRITERION_B_MAX,
    CRITERION_C_MAX,
    CRITERION_D_BONUS_MAX,
    KRA4_MAX_POINTS,
    is_kra4_indicator,
)
from kra_configuration.kra4_indicator_registry import all_indicators


def test_kra4_catalog_has_nineteen_indicators():
    assert len(all_indicators()) == 19


def test_kra4_official_caps():
    assert KRA4_MAX_POINTS == 100.0
    assert CRITERION_A_MAX == 20.0
    assert CRITERION_B_MAX == 60.0
    assert CRITERION_C_MAX == 20.0
    assert CRITERION_D_BONUS_MAX == 20.0


def test_kra4_member_fixed_points():
    pts = estimated_points_for_bundle({}, indicator_id="kra4-a-member")
    assert pts == 5.0
    assert is_kra4_indicator("kra4-a-member")


def test_kra4_experience_years_multiplier():
    pts = estimated_points_for_bundle({"experienceYears": 2.5}, indicator_id="kra4-d-pres")
    assert pts == 12.5
