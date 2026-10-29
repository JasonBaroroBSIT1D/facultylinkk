"""Load indicator scoring parameters from published Admin configuration."""

from __future__ import annotations

from documents.scoring.section10 import CIRCULAR_AGGREGATION_METHOD
from kra_configuration.service import get_published_row

SET_INDICATOR = "kra1-a-student"
SEF_INDICATOR = "kra1-a-supervisor"
CRITERION_A_ID = "kra1-a"
CRITERION_A_MAX_KEY = "kra1-a"


def published_configuration():
    """Latest published row from PostgreSQL (not draft, not mock)."""
    return get_published_row()


def _settings_root(cfg) -> dict:
    raw = cfg.settings_json if isinstance(cfg.settings_json, dict) else {}
    return raw


def published_settings_root() -> dict | None:
    cfg = published_configuration()
    if not cfg:
        return None
    return _settings_root(cfg)


def indicator_scoring_config(indicator_id: str) -> dict:
    """Return scoring parameters for a rating-type indicator from published config only."""
    cfg = published_configuration()
    if not cfg:
        return {
            "complete": False,
            "reason": "No published Admin Official Scoring Configuration.",
            "indicatorId": indicator_id,
        }
    settings = _settings_root(cfg)
    indicators = settings.get("indicators") if isinstance(settings.get("indicators"), dict) else {}
    entry = indicators.get(indicator_id)
    if not isinstance(entry, dict):
        return {
            "complete": False,
            "reason": "Indicator is missing from the published scoring configuration.",
            "indicatorId": indicator_id,
            "configurationLabel": cfg.guideline_label,
            "publishedAt": cfg.published_at.isoformat() if cfg.published_at else None,
        }
    max_points = entry.get("maxPoints")
    multiplier = entry.get("multiplier")
    formula = entry.get("formula") if isinstance(entry.get("formula"), dict) else {}
    if multiplier is None and formula.get("type") == "rating":
        multiplier = formula.get("multiplier")
    if max_points is None and multiplier is not None:
        max_points = multiplier
    if multiplier is None and max_points is not None:
        multiplier = max_points
    try:
        max_f = float(max_points) if max_points is not None else None
        mult_f = float(multiplier) if multiplier is not None else None
    except (TypeError, ValueError):
        max_f = mult_f = None
    if max_f is None or mult_f is None:
        return {
            "complete": False,
            "reason": "Scoring configuration incomplete (maximum points or multiplier missing).",
            "indicatorId": indicator_id,
            "configurationLabel": cfg.guideline_label,
            "publishedAt": cfg.published_at.isoformat() if cfg.published_at else None,
        }
    set_sef_meta = settings.get("setSefScoring") if isinstance(settings.get("setSefScoring"), dict) else {}
    coverage = settings.get("evaluationCoverage") or settings.get("teachingEffectivenessCoverage")
    if indicator_id in (SET_INDICATOR, SEF_INDICATOR):
        if not set_sef_meta.get("officialFormulaVerified"):
            return {
                "complete": False,
                "reason": (
                    set_sef_meta.get("incompleteReason")
                    or "SET/SEF official aggregation formula has not been verified for publication."
                ),
                "indicatorId": indicator_id,
                "maxPoints": round(max_f, 4),
                "multiplier": round(mult_f, 4),
                "configurationLabel": cfg.guideline_label,
                "publishedAt": cfg.published_at.isoformat() if cfg.published_at else None,
                "setSefFormulaVerified": False,
                "evaluationCoverage": coverage,
            }
        agg = (
            set_sef_meta.get("aggregationMethod")
            or settings.get("setSefAggregationMethod")
        )
        if agg != CIRCULAR_AGGREGATION_METHOD:
            return {
                "complete": False,
                "reason": (
                    "Published SET/SEF aggregation method must be "
                    f"'{CIRCULAR_AGGREGATION_METHOD}' after Admin verification."
                ),
                "indicatorId": indicator_id,
                "maxPoints": round(max_f, 4),
                "multiplier": round(mult_f, 4),
                "aggregationMethod": agg,
                "configurationLabel": cfg.guideline_label,
                "publishedAt": cfg.published_at.isoformat() if cfg.published_at else None,
                "setSefFormulaVerified": True,
                "evaluationCoverage": coverage,
            }
    required_periods = None
    if isinstance(coverage, dict):
        required_periods = coverage.get("requiredSemesters") or coverage.get("requiredPeriods")
    criteria = settings.get("criteria") if isinstance(settings.get("criteria"), dict) else {}
    criterion_max = None
    crit_entry = criteria.get(CRITERION_A_ID)
    if isinstance(crit_entry, dict) and crit_entry.get("maxPoints") is not None:
        try:
            criterion_max = float(crit_entry["maxPoints"])
        except (TypeError, ValueError):
            criterion_max = None
    rating_scale = entry.get("ratingScale") or formula.get("ratingScale") or 100
    try:
        rating_scale_f = float(rating_scale)
    except (TypeError, ValueError):
        rating_scale_f = 100.0
    return {
        "complete": True,
        "indicatorId": indicator_id,
        "maxPoints": round(max_f, 4),
        "multiplier": round(mult_f, 4),
        "ratingScale": rating_scale_f,
        "formulaType": formula.get("type") or "rating",
        "aggregationMethod": (
            set_sef_meta.get("aggregationMethod")
            or entry.get("aggregationMethod")
            or settings.get("setSefAggregationMethod")
        ),
        "roundingRule": settings.get("roundingRule") or set_sef_meta.get("roundingRule"),
        "requiredPeriods": required_periods,
        "configurationLabel": cfg.guideline_label,
        "publishedAt": cfg.published_at.isoformat() if cfg.published_at else None,
        "configurationVersion": settings.get("version"),
        "effectiveFrom": settings.get("effectiveFrom"),
        "effectiveTo": settings.get("effectiveTo"),
        "criterionMaxPoints": criterion_max,
        "setSefFormulaVerified": bool(set_sef_meta.get("officialFormulaVerified")),
        "formulaReference": set_sef_meta.get("formulaReference"),
        "evaluationCoverage": coverage,
    }


def criterion_a_max_points() -> float | None:
    cfg = published_configuration()
    if not cfg:
        return None
    settings = _settings_root(cfg)
    criteria = settings.get("criteria") if isinstance(settings.get("criteria"), dict) else {}
    crit = criteria.get(CRITERION_A_ID)
    if isinstance(crit, dict) and crit.get("maxPoints") is not None:
        try:
            return float(crit["maxPoints"])
        except (TypeError, ValueError):
            return None
    return None
