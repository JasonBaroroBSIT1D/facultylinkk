"""Aggregate non–SET/SEF document evidence into unified KRA estimated points."""

from __future__ import annotations

from typing import Any

from models import Document, FacultyProfile

from documents.scoring.document_evidence_points import effective_document_points
from kra_configuration.service import get_published_row, kra_settings_from_json

_KRA_LABELS = {
    "kra1": "Instruction",
    "kra2": "Research",
    "kra3": "Extension",
    "kra4": "Professional Development",
}


def _kra_max_points(kra_key: str) -> float:
    row = get_published_row()
    if not row:
        return 100.0
    settings = kra_settings_from_json(row.settings_json if isinstance(row.settings_json, dict) else {})
    kras = settings.get("kras") if isinstance(settings.get("kras"), list) else []
    for kra in kras:
        if isinstance(kra, dict) and kra.get("id") == kra_key:
            try:
                return float(kra.get("maxPoints") or 100)
            except (TypeError, ValueError):
                break
    return 100.0


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

    max_pts = _kra_max_points(kra_key)
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
