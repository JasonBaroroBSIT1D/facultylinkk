"""Assess whether a SET/SEF document qualifies for simulation auto-acceptance."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from models import Document

from documents.ocr.set_sef_metadata import is_set_sef_indicator
from documents.scoring.set_sef_aggregate import parse_rating_percent
from documents.set_sef_auto_approval.policy import POLICY_VERSION
from documents.storage import resolve_path


def _ocr_completed(raw: str | None) -> bool:
    value = (raw or "pending").strip().lower()
    return value in ("completed", "complete", "done", "success")


_YEAR_RE = re.compile(r"^20\d{2}-20\d{2}$")
_HUMAN_REVIEW_ACTIONS = frozenset(
    {"approve", "reject", "revision", "reopen", "hold", "correct_metadata", "metadata_correction"}
)


@dataclass
class CheckResult:
    ok: bool
    message: str


@dataclass
class AutoApprovalAssessment:
    eligible: bool
    checks: dict[str, CheckResult] = field(default_factory=dict)
    withheld_reasons: list[str] = field(default_factory=list)
    policy_version: str = POLICY_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "policyVersion": self.policy_version,
            "eligible": self.eligible,
            "checks": {key: {"ok": c.ok, "message": c.message} for key, c in self.checks.items()},
            "withheldReasons": self.withheld_reasons,
        }


def _normalize_name(value: str) -> str:
    text = re.sub(r"[^a-z0-9\s]", " ", (value or "").lower())
    return " ".join(text.split())


def _names_match(extracted: str, profile_name: str) -> bool:
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


def _period_key(info: dict) -> tuple[str, str]:
    return ((info.get("Academic year") or "").strip(), (info.get("Semester") or "").strip())


def _has_manual_review_history(info: dict) -> bool:
    for entry in info.get("reviewHistory") or []:
        if not isinstance(entry, dict):
            continue
        action = (entry.get("action") or "").strip().lower()
        actor_id = entry.get("actorId")
        if action in _HUMAN_REVIEW_ACTIONS and actor_id:
            return True
    if info.get("Reviewer correction log"):
        return True
    if (info.get("Validation status") or "").strip().lower() in (
        "needs verification",
        "manual review",
        "on hold",
    ):
        return True
    if (info.get("Reviewer oversight status") or "").strip():
        return True
    return False


def _find_period_conflicts(doc: Document, info: dict) -> str | None:
    from documents.service import _active_docs_query

    year, sem = _period_key(info)
    if not year or not sem:
        return None
    others = (
        _active_docs_query()
        .filter(
            Document.faculty_profile_id == doc.faculty_profile_id,
            Document.indicator_id == doc.indicator_id,
            Document.id != doc.id,
        )
        .all()
    )
    for other in others:
        oinfo = other.extracted_info or {}
        if _period_key(oinfo) != (year, sem):
            continue
        if other.file_hash and doc.file_hash and other.file_hash == doc.file_hash:
            return "An identical file is already on record for this faculty and indicator."
        if other.status in ("approved", "valid", "pending_review", "reviewer_required"):
            return (
                f"Another document already covers {year} · {sem} for this indicator "
                f"({other.public_id})."
            )
    return None


def assess_document(doc: Document) -> AutoApprovalAssessment:
    checks: dict[str, CheckResult] = {}
    reasons: list[str] = []

    def fail(check_id: str, message: str) -> None:
        checks[check_id] = CheckResult(False, message)
        reasons.append(message)

    def pass_(check_id: str, message: str) -> None:
        checks[check_id] = CheckResult(True, message)

    if not is_set_sef_indicator(doc.indicator_id):
        fail("scope", "Automatic acceptance applies only to SET/SEF indicators.")
        return AutoApprovalAssessment(eligible=False, checks=checks, withheld_reasons=reasons)

    info = dict(doc.extracted_info or {})
    prior = info.get("autoValidation") if isinstance(info.get("autoValidation"), dict) else {}
    if prior.get("decisionSource") == "system_auto_approval" and doc.status in ("approved", "valid"):
        pass_("already_decided", "Document was already auto-accepted for simulation.")
        return AutoApprovalAssessment(
            eligible=False, checks=checks, withheld_reasons=["Already auto-accepted for simulation."]
        )

    if doc.status in ("rejected", "needs_revision"):
        fail("prior_decision", f"Document status is {doc.status}; manual review required.")
    elif doc.status in ("approved", "valid") and prior.get("decisionSource") != "system_auto_approval":
        fail("prior_decision", "Document already has a reviewer decision.")

    if _has_manual_review_history(info):
        fail("manual_history", "Manual review required: reviewer hold, rejection, or correction on record.")

    if not _ocr_completed(doc.ocr_status):
        fail("ocr_complete", "OCR processing has not completed successfully.")
    else:
        pass_("ocr_complete", "OCR processing completed.")

    metadata_issues: list[str] = []
    verification = (info.get("Indicator verification status") or "").strip().upper()
    if verification != "MATCH":
        metadata_issues.append(
            f"Selected indicator does not match extracted evaluation type ({verification or 'missing'})."
        )

    required = [
        "Faculty name",
        "Evaluation type",
        "Academic year",
        "Semester",
        "Extracted rating",
        "Rating scale",
    ]
    missing = [key for key in required if not (info.get(key) or "").strip()]
    if missing:
        metadata_issues.append(f"Metadata incomplete: {', '.join(missing)}.")

    profile = doc.faculty_profile
    profile_name = profile.user.full_name if profile and profile.user else ""
    extracted_name = (info.get("Faculty name") or "").strip()
    if extracted_name and profile_name and not _names_match(extracted_name, profile_name):
        metadata_issues.append("Faculty identity does not match the document owner's profile.")

    kind = (info.get("Detected evaluation kind") or "").strip().upper()
    if doc.indicator_id == "kra1-a-student" and kind != "SET":
        metadata_issues.append("Detected evaluation type does not match SET indicator.")
    elif doc.indicator_id == "kra1-a-supervisor" and kind != "SEF":
        metadata_issues.append("Detected evaluation type does not match SEF indicator.")

    scale_raw = info.get("Rating scale")
    try:
        scale = float(scale_raw) if scale_raw is not None else 100.0
    except (TypeError, ValueError):
        scale = 100.0
    rating_pct, scale_used = parse_rating_percent(info.get("Extracted rating"), default_scale=scale)
    ambiguous_fields = (info.get("Ambiguous extraction fields") or "").strip()
    rating_ambiguous = "rating" in ambiguous_fields.lower() or "extracted rating" in ambiguous_fields.lower()
    if rating_pct is None or rating_pct <= 0 or rating_pct > 100:
        metadata_issues.append("Rating ambiguous or outside the stated scale.")
    elif rating_ambiguous:
        metadata_issues.append("Rating marked ambiguous in extraction.")

    if metadata_issues:
        fail("metadata_validation", metadata_issues[0] if len(metadata_issues) == 1 else "; ".join(metadata_issues))
    else:
        pass_(
            "metadata_validation",
            f"Metadata complete: indicator MATCH, identity, type, and rating ({rating_pct}% on scale {scale_used:g}).",
        )

    period_issues: list[str] = []
    year = (info.get("Academic year") or "").strip()
    sem = (info.get("Semester") or "").strip()
    if not _YEAR_RE.match(year):
        period_issues.append("Evaluation-period eligibility: academic year format is invalid.")
    elif sem not in ("1st Semester", "2nd Semester"):
        period_issues.append("Evaluation-period eligibility: semester must be 1st or 2nd Semester.")

    dup_msg = None
    if doc.file_hash:
        from documents.service import _active_docs_query

        twin = (
            _active_docs_query()
            .filter_by(
                faculty_profile_id=doc.faculty_profile_id,
                indicator_id=doc.indicator_id,
                file_hash=doc.file_hash,
            )
            .filter(Document.id != doc.id)
            .first()
        )
        if twin:
            dup_msg = "Duplicate file for the same faculty and indicator."
    conflict = _find_period_conflicts(doc, info)
    if dup_msg:
        period_issues.append(dup_msg)
    elif conflict:
        period_issues.append(conflict)

    if period_issues:
        fail("evaluation_period_eligibility", period_issues[0] if len(period_issues) == 1 else "; ".join(period_issues))
    elif year and sem:
        pass_("evaluation_period_eligibility", f"Evaluation period {year} · {sem} is eligible with no conflicts.")
    else:
        pass_("evaluation_period_eligibility", "Evaluation period checks deferred until metadata is complete.")

    extraction_status = (info.get("SET/SEF extraction status") or "").strip().lower()
    ocr_warnings = (info.get("OCR warnings") or "").strip()
    quality_notes: list[str] = []
    quality_failures: list[str] = []

    if extraction_status != "complete":
        quality_failures.append("Extraction incomplete.")
    if ambiguous_fields:
        quality_failures.append(f"Ambiguous extracted values ({ambiguous_fields}).")
    if ocr_warnings:
        quality_failures.append(f"OCR reported warnings ({ocr_warnings}).")

    confidence = doc.ocr_confidence
    if confidence is not None and confidence < 65.0 and not quality_failures:
        quality_notes.append(
            f"OCR confidence is low ({confidence:.1f}%); accepted for simulation based on validated field text only."
        )
    elif confidence is not None and not quality_failures:
        quality_notes.append(f"OCR confidence {confidence:.1f}%.")
    elif confidence is None and not quality_failures:
        quality_notes.append("OCR confidence unavailable; field-level validation used for simulation.")

    if quality_failures:
        msg = quality_failures[0] if len(quality_failures) == 1 else "; ".join(quality_failures)
        if "ambiguous" in msg.lower():
            fail("ocr_extraction_quality", f"Manual review required: {msg}")
        elif "incomplete" in msg.lower():
            fail("ocr_extraction_quality", f"Metadata incomplete: {msg}")
        else:
            fail("ocr_extraction_quality", f"Manual review required: {msg}")
    else:
        note = quality_notes[0] if quality_notes else "Extraction quality sufficient for simulation."
        pass_("ocr_extraction_quality", note)

    if not doc.file_path or not resolve_path(doc.file_path):
        fail("file_accessible", "Original file is missing or not accessible.")
    else:
        pass_("file_accessible", "Original PDF is stored for reviewer inspection.")

    eligible = not reasons
    return AutoApprovalAssessment(eligible=eligible, checks=checks, withheld_reasons=reasons)
