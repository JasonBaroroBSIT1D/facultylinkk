"""Word (.docx) text extraction."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from documents.ocr.word import extract_docx_file

DOCX_XML = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Student Evaluation of Teaching</w:t></w:r></w:p>
    <w:p><w:r><w:t>Faculty: Test Faculty</w:t></w:r></w:p>
  </w:body>
</w:document>"""


def _minimal_docx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", DOCX_XML)
    return buf.getvalue()


def test_extract_docx_file(tmp_path: Path):
    path = tmp_path / "sample.docx"
    path.write_bytes(_minimal_docx_bytes())
    result = extract_docx_file(path)
    assert "Student Evaluation of Teaching" in result.text
    assert result.method == "docx_text"
    assert result.confidence is None
