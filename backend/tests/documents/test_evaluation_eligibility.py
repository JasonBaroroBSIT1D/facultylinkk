"""Section 10 eligibility service (no PostgreSQL writes)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.evaluation_eligibility import (
    apply_eligibility_update,
    eligibility_for_scoring,
    normalize_store,
    reviewer_can_manage,
    _validate_body,
)
from documents.scoring.set_sef_aggregate import aggregate_indicator
from documents.scoring.section10 import resolve_divisor


def test_reviewer_can_manage_assignment():
    reviewer = SimpleNamespace(id=7, public_id="usr_r", full_name="Reviewer")
    profile = SimpleNamespace(reviewer_user_id=7, public_id="fac_x")
    assert reviewer_can_manage(reviewer, profile) is True
    profile.reviewer_user_id = 8
    assert reviewer_can_manage(reviewer, profile) is False


def test_verified_requires_evidence_attestation_and_summary():
    body = {
        "section10Code": "study_leave",
        "eligibleSemesterCount": 4,
        "justification": "Verified against HR study-leave memo.",
        "reviewerVerified": True,
        "evidenceOnFileAttested": False,
        "supportingEvidenceSummary": "Approved study leave 2024-2025 on file.",
    }
    _, err = _validate_body(body, verifying=True, clearing=False)
    assert err == "evidence_attestation_required"


def test_semester_count_alone_insufficient_without_verification_bundle():
    body = {
        "section10Code": "study_leave",
        "eligibleSemesterCount": 4,
        "justification": "Short",
        "reviewerVerified": True,
        "evidenceOnFileAttested": True,
        "supportingEvidenceSummary": "Leave papers on file.",
    }
    _, err = _validate_body(body, verifying=True, clearing=False)
    assert err == "justification_required"


def test_eligibility_for_scoring_requires_verified_and_attested():
    raw = {
        "current": {
            "section10Code": "study_leave",
            "eligibleSemesterCount": 4,
            "reviewerVerified": True,
            "evidenceOnFileAttested": True,
        }
    }
    scoring = eligibility_for_scoring(raw)
    assert scoring["reviewerVerified"] is True
    assert scoring["eligibleSemesterCount"] == 4
    raw["current"]["evidenceOnFileAttested"] = False
    scoring2 = eligibility_for_scoring(raw)
    assert scoring2["reviewerVerified"] is False


def test_scoring_recalculation_with_verified_section10(monkeypatch):
    raw = {
        "current": {
            "section10Code": "study_leave",
            "eligibleSemesterCount": 4,
            "reviewerVerified": True,
            "evidenceOnFileAttested": True,
        }
    }
    elig = eligibility_for_scoring(raw)
    cov = {"standardRequiredSemesters": 6}
    div = resolve_divisor(cov, elig)
    assert div.eligible_divisor == 4

    monkeypatch.setattr(
        "documents.scoring.set_sef_aggregate.indicator_scoring_config",
        lambda _ind: {
            "complete": True,
            "maxPoints": 36.0,
            "multiplier": 36.0,
            "ratingScale": 100.0,
            "aggregationMethod": "circular_jc_2026_semester_average",
            "roundingRule": "two_decimals",
            "evaluationCoverage": cov,
        },
    )
    monkeypatch.setattr("documents.scoring.set_sef_aggregate.published_settings_root", lambda: {"evaluationCoverage": cov})

    def doc(rating: str, ay: str, sem: str):
        return SimpleNamespace(
            public_id="d_" + ay + sem,
            file_name="f.pdf",
            indicator_id="kra1-a-student",
            status="approved",
            ocr_status="completed",
            submitted_at=None,
            extracted_info={
                "Academic year": ay,
                "Semester": sem + " Semester",
                "Extracted rating": rating,
            },
        )

    docs = [
        doc("90", "2023-2024", "1"),
        doc("88", "2023-2024", "2"),
        doc("92", "2024-2025", "1"),
        doc("91", "2024-2025", "2"),
    ]
    block = aggregate_indicator(docs, "kra1-a-student", faculty_eligibility=elig)
    assert block["provisionalPoints"] == 32.49
    assert block["eligibility"]["eligibleDivisor"] == 4


def test_apply_eligibility_update_audit(monkeypatch):
    reviewer = SimpleNamespace(id=1, public_id="usr_rev", full_name="Rev A")
    profile = SimpleNamespace(
        id=10,
        public_id="fac_test",
        reviewer_user_id=1,
        evaluation_eligibility_json=None,
    )
    commits = []

    def fake_commit():
        commits.append(1)

    monkeypatch.setattr("documents.evaluation_eligibility.db.session.commit", fake_commit)

    body = {
        "section10Code": "study_leave",
        "eligibleSemesterCount": 5,
        "justification": "Verified study leave documentation in HR folder.",
        "supportingEvidenceSummary": "Board-approved study leave SY 2024-2025 on file.",
        "evidenceOnFileAttested": True,
        "reviewerVerified": True,
    }
    apply_eligibility_update(reviewer, profile, body)
    store = normalize_store(profile.evaluation_eligibility_json)
    assert store["current"]["section10Code"] == "study_leave"
    assert len(store["auditLog"]) == 1
    assert store["auditLog"][0]["previous"] is None
    assert commits == [1]
