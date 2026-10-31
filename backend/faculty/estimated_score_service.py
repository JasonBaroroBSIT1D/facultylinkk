"""Persist unified estimated KRA scores and audit trail (PostgreSQL)."""

from __future__ import annotations

import json
from typing import Any

from extensions import db
from models import AuditLog, FacultyProfile, KraScore, User

from faculty.rank_simulation_engine import MOBILE_KRA_KEYS, SIMULATION_DISCLAIMER, compute_rank_simulation
from kra_configuration.service import get_published_row, kra_settings_from_json


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


def _previous_totals(profile: FacultyProfile) -> dict[str, float | None]:
    rows = KraScore.query.filter_by(faculty_profile_id=profile.id).all()
    return {row.kra_key: float(row.estimated_points or row.verified_points or 0) for row in rows}


def persist_unified_kra_scores(profile: FacultyProfile, kra_blocks: list[dict[str, Any]]) -> None:
    existing = {row.kra_key: row for row in profile.kra_scores}
    for block in kra_blocks:
        key = block.get("kraId")
        if key not in MOBILE_KRA_KEYS:
            continue
        est = block.get("estimatedPoints")
        if est is None and not block.get("assessed"):
            continue
        points = float(est or 0)
        row = existing.get(key)
        if not row:
            row = KraScore(
                faculty_profile_id=profile.id,
                kra_key=key,
                estimated_points=points,
                verified_points=points,
                target_points=block.get("maxPoints") or _kra_max_points(key),
                document_count=block.get("documentCount") or 0,
                status_label=block.get("statusLabel") or "Estimated",
            )
            db.session.add(row)
        else:
            row.estimated_points = points
            row.verified_points = points
            row.document_count = block.get("documentCount") or row.document_count or 0
            row.status_label = block.get("statusLabel") or row.status_label
            row.target_points = block.get("maxPoints") or row.target_points
            if isinstance(block.get("breakdown"), list):
                row.breakdown_json = block["breakdown"]
    db.session.flush()


def record_estimated_score_audit(
    *,
    profile: FacultyProfile,
    actor: User | None,
    previous: dict[str, float | None],
    kra_blocks: list[dict[str, Any]],
    reason: str,
    document_id: str | None = None,
    criterion: str | None = None,
) -> None:
    updated = {b["kraId"]: b.get("estimatedPoints") for b in kra_blocks if b.get("kraId")}
    if previous == updated:
        return
    cfg = get_published_row()
    version = None
    if cfg and isinstance(cfg.settings_json, dict):
        version = cfg.settings_json.get("version")
    detail = {
        "facultyId": profile.public_id,
        "previousByKra": previous,
        "updatedByKra": updated,
        "reason": reason,
        "documentId": document_id,
        "criterion": criterion,
        "scoringConfigurationVersion": version,
    }
    db.session.add(
        AuditLog(
            actor_user_id=actor.id if actor else None,
            action="Estimated KRA score updated",
            target_id=profile.public_id,
            detail=json.dumps(detail, ensure_ascii=False)[:8000],
        )
    )


def recalculate_faculty_estimated_scores(
    profile: FacultyProfile,
    *,
    actor: User | None = None,
    reason: str = "recalculation",
    document_id: str | None = None,
    criterion: str | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    previous = _previous_totals(profile)
    simulation = compute_rank_simulation(profile)
    kra_blocks = simulation.get("kraScores") or []
    persist_unified_kra_scores(profile, kra_blocks)
    record_estimated_score_audit(
        profile=profile,
        actor=actor,
        previous=previous,
        kra_blocks=kra_blocks,
        reason=reason,
        document_id=document_id,
        criterion=criterion,
    )
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return simulation


def estimated_assessment_payload(profile: FacultyProfile) -> dict[str, Any]:
    sim = compute_rank_simulation(profile)
    return {
        "estimatedAssessment": {
            "kraScores": sim.get("kraScores"),
            "estimatedTotalKraPoints": sim.get("estimatedTotalKraPoints"),
            "weightedEstimatedScore": sim.get("weightedEstimatedScore"),
            "simulation": {
                "currentRank": sim.get("currentRank"),
                "targetRank": sim.get("targetRank"),
                "eligibilityStatus": sim.get("eligibilityStatus"),
                "eligibilityLabel": sim.get("eligibilityLabel"),
                "missingRequirements": sim.get("missingRequirements"),
                "areasToImprove": sim.get("areasToImprove"),
                "disclaimer": SIMULATION_DISCLAIMER,
            },
        }
    }
