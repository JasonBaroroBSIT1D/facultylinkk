"""Resolve applicable official scoring configuration (Phase C5)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from evaluation_periods.service import DEFAULT_TIMEZONE, local_today
from kra_configuration.statuses import SCORABLE_STATUSES, STATUS_DRAFT
from models import KraConfiguration


@dataclass(frozen=True)
class ScoringConfigurationResolution:
    """Result of resolving which configuration row applies."""

    row: KraConfiguration | None
    as_of_date: date
    provenance: str
    """One of: explicit_id, evaluation_period, applicable_as_of, none_available."""

    @property
    def has_applicable_row(self) -> bool:
        return self.row is not None


def _parse_iso_date(raw: str | None) -> date | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def effective_window(settings_json: dict | None) -> tuple[date | None, date | None]:
    root = settings_json if isinstance(settings_json, dict) else {}
    return _parse_iso_date(root.get("effectiveFrom")), _parse_iso_date(root.get("effectiveTo"))


def row_is_applicable_on(row: KraConfiguration, as_of: date) -> bool:
    if row.status == STATUS_DRAFT or row.published_at is None:
        return False
    if row.status not in SCORABLE_STATUSES:
        return False
    eff_from, eff_to = effective_window(row.settings_json if isinstance(row.settings_json, dict) else {})
    if eff_from is not None and as_of < eff_from:
        return False
    if eff_to is not None and as_of > eff_to:
        return False
    return True


def select_best_applicable_row(rows: list[KraConfiguration], as_of: date) -> KraConfiguration | None:
    """Pick the configuration with the latest effectiveFrom (then published_at) among applicable rows."""
    candidates: list[tuple[tuple[date, datetime], KraConfiguration]] = []
    for row in rows:
        if not row_is_applicable_on(row, as_of):
            continue
        sj = row.settings_json if isinstance(row.settings_json, dict) else {}
        eff_from, _ = effective_window(sj)
        sort_from = eff_from or date.min
        pub = row.published_at or datetime.min.replace(tzinfo=None)
        if getattr(pub, "tzinfo", None) is not None:
            pub = pub.replace(tzinfo=None)
        candidates.append(((sort_from, pub), row))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _query_scorable_rows() -> list[KraConfiguration]:
    return (
        KraConfiguration.query.filter(
            KraConfiguration.status.in_(tuple(SCORABLE_STATUSES)),
            KraConfiguration.published_at.isnot(None),
        )
        .all()
    )


def resolve_scoring_configuration(
    *,
    as_of: date | None = None,
    kra_configuration_id: int | None = None,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> ScoringConfigurationResolution:
    """
    Resolve the official scoring configuration for calculations.

    Draft rows are never returned. Future-effective versions are excluded for the given as-of date.
    """
    as_of_date = as_of or local_today(timezone_name)

    if kra_configuration_id is not None:
        row = KraConfiguration.query.filter(KraConfiguration.id == kra_configuration_id).first()
        if row and row.status != STATUS_DRAFT and row.published_at is not None:
            return ScoringConfigurationResolution(
                row=row,
                as_of_date=as_of_date,
                provenance="explicit_id",
            )
        return ScoringConfigurationResolution(row=None, as_of_date=as_of_date, provenance="explicit_id")

    row = select_best_applicable_row(_query_scorable_rows(), as_of_date)
    return ScoringConfigurationResolution(
        row=row,
        as_of_date=as_of_date,
        provenance="applicable_as_of" if row else "none_available",
    )


def resolve_for_evaluation_period(period) -> ScoringConfigurationResolution:
    """Use evaluation period binding when set; otherwise applicable config for period start."""
    if period is None:
        return resolve_scoring_configuration()
    bound_id = getattr(period, "kra_configuration_id", None)
    if bound_id:
        return resolve_scoring_configuration(kra_configuration_id=int(bound_id))
    start = getattr(period, "start_date", None)
    return resolve_scoring_configuration(as_of=start if isinstance(start, date) else None)


def settings_blob_from_resolution(resolution: ScoringConfigurationResolution) -> dict[str, Any]:
    from kra_configuration.service import kra_settings_from_json

    if not resolution.row:
        return kra_settings_from_json({})
    sj = resolution.row.settings_json if isinstance(resolution.row.settings_json, dict) else {}
    return kra_settings_from_json(sj)


def resolution_metadata(resolution: ScoringConfigurationResolution) -> dict[str, Any]:
    row = resolution.row
    if not row:
        return {
            "configurationId": None,
            "version": None,
            "guidelineLabel": None,
            "effectiveFrom": None,
            "effectiveTo": None,
            "publishedAt": None,
            "provenance": resolution.provenance,
            "asOfDate": resolution.as_of_date.isoformat(),
            "scoringVersionProvenance": "none_available",
        }
    sj = row.settings_json if isinstance(row.settings_json, dict) else {}
    eff_from, eff_to = effective_window(sj)
    return {
        "configurationId": row.id,
        "version": sj.get("version"),
        "guidelineLabel": row.guideline_label,
        "effectiveFrom": eff_from.isoformat() if eff_from else sj.get("effectiveFrom"),
        "effectiveTo": eff_to.isoformat() if eff_to else sj.get("effectiveTo"),
        "publishedAt": row.published_at.isoformat() if row.published_at else None,
        "status": row.status,
        "provenance": resolution.provenance,
        "asOfDate": resolution.as_of_date.isoformat(),
        "scoringVersionProvenance": resolution.provenance,
    }
