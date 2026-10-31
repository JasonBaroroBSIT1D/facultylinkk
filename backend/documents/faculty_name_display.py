"""Faculty name resolution for documents and SET/SEF evaluation records (read-only)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import Document, DocumentTeachingEvaluation, FacultyProfile


def _normalize_name(value: str) -> str:
    text = re.sub(r"[^a-z0-9\s]", " ", (value or "").lower())
    return " ".join(text.split())


def names_match(extracted: str, profile_name: str) -> bool:
    a = _normalize_name(extracted)
    b = _normalize_name(profile_name)
    if not a or not b:
        return False
    if a == b:
        return True
    a_tokens = set(a.split())
    b_tokens = set(b.split())
    if len(a_tokens) >= 2 and len(b_tokens) >= 2:
        return a_tokens <= b_tokens or b_tokens <= a_tokens
    return False


def extracted_name_from_document(info: dict) -> str:
    for key in ("Faculty name on document", "Faculty name", "Extracted names", "Extracted author(s)"):
        raw = (info.get(key) or "").strip()
        if raw:
            return raw
    return ""


def account_owner_name(profile: FacultyProfile | None, doc: Document) -> str:
    owner = ""
    if profile and profile.user:
        owner = (profile.user.full_name or "").strip()
    fp = getattr(doc, "faculty_profile", None)
    if not owner and fp and getattr(fp, "user", None):
        owner = (fp.user.full_name or "").strip()
    return owner


def resolve_faculty_name_fields(
    *,
    owner: str,
    extracted_name: str,
    detected_on_doc: bool,
    extraction_status: str = "",
) -> dict:
    """Display fields only — never substitute the account profile name for OCR extraction."""
    from documents.document_ownership_verification import (
        LABELS,
        STATUS_MISMATCH,
        STATUS_NEEDS_REVIEW,
        STATUS_NOT_DETECTED,
        names_match_flexible,
    )

    status_raw = (extraction_status or "").strip().lower()
    ambiguous = status_raw == "ambiguous"
    faculty_name_on_document = extracted_name if detected_on_doc else None
    document_name_on_file = extracted_name if detected_on_doc else None

    if ambiguous and extracted_name:
        verification_status = STATUS_NEEDS_REVIEW
        faculty_name = "Not detected"
        faculty_name_source = "ambiguous"
        needs_verification = True
        faculty_name_note = (
            "Multiple possible faculty names appear on this document. "
            "Ownership requires manual review."
        )
    elif not detected_on_doc:
        verification_status = STATUS_NOT_DETECTED
        faculty_name = "Not detected"
        faculty_name_source = "not_detected"
        needs_verification = True
        faculty_name_note = (
            "The faculty name was not detected on this document. "
            "Your account name is not shown as if it were extracted from the PDF."
        )
    elif owner and not names_match_flexible(extracted_name, owner):
        verification_status = STATUS_MISMATCH
        faculty_name = extracted_name
        faculty_name_source = "document"
        needs_verification = True
        faculty_name_note = (
            f"The faculty name found in this document ({extracted_name}) does not match "
            f"your account ({owner}). Please check the uploaded document."
        )
    else:
        verification_status = "name_matched"
        faculty_name = extracted_name
        faculty_name_source = "document"
        needs_verification = False
        faculty_name_note = None

    return {
        "facultyName": faculty_name,
        "facultyNameOnDocument": faculty_name_on_document or "Not detected",
        "facultyNameSource": faculty_name_source,
        "facultyNameNote": faculty_name_note,
        "needsVerification": needs_verification,
        "documentNameOnFile": document_name_on_file,
        "accountOwnerName": owner or None,
        "uploadedBy": owner or None,
        "nameVerificationStatus": verification_status,
        "nameVerificationLabel": LABELS.get(verification_status, "Needs Manual Review"),
    }


def teaching_evaluation_faculty_fields(
    doc: Document,
    profile: FacultyProfile | None = None,
    *,
    tev: DocumentTeachingEvaluation | None = None,
) -> dict:
    """Faculty name display for one SET/SEF evaluation record (OCR metadata + profile fallback)."""
    info = dict(doc.extracted_info or {})
    owner = account_owner_name(profile, doc)

    extracted_name = ""
    from_record_meta = False
    if tev is not None:
        meta = dict(tev.extracted_metadata or {})
        raw = (meta.get("facultyName") or "").strip()
        if raw:
            extracted_name = raw
            from_record_meta = True

    if not extracted_name:
        extracted_name = extracted_name_from_document(info)
        extraction_status = (info.get("Faculty name extraction status") or "").strip().lower()
        if extraction_status == "not_detected":
            extracted_name = ""

    extraction_status = (info.get("Faculty name extraction status") or "").strip().lower()
    if from_record_meta:
        detected_on_doc = bool(extracted_name)
    else:
        detected_on_doc = bool(extracted_name) and extraction_status not in ("not_detected", "")

    return resolve_faculty_name_fields(
        owner=owner,
        extracted_name=extracted_name,
        detected_on_doc=detected_on_doc,
        extraction_status=extraction_status,
    )
