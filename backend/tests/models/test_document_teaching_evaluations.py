"""DocumentTeachingEvaluation — unit tests only (no PostgreSQL writes).

Persistence, FK, and uniqueness rules are covered here without touching the
facultylink database. Integration tests that INSERT rows remain disabled until
a safe isolated strategy exists (see tests/db_safety.py).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from documents.scoring.set_sef_aggregate import collect_period_rows
from models import DocumentTeachingEvaluation


def test_invalid_evaluation_type_rejected():
    with pytest.raises(ValueError, match="SET or SEF"):
        DocumentTeachingEvaluation(
            document_id=1,
            evaluation_type="INVALID",
            indicator_id="kra1-a-student",
        )


def test_invalid_indicator_mapping_rejected():
    with pytest.raises(ValueError, match="indicator_id"):
        DocumentTeachingEvaluation(
            document_id=1,
            evaluation_type="SET",
            indicator_id="kra1-a-supervisor",
        )


def test_set_sef_scoring_legacy_document_without_children():
    """Documents without linked evaluations still score from extracted_info."""
    doc = SimpleNamespace(
        public_id="doc_x",
        file_name="x.pdf",
        indicator_id="kra1-a-student",
        status="approved",
        ocr_status="completed",
        submitted_at=None,
        teaching_evaluations=[],
        extracted_info={
            "Academic year": "2024-2025",
            "Semester": "1st Semester",
            "Extracted rating": "95 / 100",
            "Rating scale": "100",
        },
    )
    rows = collect_period_rows([doc], "kra1-a-student")
    assert len(rows) == 1
    assert rows[0]["ratingPercent"] == 95.0
