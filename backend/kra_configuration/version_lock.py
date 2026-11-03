"""Historical scoring version binding (Phase C5)."""

from __future__ import annotations

from datetime import date
from typing import Any

from evaluation_periods.service import published_period_row
from extensions import db
from kra_configuration.resolver import (
    ScoringConfigurationResolution,
    resolve_scoring_configuration,
    resolve_for_evaluation_period,
    settings_blob_from_resolution,
)
from models import Document, KraConfiguration


def bind_evaluation_period_configuration(period) -> None:
    """
    Assign scoring configuration to an evaluation period once (non-destructive).

    Called when Admin publishes the period. Does not overwrite an existing binding.
    """
    if period is None or getattr(period, "kra_configuration_id", None):
        return
    as_of = getattr(period, "start_date", None)
    resolution = resolve_scoring_configuration(as_of=as_of if isinstance(as_of, date) else None)
    if resolution.row:
        period.kra_configuration_id = resolution.row.id


def document_has_finalized_scoring(doc: Document) -> bool:
    if doc.status not in ("approved", "valid"):
        return False
    if doc.verified_points is not None and float(doc.verified_points) >= 0:
        return True
    if doc.reviewer_score is not None and float(doc.reviewer_score) >= 0:
        return True
    info = doc.extracted_info if isinstance(doc.extracted_info, dict) else {}
    bundle = info.get("criterionCEvidenceBundle")
    if isinstance(bundle, dict):
        ra = bundle.get("reviewerAssessment")
        if isinstance(ra, dict) and (ra.get("reviewStatus") or "").lower() == "approved":
            return True
    bundle2 = info.get("kra2EvidenceBundle")
    if isinstance(bundle2, dict):
        ra2 = bundle2.get("reviewerAssessment")
        if isinstance(ra2, dict) and (ra2.get("reviewStatus") or "").lower() == "approved":
            return True
    return False


def maybe_lock_document_scoring_configuration(doc: Document) -> None:
    """Persist applicable configuration id when a document reaches finalized scoring (once)."""
    if getattr(doc, "scoring_kra_configuration_id", None):
        return
    if not document_has_finalized_scoring(doc):
        return
    resolution = resolve_scoring_configuration()
    if resolution.row:
        doc.scoring_kra_configuration_id = resolution.row.id
        db.session.flush()


def record_configuration_in_criterion_c_bundle(
    bundle: dict[str, Any],
    *,
    resolution: ScoringConfigurationResolution,
) -> None:
    _record_configuration_in_evidence_bundle(bundle, resolution=resolution)


def record_configuration_in_kra2_bundle(
    bundle: dict[str, Any],
    *,
    resolution: ScoringConfigurationResolution,
) -> None:
    _record_configuration_in_evidence_bundle(bundle, resolution=resolution)


def _record_configuration_in_evidence_bundle(
    bundle: dict[str, Any],
    *,
    resolution: ScoringConfigurationResolution,
) -> None:
    if not isinstance(bundle, dict) or not resolution.row:
        return
    sj = resolution.row.settings_json if isinstance(resolution.row.settings_json, dict) else {}
    bundle["scoringConfiguration"] = {
        "configurationId": resolution.row.id,
        "version": sj.get("version"),
        "effectiveFrom": sj.get("effectiveFrom"),
        "provenance": resolution.provenance,
    }


def resolve_settings_for_document(doc: Document | None) -> tuple[dict[str, Any], ScoringConfigurationResolution]:
    """Settings for scoring a specific document (locked version or evaluation context)."""
    if doc is not None and getattr(doc, "scoring_kra_configuration_id", None):
        resolution = resolve_scoring_configuration(kra_configuration_id=int(doc.scoring_kra_configuration_id))
        return settings_blob_from_resolution(resolution), resolution
    period = published_period_row()
    resolution = resolve_for_evaluation_period(period)
    return settings_blob_from_resolution(resolution), resolution


def resolve_settings_for_faculty_simulation() -> tuple[dict[str, Any], ScoringConfigurationResolution]:
    period = published_period_row()
    resolution = resolve_for_evaluation_period(period)
    return settings_blob_from_resolution(resolution), resolution


def load_row_for_document_display(doc: Document) -> KraConfiguration | None:
    lock_id = getattr(doc, "scoring_kra_configuration_id", None)
    if lock_id:
        return KraConfiguration.query.filter(KraConfiguration.id == int(lock_id)).first()
    return None
