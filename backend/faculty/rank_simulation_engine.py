"""Dynamic faculty rank-upgrade simulation (PostgreSQL + published scoring only)."""

from __future__ import annotations

import re
from typing import Any

from models import Document, FacultyProfile

from documents.scoring.config_loader import criterion_a_max_points
from documents.teaching_effectiveness import teaching_effectiveness_payload
from faculty.kra_document_aggregate import aggregate_criterion_documents, aggregate_documents_for_kra
from kra_configuration.published_limits import (
    criterion_display_name,
    criterion_is_bonus,
    criteria_entries_for_kra,
    published_criterion_max_points,
    published_kra_max_points,
)
from kra_configuration.resolver import resolution_metadata
from kra_configuration.service import get_published_row
from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

SIMULATION_DISCLAIMER = (
    "Estimated KRA scores and potential rank eligibility are provided for faculty self-assessment "
    "and preparation only. They do not constitute official DBM–CHED rank upgrade, reclassification "
    "approval, or certification."
)

MOBILE_KRA_KEYS = ("kra1", "kra2", "kra3", "kra4")
KRA_LABELS = {
    "kra1": "Instruction",
    "kra2": "Research",
    "kra3": "Extension",
    "kra4": "Professional Development",
}

TABLE_22_DEFAULTS: dict[str, dict[str, float]] = {
    "Instructor": {"kra1": 60, "kra2": 10, "kra3": 20, "kra4": 10},
    "Asst. Professor": {"kra1": 50, "kra2": 20, "kra3": 20, "kra4": 10},
    "Assoc. Professor": {"kra1": 40, "kra2": 30, "kra3": 20, "kra4": 10},
    "Professor": {"kra1": 30, "kra2": 40, "kra3": 20, "kra4": 10},
    "College/University Professor": {"kra1": 20, "kra2": 50, "kra3": 20, "kra4": 10},
}

ELIGIBILITY_ELIGIBLE = "eligible_validated"
ELIGIBILITY_PROVISIONAL = "provisionally_on_track"
ELIGIBILITY_UNDER_ASSESSMENT = "under_assessment"
ELIGIBILITY_ADDITIONAL = "additional_requirements"
ELIGIBILITY_CANNOT_DETERMINE = "rules_unavailable"


def resolve_rank_band(rank: str | None) -> str:
    text = (rank or "").strip().lower()
    if not text:
        return "Instructor"
    if "college" in text or "university professor" in text or "col./univ" in text:
        return "College/University Professor"
    if "assoc" in text:
        return "Assoc. Professor"
    if "asst" in text or "assistant" in text:
        return "Asst. Professor"
    if "professor" in text and "instructor" not in text:
        return "Professor"
    return "Instructor"


def _published_settings() -> tuple[dict[str, Any], Any]:
    blob, resolution = resolve_settings_for_faculty_simulation()
    return blob, resolution


def weights_for_rank(rank: str | None) -> tuple[str, dict[str, float]]:
    band = resolve_rank_band(rank)
    settings, resolution = _published_settings()
    published = settings.get("rankWeights")
    if (not published or not isinstance(published, dict) or band not in published) and resolution.row:
        column_rw = resolution.row.rank_weights if isinstance(resolution.row.rank_weights, dict) else {}
        if column_rw:
            published = column_rw
    source = {}
    if isinstance(published, dict) and band in published and isinstance(published[band], dict):
        source = published[band]
    elif band in TABLE_22_DEFAULTS:
        source = TABLE_22_DEFAULTS[band]
    else:
        source = TABLE_22_DEFAULTS["Instructor"]
    mobile_map = {
        "kra1": "instruction",
        "kra2": "research",
        "kra3": "extension",
        "kra4": "professionalDevelopment",
    }
    weights: dict[str, float] = {}
    for kra_id in MOBILE_KRA_KEYS:
        raw = source.get(kra_id)
        if raw is None:
            raw = source.get(mobile_map[kra_id])
        try:
            weights[kra_id] = float(raw) if raw is not None else 0.0
        except (TypeError, ValueError):
            weights[kra_id] = 0.0
    return band, weights


def _round2(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def unified_teaching_estimated_points(te: dict[str, Any]) -> float | None:
    """Single KRA I estimate: eligible pending + accepted SET/SEF evidence."""
    prov = te.get("combinedProvisionalPoints")
    val = te.get("combinedValidatedPoints")
    if prov is not None:
        return _round2(float(prov))
    if val is not None:
        return _round2(float(val))
    return None


def unified_teaching_validated_points(te: dict[str, Any]) -> float | None:
    """Reviewer-validated Criterion A (SET/SEF) points only."""
    val = te.get("combinedValidatedPoints")
    if val is not None:
        return _round2(float(val))
    return None


def _weighted_estimated_total(kra_points: dict[str, dict[str, Any]], weights: dict[str, float]) -> float | None:
    any_assessed = False
    total = 0.0
    for kra_id in MOBILE_KRA_KEYS:
        block = kra_points.get(kra_id) or {}
        if not block.get("assessed"):
            continue
        pts = block.get("estimatedPoints")
        if pts is None:
            continue
        any_assessed = True
        cap = block.get("maxPoints")
        if cap is not None:
            pts = min(float(pts), float(cap))
        total += float(pts) * (weights.get(kra_id, 0) / 100.0)
    if not any_assessed:
        return None
    return _round2(total)


def _attach_unified_aliases(block: dict[str, Any]) -> dict[str, Any]:
    est = block.get("estimatedPoints")
    val = block.get("validatedPoints")
    if val is None:
        val = est
    block["validatedPoints"] = val
    block["provisionalPoints"] = est
    block["currentPoints"] = int(round(float(est or 0)))
    return block


def _weighted_total(kra_points: dict[str, dict[str, Any]], weights: dict[str, float], *, use_validated: bool) -> float | None:
    key = "validatedPoints" if use_validated else "provisionalPoints"
    any_assessed = False
    total = 0.0
    for kra_id in MOBILE_KRA_KEYS:
        block = kra_points.get(kra_id) or {}
        if not block.get("assessed"):
            continue
        pts = block.get(key)
        if pts is None:
            if use_validated:
                continue
            pts = block.get("validatedPoints")
            if pts is None:
                continue
        any_assessed = True
        cap = block.get("maxPoints")
        if cap is not None:
            pts = min(float(pts), float(cap))
        total += float(pts) * (weights.get(kra_id, 0) / 100.0)
    if not any_assessed:
        return None
    return _round2(total)


def _doc_counts(profile: FacultyProfile) -> dict[str, int]:
    counts = {k: 0 for k in MOBILE_KRA_KEYS}
    rows = (
        Document.query.filter_by(faculty_profile_id=profile.id)
        .filter(Document.deleted_at.is_(None))
        .all()
    )
    for doc in rows:
        key = (doc.kra_id or "").strip()
        if key in counts:
            counts[key] += 1
    return counts


def _kra_from_documents(profile: FacultyProfile, key: str, doc_count: int) -> dict[str, Any]:
    block = aggregate_documents_for_kra(profile, key)
    if doc_count and not block.get("documentCount"):
        block["documentCount"] = doc_count
    settings, _resolution = _published_settings()
    block["targetPoints"] = int(round(block.get("maxPoints") or published_kra_max_points(key, settings)))
    criteria_scores: list[dict[str, Any]] = []
    for entry in criteria_entries_for_kra(settings, key):
        cid = entry["criterionId"]
        crit = aggregate_criterion_documents(profile, key, cid)
        row: dict[str, Any] = {
            "criterionId": cid,
            "name": criterion_display_name(cid, entry),
            "maxPoints": float(entry.get("maxPoints") or crit.get("maxPoints") or 0),
            "estimatedPoints": crit.get("estimatedPoints"),
            "bonus": criterion_is_bonus(entry),
        }
        if crit.get("integrationState"):
            row["integrationState"] = crit.get("integrationState")
        if crit.get("accomplishmentPreviewPoints") is not None:
            row["accomplishmentPreviewPoints"] = crit.get("accomplishmentPreviewPoints")
            row["accomplishmentPreviewNote"] = crit.get("accomplishmentPreviewNote")
        if crit.get("simulationAdapterEnabled") is not None:
            row["simulationAdapterEnabled"] = crit.get("simulationAdapterEnabled")
        criteria_scores.append(row)
    if criteria_scores:
        block["criteriaScores"] = criteria_scores
    return block


def _build_kra1_criteria_scores(
    profile: FacultyProfile,
    te: dict[str, Any],
    settings: dict[str, Any],
) -> list[dict[str, Any]]:
    crit_a_max = published_criterion_max_points("kra1-a", settings)
    if crit_a_max is None:
        try:
            crit_a_max = float(te.get("criterionMaxPoints") or criterion_a_max_points() or 60)
        except (TypeError, ValueError):
            crit_a_max = 60.0
    est_a = unified_teaching_estimated_points(te)
    b_block = aggregate_criterion_documents(profile, "kra1", "kra1-b")
    c_block = aggregate_criterion_documents(profile, "kra1", "kra1-c")

    by_id = {e["criterionId"]: e for e in criteria_entries_for_kra(settings, "kra1")}
    if not by_id:
        by_id = {
            "kra1-a": {"criterionId": "kra1-a", "maxPoints": crit_a_max},
            "kra1-b": {"criterionId": "kra1-b", "maxPoints": b_block.get("maxPoints") or 30},
            "kra1-c": {"criterionId": "kra1-c", "maxPoints": c_block.get("maxPoints") or 10},
        }

    scores: list[dict[str, Any]] = []
    for cid in sorted(by_id.keys()):
        entry = by_id[cid]
        if cid == "kra1-a":
            cmax = float(crit_a_max)
            est = est_a
        elif cid == "kra1-b":
            cmax = float(entry.get("maxPoints") or b_block.get("maxPoints") or 0)
            est = b_block.get("estimatedPoints")
            crit_val = b_block.get("validatedPoints")
        elif cid == "kra1-c":
            cmax = float(entry.get("maxPoints") or c_block.get("maxPoints") or 0)
            est = c_block.get("estimatedPoints")
            crit_val = c_block.get("validatedPoints")
        else:
            cmax = float(entry.get("maxPoints") or 0)
            extra = aggregate_criterion_documents(profile, "kra1", cid)
            est = extra.get("estimatedPoints")
            crit_val = extra.get("validatedPoints")
        row: dict[str, Any] = {
            "criterionId": cid,
            "name": criterion_display_name(cid, entry),
            "maxPoints": cmax,
            "estimatedPoints": _round2(float(est)) if est is not None else None,
            "bonus": criterion_is_bonus(entry),
        }
        if cid != "kra1-a" and crit_val is not None:
            row["validatedPoints"] = _round2(float(crit_val))
        src_block = b_block if cid == "kra1-b" else c_block if cid == "kra1-c" else None
        if src_block:
            if src_block.get("integrationState"):
                row["integrationState"] = src_block.get("integrationState")
            if src_block.get("accomplishmentPreviewPoints") is not None:
                row["accomplishmentPreviewPoints"] = src_block.get("accomplishmentPreviewPoints")
                row["accomplishmentPreviewNote"] = src_block.get("accomplishmentPreviewNote")
            if src_block.get("simulationAdapterEnabled") is not None:
                row["simulationAdapterEnabled"] = src_block.get("simulationAdapterEnabled")
        scores.append(row)
    return scores


def _kra1_from_teaching(profile: FacultyProfile, te: dict[str, Any], doc_count: int) -> dict[str, Any]:
    settings, _resolution = _published_settings()
    max_pts = published_kra_max_points("kra1", settings)
    criteria_scores = _build_kra1_criteria_scores(profile, te, settings)
    set_b = te.get("set") if isinstance(te.get("set"), dict) else {}
    sef_b = te.get("sef") if isinstance(te.get("sef"), dict) else {}
    set_uploads = ((set_b.get("coverageSummary") or {}).get("totalUploads") or 0)
    sef_uploads = ((sef_b.get("coverageSummary") or {}).get("totalUploads") or 0)
    has_any = set_uploads > 0 or sef_uploads > 0
    estimated = unified_teaching_estimated_points(te)
    validated = unified_teaching_validated_points(te)
    extra_points = 0.0
    extra_validated = 0.0
    extra_assessed = False
    extra_validated_assessed = False
    for row in criteria_scores:
        if row["criterionId"] == "kra1-a":
            continue
        if row.get("estimatedPoints") is not None:
            extra_assessed = True
            extra_points += float(row["estimatedPoints"])
        if row.get("validatedPoints") is not None:
            try:
                v = float(row["validatedPoints"])
            except (TypeError, ValueError):
                v = 0.0
            if v > 0:
                extra_validated_assessed = True
                extra_validated += v
    if estimated is not None or extra_assessed:
        estimated = _round2((float(estimated or 0) + extra_points))
    elif not has_any and not extra_assessed:
        estimated = None
    if validated is not None or extra_validated_assessed:
        validated = _round2((float(validated or 0) + extra_validated))
    else:
        validated = 0.0 if (estimated is not None or extra_assessed) else None
    breakdown = []
    if set_uploads:
        set_est = (
            set_b.get("provisionalPoints")
            if set_b.get("provisionalPoints") is not None
            else set_b.get("validatedPoints")
        )
        breakdown.append(
            {
                "title": "SET (student evaluation)",
                "points": int(round(float(set_est or 0))),
                "note": _set_sef_note(set_b, validated_key="validatedPoints"),
            }
        )
    if sef_uploads:
        sef_est = (
            sef_b.get("provisionalPoints")
            if sef_b.get("provisionalPoints") is not None
            else sef_b.get("validatedPoints")
        )
        breakdown.append(
            {
                "title": "SEF (supervisor evaluation)",
                "points": int(round(float(sef_est or 0))),
                "note": _set_sef_note(sef_b, validated_key="validatedPoints"),
            }
        )
    for crit_row in criteria_scores:
        cid = crit_row.get("criterionId")
        if cid not in ("kra1-b", "kra1-c"):
            continue
        est_crit = crit_row.get("estimatedPoints")
        if est_crit is None:
            continue
        label = crit_row.get("name") or cid
        breakdown.append(
            {
                "title": f"{label} (Criterion {'B' if cid == 'kra1-b' else 'C'})",
                "points": int(round(float(est_crit))),
                "note": "Estimated from eligible accomplishment evidence (simulation).",
            }
        )
    if not has_any and not extra_assessed and estimated is None:
        return _attach_unified_aliases(
            {
                "kraId": "kra1",
                "label": KRA_LABELS["kra1"],
                "assessed": False,
                "estimatedPoints": None,
                "currentPoints": 0,
                "targetPoints": int(round(max_pts)),
                "maxPoints": max_pts,
                "documentCount": doc_count,
                "statusLabel": "Not yet assessed",
                "breakdown": [],
                "teachingEffectiveness": te,
                "criteriaScores": criteria_scores,
            }
        )
    crit_disp = te.get("criterionADisplay") if isinstance(te.get("criterionADisplay"), dict) else {}
    status = (
        crit_disp.get("displayLabel")
        if crit_disp.get("displayLabel")
        else (
            "Estimated from eligible SET/SEF evidence"
            if estimated is not None
            else "Teaching evidence uploaded — scoring incomplete"
        )
    )
    return _attach_unified_aliases(
        {
            "kraId": "kra1",
            "label": KRA_LABELS["kra1"],
            "assessed": estimated is not None,
            "estimatedPoints": estimated,
            "validatedPoints": validated,
            "targetPoints": int(round(max_pts)),
            "maxPoints": max_pts,
            "documentCount": doc_count,
            "statusLabel": status,
            "breakdown": breakdown,
            "teachingEffectiveness": te,
            "criterionADisplay": crit_disp or None,
            "criteriaScores": criteria_scores,
        }
    )


def _set_sef_note(block: dict, *, validated_key: str) -> str:
    cov = block.get("coverageSummary") if isinstance(block.get("coverageSummary"), dict) else {}
    included = cov.get("includedPeriods")
    required = cov.get("requiredPeriods")
    if block.get(validated_key) is not None:
        return f"{included or 0} of {required or '—'} semester(s) in validated average."
    if block.get("provisionalPoints") is not None:
        return "Provisional component points — incomplete semester coverage or pending review."
    return (block.get("scoringNote") or "No component points yet.")[:120]


def _rank_thresholds(settings: dict) -> dict[str, Any]:
    raw = settings.get("rankUpgradeThresholds") or settings.get("rankThresholds")
    return raw if isinstance(raw, dict) else {}


def _build_checklist(
    profile: FacultyProfile,
    te: dict[str, Any],
    kra_points: dict[str, dict[str, Any]],
    *,
    config_complete: bool,
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if not config_complete:
        items.append(
            {
                "id": "config",
                "category": "configuration",
                "text": "Published official scoring configuration is incomplete or missing.",
            }
        )
    settings, _resolution = _published_settings()
    thresholds = _rank_thresholds(settings)
    if not thresholds:
        items.append(
            {
                "id": "rank_thresholds",
                "category": "configuration",
                "text": "Rank point thresholds are not configured in published Admin settings.",
            }
        )
    for label, block_key in (("SET", "set"), ("SEF", "sef")):
        block = te.get(block_key) if isinstance(te.get(block_key), dict) else {}
        for period in block.get("missingPeriods") or []:
            items.append({"id": f"missing_{block_key}", "category": "teaching", "text": f"{label}: {period}"})
        cov = block.get("coverageSummary") if isinstance(block.get("coverageSummary"), dict) else {}
        pending = (cov.get("totalUploads") or 0) - (cov.get("acceptedPeriods") or 0)
        if pending > 0:
            items.append(
                {
                    "id": f"pending_{block_key}",
                    "category": "review",
                    "text": f"{label}: {pending} semester upload(s) pending reviewer validation or incomplete scoring.",
                }
            )
    for key in ("kra2", "kra3", "kra4"):
        block = kra_points.get(key) or {}
        if not block.get("assessed"):
            items.append(
                {
                    "id": f"no_{key}",
                    "category": "kra",
                    "text": f"{KRA_LABELS[key]}: no assessed evidence yet.",
                }
            )
    target = (profile.target_rank or "").strip()
    if not target:
        items.append(
            {
                "id": "target_rank",
                "category": "profile",
                "text": "Target rank is not set on your faculty profile.",
            }
        )
    return items


def _eligibility_state(
    *,
    config_complete: bool,
    checklist: list[dict],
    weighted_estimated: float | None,
    required_score: float | None,
) -> tuple[str, str]:
    if not config_complete:
        return (
            ELIGIBILITY_CANNOT_DETERMINE,
            "Eligibility cannot be determined — published official scoring rules are incomplete.",
        )
    if weighted_estimated is not None and required_score is not None and weighted_estimated >= required_score:
        if not any(c["category"] == "review" for c in checklist):
            return (
                ELIGIBILITY_ELIGIBLE,
                "Estimated evidence meets configured weighted score threshold (simulation only — not official certification).",
            )
    if weighted_estimated is not None and weighted_estimated > 0:
        return (
            ELIGIBILITY_PROVISIONAL,
            "Estimated score suggests progress toward configured thresholds — not confirmed eligibility.",
        )
    if any(c["category"] == "profile" for c in checklist):
        return ELIGIBILITY_UNDER_ASSESSMENT, "Eligibility under assessment — complete your faculty profile (target rank)."
    if required_score is None:
        return (
            ELIGIBILITY_UNDER_ASSESSMENT,
            "Eligibility under assessment — rank point thresholds are not configured in published Admin settings.",
        )
    if checklist:
        return ELIGIBILITY_ADDITIONAL, "Additional requirements needed before rank upgrade simulation can show progress."
    return ELIGIBILITY_UNDER_ASSESSMENT, "Eligibility under assessment — upload and validate more evidence."


def compute_rank_simulation(profile: FacultyProfile) -> dict[str, Any]:
    """Evidence-based rank simulation payload for mobile/web (no DB writes)."""
    te = teaching_effectiveness_payload(profile)
    doc_counts = _doc_counts(profile)
    kra_points: dict[str, dict[str, Any]] = {}
    kra_points["kra1"] = _kra1_from_teaching(profile, te, doc_counts.get("kra1", 0))
    for key in ("kra2", "kra3", "kra4"):
        block = _kra_from_documents(profile, key, doc_counts.get(key, 0))
        kra_points[key] = _attach_unified_aliases(block)

    current_rank = profile.current_rank or ""
    target_rank = (profile.target_rank or "").strip()
    band, weights = weights_for_rank(current_rank)
    sim_settings, sim_resolution = _published_settings()
    published_row = sim_resolution.row or get_published_row()
    config_complete = bool(published_row) and bool(
        (te.get("configurationComplete") is True)
        or (kra_points["kra1"].get("teachingEffectiveness") and te.get("configurationComplete"))
    )
    if published_row and isinstance(published_row.settings_json, dict):
        set_sef = published_row.settings_json.get("setSefScoring")
        if isinstance(set_sef, dict) and not set_sef.get("officialFormulaVerified"):
            config_complete = False

    weighted_estimated = _weighted_estimated_total(kra_points, weights)

    thresholds = _rank_thresholds(sim_settings)
    target_key = target_rank or band
    threshold_entry = thresholds.get(target_rank) or thresholds.get(target_key) or thresholds.get(band)
    required_score = None
    if isinstance(threshold_entry, dict):
        try:
            required_score = float(threshold_entry.get("requiredWeightedScore") or threshold_entry.get("minimumScore"))
        except (TypeError, ValueError):
            required_score = None
    elif isinstance(threshold_entry, (int, float)):
        required_score = float(threshold_entry)

    checklist = _build_checklist(profile, te, kra_points, config_complete=config_complete)
    eligibility_code, eligibility_label = _eligibility_state(
        config_complete=config_complete,
        checklist=checklist,
        weighted_estimated=weighted_estimated,
        required_score=required_score,
    )

    progress_percent = None
    progress_label = "Assessment incomplete"
    if required_score is not None and required_score > 0:
        if weighted_estimated is not None:
            progress_percent = round(min(100.0, max(0.0, (weighted_estimated / required_score) * 100.0)), 1)
            progress_label = "Progress toward configured weighted score threshold (simulation)"
        else:
            progress_label = "Assessment incomplete — no scored KRA evidence yet"
    elif weighted_estimated is not None:
        progress_label = "Estimated weighted score available — rank threshold not configured"

    kra_list = [kra_points[k] for k in MOBILE_KRA_KEYS]
    estimated_sum = sum(
        float(kra_points[k].get("estimatedPoints") or 0)
        for k in MOBILE_KRA_KEYS
        if kra_points[k].get("assessed") and kra_points[k].get("estimatedPoints") is not None
    )
    validated_sum = sum(
        float(kra_points[k].get("validatedPoints") or 0)
        for k in MOBILE_KRA_KEYS
        if kra_points[k].get("assessed")
    )

    return {
        "currentRank": current_rank,
        "targetRank": target_rank,
        "nextPossibleRank": target_rank or "",
        "weightBand": band,
        "appliedWeights": weights,
        "kraConfigVersion": (
            sim_settings.get("version")
            or (published_row.settings_json or {}).get("version")
            if published_row and isinstance(published_row.settings_json, dict)
            else None
        ),
        "scoringConfiguration": resolution_metadata(sim_resolution),
        "rankWeightsPolicy": {
            "source": "published_admin_configuration"
            if (sim_settings.get("rankWeights") or (published_row.rank_weights if published_row else {}))
            else "table_22_defaults_in_engine",
            "publishedRankWeightsPresent": bool(
                sim_settings.get("rankWeights") or (published_row.rank_weights if published_row else {})
            ),
        },
        "scoringFormula": "Weighted Final Score = Σ (KRA points × Table 2.2 rank weight %)",
        "teachingEffectiveness": {
            "combinedProvisionalPoints": te.get("combinedProvisionalPoints"),
            "combinedValidatedPoints": te.get("combinedValidatedPoints"),
            "criterionMaxPoints": te.get("criterionMaxPoints"),
            "set": te.get("set"),
            "sef": te.get("sef"),
        },
        "estimatedTotalKraPoints": _round2(estimated_sum) if estimated_sum else 0,
        "estimatedKraPoints": _round2(estimated_sum) if estimated_sum else 0,
        "validatedKraPoints": _round2(validated_sum) if validated_sum else 0,
        "provisionalKraPoints": _round2(estimated_sum) if estimated_sum else None,
        "weightedEstimatedScore": weighted_estimated,
        "weightedValidatedScore": _weighted_total(kra_points, weights, use_validated=True),
        "weightedProvisionalScore": weighted_estimated,
        "requiredWeightedScore": required_score,
        "progressPercent": progress_percent,
        "progressLabel": progress_label,
        "eligibilityStatus": eligibility_code,
        "eligibilityLabel": eligibility_label,
        "missingRequirements": checklist,
        "kraScores": kra_list,
        "configurationComplete": config_complete,
        "currentPoints": int(round(estimated_sum)) if estimated_sum else 0,
        "requiredPoints": int(round(required_score)) if required_score is not None else 0,
        "areasToImprove": _areas_to_improve(kra_points, checklist),
        "disclaimer": SIMULATION_DISCLAIMER,
        "isDynamic": True,
    }


def _areas_to_improve(kra_points: dict[str, dict], checklist: list[dict]) -> list[dict]:
    areas: list[dict] = []
    for key in MOBILE_KRA_KEYS:
        block = kra_points.get(key) or {}
        max_pts = block.get("maxPoints") or 100
        current = block.get("estimatedPoints")
        if current is None:
            current = block.get("validatedPoints")
        if current is None:
            current = block.get("provisionalPoints") or 0
        try:
            room = max(0, int(round(float(max_pts) - float(current))))
        except (TypeError, ValueError):
            room = 0
        if room <= 0 and block.get("assessed"):
            continue
        guidance = next((c["text"] for c in checklist if c["id"] in (f"no_{key}", f"missing_{key}")), "")
        if not guidance and not block.get("assessed"):
            guidance = f"Upload evidence for {KRA_LABELS[key]} to include it in your simulation."
        elif not guidance:
            guidance = f"Additional validated points may still be earned in {KRA_LABELS[key]}."
        areas.append(
            {
                "kraId": key,
                "recommendedPoints": room,
                "guidance": guidance,
            }
        )
    return areas[:4]


def kra_scores_for_mobile(profile: FacultyProfile) -> list[dict]:
    sim = compute_rank_simulation(profile)
    return sim["kraScores"]


def simulation_for_mobile(profile: FacultyProfile) -> dict[str, Any]:
    sim = compute_rank_simulation(profile)
    return {
        "currentRank": sim["currentRank"],
        "targetRank": sim["nextPossibleRank"] or sim["targetRank"],
        "currentPoints": sim["currentPoints"],
        "requiredPoints": sim["requiredPoints"],
        "eligibilityLabel": sim["eligibilityLabel"],
        "eligibilityStatus": sim["eligibilityStatus"],
        "estimatedKraPoints": sim.get("estimatedKraPoints"),
        "estimatedTotalKraPoints": sim.get("estimatedTotalKraPoints"),
        "validatedKraPoints": sim["validatedKraPoints"],
        "provisionalKraPoints": sim["provisionalKraPoints"],
        "weightedEstimatedScore": sim.get("weightedEstimatedScore"),
        "weightedValidatedScore": sim["weightedValidatedScore"],
        "weightedProvisionalScore": sim["weightedProvisionalScore"],
        "teachingEffectivenessScore": sim["teachingEffectiveness"].get("combinedProvisionalPoints")
        or sim["teachingEffectiveness"].get("combinedValidatedPoints"),
        "disclaimer": sim.get("disclaimer") or SIMULATION_DISCLAIMER,
        "progressPercent": sim["progressPercent"],
        "progressLabel": sim["progressLabel"],
        "missingRequirements": sim["missingRequirements"],
        "areasToImprove": sim["areasToImprove"],
        "weightBand": sim["weightBand"],
        "appliedWeights": sim["appliedWeights"],
        "kraConfigVersion": sim.get("kraConfigVersion") or 0,
        "scoringFormula": sim["scoringFormula"],
        "configurationComplete": sim["configurationComplete"],
        "isDynamic": True,
        "isPlaceholder": False,
    }
