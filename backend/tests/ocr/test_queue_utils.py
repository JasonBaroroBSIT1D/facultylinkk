"""OCR status normalization."""

from documents.ocr.queue import normalize_ocr_status


def test_normalize_ocr_status():
    assert normalize_ocr_status("complete") == "completed"
    assert normalize_ocr_status("COMPLETED") == "completed"
    assert normalize_ocr_status("processing") == "processing"
    assert normalize_ocr_status("failed") == "failed"
    assert normalize_ocr_status(None) == "pending"
