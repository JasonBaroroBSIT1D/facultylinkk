"""Fail-closed database guard for live QA scripts (never write to production)."""

from __future__ import annotations

import os
import sys

_QA_DB_NAME = "facultylink_qa"


def apply_qa_database_env() -> None:
    """If FACULTYLINK_QA_DATABASE_URL is set, point DATABASE_URL at it before app import."""
    qa_url = (os.environ.get("FACULTYLINK_QA_DATABASE_URL") or "").strip()
    if qa_url:
        os.environ["DATABASE_URL"] = qa_url
        os.environ["FACULTYLINK_QA_DATABASE_ALLOWED"] = "1"


def resolve_database_url() -> str:
    from config import Config

    return (os.environ.get("DATABASE_URL") or Config.SQLALCHEMY_DATABASE_URI or "").strip()


def database_name_from_url(url: str) -> str:
    from tests.db_safety import database_name_from_url as _name

    return _name(url)


def is_isolated_qa_database_active() -> bool:
    """True when the app is connected to facultylink_qa (not production facultylink)."""
    try:
        apply_qa_database_env()
        return database_name_from_url(resolve_database_url()) == _QA_DB_NAME
    except Exception:
        return False


def qa_tag_excluded_from_scoring_totals() -> bool:
    """
    [KRA*-QA] titles are excluded from rank/criterion totals on production.

    On facultylink_qa they count so E2E can verify aggregation without touching production.
    """
    if is_isolated_qa_database_active():
        return False
    return True


def require_qa_test_database() -> str:
    """
    Abort unless the active SQLAlchemy URL targets the isolated QA database.

    Production `facultylink` is never permitted for scripts that insert QA rows.
    """
    apply_qa_database_env()
    url = resolve_database_url()
    if not url:
        print("DATABASE_URL is not configured.", file=sys.stderr)
        raise SystemExit(3)
    name = database_name_from_url(url)
    if name != _QA_DB_NAME:
        print(
            f"Refusing QA writes: database {name!r} is not {_QA_DB_NAME!r}. "
            f"Set FACULTYLINK_QA_DATABASE_URL to a PostgreSQL URL whose database name is "
            f"{_QA_DB_NAME!r} (see backend/.env.example).",
            file=sys.stderr,
        )
        raise SystemExit(3)
    if os.environ.get("FACULTYLINK_QA_DATABASE_ALLOWED", "").strip() != "1":
        print(
            "Refusing QA writes: set FACULTYLINK_QA_DATABASE_ALLOWED=1 when using the QA database.",
            file=sys.stderr,
        )
        raise SystemExit(3)
    return name


def qa_faculty_user():
    """Prefer dedicated QA faculty account; never fall back to arbitrary production faculty."""
    from models import FacultyProfile, User

    email = (os.environ.get("QA_FACULTY_EMAIL") or "").strip()
    if email:
        user = User.query.filter_by(email=email, role="faculty", is_active=True).first()
        if not user:
            print(f"QA faculty user not found: {email}", file=sys.stderr)
            raise SystemExit(4)
        profile = FacultyProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            print(f"QA faculty profile missing for {email}", file=sys.stderr)
            raise SystemExit(4)
        return user, profile

    user = (
        User.query.filter(User.role == "faculty", User.is_active.is_(True), User.email.ilike("%qa%"))
        .order_by(User.id.asc())
        .first()
    )
    if not user:
        print(
            "Set QA_FACULTY_EMAIL to an isolated test faculty account on the QA database.",
            file=sys.stderr,
        )
        raise SystemExit(4)
    profile = FacultyProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        raise SystemExit(4)
    return user, profile


def qa_reviewer_for_profile(profile) -> "User":
    from models import User

    reviewer_id = getattr(profile, "reviewer_user_id", None)
    reviewer = User.query.get(reviewer_id) if reviewer_id else None
    if reviewer and reviewer.is_active:
        return reviewer
    email = (os.environ.get("QA_REVIEWER_EMAIL") or "").strip()
    if email:
        reviewer = User.query.filter_by(email=email, role="reviewer", is_active=True).first()
        if reviewer:
            return reviewer
    reviewer = User.query.filter_by(role="reviewer", is_active=True).order_by(User.id.asc()).first()
    if not reviewer:
        print("No reviewer on QA database.", file=sys.stderr)
        raise SystemExit(4)
    return reviewer
