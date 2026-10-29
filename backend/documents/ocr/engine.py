"""Route stored uploads to image or PDF OCR handlers."""

from __future__ import annotations

from pathlib import Path

from documents.ocr.images import ocr_image_file
from documents.ocr.pdf import ocr_pdf_file
from documents.ocr.result import OcrProcessingError, OcrResult
from documents.ocr.word import extract_docx_file

IMAGE_MIME = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def run_ocr_on_file(*, path: Path, mime_type: str) -> OcrResult:
    mime = (mime_type or "").split(";")[0].strip().lower()
    if mime == "application/pdf":
        return ocr_pdf_file(path)
    if mime == DOCX_MIME:
        return extract_docx_file(path)
    if mime in IMAGE_MIME:
        return ocr_image_file(path, mime_type=mime)
    raise OcrProcessingError("unsupported_type", "This file type is not supported for OCR.")
