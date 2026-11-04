"""OCR for KRA II Criterion C — Acting Performance (kra2-c-acting)."""

from documents.kra2_evidence.ocr_extraction import (
    build_extraction_payload,
    extract_fields_for_indicator,
    merge_ocr_into_bundle,
)


def test_acting_performance_extracts_play_title_not_invention_fragment():
    text = """
    Proof of invitation/acceptance as actor
    Title of the Play: The Merchant of Summer
    Performer: Maria Santos
    Performance venue: Cultural Center of the Philippines
    Date of performance: 2025-03-15
    """
    fields = extract_fields_for_indicator(text, "kra2-c-acting")
    assert fields.get("outputTitle") == "The Merchant of Summer"
    assert "invention" not in (fields.get("outputTitle") or "").lower()
    assert fields.get("authorsLine")
    assert "registrationNumber" not in fields


def test_invention_fragment_rejected_as_title():
    text = """
    Name of invention / Title
    / invention
    Inventor: Someone
    """
    fields = extract_fields_for_indicator(text, "kra2-c-acting")
    assert "outputTitle" not in fields or "invention" not in fields.get("outputTitle", "").lower()


def test_merge_does_not_apply_registration_fields_to_criterion_c():
    bundle = {
        "indicatorId": "kra2-c-acting",
        "outputTitle": "",
    }
    extraction = build_extraction_payload(
        {"outputTitle": "Hamlet", "registrationNumber": "PH-999", "authorsLine": "J. Baroro"},
        indicator_id="kra2-c-acting",
    )
    merge_ocr_into_bundle(bundle, extraction)
    assert bundle.get("outputTitle") == "Hamlet"
    assert "registrationNumber" not in bundle
