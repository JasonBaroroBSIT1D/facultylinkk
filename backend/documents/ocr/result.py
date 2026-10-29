"""OCR result types."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OcrResult:
    text: str
    confidence: float | None
    method: str
    page_count: int = 1
    warnings: list[str] = field(default_factory=list)


class OcrProcessingError(Exception):
    """User-safe OCR failure (no file paths in message)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
