"""Pytest fixtures — single production database (facultylink) only.

Integration tests that write to PostgreSQL are skipped until an isolated test
strategy is configured. The health test uses a read-only SELECT via /api/health.
"""

import pytest

from config import Config
from factory import create_app


@pytest.fixture()
def app():
    return create_app(Config)


@pytest.fixture()
def client(app):
    return app.test_client()
