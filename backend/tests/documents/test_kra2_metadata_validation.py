"""Metadata validation — reject OCR instruction text; persist draft on failed submit."""

from __future__ import annotations

from documents.kra2_evidence.ocr_extraction import extract_fields_for_indicator, is_metadata_label_value
from documents.kra2_evidence.validation import validate_kra2_bundle


def test_instruction_sentence_rejected_as_authors_line():
    sample = """
Title of performance
Hamlet
Performer
You can try reading again or enter the missing information below.
Performance venue
City Theater
Date of performance
May 1, 2025
"""
    fields = extract_fields_for_indicator(sample, "kra2-c-acting")
    assert "authorsLine" not in fields or not fields.get("authorsLine")
    assert is_metadata_label_value(
        "You can try reading again or enter the missing information below.",
        field_id="authorsLine",
    )


def test_bundle_validation_rejects_instruction_authors():
    bundle = {
        "indicatorId": "kra2-c-acting",
        "contribution": "not-applicable",
        "outputTitle": "Hamlet Guest Role",
        "authorsLine": "Please enter the performer name in the field below.",
        "outputVenue": "CCP",
        "publicationDate": "2025-03-15",
        "checklist": {
            "primary_output": {"documentId": "doc1", "status": "uploaded"},
            "program_documentation": {"documentId": "doc2", "status": "uploaded"},
            "media_documentation": {"documentId": "doc3", "status": "uploaded"},
            "role_certification": {"documentId": "doc4", "status": "uploaded"},
        },
    }
    v = validate_kra2_bundle(bundle, indicator_id="kra2-c-acting")
    assert v["readyForSubmission"] is False
    assert any("author" in b.lower() or "inventor" in b.lower() for b in v["submissionBlockers"])


def test_valid_title_passes_validation():
    bundle = {
        "indicatorId": "kra2-c-acting",
        "contribution": "not-applicable",
        "outputTitle": "wowow",
        "authorsLine": "Maria Santos",
        "outputVenue": "CCP",
        "publicationDate": "2025-03-15",
        "checklist": {
            "primary_output": {"documentId": "doc1", "status": "uploaded"},
            "program_documentation": {"documentId": "doc2", "status": "uploaded"},
            "media_documentation": {"documentId": "doc3", "status": "uploaded"},
            "role_certification": {"documentId": "doc4", "status": "uploaded"},
        },
    }
    v = validate_kra2_bundle(bundle, indicator_id="kra2-c-acting")
    assert v["readyForSubmission"] is True
