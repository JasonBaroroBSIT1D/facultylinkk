"""PDF text extraction and page-level OCR for scanned PDFs."""

from __future__ import annotations

import io
from pathlib import Path

import pymupdf as fitz
from PIL import Image

from documents.ocr.config import (
    ocr_max_pdf_pages,
    ocr_page_text_min_chars,
    ocr_pdf_render_dpi,
    ocr_runtime_status,
)
from documents.ocr.images import mean_word_confidence, _preprocess
from documents.ocr.result import OcrProcessingError, OcrResult


def _page_needs_ocr(page: fitz.Page, min_chars: int) -> bool:
    text = (page.get_text("text") or "").strip()
    return len(text) < min_chars


def _ocr_pixmap(page: fitz.Page, dpi: int) -> tuple[str, float | None]:
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    processed = _preprocess(img)
    return mean_word_confidence(processed)


def ocr_pdf_file(path: Path) -> OcrResult:
    try:
        doc = fitz.open(path)
    except Exception as exc:  # noqa: BLE001
        raise OcrProcessingError("corrupt_pdf", "The PDF file could not be opened.") from exc
    if doc.is_encrypted or doc.needs_pass:
        doc.close()
        raise OcrProcessingError("password_protected", "Password-protected PDFs are not supported.")
    page_count = doc.page_count
    if page_count == 0:
        doc.close()
        raise OcrProcessingError("empty_pdf", "The PDF has no pages.")
    max_pages = ocr_max_pdf_pages()
    if page_count > max_pages:
        doc.close()
        raise OcrProcessingError(
            "too_many_pages",
            f"The PDF has {page_count} pages; the limit is {max_pages}.",
        )
    min_chars = ocr_page_text_min_chars()
    dpi = ocr_pdf_render_dpi()
    parts: list[str] = []
    confidences: list[float] = []
    methods: set[str] = set()
    warnings: list[str] = []
    limit = min(page_count, max_pages)
    if page_count > max_pages:
        warnings.append(f"Only the first {max_pages} pages were processed.")

    needs_ocr = False
    for index in range(limit):
        page = doc.load_page(index)
        if _page_needs_ocr(page, min_chars):
            needs_ocr = True
            break
    if needs_ocr:
        runtime = ocr_runtime_status()
        if not runtime.available:
            doc.close()
            raise OcrProcessingError("tesseract_unavailable", runtime.message)

    for index in range(limit):
        page = doc.load_page(index)
        direct = (page.get_text("text") or "").strip()
        if len(direct) >= min_chars:
            parts.append(direct)
            methods.add("pdf_text")
            continue
        ocr_text, conf = _ocr_pixmap(page, dpi)
        if ocr_text:
            parts.append(ocr_text)
            methods.add("tesseract_pdf_page")
            if conf is not None:
                confidences.append(conf)
        elif direct:
            parts.append(direct)
            methods.add("pdf_text_partial")

    doc.close()
    combined = "\n\n".join(p for p in parts if p).strip()
    if not combined:
        method = "tesseract_pdf" if "tesseract_pdf_page" in methods else "pdf_text"
        return OcrResult(text="", confidence=None, method=method, page_count=limit, warnings=warnings)

    if methods == {"pdf_text"}:
        method = "pdf_text"
    elif "pdf_text" in methods and "tesseract_pdf_page" in methods:
        method = "pdf_mixed"
    else:
        method = "tesseract_pdf"

    confidence = sum(confidences) / len(confidences) if confidences else None
    return OcrResult(
        text=combined,
        confidence=confidence,
        method=method,
        page_count=limit,
        warnings=warnings,
    )
