"""Criterion A display metadata (no DB, formulas unchanged)."""

from documents.scoring.criterion_a_display import enrich_criterion_a_summary


def _block(prov=None, val=None, uploads=1, missing=None, note=""):
    return {
        "provisionalPoints": prov,
        "validatedPoints": val,
        "scoringNote": note,
        "missingPeriods": missing or [],
        "coverageSummary": {
            "totalUploads": uploads,
            "requiredPeriods": 6,
            "evidencedRatings": uploads,
        },
    }


def test_set_only_shows_incomplete_awaiting_sef():
    summary = enrich_criterion_a_summary(
        {
            "set": _block(prov=32.4),
            "sef": _block(uploads=0),
            "combinedProvisionalPoints": None,
            "combinedValidatedPoints": None,
        }
    )
    assert summary["estimatedPoints"] is None
    disp = summary["criterionADisplay"]
    assert disp["status"] == "incomplete_awaiting_sef"
    assert disp["set"]["estimatedPoints"] == 32.4
    assert disp["sef"]["state"] == "awaiting_evidence"


def test_both_components_yields_authoritative_estimate():
    summary = enrich_criterion_a_summary(
        {
            "set": _block(prov=32.4),
            "sef": _block(prov=21.12),
            "combinedProvisionalPoints": 53.52,
            "combinedValidatedPoints": None,
        }
    )
    assert summary["estimatedPoints"] == 53.52
    assert summary["criterionADisplay"]["status"] == "complete"


def test_not_computable_not_shown_as_zero():
    summary = enrich_criterion_a_summary(
        {
            "set": _block(uploads=2, note="Incomplete coverage"),
            "sef": _block(uploads=0),
            "combinedProvisionalPoints": None,
        }
    )
    assert summary["estimatedPoints"] is None
    assert summary["criterionADisplay"]["set"]["state"] == "not_computable"
    assert "Not yet computable" in summary["criterionADisplay"]["set"]["displayLabel"]
