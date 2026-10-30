from datetime import date

from evaluation_periods.service import calendar_status


def test_calendar_status_upcoming():
    assert calendar_status(date(2026, 11, 1), date(2026, 11, 3), today=date(2026, 10, 30)) == "upcoming"


def test_calendar_status_open_inclusive():
    assert calendar_status(date(2026, 10, 30), date(2026, 11, 1), today=date(2026, 10, 30)) == "open"
    assert calendar_status(date(2026, 10, 30), date(2026, 11, 1), today=date(2026, 11, 1)) == "open"


def test_calendar_status_closed():
    assert calendar_status(date(2026, 10, 30), date(2026, 11, 1), today=date(2026, 11, 2)) == "closed"
