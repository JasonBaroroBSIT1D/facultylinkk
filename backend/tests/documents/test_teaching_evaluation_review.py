"""Teaching evaluation review helpers (no database)."""

from __future__ import annotations

import pytest

from documents.teaching_evaluation_review import _normalize_decision


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("approve", "approved"),
        ("approved", "approved"),
        ("reject", "rejected"),
        ("revision", "needs_revision"),
        ("needs_revision", "needs_revision"),
    ],
)
def test_normalize_decision(raw, expected):
    assert _normalize_decision(raw) == expected


def test_normalize_decision_invalid():
    with pytest.raises(ValueError, match="invalid_decision"):
        _normalize_decision("maybe")
