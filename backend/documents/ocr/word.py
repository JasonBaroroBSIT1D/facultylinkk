"""Extract plain text from .docx (Office Open XML) without external dependencies."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from documents.ocr.result import OcrProcessingError, OcrResult

_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _docx_text_from_bytes(raw: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if "word/document.xml" not in archive.namelist():
                raise OcrProcessingError("invalid_docx", "The Word document is missing document content.")
            xml_bytes = archive.read("word/document.xml")
    except zipfile.BadZipFile as exc:
        raise OcrProcessingError("invalid_docx", "The file is not a valid Word document.") from exc

    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise OcrProcessingError("invalid_docx", "The Word document could not be parsed.") from exc

    paragraphs: list[str] = []
    for para in root.iter(f"{_W_NS}p"):
        runs = []
        for node in para.iter(f"{_W_NS}t"):
            if node.text:
                runs.append(node.text)
        line = "".join(runs).strip()
        if line:
            paragraphs.append(line)
    text = "\n".join(paragraphs).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def extract_docx_file(path: Path) -> OcrResult:
    raw = path.read_bytes()
    if not raw.startswith(b"PK"):
        raise OcrProcessingError("invalid_docx", "The file is not a valid Word document.")
    text = _docx_text_from_bytes(raw)
    return OcrResult(
        text=text,
        confidence=None,
        method="docx_text",
        page_count=1,
        warnings=[] if text else ["No readable text was found in the Word document."],
    )
