"""Backward-compatible re-exports — see ``ocr_extraction.py``."""

from documents.kra2_evidence.ocr_extraction import (  # noqa: F401
    OCR_EXTRACTION_KEY,
    ensure_publication_ocr_extraction,
    extract_fields_for_indicator,
    merge_ocr_into_bundle,
    ocr_text_from_document,
    parse_and_store_kra2_ocr,
)


def parse_publication_hints(text: str) -> dict[str, str]:
    return extract_fields_for_indicator(text, "kra2-a-journal-sole")
