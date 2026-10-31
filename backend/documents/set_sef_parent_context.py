"""SET/SEF parent PDF vs child evaluation status (API envelope, no DB writes)."""

from __future__ import annotations

from typing import Any

from models import Document, DocumentTeachingEvaluation

from documents.ocr.queue import normalize_ocr_status
from documents.criterion_a_upload import is_auto_criterion_a_upload
from documents.ocr.set_sef_metadata import is_set_sef_indicator
from documents.scoring.set_sef_aggregate import _tev_incomplete, _tev_review_bucket
from documents.status_map import document_status_to_web


def _iter_tev(doc: Document) -> list[DocumentTeachingEvaluation]:
    rel = getattr(doc, "teaching_evaluations", None)
    if rel is None:
        return []
    try:
        return list(rel.all())
    except AttributeError:
        try:
            return list(rel)
        except TypeError:
            return []


def _composition_label(doc: Document) -> str:
    info = dict(doc.extracted_info or {})
    raw = (info.get("Document evaluation composition") or "").strip()
    if raw:
        return raw
    return "Uncertain evaluation content"


def _web_validation_bucket(reviewer_status: str | None, *, incomplete: bool) -> str:
    bucket = _tev_review_bucket(reviewer_status, incomplete=incomplete)
    return bucket


def child_validation_summary_for_document(
    doc: Document,
    *,
    indicator_id: str | None = None,
) -> dict[str, int]:
    """Counts child SET/SEF rows by review bucket (optionally one indicator)."""
    counts = {
        "total": 0,
        "validated": 0,
        "pending": 0,
        "needsRevision": 0,
        "rejected": 0,
        "incomplete": 0,
    }
    for tev in _iter_tev(doc):
        if indicator_id and tev.indicator_id != indicator_id:
            continue
        meta = dict(tev.extracted_metadata or {})
        incomplete = _tev_incomplete(meta)
        bucket = _web_validation_bucket(tev.reviewer_validation_status, incomplete=incomplete)
        counts["total"] += 1
        if bucket == "accepted":
            counts["validated"] += 1
        elif bucket == "pending":
            counts["pending"] += 1
        elif bucket == "revision":
            counts["needsRevision"] += 1
        elif bucket == "rejected":
            counts["rejected"] += 1
        elif bucket == "incomplete":
            counts["incomplete"] += 1
    return counts


def document_processing_status(doc: Document) -> dict[str, Any]:
    """OCR and upload workflow for the parent PDF (not semester validation)."""
    info = dict(doc.extracted_info or {})
    ocr = normalize_ocr_status(doc.ocr_status)
    workflow = document_status_to_web(doc)
    source = (info.get("Approval decision source") or "").strip()
    return {
        "ocrStatus": ocr,
        "documentWorkflowStatus": workflow,
        "simulationAutoAccepted": source == "system_auto_approval"
        or (
            isinstance(info.get("autoValidation"), dict)
            and info["autoValidation"].get("decisionSource") == "system_auto_approval"
        ),
        "composition": _composition_label(doc),
        "detectedSectionCount": _int(info.get("Detected evaluation section count")),
        "linkedEvaluationCount": len(_iter_tev(doc)),
    }


def _int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def summary_line(
    composition: str,
    counts: dict[str, int],
    *,
    indicator_scope: str | None = None,
) -> str:
    total = counts.get("total") or 0
    if total <= 0:
        return f"{composition} · no linked evaluation records yet"
    parts = [composition, f"{total} evaluation{'s' if total != 1 else ''}"]
    if indicator_scope:
        parts.append(indicator_scope)
    detail: list[str] = []
    if counts.get("validated"):
        detail.append(f"{counts['validated']} validated")
    if counts.get("pending"):
        detail.append(f"{counts['pending']} pending")
    if counts.get("needsRevision"):
        detail.append(f"{counts['needsRevision']} needs revision")
    if counts.get("rejected"):
        detail.append(f"{counts['rejected']} rejected")
    if counts.get("incomplete"):
        detail.append(f"{counts['incomplete']} incomplete")
    if detail:
        parts.append(", ".join(detail))
    return " · ".join(parts)


def estimated_points_explanation(doc: Document, *, indicator_id: str | None = None) -> str | None:
    """Why this parent PDF may show zero credited/validated points."""
    if not (
        is_set_sef_indicator(doc.indicator_id or "")
        or is_auto_criterion_a_upload(doc.indicator_id)
        or doc.criterion_id == "kra1-a"
    ):
        return None
    counts = child_validation_summary_for_document(doc, indicator_id=indicator_id)
    if counts["total"] == 0:
        return "No SET/SEF semester records linked yet — complete OCR or wait for extraction."
    if counts["validated"] == 0:
        if counts["pending"] > 0:
            return (
                "Instruction (KRA I) points come from SET/SEF semester records, not this PDF row. "
                f"{counts['pending']} semester record(s) pending review — "
                "eligible pending ratings may still appear in component estimates."
            )
        if counts["incomplete"] > 0:
            return "Incomplete OCR metadata — reviewer must confirm or correct before scoring."
        return "No reviewer-validated semester records yet for estimated KRA scoring."
    verified = doc.verified_points
    estimated = doc.estimated_points
    if (verified or 0) == 0 and (estimated or 0) == 0:
        return (
            "Validated semester records exist but Criterion A points follow the published "
            "SET/SEF formula (coverage, divisor, and indicator caps) — see teaching effectiveness summary."
        )
    return None


def set_sef_parent_context(
    doc: Document,
    *,
    indicator_id: str | None = None,
) -> dict[str, Any] | None:
    """API envelope: separate PDF processing from child evaluation validation."""
    if doc.criterion_id != "kra1-a" and not is_set_sef_indicator(doc.indicator_id or ""):
        tev = _iter_tev(doc)
        if not tev:
            return None
    elif not is_set_sef_indicator(doc.indicator_id or "") and not _iter_tev(doc):
        return None

    scope_indicator = indicator_id or doc.indicator_id
    counts = child_validation_summary_for_document(doc, indicator_id=scope_indicator if indicator_id else None)
    processing = document_processing_status(doc)
    composition = processing["composition"]
    if indicator_id == DocumentTeachingEvaluation.INDICATOR_BY_TYPE["SET"]:
        scope_label = "this indicator folder (SET)"
    elif indicator_id == DocumentTeachingEvaluation.INDICATOR_BY_TYPE["SEF"]:
        scope_label = "this indicator folder (SEF)"
    else:
        scope_label = None

    line = summary_line(composition, counts, indicator_scope=scope_label)
    all_counts = child_validation_summary_for_document(doc)
    pending_children = all_counts["pending"] + all_counts["incomplete"]
    parent_workflow_approved = doc.status in ("approved", "valid")

    info = dict(doc.extracted_info or {})
    list_display_status = "pending-review"
    if info.get("Document classification status") == "needs_classification":
        list_display_status = "reviewer-required"
    elif counts["total"] == 0:
        list_display_status = processing["documentWorkflowStatus"]
    elif counts["validated"] == counts["total"] and counts["total"] > 0:
        list_display_status = "approved"
    elif counts["needsRevision"] > 0:
        list_display_status = "revision"
    elif counts["rejected"] == counts["total"]:
        list_display_status = "rejected"
    elif pending_children > 0 or counts["pending"] > 0:
        list_display_status = "pending-review"

    return {
        "composition": composition,
        "summaryLine": line,
        "processing": processing,
        "childValidationSummary": counts,
        "allChildValidationSummary": all_counts,
        "listDisplayStatus": list_display_status,
        "independentValidationRequired": counts["total"] > 0,
        "estimatedPointsExplanation": estimated_points_explanation(
            doc, indicator_id=indicator_id
        ),
        "parentWorkflowApproved": parent_workflow_approved,
        "note": (
            "Document-level approval or simulation auto-accept applies to the uploaded PDF only. "
            "Each SET/SEF semester record requires its own reviewer validation for scoring."
        )
        if all_counts["total"] > 0
        else None,
    }


def source_document_summaries(
    docs: list[Document],
    indicator_id: str,
) -> list[dict[str, Any]]:
    """One entry per parent PDF that contributes evaluations to an indicator folder."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for doc in docs:
        if doc.deleted_at is not None:
            continue
        children = [t for t in _iter_tev(doc) if t.indicator_id == indicator_id]
        legacy = doc.indicator_id == indicator_id and not children
        if not children and not legacy:
            continue
        if doc.public_id in seen:
            continue
        seen.add(doc.public_id)
        ctx = set_sef_parent_context(doc, indicator_id=indicator_id) or {}
        rows.append(
            {
                "documentId": doc.public_id,
                "fileName": doc.file_name,
                "uploadIndicatorId": doc.indicator_id,
                "processing": ctx.get("processing") or document_processing_status(doc),
                "summaryLine": ctx.get("summaryLine"),
                "childValidationSummary": ctx.get("childValidationSummary")
                or child_validation_summary_for_document(doc, indicator_id=indicator_id),
                "estimatedPointsExplanation": ctx.get("estimatedPointsExplanation"),
            }
        )
    return rows


def workspace_teaching_evaluation_stats(
    docs: list[Document],
) -> dict[str, int]:
    """Reviewer dashboard: count child evaluation validation buckets (not parent PDFs)."""
    totals = {
        "evaluationRecordsTotal": 0,
        "evaluationRecordsPending": 0,
        "evaluationRecordsValidated": 0,
        "evaluationRecordsNeedsRevision": 0,
        "evaluationRecordsRejected": 0,
        "evaluationRecordsIncomplete": 0,
    }
    for doc in docs:
        if doc.criterion_id != "kra1-a":
            continue
        for tev in _iter_tev(doc):
            meta = dict(tev.extracted_metadata or {})
            incomplete = _tev_incomplete(meta)
            bucket = _web_validation_bucket(tev.reviewer_validation_status, incomplete=incomplete)
            totals["evaluationRecordsTotal"] += 1
            if bucket == "accepted":
                totals["evaluationRecordsValidated"] += 1
            elif bucket == "pending":
                totals["evaluationRecordsPending"] += 1
            elif bucket == "revision":
                totals["evaluationRecordsNeedsRevision"] += 1
            elif bucket == "rejected":
                totals["evaluationRecordsRejected"] += 1
            elif bucket == "incomplete":
                totals["evaluationRecordsIncomplete"] += 1
    return totals
