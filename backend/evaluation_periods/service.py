"""Evaluation period persistence and shared calendar status (Asia/Manila)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from extensions import db
from models import EvaluationPeriod, new_public_id

DEFAULT_TIMEZONE = "Asia/Manila"
PRIMARY_PERIOD_TYPE = "rank_reclassification"
WEB_PERIOD_ID = "evaluation"
DEFAULT_LABEL = "Rank Upgrade and Reclassification"

PUBLISHED_DB_STATUSES = frozenset({"published", "active"})


def local_today(timezone_name: str = DEFAULT_TIMEZONE) -> date:
    try:
        tz = ZoneInfo(timezone_name or DEFAULT_TIMEZONE)
    except Exception:
        tz = ZoneInfo(DEFAULT_TIMEZONE)
    return datetime.now(tz).date()


def calendar_status(
    start: date,
    end: date,
    *,
    today: date | None = None,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> str:
    """Upcoming before start; Open on start through end (inclusive); Closed after end."""
    if today is None:
        today = local_today(timezone_name)
    if today < start:
        return "upcoming"
    if today > end:
        return "closed"
    return "open"


def is_published_db_status(status: str | None) -> bool:
    return (status or "").strip().lower() in PUBLISHED_DB_STATUSES


def _period_timezone(period: EvaluationPeriod) -> str:
    return (period.timezone or DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE


def _parse_iso_date(raw: str | None, field: str) -> date:
    text = (raw or "").strip()
    if not text:
        raise ValueError(f"missing_{field}")
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(f"invalid_{field}") from exc


def primary_period_row() -> EvaluationPeriod | None:
    row = EvaluationPeriod.query.filter_by(period_type=PRIMARY_PERIOD_TYPE).first()
    if row:
        return row
    return EvaluationPeriod.query.order_by(EvaluationPeriod.id.asc()).first()


def published_period_row() -> EvaluationPeriod | None:
    rows = (
        EvaluationPeriod.query.filter(EvaluationPeriod.status.in_(tuple(PUBLISHED_DB_STATUSES)))
        .order_by(EvaluationPeriod.start_date.desc())
        .all()
    )
    return rows[0] if rows else None


def period_to_admin_api(period: EvaluationPeriod) -> dict:
    published = is_published_db_status(period.status)
    tz = _period_timezone(period)
    return {
        "id": WEB_PERIOD_ID,
        "publicId": period.public_id,
        "label": period.label,
        "startDate": period.start_date.isoformat(),
        "endDate": period.end_date.isoformat(),
        "visibility": "all" if published else "draft",
        "published": published,
        "timezone": tz,
        "calendarStatus": calendar_status(period.start_date, period.end_date, timezone_name=tz),
    }


def period_to_reviewer_api(period: EvaluationPeriod) -> dict:
    row = period_to_admin_api(period)
    row["status"] = row["calendarStatus"]
    return row


def period_to_faculty_preparation_api(period: EvaluationPeriod) -> dict:
    tz = _period_timezone(period)
    cal = calendar_status(period.start_date, period.end_date, timezone_name=tz)
    until = period.review_close or period.end_date
    return {
        "cycleName": period.label,
        "startDate": period.start_date.isoformat(),
        "endDate": period.end_date.isoformat(),
        "reviewerAvailableUntil": until.isoformat(),
        "status": cal,
        "periodType": period.period_type,
        "published": True,
        "visibility": "published",
    }


def list_admin_periods_api() -> list[dict]:
    period = primary_period_row()
    if not period:
        return []
    return [period_to_admin_api(period)]


def list_published_periods_api() -> list[dict]:
    period = published_period_row()
    if not period:
        return []
    return [period_to_reviewer_api(period)]


def faculty_preparation_period_api() -> dict | None:
    period = published_period_row()
    if not period:
        return None
    return period_to_faculty_preparation_api(period)


def save_admin_periods(periods_payload: list[dict]) -> list[dict]:
    if not periods_payload:
        raise ValueError("empty_periods")

    item = periods_payload[0] or {}
    start = _parse_iso_date(item.get("startDate"), "start_date")
    end = _parse_iso_date(item.get("endDate"), "end_date")
    if end < start:
        raise ValueError("end_before_start")

    visibility = (item.get("visibility") or "").strip().lower()
    published_flag = item.get("published")
    published = bool(published_flag) or visibility in {"all", "reviewers", "faculty"}
    if published and (not start or not end):
        raise ValueError("missing_dates_for_publish")

    period = primary_period_row()
    if not period:
        period = EvaluationPeriod(
            public_id=new_public_id("per_"),
            period_type=PRIMARY_PERIOD_TYPE,
            label=DEFAULT_LABEL,
            start_date=start,
            end_date=end,
            status="draft",
            timezone=DEFAULT_TIMEZONE,
        )
        db.session.add(period)

    period.label = (item.get("label") or DEFAULT_LABEL).strip() or DEFAULT_LABEL
    period.start_date = start
    period.end_date = end
    period.status = "published" if published else "draft"
    period.timezone = (item.get("timezone") or period.timezone or DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE

    if period.submission_open is None:
        period.submission_open = start
    if period.submission_close is None:
        period.submission_close = end
    if period.review_open is None:
        period.review_open = start
    if period.review_close is None:
        period.review_close = end

    db.session.commit()
    return [period_to_admin_api(period)]
