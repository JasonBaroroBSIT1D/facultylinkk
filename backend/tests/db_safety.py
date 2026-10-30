"""Fail-closed guards so pytest cannot destroy the facultylink database."""

from __future__ import annotations

import os
import types
from urllib.parse import urlparse

_BLOCKED_MESSAGE = (
    "Blocked destructive SQLAlchemy call during pytest. "
    "FacultyLink uses a single PostgreSQL database (facultylink). "
    "db.create_all() and db.drop_all() are never allowed in automated tests."
)

_ENV_ALLOW_DESTRUCTIVE = "FACULTYLINK_ALLOW_DESTRUCTIVE_DB"
_ENV_ALLOW_DB_WRITES = "FACULTYLINK_ALLOW_DB_WRITES"


def running_under_pytest() -> bool:
    return os.environ.get("PYTEST_CURRENT_TEST") is not None


def destructive_allowed() -> bool:
    return os.environ.get(_ENV_ALLOW_DESTRUCTIVE) == "1"


def db_writes_allowed() -> bool:
    return os.environ.get(_ENV_ALLOW_DB_WRITES) == "1"


def database_name_from_url(url: str) -> str:
    normalized = url.replace("postgresql+psycopg", "postgresql")
    return urlparse(normalized).path.lstrip("/").split("?")[0]


def assert_production_database_url(url: str) -> None:
    """Ensure automated tests target only the facultylink database name."""
    name = database_name_from_url(url)
    if name != "facultylink":
        raise RuntimeError(
            f"Refusing to run tests against database {name!r}. "
            "Expected database name 'facultylink'."
        )
    if url.lower().startswith("sqlite:"):
        raise RuntimeError("SQLite URIs are not permitted for FacultyLink tests.")


def install_sqlalchemy_destructive_guards() -> None:
    """Patch db.create_all / db.drop_all to fail closed under pytest."""
    from extensions import db

    if getattr(db, "_facultylink_destructive_guard_installed", False):
        return

    original_create_all = db.create_all
    original_drop_all = db.drop_all

    def guarded_create_all(self, *args, **kwargs):
        if running_under_pytest() and not destructive_allowed():
            raise RuntimeError(_BLOCKED_MESSAGE)
        return original_create_all(*args, **kwargs)

    def guarded_drop_all(self, *args, **kwargs):
        if running_under_pytest() and not destructive_allowed():
            raise RuntimeError(_BLOCKED_MESSAGE)
        return original_drop_all(*args, **kwargs)

    db.create_all = types.MethodType(guarded_create_all, db)  # type: ignore[method-assign]
    db.drop_all = types.MethodType(guarded_drop_all, db)  # type: ignore[method-assign]
    db._facultylink_destructive_guard_installed = True  # type: ignore[attr-defined]
