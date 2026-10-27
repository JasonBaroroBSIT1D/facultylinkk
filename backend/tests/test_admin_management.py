"""Admin management helpers — read-only / logic checks (no destructive DB writes)."""

import pytest

from auth.admin_management import _PENDING_DOC_STATUSES


pytestmark = pytest.mark.skip(
    reason="Admin management integration tests require an isolated database; run manually against a copy."
)


def test_pending_statuses_defined():
    assert "pending_review" in _PENDING_DOC_STATUSES
