"""PDF text-layer extraction (no Tesseract required)."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz
import pytest

from documents.ocr.pdf import ocr_pdf_file


def test_text_pdf_extracts_without_ocr(tmp_path: Path):
    path = tmp_path / "text.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "FacultyLink OCR unit test paragraph with enough selectable text for PDF extraction.",
    )
    doc.save(path)
    doc.close()

    result = ocr_pdf_file(path)
    assert result.method == "pdf_text"
    assert "FacultyLink" in result.text
    assert result.confidence is None


def test_password_protected_pdf(tmp_path: Path):
    path = tmp_path / "locked.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(path, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="secret")
    doc.close()

    from documents.ocr.result import OcrProcessingError

    with pytest.raises(OcrProcessingError) as exc:
        ocr_pdf_file(path)
    assert exc.value.code == "password_protected"


def test_corrupt_pdf(tmp_path: Path):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"not a pdf")

    from documents.ocr.result import OcrProcessingError

    with pytest.raises(OcrProcessingError):
        ocr_pdf_file(path)
