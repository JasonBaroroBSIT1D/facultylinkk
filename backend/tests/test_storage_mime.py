"""Upload MIME resolution (PDF octet-stream from mobile clients)."""

from __future__ import annotations

import io

import pytest
from werkzeug.datastructures import FileStorage

from documents.storage import resolve_upload_mime, save_upload, sniff_mime


def test_sniff_pdf():
    assert sniff_mime(b"%PDF-1.4\n") == "application/pdf"


def test_resolve_octet_stream_pdf_by_magic():
    raw = b"%PDF-1.7 test content"
    mime = resolve_upload_mime(raw, "report.PDF", "application/octet-stream")
    assert mime == "application/pdf"


def test_resolve_empty_mime_pdf():
    raw = b"%PDF-1.4"
    assert resolve_upload_mime(raw, "doc.pdf", None) == "application/pdf"


def test_reject_fake_pdf_extension():
    with pytest.raises(ValueError, match="invalid_pdf"):
        resolve_upload_mime(b"not a pdf", "fake.pdf", "application/octet-stream")


def test_accept_docx_by_extension_and_zip_signature():
    raw = b"PK\x03\x04" + b"\x00" * 20
    mime = resolve_upload_mime(raw, "notes.docx", "application/octet-stream")
    assert mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_declared_pdf_must_match_signature():
    with pytest.raises(ValueError, match="invalid_pdf"):
        resolve_upload_mime(b"not pdf", "x.pdf", "application/pdf")


def test_png_sniff():
    header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    assert resolve_upload_mime(header, "scan.png", "application/octet-stream") == "image/png"


def test_save_upload_accepts_octet_stream_pdf(app, tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", tmp_path)
    raw = b"%PDF-1.4\n% minimal"
    storage = FileStorage(
        stream=io.BytesIO(raw),
        filename="evidence.pdf",
        content_type="application/octet-stream",
    )
    with app.app_context():
        rel, digest, size, mime = save_upload(storage, faculty_profile_id=1)
    assert mime == "application/pdf"
    assert size == len(raw)
    assert digest
