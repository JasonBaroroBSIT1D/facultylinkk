"""Apply SET/SEF automatic approval after OCR (policy-gated)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from extensions import db
from models import AuditLog, Document, DocumentOcrJob

from documents.set_sef_auto_approval.assess import AutoApprovalAssessment, assess_document
from documents.set_sef_auto_approval.policy import POLICY_VERSION, is_auto_approval_active
from documents.ocr.set_sef_metadata import is_set_sef_indicator


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_system_auto_approval_history(doc: Document, *, remarks: str) -> None:
    info = dict(doc.extracted_info or {})
    history = list(info.get("reviewHistory") or [])
    history.append(
        {
            "at": _utcnow_iso(),
            "actorId": None,
            "actorName": "System (simulation auto-accept)",
            "action": "auto_approve",
            "remarks": remarks,
            "status": "approved",
            "decisionSource": "system_auto_approval",
        }
    )
    info["reviewHistory"] = history[-50:]
    info["Approval decision source"] = "system_auto_approval"
    doc.extracted_info = info


def record_auto_approval_audit(doc: Document, assessment_dict: dict, *, previous_status: str) -> None:
    detail = {
        "documentId": doc.public_id,
        "facultyId": doc.faculty_profile.public_id if doc.faculty_profile else None,
        "indicatorId": doc.indicator_id,
        "previousStatus": previous_status,
        "newStatus": doc.status,
        "decisionSource": "system_auto_approval",
        "policyVersion": POLICY_VERSION,
        "validation": assessment_dict,
        "timestamp": _utcnow_iso(),
        "explanation": (
            "Auto-accepted for FacultyLink simulation: SET/SEF evaluation checks passed. "
            "Not official document authentication or institutional certification."
        ),
    }
    db.session.add(
        AuditLog(
            actor_user_id=None,
            action="SET/SEF simulation auto-accept",
            target_id=doc.public_id,
            detail=json.dumps(detail, ensure_ascii=False)[:8000],
        )
    )


def maybe_auto_approve_after_ocr(doc: Document, job: DocumentOcrJob | None = None) -> None:
    """Run after OCR success. Always stores assessment; approves only when policy is active."""
    if not is_set_sef_indicator(doc.indicator_id):
        return

    locked = db.session.get(Document, doc.id, with_for_update=True)
    if not locked:
        return
    doc = locked

    info = dict(doc.extracted_info or {})
    prior_av = info.get("autoValidation") if isinstance(info.get("autoValidation"), dict) else {}
    job_id = job.id if job else None
    if job_id is not None and prior_av.get("ocrJobId") == job_id:
        if prior_av.get("decisionSource") == "system_auto_approval":
            return
        if prior_av.get("decisionSource") == "withheld" and not is_auto_approval_active():
            return

    assessment = assess_document(doc)
    assessment_dict = assessment.to_dict()
    assessment_dict["assessedAt"] = _utcnow_iso()
    if job_id is not None:
        assessment_dict["ocrJobId"] = job_id

    if not is_auto_approval_active():
        assessment_dict["decisionSource"] = "withheld"
        assessment_dict["policyActive"] = False
        assessment_dict["withheldReasons"] = assessment.withheld_reasons + [
            "Simulation auto-accept policy is disabled."
        ]
        info["autoValidation"] = assessment_dict
        doc.extracted_info = info
        return

    if doc.status != "pending_review":
        assessment_dict["decisionSource"] = "withheld"
        assessment_dict["policyActive"] = True
        assessment_dict["withheldReasons"] = assessment.withheld_reasons or [
            f"Document status is {doc.status}."
        ]
        info["autoValidation"] = assessment_dict
        doc.extracted_info = info
        return

    if not assessment.eligible:
        assessment_dict["decisionSource"] = "withheld"
        assessment_dict["policyActive"] = True
        info["autoValidation"] = assessment_dict
        doc.extracted_info = info
        return

    previous_status = doc.status
    doc.status = "approved"
    doc.reviewed_at = datetime.now(timezone.utc)
    doc.reviewer_remarks = (
        "Auto-accepted for FacultyLink simulation after SET/SEF evaluation checks "
        f"(policy {POLICY_VERSION}). Not official document certification."
    )
    append_system_auto_approval_history(doc, remarks=doc.reviewer_remarks)
    assessment_dict["decisionSource"] = "system_auto_approval"
    assessment_dict["policyActive"] = True
    assessment_dict["approvedAt"] = _utcnow_iso()
    info = dict(doc.extracted_info or {})
    info["autoValidation"] = assessment_dict
    doc.extracted_info = info
    record_auto_approval_audit(doc, assessment_dict, previous_status=previous_status)


def reassess_set_sef_simulation_accept(doc: Document) -> AutoApprovalAssessment:
    """Re-run simulation auto-accept after OCR (e.g. policy enabled). Does not re-OCR."""
    if not is_set_sef_indicator(doc.indicator_id):
        assessment = assess_document(doc)
        return assessment
    prior_av = (doc.extracted_info or {}).get("autoValidation")
    prior_av = prior_av if isinstance(prior_av, dict) else {}
    job_id = prior_av.get("ocrJobId")
    job = db.session.get(DocumentOcrJob, job_id) if job_id else None
    maybe_auto_approve_after_ocr(doc, job)
    return assess_document(doc)
