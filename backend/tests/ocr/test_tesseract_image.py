"""Image OCR integration (requires Tesseract)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from documents.ocr.config import refresh_tesseract_availability
from documents.ocr.images import ocr_image_file


@pytest.fixture(scope="module")
def tesseract_available() -> bool:
    return refresh_tesseract_availability().available


def _make_text_png(path: Path, text: str) -> None:
    img = Image.new("RGB", (400, 120), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 40), text, fill="black")
    img.save(path, format="PNG")


@pytest.mark.skipif(
    not refresh_tesseract_availability().available,
    reason="Tesseract not installed",
)
def test_png_ocr_reads_text(tmp_path: Path, tesseract_available: bool):
    path = tmp_path / "sample.png"
    _make_text_png(path, "Hello FacultyLink OCR")
    result = ocr_image_file(path, mime_type="image/png")
    assert "FacultyLink" in result.text or "Hello" in result.text
