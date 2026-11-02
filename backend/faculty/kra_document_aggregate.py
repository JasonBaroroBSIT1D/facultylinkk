"""Aggregate non–SET/SEF document evidence into unified KRA estimated points."""

from __future__ import annotations

from typing import Any

from models import Document, FacultyProfile

from documents.scoring.document_evidence_points import effective_document_points
from kra_configuration.published_limits import published_kra_max_points

_KRA_LABELS = {
    "kra1": "Instruction",
    "kra2": "Research",
    "kra3": "Extension",
    "kra4": "Professional Development",
}


def aggregate_documents_for_kra(profile: FacultyProfile, kra_key: str) -> dict[str, Any]:
    docs = (
        Document.query.filter_by(faculty_profile_id=profile.id, kra_id=kra_key)
        .filter(Document.deleted_at.is_(None))
        .all()
    )
    best_by_indicator: dict[str, tuple[Document, float]] = {}
    for doc in docs:
        pts = effective_document_points(doc)
        if pts is None:
            continue
        key = (doc.indicator_id or doc.public_id).strip()
        prev = best_by_indicator.get(key)
        if prev is None or pts > prev[1]:
            best_by_indicator[key] = (doc, pts)

    max_pts = published_kra_max_points(kra_key)
    total = 0.0
    breakdown: list[dict] = []
    for _key, (doc, pts) in sorted(best_by_indicator.items(), key=lambda item: -item[1][1]):
        capped = min(pts, max_pts)
        total += capped
        breakdown.append(
            {
                "title": doc.title or doc.public_id,
                "points": round(capped, 2),
                "note": f"Document {doc.public_id} · status {doc.status}",
            }
        )
    total = round(min(total, max_pts), 2)
    doc_count = len(docs)
    has_evidence = any(effective_document_points(d) is not None for d in docs)
    assessed = doc_count > 0 and (total > 0 or has_evidence)
    return {
        "kraId": kra_key,
        "label": _KRA_LABELS[kra_key],
        "assessed": assessed,
        "estimatedPoints": total if assessed else None,
        "documentCount": doc_count,
        "statusLabel": "Estimated from eligible evidence"
        if assessed
        else ("Not yet assessed" if doc_count == 0 else "Awaiting eligible evidence"),
        "breakdown": breakdown[:20],
        "maxPoints": max_pts,
    }


def aggregate_criterion_documents(
    profile: FacultyProfile,
    kra_key: str,
    criterion_id: str,
) -> dict[str, Any]:
    """Best eligible document points for one criterion (excludes other criteria)."""
    from kra_configuration.published_limits import published_criterion_max_points

    docs = (
        Document.query.filter_by(
            faculty_profile_id=profile.id,
            kra_id=kra_key,
            criterion_id=criterion_id,
        )
        .filter(Document.deleted_at.is_(None))
        .all()
    )
    max_pts = published_criterion_max_points(criterion_id)
    if max_pts is None:
        max_pts = 0.0

    best_by_indicator: dict[str, tuple[Document, float]] = {}
    for doc in docs:
        pts = effective_document_points(doc)
        if pts is None:
            continue
        key = (doc.indicator_id or doc.public_id).strip()
        prev = best_by_indicator.get(key)
        if prev is None or pts > prev[1]:
            best_by_indicator[key] = (doc, pts)

    total = 0.0
    for _key, (_doc, pts) in best_by_indicator.items():
        total += min(pts, max_pts) if max_pts > 0 else pts
    if max_pts > 0:
        total = min(total, max_pts)
    total = round(total, 2)
    has_evidence = any(effective_document_points(d) is not None for d in docs)
    assessed = has_evidence and total > 0
    return {
        "criterionId": criterion_id,
        "estimatedPoints": total if assessed else None,
        "maxPoints": max_pts,
        "assessed": assessed,
        "documentCount": len(docs),
    }
