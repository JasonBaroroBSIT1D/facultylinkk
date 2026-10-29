"""Tesseract availability and OCR limits (env-configurable)."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Optional

import pytesseract

_RUNTIME: Optional["OcrRuntimeStatus"] = None


@dataclass(frozen=True)
class OcrRuntimeStatus:
    available: bool
    tesseract_path: str | None
    tesseract_version: str | None
    message: str


def _resolve_tesseract_cmd() -> str | None:
    explicit = (os.getenv("TESSERACT_CMD") or "").strip()
    if explicit:
        return explicit
    found = shutil.which("tesseract")
    return found


def refresh_tesseract_availability() -> OcrRuntimeStatus:
    """Detect Tesseract; safe to call at startup (does not raise)."""
    global _RUNTIME
    cmd = _resolve_tesseract_cmd()
    if not cmd:
        _RUNTIME = OcrRuntimeStatus(
            available=False,
            tesseract_path=None,
            tesseract_version=None,
            message="Tesseract executable not found. Set TESSERACT_CMD or install Tesseract.",
        )
        return _RUNTIME
    pytesseract.pytesseract.tesseract_cmd = cmd
    try:
        version = pytesseract.get_tesseract_version()
        version_str = str(version)
    except Exception as exc:  # noqa: BLE001 — diagnostic only
        _RUNTIME = OcrRuntimeStatus(
            available=False,
            tesseract_path=cmd,
            tesseract_version=None,
            message=f"Tesseract at {cmd!r} could not be invoked: {exc}",
        )
        return _RUNTIME
    _RUNTIME = OcrRuntimeStatus(
        available=True,
        tesseract_path=cmd,
        tesseract_version=version_str,
        message="OK",
    )
    return _RUNTIME


def ocr_runtime_status() -> OcrRuntimeStatus:
    if _RUNTIME is None:
        return refresh_tesseract_availability()
    return _RUNTIME


def ocr_max_pdf_pages() -> int:
    return max(1, int(os.getenv("OCR_MAX_PDF_PAGES", "50")))


def ocr_pdf_render_dpi() -> int:
    return max(72, min(400, int(os.getenv("OCR_PDF_DPI", "200"))))


def ocr_page_text_min_chars() -> int:
    return max(10, int(os.getenv("OCR_PAGE_TEXT_MIN_CHARS", "40")))


def ocr_timeout_seconds() -> int:
    return max(10, int(os.getenv("OCR_TIMEOUT_SECONDS", "120")))


def ocr_excerpt_max_chars() -> int:
    return max(500, int(os.getenv("OCR_EXCERPT_MAX_CHARS", "12000")))


def ocr_max_attempts() -> int:
    return max(1, min(10, int(os.getenv("OCR_MAX_ATTEMPTS", "3"))))


def ocr_stale_processing_minutes() -> int:
    return max(5, int(os.getenv("OCR_STALE_PROCESSING_MINUTES", "20")))
