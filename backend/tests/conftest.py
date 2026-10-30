"""Pytest fixtures with fail-closed protection for the facultylink database."""

from __future__ import annotations

import pytest

from config import Config
from factory import create_app
from tests.db_safety import (
    assert_production_database_url,
    db_writes_allowed,
    install_sqlalchemy_destructive_guards,
)

install_sqlalchemy_destructive_guards()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "db_write: test persists or mutates PostgreSQL rows (disabled by default)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if db_writes_allowed():
        return
    skip_db = pytest.mark.skip(
        reason=(
            "Database write integration tests are disabled to protect the "
            "facultylink PostgreSQL database. Run only unit tests, or set "
            "FACULTYLINK_ALLOW_DB_WRITES=1 when executing against an approved copy."
        )
    )
    for item in items:
        if "db_write" in item.keywords:
            item.add_marker(skip_db)


@pytest.fixture()
def app():
    url = Config.database_url()
    assert_production_database_url(url)
    return create_app(Config)


@pytest.fixture()
def client(app):
    return app.test_client()
