"""Image loading and Tesseract OCR for raster uploads."""

from __future__ import annotations

import io
from pathlib import Path

import pytesseract
from PIL import Image, ImageEnhance, ImageOps

from documents.ocr.config import ocr_runtime_status
from documents.ocr.result import OcrProcessingError, OcrResult


def _open_image_bytes(raw: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(raw))
    except Exception as exc:  # noqa: BLE001
        raise OcrProcessingError("corrupt_image", "The image file could not be read.") from exc
    if getattr(img, "is_animated", False):
        img.seek(0)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return img


def _preprocess(img: Image.Image) -> Image.Image:
    gray = img.convert("L")
    return ImageEnhance.Contrast(gray).enhance(1.15)


def mean_word_confidence(img: Image.Image) -> tuple[str, float | None]:
    """
    Run Tesseract and return (text, mean confidence).

    Confidence is the mean of per-word confidences from image_to_data where conf > 0.
    Invalid Tesseract conf values (-1) are ignored. Returns None if no valid words.
    """
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    texts: list[str] = []
    confs: list[float] = []
    n = len(data.get("text") or [])
    for i in range(n):
        word = (data["text"][i] or "").strip()
        if not word:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            continue
        if conf <= 0:
            continue
        texts.append(word)
        confs.append(conf)
    body = " ".join(texts).strip()
    if not confs:
        plain = pytesseract.image_to_string(img).strip()
        return plain, None
    return body, sum(confs) / len(confs)


def ocr_image_file(path: Path, *, mime_type: str) -> OcrResult:
    runtime = ocr_runtime_status()
    if not runtime.available:
        raise OcrProcessingError("tesseract_unavailable", runtime.message)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise OcrProcessingError("read_failed", "The uploaded file could not be read.") from exc
    if not raw:
        raise OcrProcessingError("empty_file", "The file is empty.")
    img = _open_image_bytes(raw)
    processed = _preprocess(img)
    text, confidence = mean_word_confidence(processed)
    warnings: list[str] = []
    if mime_type == "image/gif":
        warnings.append("Animated GIF: only the first frame was processed.")
    return OcrResult(
        text=text,
        confidence=confidence,
        method="tesseract_image",
        page_count=1,
        warnings=warnings,
    )
