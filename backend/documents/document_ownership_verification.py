"""Document ownership verification from OCR-extracted faculty names (universal, rule-based)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from documents.faculty_name_display import (
    account_owner_name,
    extracted_name_from_document,
    names_match,
)

if TYPE_CHECKING:
    from models import Document, FacultyProfile

STATUS_MATCHED = "name_matched"
STATUS_MISMATCH = "name_mismatch"
STATUS_NOT_DETECTED = "name_not_detected"
STATUS_NEEDS_REVIEW = "needs_manual_review"

LABELS = {
    STATUS_MATCHED: "Name Matched",
    STATUS_MISMATCH: "Name Mismatch",
    STATUS_NOT_DETECTED: "Name Not Detected",
    STATUS_NEEDS_REVIEW: "Needs Manual Review",
}


def _normalize_name(value: str) -> str:
    text = re.sub(r"[^a-z0-9\s]", " ", (value or "").lower())
    return " ".join(text.split())


def name_variants(raw: str) -> set[str]:
    """Normalized variants for comma-style and reversed order names."""
    base = _normalize_name(raw)
    variants = {base} if base else set()
    text = (raw or "").strip()
    if "," in text:
        left, right = [p.strip() for p in text.split(",", 1)]
        if left and right:
            variants.add(_normalize_name(f"{right} {left}"))
    tokens = base.split()
    if len(tokens) >= 2:
        variants.add(_normalize_name(" ".join(reversed(tokens))))
    return {v for v in variants if v}


def names_match_flexible(extracted: str, profile_name: str) -> bool:
    if names_match(extracted, profile_name):
        return True
    a_vars = name_variants(extracted)
    b_vars = name_variants(profile_name)
    for a in a_vars:
        for b in b_vars:
            if a == b:
                return True
            a_tokens = set(a.split())
            b_tokens = set(b.split())
            if len(a_tokens) >= 2 and len(b_tokens) >= 2:
                if a_tokens <= b_tokens or b_tokens <= a_tokens:
                    return True
    return False


def _extraction_status(info: dict) -> str:
    return (info.get("Faculty name extraction status") or "").strip().lower()


def verify_document_ownership(
    doc: Document,
    profile: FacultyProfile | None = None,
) -> dict[str, Any]:
    """Determine ownership verification from stored OCR fields (no profile name as extract)."""
    info = dict(doc.extracted_info or {})
    owner = account_owner_name(profile, doc)
    extracted = extracted_name_from_document(info)
    status_raw = _extraction_status(info)
    ambiguous = status_raw == "ambiguous" or bool((info.get("Faculty name candidates") or "").strip())

    if ambiguous and extracted:
        return _result(
            STATUS_NEEDS_REVIEW,
            owner=owner,
            extracted=extracted,
            message=(
                "Multiple possible faculty names were detected on this document. "
                "A reviewer must confirm ownership before it can count toward scoring."
            ),
            scoring_eligible=False,
        )

    if status_raw == "not_detected" or not extracted:
        return _result(
            STATUS_NOT_DETECTED,
            owner=owner,
            extracted=None,
            message=(
                "The faculty name was not detected on this document. "
                "It is not assumed to belong to the uploading account until reviewed."
            ),
            scoring_eligible=False,
        )

    if owner and not names_match_flexible(extracted, owner):
        return _result(
            STATUS_MISMATCH,
            owner=owner,
            extracted=extracted,
            message=(
                f"The faculty name found in this document ({extracted}) does not match "
                f"the account owner ({owner}). Please check the uploaded document."
            ),
            scoring_eligible=False,
        )

    if owner and names_match_flexible(extracted, owner):
        return _result(
            STATUS_MATCHED,
            owner=owner,
            extracted=extracted,
            message="The faculty name on the document matches the authenticated account.",
            scoring_eligible=True,
        )

    return _result(
        STATUS_NEEDS_REVIEW,
        owner=owner,
        extracted=extracted,
        message="Ownership could not be confirmed automatically and requires review.",
        scoring_eligible=False,
    )


def _result(
    status: str,
    *,
    owner: str,
    extracted: str | None,
    message: str,
    scoring_eligible: bool,
) -> dict[str, Any]:
    return {
        "status": status,
        "statusLabel": LABELS[status],
        "uploadedBy": owner or None,
        "facultyNameOnDocument": extracted,
        "accountOwnerName": owner or None,
        "message": message,
        "scoringEligible": scoring_eligible,
        "needsVerification": status in (STATUS_MISMATCH, STATUS_NEEDS_REVIEW),
    }


def apply_ownership_to_extracted_info(doc: Document, profile: FacultyProfile | None = None) -> dict:
    """Persist verification summary on extracted_info (non-destructive merge)."""
    info = dict(doc.extracted_info or {})
    result = verify_document_ownership(doc, profile)
    info["Document ownership verification status"] = result["status"]
    info["Document ownership verification label"] = result["statusLabel"]
    info["Document ownership verification message"] = result["message"]
    info["Document ownership scoring eligible"] = result["scoringEligible"]
    if result.get("facultyNameOnDocument"):
        info["Faculty name on document"] = result["facultyNameOnDocument"]
    return info


def _legacy_without_ownership_ocr(info: dict) -> bool:
    """Uploaded before ownership OCR fields existed (preserve scoring for validated records)."""
    if info.get("Document ownership verification status"):
        return False
    status_raw = (info.get("Faculty name extraction status") or "").strip()
    if status_raw:
        return False
    if extracted_name_from_document(info):
        return False
    return True


def document_scoring_eligible(doc: Document, profile: FacultyProfile | None = None) -> bool:
    info = dict(doc.extracted_info or {})
    flag = info.get("Document ownership scoring eligible")
    if flag is False:
        return False
    if flag is True:
        return True
    if _legacy_without_ownership_ocr(info):
        return True
    return verify_document_ownership(doc, profile)["scoringEligible"]


def ownership_blocks_auto_validation(doc: Document, profile: FacultyProfile | None = None) -> bool:
    status = verify_document_ownership(doc, profile)["status"]
    return status != STATUS_MATCHED
