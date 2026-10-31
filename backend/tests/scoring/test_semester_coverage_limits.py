"""Six-semester SET/SEF coverage caps and duplicate exclusion (no database)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.scoring.set_sef_aggregate import aggregate_indicator


def _config(divisor: int = 6):
    return {
        "complete": True,
        "maxPoints": 36.0,
        "multiplier": 36.0,
        "ratingScale": 100.0,
        "aggregationMethod": "circular_jc_2026_semester_average",
        "roundingRule": "two_decimals",
        "evaluationCoverage": {"standardRequiredSemesters": divisor},
    }


def _tev(
    public_id: str,
    ay: str,
    sem: str,
    rating: str,
    *,
    indicator: str = "kra1-a-student",
    etype: str = "SET",
    status: str = "approved",
):
    pct = float(rating.split("/")[0])
    return SimpleNamespace(
        public_id=public_id,
        indicator_id=indicator,
        evaluation_type=etype,
        academic_year=ay,
        semester=sem,
        rating_raw=rating,
        rating_scale=100.0,
        rating_percent=pct,
        reviewer_validation_status=status,
        ocr_verification_status="match",
        extracted_metadata={},
        source_section_ref=public_id,
    )


def _doc(public_id: str, children: list):
    return SimpleNamespace(
        public_id=public_id,
        file_name=f"{public_id}.pdf",
        indicator_id="kra1-a-teaching-evidence",
        status="approved",
        ocr_status="completed",
        submitted_at=None,
        extracted_info={},
        teaching_evaluations=children,
    )


def _six_periods(prefix: str, *, indicator: str, etype: str):
    pairs = [
        ("2021-2022", "1st Semester"),
        ("2021-2022", "2nd Semester"),
        ("2022-2023", "1st Semester"),
        ("2022-2023", "2nd Semester"),
        ("2023-2024", "1st Semester"),
        ("2023-2024", "2nd Semester"),
    ]
    return [
        _tev(f"{prefix}-{i}", ay, sem, "90/100", indicator=indicator, etype=etype)
        for i, (ay, sem) in enumerate(pairs)
    ]


def test_six_individual_plus_combined_pdf_counts_six_unique_set(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: _config(6),
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {})

    individual = [_doc(f"set-{i}", [_tev(f"t{i}", ay, sem, "90/100")]) for i, (ay, sem) in enumerate([
        ("2021-2022", "1st Semester"),
        ("2021-2022", "2nd Semester"),
        ("2022-2023", "1st Semester"),
        ("2022-2023", "2nd Semester"),
        ("2023-2024", "1st Semester"),
        ("2023-2024", "2nd Semester"),
    ])]
    combined = _doc("combined", _six_periods("dup", indicator="kra1-a-student", etype="SET"))
    block = aggregate_indicator(individual + [combined], "kra1-a-student")

    cov = block["coverageSummary"]
    assert cov["uniqueEligibleSemesters"] == 6
    assert cov["excludedDuplicateRecords"] >= 6
    assert block["provisionalPoints"] is not None
    assert len(block["ratingsUsed"]) == 6


def test_duplicate_approved_keeps_one_for_scoring(monkeypatch):
    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: _config(1),
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {})
    docs = [
        _doc("d1", [_tev("t1", "2024-2025", "1st Semester", "90/100")]),
        _doc("d2", [_tev("t2", "2024-2025", "1st Semester", "95/100")]),
    ]
    block = aggregate_indicator(docs, "kra1-a-student")
    assert block["coverageSummary"]["uniqueEligibleSemesters"] == 1
    assert block["validatedPoints"] == 32.4
    assert block["coverageSummary"]["excludedDuplicateRecords"] == 1
