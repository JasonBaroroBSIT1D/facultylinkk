"""Published KRA overall maximum vs criterion maximums (JC 01 s. 2026, no DB)."""

from __future__ import annotations

from kra_configuration.published_limits import (
    criterion_is_bonus,
    published_kra_max_points,
    published_criterion_max_points,
    format_criterion_user_label,
    published_criterion_user_label,
)


def _jc_2026_style_settings() -> dict:
    """Representative published blob: overall KRA max 100; criteria may exceed when summed."""
    return {
        "kras": {
            "kra1": {"maxPoints": 100, "name": "Instruction"},
            "kra2": {"maxPoints": 100, "name": "Research"},
            "kra3": {"maxPoints": 100, "name": "Extension"},
            "kra4": {"maxPoints": 100, "name": "Professional Development"},
        },
        "criteria": {
            "kra1-a": {"maxPoints": 60, "name": "Criterion A — Teaching Effectiveness"},
            "kra1-b": {"maxPoints": 30, "name": "Criterion B — Instructional Materials Development and Academic Programs"},
            "kra1-c": {"maxPoints": 10, "name": "Criterion C — Research Advising and Mentorship Services"},
            "kra2-a": {"maxPoints": 100, "name": "Criterion A — Research Publications and Creative Works"},
            "kra2-b": {"maxPoints": 100, "name": "Criterion B — Patents, Utility Models, and Commercialization"},
            "kra2-c": {"maxPoints": 100, "name": "Criterion C — Citations and Research Impact"},
            "kra3-a": {"maxPoints": 30, "name": "Criterion A — Linkages and Income Generation"},
            "kra3-b": {"maxPoints": 50, "name": "Criterion B — Extension and Public Service"},
            "kra3-c": {"maxPoints": 20, "name": "Criterion C — Client Satisfaction"},
            "kra3-d": {"maxPoints": 20, "name": "Criterion D — Leadership in Extension (Bonus)", "bonus": True},
            "kra4-a": {"maxPoints": 20, "name": "Criterion A — Professional Licenses and Certifications"},
            "kra4-b": {"maxPoints": 60, "name": "Criterion B — Trainings and Professional Activities"},
            "kra4-c": {"maxPoints": 20, "name": "Criterion C — Awards and Recognition"},
            "kra4-d": {"maxPoints": 20, "name": "Criterion D — Leadership in Professional Development (Bonus)", "bonus": True},
        },
    }


def test_all_kras_overall_max_100_from_kra_row_not_criterion_sum():
    settings = _jc_2026_style_settings()
    for kra_id in ("kra1", "kra2", "kra3", "kra4"):
        assert published_kra_max_points(kra_id, settings) == 100.0


def test_kra2_alternative_categories_do_not_sum_to_300():
    settings = _jc_2026_style_settings()
    assert published_criterion_max_points("kra2-a", settings) == 100.0
    assert published_criterion_max_points("kra2-b", settings) == 100.0
    assert published_criterion_max_points("kra2-c", settings) == 100.0
    assert published_kra_max_points("kra2", settings) == 100.0


def test_kra3_bonus_excluded_from_fallback_sum_only():
    settings = _jc_2026_style_settings()
    assert criterion_is_bonus(settings["criteria"]["kra3-d"]) is True
    # Without kras row, fallback sums non-bonus only → 100
    no_kra_row = {"criteria": settings["criteria"]}
    assert published_kra_max_points("kra3", no_kra_row) == 100.0


def test_kra4_bonus_excluded_from_fallback_sum():
    settings = _jc_2026_style_settings()
    no_kra_row = {"criteria": settings["criteria"]}
    assert published_kra_max_points("kra4", no_kra_row) == 100.0


def test_criterion_user_label_from_published_config():
    settings = _jc_2026_style_settings()
    name = format_criterion_user_label("kra2-a", settings["criteria"]["kra2-a"])
    assert name.startswith("Criterion A —")
    assert "kra2-a" not in name


def test_criterion_user_label_fallback_letter_only():
    settings = {"criteria": {"kra3-b": {"maxPoints": 50}}}
    assert published_criterion_user_label("kra3-b", settings) == "Criterion B"


def test_criterion_user_label_never_returns_internal_id():
    assert published_criterion_user_label("kra4-c", {"criteria": {}}) == "Criterion C"
