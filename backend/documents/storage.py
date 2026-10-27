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
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)
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


def save_upload(file: FileStorage, faculty_profile_id: int) -> tuple[str, str, int, str]:
    if not file or not file.filename:
        raise ValueError("missing_file")
    raw = file.read()
    if not raw:
        raise ValueError("empty_file")
    if len(raw) > MAX_BYTES:
        raise ValueError("file_too_large")
    mime = (file.mimetype or "").split(";")[0].strip().lower()
    if mime not in ALLOWED_MIME:
        raise ValueError("unsupported_type")
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
