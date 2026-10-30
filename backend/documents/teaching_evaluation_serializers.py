"""Serialize DocumentTeachingEvaluation for API and folder views."""

from __future__ import annotations

from models import Document, DocumentTeachingEvaluation

from documents.status_map import DB_TO_WEB, document_status_to_web


def _web_validation_status(raw: str | None) -> str:
    if not raw:
        return "pending-review"
    key = raw.strip().lower().replace("-", "_")
    return DB_TO_WEB.get(key, "pending-review")


def teaching_evaluation_to_web(tev: DocumentTeachingEvaluation, doc: Document) -> dict:
    meta = dict(tev.extracted_metadata or {})
    status_web = _web_validation_status(tev.reviewer_validation_status)
    incomplete = bool(meta.get("missingFields")) or meta.get("extractionStatus") in (
        "partial",
        "ambiguous",
    )
    return {
        "id": tev.public_id,
        "teachingEvaluationId": tev.public_id,
        "documentId": doc.public_id,
        "fileName": doc.file_name,
        "uploadIndicatorId": doc.indicator_id,
        "evaluationType": tev.evaluation_type,
        "indicatorId": tev.indicator_id,
        "academicYear": tev.academic_year,
        "semester": tev.semester,
        "ratingRaw": tev.rating_raw,
        "ratingScale": tev.rating_scale,
        "ratingPercent": tev.rating_percent,
        "extractionStatus": meta.get("extractionStatus"),
        "ocrVerificationStatus": tev.ocr_verification_status,
        "reviewerValidationStatus": status_web,
        "reviewDisplayStatus": status_web,
        "sourceSectionRef": tev.source_section_ref,
        "reviewerRemarks": tev.reviewer_remarks,
        "missingFields": meta.get("missingFields") or [],
        "ambiguousFields": meta.get("ambiguousFields") or [],
        "uncertaintyNotes": meta.get("uncertaintyNotes") or [],
        "correctionHistory": tev.correction_history_json or [],
        "incompleteExtraction": incomplete,
        "duplicatePeriodWarning": False,
        "createdAt": tev.created_at.isoformat() if tev.created_at else None,
        "updatedAt": tev.updated_at.isoformat() if tev.updated_at else None,
    }


def legacy_document_period_row(doc: Document) -> dict:
    info = dict(doc.extracted_info or {})
    return {
        "id": doc.public_id,
        "teachingEvaluationId": None,
        "documentId": doc.public_id,
        "fileName": doc.file_name,
        "uploadIndicatorId": doc.indicator_id,
        "evaluationType": info.get("Detected evaluation kind") or None,
        "indicatorId": doc.indicator_id,
        "academicYear": info.get("Academic year"),
        "semester": info.get("Semester"),
        "ratingRaw": info.get("Extracted rating"),
        "ratingScale": info.get("Rating scale"),
        "ratingPercent": None,
        "extractionStatus": info.get("SET/SEF extraction status"),
        "ocrVerificationStatus": info.get("Indicator verification status"),
        "reviewerValidationStatus": document_status_to_web(doc),
        "reviewDisplayStatus": document_status_to_web(doc),
        "sourceSectionRef": None,
        "reviewerRemarks": doc.reviewer_remarks,
        "missingFields": [],
        "ambiguousFields": [],
        "uncertaintyNotes": [],
        "correctionHistory": [],
        "incompleteExtraction": info.get("SET/SEF extraction status") == "partial",
        "duplicatePeriodWarning": False,
        "legacyDocumentLevel": True,
    }


def folder_evaluation_records(profile_id: int, indicator_id: str, docs: list[Document]) -> list[dict]:
    rows: list[dict] = []
    for doc in docs:
        if doc.faculty_profile_id != profile_id:
            continue
        children = [
            tev
            for tev in doc.teaching_evaluations
            if tev.indicator_id == indicator_id
        ]
        if children:
            for tev in sorted(
                children,
                key=lambda t: (
                    t.academic_year or "",
                    t.semester or "",
                    t.evaluation_type or "",
                ),
            ):
                rows.append(teaching_evaluation_to_web(tev, doc))
        elif doc.indicator_id == indicator_id:
            rows.append(legacy_document_period_row(doc))
    return rows


def apply_duplicate_period_flags(rows: list[dict]) -> None:
    seen: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        et = (row.get("evaluationType") or "").strip().upper()
        year = (row.get("academicYear") or "").strip()
        sem = (row.get("semester") or "").strip()
        if not et or not year or not sem:
            continue
        key = (et, year, sem)
        prior = seen.get(key)
        if prior:
            prior["duplicatePeriodWarning"] = True
            row["duplicatePeriodWarning"] = True
        else:
            seen[key] = row
