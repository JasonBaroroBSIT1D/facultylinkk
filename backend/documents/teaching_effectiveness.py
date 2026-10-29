"""Teaching Effectiveness (Criterion A) payloads for API consumers."""

from __future__ import annotations

from models import Document, FacultyProfile

from documents.scoring.set_sef_aggregate import build_criterion_a_summary
from documents.status_map import document_status_to_web


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
    docs = [
        d
        for d in _active_docs_for_profile(profile.id)
        if d.indicator_id == indicator_id
    ]
    from documents.scoring.set_sef_aggregate import aggregate_indicator

    block = aggregate_indicator(
        docs,
        indicator_id,
        faculty_eligibility=faculty_eligibility_from_profile(profile),
    )
    block["facultyId"] = profile.public_id
    block["documentSummaries"] = [
        {
            "id": d.public_id,
            "fileName": d.file_name,
            "status": document_status_to_web(d),
            "academicYear": (d.extracted_info or {}).get("Academic year"),
            "semester": (d.extracted_info or {}).get("Semester"),
            "rating": (d.extracted_info or {}).get("Extracted rating"),
            "ratingScale": (d.extracted_info or {}).get("Rating scale"),
            "ocrVerification": (d.extracted_info or {}).get("Indicator verification status"),
            "reviewerValidationStatus": document_status_to_web(d),
        }
        for d in docs
    ]
    return block
