"""Criterion A unified Supporting Documents workspace (read-only API envelope)."""

from __future__ import annotations

from typing import Any

from models import Document, DocumentTeachingEvaluation, FacultyProfile

from documents.ocr.queue import normalize_ocr_status
from documents.scoring.set_sef_aggregate import _tev_incomplete
from documents.set_sef_parent_context import (
    child_validation_summary_for_document,
    document_processing_status,
    set_sef_parent_context,
)
from documents.status_map import document_status_to_web
from documents.scoring.config_loader import SET_INDICATOR, SEF_INDICATOR
from documents.scoring.set_sef_aggregate import annotate_evaluation_records
from documents.teaching_evaluation_serializers import (
    apply_duplicate_period_flags,
    folder_evaluation_records,
)


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


def composition_display_label(doc: Document) -> str:
    info = dict(doc.extracted_info or {})
    if (info.get("Document classification status") or "").strip() == "needs_classification":
        return "Needs Classification"
    raw = (info.get("Document evaluation composition") or "").strip()
    if not raw:
        processing = document_processing_status(doc)
        raw = (processing.get("composition") or "").strip()
    mapping = {
        "SET only": "SET Only",
        "SEF only": "SEF Only",
        "Mixed SET and SEF": "Mixed SET and SEF",
        "Uncertain evaluation content": "Needs Classification",
        "No evaluation sections detected": "Needs Classification",
    }
    return mapping.get(raw, raw or "Unknown")


def completeness_status_label(doc: Document) -> str:
    info = dict(doc.extracted_info or {})
    if (info.get("Document classification status") or "").strip() == "needs_classification":
        return "Needs Classification"
    ocr = normalize_ocr_status(doc.ocr_status)
    if ocr in ("pending", "processing", "failed"):
        return "Incomplete"
    tev = list(getattr(doc, "teaching_evaluations", []) or [])
    try:
        tev = list(doc.teaching_evaluations.all())
    except Exception:
        pass
    if not tev:
        extraction = (info.get("SET/SEF extraction status") or "").strip().lower()
        if ocr == "completed" and extraction in ("", "partial", "failed"):
            return "Incomplete"
        if ocr != "completed":
            return "Incomplete"
        return "Incomplete"
    for row in tev:
        meta = dict(row.extracted_metadata or {})
        if _tev_incomplete(meta):
            return "Incomplete"
    return "Complete"


def ocr_status_label(doc: Document) -> str:
    ocr = normalize_ocr_status(doc.ocr_status)
    labels = {
        "pending": "Pending",
        "processing": "Processing",
        "completed": "Completed",
        "failed": "Failed",
    }
    return labels.get(ocr, ocr.replace("_", " ").title())


def validation_progress_label(counts: dict[str, int]) -> str | None:
    total = int(counts.get("total") or 0)
    if total <= 0:
        return None
    validated = int(counts.get("validated") or 0)
    return f"{validated} of {total} evaluations validated"


def aggregate_child_validation(source_documents: list[dict[str, Any]]) -> dict[str, int]:
    """Sum child evaluation buckets across all Criterion A source PDFs (authoritative for progress)."""
    keys = ("total", "validated", "pending", "needsRevision", "rejected", "incomplete")
    out = {k: 0 for k in keys}
    for row in source_documents:
        counts = row.get("childValidationSummary") or {}
        for key in keys:
            out[key] += int(counts.get(key) or 0)
    return out


def _iter_tev(doc: Document) -> list[DocumentTeachingEvaluation]:
    rel = getattr(doc, "teaching_evaluations", None)
    if rel is None:
        return []
    try:
        return list(rel.all())
    except Exception:
        try:
            return list(rel)
        except TypeError:
            return []


def _record_type_counts(doc: Document) -> tuple[int, int]:
    set_count = 0
    sef_count = 0
    for tev in _iter_tev(doc):
        if tev.indicator_id == DocumentTeachingEvaluation.INDICATOR_BY_TYPE["SET"]:
            set_count += 1
        elif tev.indicator_id == DocumentTeachingEvaluation.INDICATOR_BY_TYPE["SEF"]:
            sef_count += 1
    return set_count, sef_count


def source_document_workspace_row(doc: Document) -> dict[str, Any]:
    processing = document_processing_status(doc)
    ctx = set_sef_parent_context(doc) or {}
    counts = child_validation_summary_for_document(doc)
    set_count, sef_count = _record_type_counts(doc)
    info = dict(doc.extracted_info or {})
    return {
        "documentId": doc.public_id,
        "fileName": doc.file_name,
        "title": doc.title,
        "uploadIndicatorId": doc.indicator_id,
        "uploadedAt": _iso(doc.submitted_at or doc.created_at),
        "ocrStatus": ocr_status_label(doc),
        "ocrStatusRaw": normalize_ocr_status(doc.ocr_status),
        "composition": processing.get("composition"),
        "compositionDisplay": composition_display_label(doc),
        "completenessStatus": completeness_status_label(doc),
        "setRecordCount": set_count,
        "sefRecordCount": sef_count,
        "totalEvaluationRecords": counts.get("total") or 0,
        "childValidationSummary": counts,
        "validationProgressLabel": validation_progress_label(counts),
        "parentWorkflowApproved": bool(ctx.get("parentWorkflowApproved")),
        "reviewDisplayStatus": ctx.get("listDisplayStatus") or document_status_to_web(doc),
        "summaryLine": ctx.get("summaryLine"),
        "processing": processing,
        "documentWorkflowStatus": document_status_to_web(doc),
        "estimatedPointsExplanation": ctx.get("estimatedPointsExplanation"),
        "classificationStatus": info.get("Document classification status"),
    }


def build_criterion_a_workspace(
    profile: FacultyProfile,
    docs: list[Document],
    *,
    teaching_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """All Criterion A parent PDFs (once each) plus merged evaluation records for one faculty profile."""
    source_documents = [source_document_workspace_row(doc) for doc in docs]
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for indicator_id in (
        DocumentTeachingEvaluation.INDICATOR_BY_TYPE["SET"],
        DocumentTeachingEvaluation.INDICATOR_BY_TYPE["SEF"],
    ):
        for row in folder_evaluation_records(profile.id, indicator_id, docs, profile=profile):
            tev_id = str(row.get("teachingEvaluationId") or "")
            if tev_id and tev_id in seen:
                continue
            if tev_id:
                seen.add(tev_id)
            records.append(row)
    apply_duplicate_period_flags(records)
    if teaching_summary:
        set_block = teaching_summary.get("set") if isinstance(teaching_summary.get("set"), dict) else {}
        sef_block = teaching_summary.get("sef") if isinstance(teaching_summary.get("sef"), dict) else {}
        set_rows = [r for r in records if r.get("indicatorId") == SET_INDICATOR or r.get("evaluationType") == "SET"]
        sef_rows = [r for r in records if r.get("indicatorId") == SEF_INDICATOR or r.get("evaluationType") == "SEF"]
        annotate_evaluation_records(set_rows, set_block)
        annotate_evaluation_records(sef_rows, sef_block)
    child_validation = aggregate_child_validation(source_documents)
    totals = {
        "sourceDocumentCount": len(source_documents),
        "evaluationRecordCount": len(records),
        "setRecordCount": sum(r.get("setRecordCount") or 0 for r in source_documents),
        "sefRecordCount": sum(r.get("sefRecordCount") or 0 for r in source_documents),
        "childValidation": child_validation,
        "validationProgressLabel": validation_progress_label(child_validation),
    }
    semester_coverage = None
    if teaching_summary:
        semester_coverage = {
            "setSemesterSlots": (teaching_summary.get("set") or {}).get("semesterSlots") or [],
            "sefSemesterSlots": (teaching_summary.get("sef") or {}).get("semesterSlots") or [],
            "requiredSemestersPerIndicator": (
                ((teaching_summary.get("set") or {}).get("coverageSummary") or {}).get("requiredPeriods")
            ),
            "uniqueEligibleSet": ((teaching_summary.get("set") or {}).get("coverageSummary") or {}).get(
                "uniqueEligibleSemesters"
            ),
            "uniqueEligibleSef": ((teaching_summary.get("sef") or {}).get("coverageSummary") or {}).get(
                "uniqueEligibleSemesters"
            ),
        }
    return {
        "criterionId": "kra1-a",
        "facultyId": profile.public_id,
        "title": "Supporting Documents",
        "sourceDocuments": source_documents,
        "evaluationRecords": records,
        "semesterCoverage": semester_coverage,
        "totals": totals,
    }
