"""Admin management helpers — read-only / logic checks (no destructive DB writes)."""

import pytest

from auth.admin_management import _PENDING_DOC_STATUSES


pytestmark = [
    pytest.mark.skip(
        reason=(
            "Admin management integration tests are disabled to protect facultylink. "
            "Run manually against a pg_dump copy only."
        )
    ),
    pytest.mark.db_write,
]


def test_pending_statuses_defined():
    assert "pending_review" in _PENDING_DOC_STATUSES
