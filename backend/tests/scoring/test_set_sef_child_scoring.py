"""SET/SEF scoring from DocumentTeachingEvaluation rows (no database)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.scoring.set_sef_aggregate import aggregate_indicator, collect_period_rows


def _verified_config(multiplier: float = 36.0):
    return {
        "complete": True,
        "maxPoints": multiplier,
        "multiplier": multiplier,
        "ratingScale": 100.0,
        "aggregationMethod": "circular_jc_2026_semester_average",
        "roundingRule": "two_decimals",
        "evaluationCoverage": {"standardRequiredSemesters": 1},
    }


def _tev(public_id: str, ay: str, sem: str, rating: str, *, status: str | None = "approved"):
    pct = float(rating.split("/")[0]) if "/" in rating else float(rating)
    return SimpleNamespace(
        public_id=public_id,
        indicator_id="kra1-a-student",
        evaluation_type="SET",
        academic_year=ay,
        semester=sem,
        rating_raw=rating if "/" in rating else f"{rating}/100",
        rating_scale=100.0,
        rating_percent=pct,
        reviewer_validation_status=status,
        ocr_verification_status="match",
        extracted_metadata={},
        source_section_ref=f"page-{public_id}",
    )


def _doc(public_id: str, *, children: list | None = None, legacy_rating: str | None = None):
    info = {}
    if legacy_rating:
        info = {
            "Academic year": "2024-2025",
            "Semester": "1st Semester",
            "Extracted rating": legacy_rating,
            "Rating scale": "100",
        }
    return SimpleNamespace(
        public_id=public_id,
        file_name=f"{public_id}.pdf",
        indicator_id="kra1-a-student",
        status="approved",
        ocr_status="completed",
        submitted_at=None,
        extracted_info=info,
        teaching_evaluations=children or [],
    )


def test_child_records_used_instead_of_document_metadata(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: _verified_config(),
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {})
    doc = _doc(
        "mixed",
        children=[_tev("t1", "2024-2025", "1st Semester", "90/100")],
        legacy_rating="50/100",
    )
    rows = collect_period_rows([doc], "kra1-a-student")
    assert len(rows) == 1
    assert rows[0]["ratingPercent"] == 90.0
    block = aggregate_indicator([doc], "kra1-a-student")
    assert block["provisionalPoints"] == 32.4
    assert block["coverageSummary"]["detectedEvaluationRecords"] == 1


def test_document_auto_approve_does_not_validate_unreviewed_child(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: _verified_config(),
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {})
    doc = _doc("auto", children=[_tev("t1", "2024-2025", "1st Semester", "90/100", status=None)])
    block = aggregate_indicator([doc], "kra1-a-student")
    assert block["provisionalPoints"] == 32.4
    assert block["validatedPoints"] is None
    assert block["coverageSummary"]["verifiedEligibleRecords"] == 0
    assert block["coverageSummary"]["pendingRecords"] == 1


def test_same_semesters_one_pdf_vs_many_pdfs(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: _verified_config(),
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {})
    single = _doc(
        "one",
        children=[
            _tev("a", "2024-2025", "1st Semester", "90/100"),
            _tev("b", "2024-2025", "2nd Semester", "80/100"),
        ],
    )
    many = [
        _doc("d1", children=[_tev("a", "2024-2025", "1st Semester", "90/100")]),
        _doc("d2", children=[_tev("b", "2024-2025", "2nd Semester", "80/100")]),
    ]
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: {
            **_verified_config(),
            "evaluationCoverage": {"standardRequiredSemesters": 2},
        },
    )
    block_one = aggregate_indicator([single], "kra1-a-student")
    block_many = aggregate_indicator(many, "kra1-a-student")
    assert block_one["provisionalPoints"] == block_many["provisionalPoints"]
    assert block_one["validatedPoints"] == block_many["validatedPoints"]


def test_mixed_pdf_set_and_sef_from_same_upload(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda ind: _verified_config(36.0 if ind == "kra1-a-student" else 24.0),
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {})
    set_tev = _tev("s1", "2024-2025", "1st Semester", "90/100")
    sef_tev = SimpleNamespace(
        public_id="f1",
        indicator_id="kra1-a-supervisor",
        evaluation_type="SEF",
        academic_year="2024-2025",
        semester="1st Semester",
        rating_raw="88/100",
        rating_scale=100.0,
        rating_percent=88.0,
        reviewer_validation_status="approved",
        ocr_verification_status="match",
        extracted_metadata={},
        source_section_ref="page-sef",
    )
    doc = _doc("mixed", children=[set_tev, sef_tev])
    set_block = aggregate_indicator([doc], "kra1-a-student")
    sef_block = aggregate_indicator([doc], "kra1-a-supervisor")
    assert set_block["coverageSummary"]["detectedEvaluationRecords"] == 1
    assert sef_block["coverageSummary"]["detectedEvaluationRecords"] == 1
    assert set_block["validatedPoints"] == 32.4
    assert sef_block["validatedPoints"] == 21.12


def test_duplicate_approved_records_excluded_with_conflict(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: _verified_config(),
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {})
    docs = [
        _doc("d1", children=[_tev("t1", "2024-2025", "1st Semester", "90/100")]),
        _doc("d2", children=[_tev("t2", "2024-2025", "1st Semester", "95/100")]),
    ]
    block = aggregate_indicator(docs, "kra1-a-student")
    assert block["coverageSummary"]["excludedDuplicateRecords"] == 1
    assert block["coverageSummary"]["uniqueEligibleSemesters"] == 1
    assert block["validatedPoints"] == 32.4
    assert any("already recorded" in (e.get("exclusionReason") or "").lower() for e in block["excludedPeriods"])
