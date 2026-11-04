"""Aggregate non–SET/SEF document evidence into unified KRA estimated points."""

from __future__ import annotations

from typing import Any

from models import Document, FacultyProfile

from documents.scoring.document_evidence_points import effective_document_points
from kra_configuration.published_limits import published_criterion_max_points, published_kra_max_points

_KRA_LABELS = {
    "kra1": "Instruction",
    "kra2": "Research",
    "kra3": "Extension",
    "kra4": "Professional Development",
}

CRITERION_B_ID = "kra1-b"
CRITERION_C_ID = "kra1-c"
KRA2_CRITERION_A_ID = "kra2-a"
KRA2_CRITERION_B_ID = "kra2-b"
KRA2_CRITERION_C_ID = "kra2-c"
KRA3_CRITERION_A_ID = "kra3-a"
KRA3_CRITERION_B_ID = "kra3-b"
KRA3_CRITERION_C_ID = "kra3-c"
KRA3_CRITERION_D_ID = "kra3-d"


def _legacy_aggregate_criterion_from_documents(
    docs: list[Document],
    criterion_id: str,
    max_pts: float,
) -> dict[str, Any]:
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
        "scoringSource": "legacy_document_points",
    }


def aggregate_criterion_documents_from_list(
    docs: list[Document],
    *,
    kra_key: str,
    criterion_id: str,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Aggregate one criterion from an in-memory document list (tests + production).

    Criterion B uses the bundle simulation adapter when
    ``CRITERION_B_SIMULATION_ADAPTER_ENABLED`` is true; otherwise legacy
    ``effective_document_points`` aggregation unchanged since Phase 2.
    """
    max_pts = published_criterion_max_points(criterion_id, settings)
    if max_pts is None:
        max_pts = 0.0

    if criterion_id == CRITERION_B_ID:
        from documents.scoring.criterion_b_simulation_adapter import (
            CRITERION_B_SIMULATION_ADAPTER_ENABLED,
            aggregate_criterion_b_simulation_from_documents,
        )
        from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

        if settings is not None:
            blob = settings
        else:
            blob, _resolution = resolve_settings_for_faculty_simulation()
        block = aggregate_criterion_b_simulation_from_documents(docs, settings=blob)
        est = block.get("estimatedPoints")
        preview = None
        if est is not None:
            try:
                preview_val = float(est)
                if preview_val >= 0:
                    preview = preview_val
            except (TypeError, ValueError):
                preview = None

        if CRITERION_B_SIMULATION_ADAPTER_ENABLED:
            if est is None:
                from documents.criterion_b_evidence.bundle import (
                    bundle_from_document,
                    is_supporting_evidence_document,
                )

                has_bundle_primary = any(
                    not is_supporting_evidence_document(d) and bundle_from_document(d) is not None
                    for d in docs
                )
                if not has_bundle_primary:
                    legacy = _legacy_aggregate_criterion_from_documents(docs, criterion_id, float(max_pts))
                    if legacy.get("estimatedPoints") is not None:
                        legacy["simulationAdapterEnabled"] = True
                        legacy["scoringSource"] = "legacy_document_points"
                        legacy["aggregationPolicy"] = "legacy_document_points_fallback"
                        return legacy
            return {
                "criterionId": criterion_id,
                "estimatedPoints": est,
                "maxPoints": float(block.get("maxPoints") or max_pts),
                "assessed": est is not None,
                "documentCount": int(block.get("documentCount") or 0),
                "scoringSource": block.get("scoringSource"),
                "aggregationPolicy": "provisional_output_deduplication",
                "simulationAdapterEnabled": True,
                "currentScoreSource": "criterion_b_evidence_bundle",
            }

        if preview is None:
            legacy = _legacy_aggregate_criterion_from_documents(docs, criterion_id, float(max_pts))
            if legacy.get("estimatedPoints") is not None:
                legacy["simulationAdapterEnabled"] = False
                return legacy

        return {
            "criterionId": criterion_id,
            "estimatedPoints": None,
            "maxPoints": float(block.get("maxPoints") or max_pts),
            "assessed": False,
            "documentCount": int(block.get("documentCount") or len(docs)),
            "scoringSource": "legacy_document_points",
            "simulationAdapterEnabled": False,
            "integrationState": "criterion_b_adapter_disabled"
            if preview is not None
            else None,
            "accomplishmentPreviewPoints": preview,
            "accomplishmentPreviewNote": (
                "Accomplishment scores are saved but not yet included in KRA totals. "
                "Criterion B rank/KRA integration requires enabling the simulation adapter."
            )
            if preview is not None
            else None,
        }

    if criterion_id in (
        KRA3_CRITERION_A_ID,
        KRA3_CRITERION_B_ID,
        KRA3_CRITERION_C_ID,
        KRA3_CRITERION_D_ID,
    ):
        from documents.scoring.kra3_simulation_adapter import (
            KRA3_SIMULATION_ADAPTER_ENABLED,
            aggregate_kra3_criterion_simulation_from_documents,
        )
        from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

        if settings is not None:
            blob = settings
            applicable = bool(settings.get("criteria"))
        else:
            blob, resolution = resolve_settings_for_faculty_simulation()
            applicable = resolution.has_applicable_row
        block = aggregate_kra3_criterion_simulation_from_documents(
            docs,
            criterion_id=criterion_id,
            settings=blob,
            applicable_config_present=applicable or bool(blob and blob.get("criteria")),
        )
        return {
            "criterionId": criterion_id,
            "estimatedPoints": block.get("estimatedPoints"),
            "validatedPoints": block.get("validatedPoints"),
            "maxPoints": float(block.get("maxPoints") or max_pts),
            "assessed": bool(block.get("assessed")),
            "documentCount": int(block.get("documentCount") or len(docs)),
            "scoringSource": block.get("scoringSource"),
            "aggregationPolicy": block.get("aggregationPolicy"),
            "simulationAdapterEnabled": KRA3_SIMULATION_ADAPTER_ENABLED,
            "accomplishments": block.get("accomplishments") or [],
        }

    if criterion_id in (KRA2_CRITERION_A_ID, KRA2_CRITERION_B_ID, KRA2_CRITERION_C_ID):
        from documents.scoring.kra2_simulation_adapter import (
            KRA2_SIMULATION_ADAPTER_ENABLED,
            aggregate_kra2_criterion_simulation_from_documents,
        )
        from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

        if settings is not None:
            blob = settings
            applicable = bool(settings.get("criteria"))
        else:
            blob, resolution = resolve_settings_for_faculty_simulation()
            applicable = resolution.has_applicable_row
        if KRA2_SIMULATION_ADAPTER_ENABLED:
            block = aggregate_kra2_criterion_simulation_from_documents(
                docs,
                criterion_id=criterion_id,
                settings=blob,
                applicable_config_present=applicable,
            )
            return {
                "criterionId": criterion_id,
                "estimatedPoints": block.get("estimatedPoints"),
                "validatedPoints": block.get("validatedPoints"),
                "maxPoints": float(block.get("maxPoints") or max_pts),
                "assessed": bool(block.get("assessed")),
                "documentCount": int(block.get("documentCount") or len(docs)),
                "scoringSource": block.get("scoringSource"),
                "aggregationPolicy": block.get("aggregationPolicy"),
                "simulationAdapterEnabled": True,
                "accomplishments": block.get("accomplishments") or [],
            }
        block = aggregate_kra2_criterion_simulation_from_documents(
            docs,
            criterion_id=criterion_id,
            settings=blob,
            applicable_config_present=applicable,
        )
        preview = block.get("estimatedPoints")
        legacy = _legacy_aggregate_criterion_from_documents(docs, criterion_id, float(max_pts))
        if preview is None and legacy.get("estimatedPoints") is not None:
            legacy["simulationAdapterEnabled"] = False
            legacy["integrationState"] = "kra2_adapter_disabled"
            return legacy
        est = preview if preview is not None else None
        return {
            "criterionId": criterion_id,
            "estimatedPoints": est,
            "validatedPoints": block.get("validatedPoints"),
            "maxPoints": float(block.get("maxPoints") or max_pts),
            "assessed": bool(est is not None or block.get("validatedPoints")),
            "documentCount": len(docs),
            "scoringSource": block.get("scoringSource") or "legacy_document_points",
            "simulationAdapterEnabled": False,
            "integrationState": "kra2_adapter_disabled" if preview is None else None,
            "accomplishmentPreviewPoints": preview,
            "accomplishmentPreviewNote": (
                "KRA II accomplishment estimates use published indicator points; "
                "reviewer-verified totals are reported separately."
            )
            if preview is not None
            else None,
        }

    if criterion_id == CRITERION_C_ID:
        from documents.scoring.criterion_c_simulation_adapter import (
            CRITERION_C_SIMULATION_ADAPTER_ENABLED,
            aggregate_criterion_c_simulation_from_documents,
        )
        from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

        if settings is not None:
            blob = settings
            applicable = bool(settings.get("criteria"))
        else:
            blob, resolution = resolve_settings_for_faculty_simulation()
            applicable = resolution.has_applicable_row
        if CRITERION_C_SIMULATION_ADAPTER_ENABLED:
            block = aggregate_criterion_c_simulation_from_documents(
                docs,
                settings=blob,
                applicable_config_present=applicable,
            )
            return {
                "criterionId": criterion_id,
                "estimatedPoints": block.get("estimatedPoints"),
                "validatedPoints": block.get("validatedPoints"),
                "maxPoints": float(block.get("maxPoints") or max_pts),
                "assessed": bool(block.get("assessed")),
                "documentCount": int(block.get("documentCount") or len(docs)),
                "scoringSource": block.get("scoringSource"),
                "aggregationPolicy": block.get("aggregationPolicy"),
                "simulationAdapterEnabled": True,
                "services": block.get("services") or [],
            }
        block = aggregate_criterion_c_simulation_from_documents(
            docs,
            settings=blob,
            applicable_config_present=applicable,
        )
        preview = block.get("estimatedPoints")
        legacy = _legacy_aggregate_criterion_from_documents(docs, criterion_id, float(max_pts))
        if preview is None and legacy.get("estimatedPoints") is not None:
            legacy["simulationAdapterEnabled"] = False
            legacy["integrationState"] = "criterion_c_adapter_disabled"
            return legacy
        est = preview if preview is not None else None
        return {
            "criterionId": criterion_id,
            "estimatedPoints": est,
            "validatedPoints": block.get("validatedPoints"),
            "maxPoints": float(block.get("maxPoints") or max_pts),
            "assessed": bool(est is not None or block.get("validatedPoints")),
            "documentCount": len(docs),
            "scoringSource": block.get("scoringSource") or "legacy_document_points",
            "simulationAdapterEnabled": False,
            "integrationState": "criterion_c_adapter_disabled" if preview is None else None,
            "accomplishmentPreviewPoints": preview,
            "accomplishmentPreviewNote": (
                "Criterion C accomplishment estimates use published indicator points; "
                "reviewer-verified totals are reported separately."
            )
            if preview is not None
            else None,
        }

    return _legacy_aggregate_criterion_from_documents(docs, criterion_id, float(max_pts))


def aggregate_documents_for_kra(profile: FacultyProfile, kra_key: str) -> dict[str, Any]:
    docs = (
        Document.query.filter_by(faculty_profile_id=profile.id, kra_id=kra_key)
        .filter(Document.deleted_at.is_(None))
        .all()
    )
    if kra_key == "kra2":
        from documents.kra2_evidence.scoring import aggregate_kra2_kra_from_documents
        from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

        settings_blob, resolution = resolve_settings_for_faculty_simulation()
        block = aggregate_kra2_kra_from_documents(
            docs,
            settings=settings_blob,
            applicable_config_present=resolution.has_applicable_row,
        )
        block["label"] = _KRA_LABELS[kra_key]
        block["statusLabel"] = (
            "Estimated from KRA II accomplishments (criteria sum capped at KRA max)"
            if block.get("assessed")
            else "Not yet assessed"
        )
        block["breakdown"] = []
        return block

    if kra_key == "kra3":
        from documents.scoring.kra3_simulation_adapter import aggregate_kra3_simulation_from_documents
        from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

        settings_blob, resolution = resolve_settings_for_faculty_simulation()
        block = aggregate_kra3_simulation_from_documents(
            docs,
            settings=settings_blob,
            applicable_config_present=resolution.has_applicable_row,
        )
        block["label"] = _KRA_LABELS[kra_key]
        block["statusLabel"] = (
            "Estimated from KRA III accomplishments (A+B+C plus bonus D, capped at 100)"
            if block.get("assessed")
            else "Not yet assessed"
        )
        block["breakdown"] = []
        return block

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
    from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

    settings_blob, _resolution = resolve_settings_for_faculty_simulation()

    docs = (
        Document.query.filter_by(
            faculty_profile_id=profile.id,
            kra_id=kra_key,
            criterion_id=criterion_id,
        )
        .filter(Document.deleted_at.is_(None))
        .all()
    )
    return aggregate_criterion_documents_from_list(
        docs,
        kra_key=kra_key,
        criterion_id=criterion_id,
        settings=settings_blob,
    )
