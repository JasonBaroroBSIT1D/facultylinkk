"""Teaching Effectiveness (Criterion A) payloads for API consumers."""

from __future__ import annotations

from models import Document, FacultyProfile

from documents.scoring.set_sef_aggregate import build_criterion_a_summary
from documents.status_map import document_status_to_web
from documents.teaching_evaluation_serializers import (
    apply_duplicate_period_flags,
    folder_evaluation_records,
)


def faculty_eligibility_from_profile(profile: FacultyProfile) -> dict | None:
    from documents.evaluation_eligibility import eligibility_for_scoring

    raw = getattr(profile, "evaluation_eligibility_json", None)
    return eligibility_for_scoring(raw if isinstance(raw, dict) else None)


def _active_docs_for_profile(profile_id: int) -> list[Document]:
    return (
        Document.query.filter(
            Document.faculty_profile_id == profile_id,
            Document.deleted_at.is_(None),
            Document.criterion_id == "kra1-a",
        )
        .order_by(Document.submitted_at.desc())
        .all()
    )


def teaching_effectiveness_payload(profile: FacultyProfile) -> dict:
    docs = _active_docs_for_profile(profile.id)
    summary = build_criterion_a_summary(
        docs,
        faculty_eligibility=faculty_eligibility_from_profile(profile),
    )
    summary["facultyId"] = profile.public_id
    return summary


def indicator_folder_payload(profile: FacultyProfile, indicator_id: str) -> dict:
    all_docs = _active_docs_for_profile(profile.id)
    from documents.scoring.set_sef_aggregate import aggregate_indicator

    block = aggregate_indicator(
        all_docs,
        indicator_id,
        faculty_eligibility=faculty_eligibility_from_profile(profile),
    )
    block["facultyId"] = profile.public_id

    evaluation_records = folder_evaluation_records(profile.id, indicator_id, all_docs)
    apply_duplicate_period_flags(evaluation_records)
    block["evaluationRecords"] = evaluation_records
    block["documents"] = evaluation_records
    block["documentSummaries"] = [
        {
            "id": row.get("documentId"),
            "fileName": row.get("fileName"),
            "status": row.get("reviewerValidationStatus"),
            "academicYear": row.get("academicYear"),
            "semester": row.get("semester"),
            "rating": row.get("ratingRaw"),
            "ratingScale": row.get("ratingScale"),
            "ocrVerification": row.get("ocrVerificationStatus"),
            "reviewerValidationStatus": row.get("reviewerValidationStatus"),
            "teachingEvaluationId": row.get("teachingEvaluationId"),
        }
        for row in evaluation_records
    ]
    return block
