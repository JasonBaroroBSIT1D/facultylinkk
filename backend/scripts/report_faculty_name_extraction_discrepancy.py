"""Read-only: stored extracted_info faculty name vs re-parse from OCR text (no writes)."""

from __future__ import annotations

import json
import sys

from config import Config
from factory import create_app
from models import Document

from documents.ocr.set_sef_metadata import (
    _clean_faculty_name_candidate,
    _resolve_document_faculty_name,
    parse_set_sef_metadata_multi,
)


def _stored_name(info: dict) -> str:
    for key in ("Faculty name on document", "Faculty name", "Extracted names"):
        val = (info.get(key) or "").strip()
        if val:
            return val
    return ""


def main() -> int:
    app = create_app(Config)
    with app.app_context():
        docs = Document.query.filter(
            Document.deleted_at.is_(None),
            Document.criterion_id == "kra1-a",
        ).all()
        rows = []
        for doc in docs:
            info = dict(doc.extracted_info or {})
            text = (doc.extracted_text or "").strip()
            if not text:
                continue
            multi = parse_set_sef_metadata_multi(text)
            expected = _resolve_document_faculty_name(text, multi)
            stored = _stored_name(info)
            stored_clean = _clean_faculty_name_candidate(stored) if stored else None
            if stored and not stored_clean:
                rows.append(
                    {
                        "documentId": doc.public_id,
                        "fileName": doc.file_name,
                        "storedFacultyName": stored,
                        "recomputedFacultyName": expected,
                        "issue": "stored_name_invalid_or_heading_token",
                    }
                )
            elif expected and stored_clean and stored_clean != expected:
                rows.append(
                    {
                        "documentId": doc.public_id,
                        "fileName": doc.file_name,
                        "storedFacultyName": stored_clean,
                        "recomputedFacultyName": expected,
                        "issue": "stored_name_differs_from_reparse",
                    }
                )
            elif not stored_clean and expected:
                rows.append(
                    {
                        "documentId": doc.public_id,
                        "fileName": doc.file_name,
                        "storedFacultyName": stored or None,
                        "recomputedFacultyName": expected,
                        "issue": "stored_name_missing_but_detectable",
                    }
                )
        print(
            json.dumps(
                {
                    "discrepancyCount": len(rows),
                    "note": (
                        "Read-only report. To refresh stored metadata, re-run OCR on the "
                        "document from Reviewer Web (explicit action) after deploying the fix."
                    ),
                    "documents": rows,
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
