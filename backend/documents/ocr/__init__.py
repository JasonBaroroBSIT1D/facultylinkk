"""Tesseract OCR pipeline for faculty evidence documents."""

from documents.ocr.config import ocr_runtime_status, refresh_tesseract_availability

__all__ = ["ocr_runtime_status", "refresh_tesseract_availability"]
