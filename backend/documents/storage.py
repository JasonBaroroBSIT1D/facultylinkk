"""Secure private file storage for faculty evidence uploads."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

ALLOWED_MIME = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)
_EXT_TO_MIME = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_GENERIC_MIME = frozenset({"", "application/octet-stream", "binary/octet-stream"})
MAX_BYTES = 25 * 1024 * 1024


def upload_root() -> Path:
    return Path(current_app.config["UPLOAD_FOLDER"])


def faculty_dir(faculty_profile_id: int) -> Path:
    path = upload_root() / "faculty" / str(faculty_profile_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_stem(name: str) -> str:
    stem = secure_filename(name) or "document"
    stem = re.sub(r"[^a-zA-Z0-9._-]", "_", stem)
    return stem[:180]


def sniff_mime(raw: bytes) -> str | None:
    """Detect MIME from magic bytes (first bytes of file)."""
    if raw.startswith(b"%PDF"):
        return "application/pdf"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(raw) >= 3 and raw[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if raw.startswith(b"GIF87a") or raw.startswith(b"GIF89a"):
        return "image/gif"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    if raw.startswith(b"PK") and b"word/" in raw[:4096]:
        return DOCX_MIME
    return None


def resolve_upload_mime(raw: bytes, filename: str, declared_mime: str | None) -> str:
    """
    Determine a trusted MIME type for storage.

    Mobile and some browsers send application/octet-stream for PDFs; we accept
    allowed types when magic bytes (or PDF signature for .pdf) match.
    """
    declared = (declared_mime or "").split(";")[0].strip().lower()
    sniffed = sniff_mime(raw[:512] if len(raw) > 512 else raw)

    if sniffed:
        if sniffed not in ALLOWED_MIME:
            raise ValueError("unsupported_type")
        if declared in ALLOWED_MIME and declared != sniffed:
            raise ValueError("mime_content_mismatch")
        return sniffed

    if declared in ALLOWED_MIME:
        if declared == "application/pdf" and not raw.startswith(b"%PDF"):
            raise ValueError("invalid_pdf")
        if declared.startswith("image/"):
            raise ValueError("invalid_file_content")
        return declared

    if declared in _GENERIC_MIME:
        ext = Path(_safe_stem(filename or "")).suffix.lower()
        by_ext = _EXT_TO_MIME.get(ext)
        if by_ext == "application/pdf":
            if raw.startswith(b"%PDF"):
                return "application/pdf"
            raise ValueError("invalid_pdf")
        if by_ext == DOCX_MIME:
            if raw.startswith(b"PK"):
                return DOCX_MIME
            raise ValueError("invalid_file_content")
        if by_ext in ALLOWED_MIME:
            raise ValueError("invalid_file_content")

    raise ValueError("unsupported_type")


def save_upload(file: FileStorage, faculty_profile_id: int) -> tuple[str, str, int, str]:
    if not file or not file.filename:
        raise ValueError("missing_file")
    raw = file.read()
    if not raw:
        raise ValueError("empty_file")
    if len(raw) > MAX_BYTES:
        raise ValueError("file_too_large")
    mime = resolve_upload_mime(raw, file.filename or "", file.mimetype)
    digest = hashlib.sha256(raw).hexdigest()
    ext = Path(_safe_stem(file.filename)).suffix.lower()
    if not ext:
        ext = ".pdf" if mime == "application/pdf" else ".bin"
    token = uuid4().hex
    stored_name = f"{token}{ext}"
    dest = faculty_dir(faculty_profile_id) / stored_name
    dest.write_bytes(raw)
    relative = dest.relative_to(upload_root()).as_posix()
    return relative, digest, len(raw), mime


def resolve_path(relative_path: str) -> Path | None:
    if not relative_path:
        return None
    root = upload_root().resolve()
    candidate = (root / relative_path).resolve()
    if not str(candidate).startswith(str(root)):
        return None
    if not candidate.is_file():
        return None
    return candidate
