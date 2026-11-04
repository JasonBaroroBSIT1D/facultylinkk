"""Advisory OCR for Annex F/G/H contribution percentages."""

from documents.kra2_evidence.ocr_extraction import build_extraction_payload, extract_fields_for_indicator

ANNEX_F = """
FICTIONAL — FOR SYSTEM TESTING ONLY
Certificate of Contribution Form — Intellectual Property (Annex F)
Percentage of Contribution: 40%
Name of Faculty Member: Jason Baroro
"""


def test_annex_f_extracts_advisory_contribution_percent():
    fields = extract_fields_for_indicator(ANNEX_F, "kra2-b-patent-g-co")
    payload = build_extraction_payload(fields, indicator_id="kra2-b-patent-g-co")
    block = payload["fields"].get("declaredContributionPercent")
    assert block is not None
    assert block["value"] == "40"
    assert block["status"] in ("extracted", "partial")


def test_annex_f_does_not_invent_without_percent_line():
    text = "Certificate of Contribution Form (Annex F)\nName: Faculty\n"
    fields = extract_fields_for_indicator(text, "kra2-b-patent-g-co")
    assert "declaredContributionPercent" not in fields
