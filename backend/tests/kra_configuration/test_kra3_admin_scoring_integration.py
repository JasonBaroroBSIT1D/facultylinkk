"""Admin-published settings drive KRA III backend scoring (not hardcoded mobile/web)."""

from __future__ import annotations

from kra_configuration.kra3_annex import published_kra3_criterion_max_points, published_kra3_indicator_base_points
from kra_configuration.published_limits import criterion_is_bonus, published_kra_max_points


def test_published_kra3_row_caps_at_100():
    settings = {
        "kras": {"kra3": {"maxPoints": 100}},
        "criteria": {
            "kra3-a": {"maxPoints": 30},
            "kra3-b": {"maxPoints": 50},
            "kra3-c": {"maxPoints": 20},
            "kra3-d": {"maxPoints": 20, "bonus": True},
        },
    }
    assert published_kra_max_points("kra3", settings) == 100.0
    assert criterion_is_bonus(settings["criteria"]["kra3-d"]) is True
    assert published_kra3_criterion_max_points("kra3-b", settings, allow_annex_fallback=False) == 50.0


def test_admin_indicator_override_beats_catalog():
    settings = {
        "indicators": {"kra3-a-linkage": {"points": 5.0}},
    }
    assert published_kra3_indicator_base_points("kra3-a-linkage", settings, allow_annex_fallback=False) == 5.0
