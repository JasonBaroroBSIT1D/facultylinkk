"""KRA II OCR metadata extraction and bundle merge."""

from types import SimpleNamespace

from documents.kra2_evidence.bundle import build_initial_bundle
from documents.kra2_evidence.ocr_extraction import (
    OCR_EXTRACTION_VERSION,
    author_match_flags,
    build_extraction_payload,
    extract_fields_for_indicator,
    merge_ocr_into_bundle,
    ocr_text_from_document,
    parse_and_store_kra2_ocr,
    validate_extracted_field,
)


def test_ocr_text_reads_extracted_text_not_legacy_ocr_block():
    doc = SimpleNamespace(
        extracted_text="Full paper body with DOI 10.1234/example.2024",
        extracted_info={"ocr": {"text": "wrong"}},
    )
    assert "Full paper" in ocr_text_from_document(doc)


def test_journal_extraction_parses_title_authors_doi():
    text = """
Title: Machine Learning for Agriculture
Authors: Jason Baroro, Maria Santos
Journal of Applied Research
Published: March 15, 2024
DOI: 10.1234/jar.2024.001
"""
    fields = extract_fields_for_indicator(text, "kra2-a-journal-sole")
    assert "Machine Learning" in fields["outputTitle"]
    assert "Jason Baroro" in fields["authorsLine"]
    assert "10.1234" in fields["publicationReference"]
    assert fields.get("publicationDate")


def test_merge_replaces_indicator_placeholder_title():
    bundle = build_initial_bundle(
        primary_document_id="doc-1",
        primary_file_hash="hash",
        indicator_id="kra2-a-journal-sole",
        output_title="Sole author of a journal article",
    )
    extraction = {
        "fields": {
            "outputTitle": {"value": "Real Article Title", "status": "extracted", "source": "ocr"},
            "authorsLine": {"value": "Jason Baroro", "status": "extracted", "source": "ocr"},
        }
    }
    merge_ocr_into_bundle(bundle, extraction)
    assert bundle["outputTitle"] == "Real Article Title"
    assert bundle["authorsLine"] == "Jason Baroro"


def test_merge_respects_metadata_confirmed():
    bundle = build_initial_bundle(
        primary_document_id="doc-1",
        primary_file_hash="hash",
        indicator_id="kra2-a-journal-sole",
        output_title="Faculty edited title",
    )
    bundle["metadataConfirmed"] = {"outputTitle": True}
    extraction = {
        "fields": {
            "outputTitle": {"value": "OCR title", "status": "extracted", "source": "ocr"},
        }
    }
    merge_ocr_into_bundle(bundle, extraction)
    assert bundle["outputTitle"] == "Faculty edited title"


def test_parse_and_store_on_completed_document():
    doc = SimpleNamespace(
        indicator_id="kra2-a-journal-sole",
        ocr_status="completed",
        extracted_text="Title: Sample\nAuthors: Jason Baroro\n2024",
        extracted_info={},
    )
    payload = parse_and_store_kra2_ocr(doc, force=True)
    assert payload is not None
    assert payload["fields"]["authorsLine"]["value"] == "Jason Baroro"


def test_author_match_flags_when_faculty_missing():
    flags = author_match_flags(authors_line="Maria Santos", faculty_display_name="Jason Baroro")
    assert "logged_in_faculty_not_detected_in_authors" in flags


def test_author_match_flags_when_faculty_present():
    flags = author_match_flags(
        authors_line="Jason Baroro and Maria Santos",
        faculty_display_name="Jason Baroro",
    )
    assert flags == []


def test_validate_rejects_publication_as_patent_number():
    val, status = validate_extracted_field(
        "registrationNumber", "publication", "kra2-b-patent-p-sole"
    )
    assert val is None
    assert status == "rejected"


def test_patent_application_acknowledgement_extraction():
    text = """
Patent application acknowledgement

Invention title
Sample Innovation Device 01

Inventor(s)
Jason Baroro; Jamie Cruz

Registration / application no.
FAKE-IP-2025-00001

Filing / event date
2025-02-12

Issuing organization
Fictional Intellectual Property Office (NOT REAL)
"""
    fields = extract_fields_for_indicator(text, "kra2-b-patent-a-sole")
    payload = build_extraction_payload(fields, indicator_id="kra2-b-patent-a-sole")
    assert payload["fields"]["outputTitle"]["value"] == "Sample Innovation Device 01"
    assert payload["fields"]["authorsLine"]["value"] == "Jason Baroro; Jamie Cruz"
    assert payload["fields"]["registrationNumber"]["value"] == "FAKE-IP-2025-00001"
    assert payload["fields"]["registrationDate"]["value"] == "2025-02-12"
    assert "Fictional Intellectual Property" in payload["fields"]["outputVenue"]["value"]


def test_patent_publication_notice_extraction():
    text = """
REPUBLIC OF THE PHILIPPINES
Intellectual Property Office of the Philippines
PATENT PUBLICATION NOTICE

Application No.: 1-2025-0001234
Publication No.: 2-2025-0005678

Title of Invention: Smart Irrigation Controller Using IoT Sensors

Inventor/s: Jason Baroro, Maria Santos

Date of Publication: November 15, 2025
"""
    fields = extract_fields_for_indicator(text, "kra2-b-patent-p-sole")
    payload = build_extraction_payload(fields, indicator_id="kra2-b-patent-p-sole")
    assert payload["version"] == OCR_EXTRACTION_VERSION
    assert payload["fields"]["registrationNumber"]["value"] == "2-2025-0005678"
    assert "Jason Baroro" in payload["fields"]["authorsLine"]["value"]
    assert "Smart Irrigation" in payload["fields"]["outputTitle"]["value"]
    assert payload["fields"]["registrationDate"]["status"] == "extracted"
    assert "November" in payload["fields"]["registrationDate"]["value"]


def test_patent_notice_title_only_does_not_fake_registration():
    text = """
Patent Publication Notice
Republic of the Philippines
2025
"""
    fields = extract_fields_for_indicator(text, "kra2-b-patent-p-sole")
    payload = build_extraction_payload(fields, indicator_id="kra2-b-patent-p-sole")
    assert "registrationNumber" not in payload["fields"]
    reg_date = payload["fields"].get("registrationDate")
    if reg_date:
        assert reg_date["status"] == "partial"
        assert reg_date["value"] == "2025"


def test_merge_replaces_invalid_registration_number_from_earlier_ocr():
    bundle = build_initial_bundle(
        primary_document_id="doc-1",
        primary_file_hash="hash",
        indicator_id="kra2-b-patent-p-sole",
        output_title="Invention patent — Publication (sole inventor)",
    )
    bundle["registrationNumber"] = "publication"
    extraction = {
        "fields": {
            "registrationNumber": {
                "value": "2-2025-0005678",
                "status": "extracted",
                "source": "ocr",
            },
        }
    }
    merge_ocr_into_bundle(bundle, extraction)
    assert bundle["registrationNumber"] == "2-2025-0005678"


def test_merge_skips_rejected_ocr_blocks():
    bundle = build_initial_bundle(
        primary_document_id="doc-1",
        primary_file_hash="hash",
        indicator_id="kra2-b-patent-p-sole",
        output_title="Invention patent — Publication (sole inventor)",
    )
    extraction = {
        "fields": {
            "registrationNumber": {"value": "publication", "status": "rejected", "source": "ocr"},
            "authorsLine": {"value": "Jason Baroro", "status": "extracted", "source": "ocr"},
        }
    }
    merge_ocr_into_bundle(bundle, extraction)
    assert bundle.get("registrationNumber") in (None, "")
    assert bundle["authorsLine"] == "Jason Baroro"
