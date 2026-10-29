"""KRA configuration draft/publish logic (PostgreSQL `kra_configuration`)."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any

from config import Config
from documents.scoring.section10 import default_evaluation_coverage
from kra_configuration.verified_scoring import apply_verified_scoring_to_settings, assess_publish_readiness
from extensions import db
from models import KraConfiguration, User

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_SUPERSEDED = "superseded"


def default_set_sef_scoring() -> dict[str, Any]:
    return {
        "officialFormulaVerified": False,
        "aggregationMethod": None,
        "roundingRule": None,
        "formulaReference": "",
        "incompleteReason": (
            "SET/SEF OSETR/OSEFR aggregation, evaluation coverage, and Section 10 divisor "
            "rules must be verified against the applicable DBM–CHED circular before official scoring."
        ),
    }


def empty_kra_settings() -> dict[str, Any]:
    return {"kras": {}, "criteria": {}, "indicators": {}, "indicatorMeta": {}}


def kra_settings_from_json(settings_json: dict | None) -> dict[str, Any]:
    root = settings_json if isinstance(settings_json, dict) else {}
    blob = empty_kra_settings()
    for key in blob:
        value = root.get(key)
        if isinstance(value, dict):
            blob[key] = deepcopy(value)
    rank = root.get("rankWeights")
    if isinstance(rank, dict):
        blob["rankWeights"] = deepcopy(rank)
    for key in ("rankUpgradeThresholds", "rankThresholds"):
        value = root.get(key)
        if isinstance(value, dict):
            blob[key] = deepcopy(value)
    return blob


def metadata_from_json(settings_json: dict | None) -> dict[str, Any]:
    root = settings_json if isinstance(settings_json, dict) else {}
    set_sef = root.get("setSefScoring")
    if not isinstance(set_sef, dict):
        set_sef = default_set_sef_scoring()
    return {
        "version": root.get("version"),
        "effectiveFrom": root.get("effectiveFrom"),
        "effectiveTo": root.get("effectiveTo"),
        "evaluationCoverage": root.get("evaluationCoverage")
        or root.get("teachingEffectivenessCoverage"),
        "setSefAggregationMethod": root.get("setSefAggregationMethod"),
        "roundingRule": root.get("roundingRule") or set_sef.get("roundingRule"),
        "ratingScaleDefault": root.get("ratingScaleDefault"),
        "setSefScoring": deepcopy(set_sef),
    }


def configuration_to_api(row: KraConfiguration) -> dict[str, Any]:
    sj = row.settings_json if isinstance(row.settings_json, dict) else {}
    return {
        "id": row.id,
        "status": row.status,
        "guidelineLabel": row.guideline_label,
        "publishedAt": row.published_at.isoformat() if row.published_at else None,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        "metadata": metadata_from_json(sj),
        "kraSettings": kra_settings_from_json(sj),
        "rankWeights": row.rank_weights if isinstance(row.rank_weights, dict) else {},
    }


def version_summary(row: KraConfiguration) -> dict[str, Any]:
    sj = row.settings_json if isinstance(row.settings_json, dict) else {}
    return {
        "id": row.id,
        "status": row.status,
        "version": sj.get("version"),
        "guidelineLabel": row.guideline_label,
        "effectiveFrom": sj.get("effectiveFrom"),
        "effectiveTo": sj.get("effectiveTo"),
        "publishedAt": row.published_at.isoformat() if row.published_at else None,
        "setSefFormulaVerified": (sj.get("setSefScoring") or {}).get("officialFormulaVerified"),
    }


def get_draft_row() -> KraConfiguration | None:
    return KraConfiguration.query.filter_by(status=STATUS_DRAFT).order_by(KraConfiguration.updated_at.desc()).first()


def get_published_row() -> KraConfiguration | None:
    return (
        KraConfiguration.query.filter(
            KraConfiguration.status == STATUS_PUBLISHED,
            KraConfiguration.published_at.isnot(None),
        )
        .order_by(KraConfiguration.published_at.desc())
        .first()
    )


def list_history_rows() -> list[KraConfiguration]:
    return (
        KraConfiguration.query.filter(
            KraConfiguration.status.in_((STATUS_PUBLISHED, STATUS_SUPERSEDED))
        )
        .order_by(KraConfiguration.published_at.desc().nullslast(), KraConfiguration.id.desc())
        .all()
    )


def _merge_settings_json(existing: dict | None, body: dict) -> dict[str, Any]:
    base = deepcopy(existing) if isinstance(existing, dict) else {}
    kra = body.get("kraSettings") or body.get("settings") or {}
    metadata = body.get("metadata") or {}

    if isinstance(kra, dict):
        for key in ("kras", "criteria", "indicators", "indicatorMeta"):
            if key in kra and isinstance(kra[key], dict):
                base[key] = deepcopy(kra[key])
        if isinstance(kra.get("rankWeights"), dict):
            base["rankWeights"] = deepcopy(kra["rankWeights"])

    if isinstance(body.get("rankWeights"), dict):
        base["rankWeights"] = deepcopy(body["rankWeights"])

    for field in (
        "version",
        "effectiveFrom",
        "effectiveTo",
        "evaluationCoverage",
        "teachingEffectivenessCoverage",
        "setSefAggregationMethod",
        "roundingRule",
        "ratingScaleDefault",
    ):
        if field in metadata and metadata[field] is not None:
            base[field] = metadata[field]

    if "setSefScoring" in metadata and isinstance(metadata["setSefScoring"], dict):
        merged = deepcopy(base.get("setSefScoring") or default_set_sef_scoring())
        merged.update(metadata["setSefScoring"])
        base["setSefScoring"] = merged
    elif "setSefScoring" not in base:
        base["setSefScoring"] = default_set_sef_scoring()

    if "evaluationCoverage" not in base or not isinstance(base.get("evaluationCoverage"), dict):
        base["evaluationCoverage"] = default_evaluation_coverage()

    return base


def _rank_weights_from_settings(settings_json: dict) -> dict:
    rw = settings_json.get("rankWeights")
    return deepcopy(rw) if isinstance(rw, dict) else {}


def save_draft(_admin: User, body: dict) -> KraConfiguration:
    row = get_draft_row()
    settings_json = _merge_settings_json(row.settings_json if row else None, body)
    rank_weights = _rank_weights_from_settings(settings_json)
    guideline = (body.get("guidelineLabel") or body.get("guideline_label") or Config.GUIDELINE_LABEL).strip()

    if row:
        row.settings_json = settings_json
        row.rank_weights = rank_weights
        row.guideline_label = guideline or row.guideline_label
    else:
        row = KraConfiguration(
            guideline_label=guideline or Config.GUIDELINE_LABEL,
            status=STATUS_DRAFT,
            published_at=None,
            rank_weights=rank_weights,
            settings_json=settings_json,
        )
        db.session.add(row)
    db.session.commit()
    return row


def _parse_effective_date(raw: str | None) -> date | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def validate_publish_payload(settings_json: dict, publish_body: dict) -> tuple[dict, str | None]:
    """Return merged publish settings with system verified SET/SEF metadata, or an error code."""
    meta = publish_body.get("metadata") if isinstance(publish_body.get("metadata"), dict) else {}
    effective_from = meta.get("effectiveFrom") or publish_body.get("effectiveFrom")
    merged = deepcopy(settings_json)

    if meta.get("effectiveTo"):
        merged["effectiveTo"] = str(meta["effectiveTo"])[:10]
    if meta.get("evaluationCoverage"):
        merged["evaluationCoverage"] = deepcopy(meta["evaluationCoverage"])
    if meta.get("roundingRule"):
        merged["roundingRule"] = meta["roundingRule"]

    if not (effective_from or "").strip():
        return merged, "effective_from_required"

    try:
        merged = apply_verified_scoring_to_settings(merged, effective_from=str(effective_from)[:10])
    except ValueError as exc:
        return merged, str(exc)

    return merged, None


def preview_publish_validation(publish_body: dict) -> dict:
    """Validate the current draft for publishing (no database writes)."""
    draft = get_draft_row()
    if not draft:
        return {
            "ready": False,
            "errors": ["draft_required"],
            "checks": [
                {
                    "id": "draft",
                    "ok": False,
                    "message": "Save a draft configuration before publishing.",
                }
            ],
            "summary": None,
            "effectiveFrom": None,
        }
    meta = publish_body.get("metadata") if isinstance(publish_body.get("metadata"), dict) else {}
    effective_from = meta.get("effectiveFrom") or publish_body.get("effectiveFrom")
    return assess_publish_readiness(draft.settings_json or {}, effective_from=effective_from)


def next_configuration_version() -> int:
    latest = (
        KraConfiguration.query.filter(
            KraConfiguration.status.in_((STATUS_PUBLISHED, STATUS_SUPERSEDED))
        )
        .order_by(KraConfiguration.id.desc())
        .first()
    )
    if not latest or not isinstance(latest.settings_json, dict):
        return 1
    current = latest.settings_json.get("version")
    try:
        return int(current) + 1
    except (TypeError, ValueError):
        return 1


def publish_draft(_admin: User, body: dict) -> KraConfiguration:
    draft = get_draft_row()
    if not draft:
        raise ValueError("draft_required")

    settings_json, error = validate_publish_payload(draft.settings_json or {}, body)
    if error:
        raise ValueError(error)

    settings_json = deepcopy(settings_json)
    settings_json["version"] = body.get("version") or next_configuration_version()
    guideline = (
        body.get("guidelineLabel")
        or body.get("guideline_label")
        or draft.guideline_label
        or Config.GUIDELINE_LABEL
    ).strip()

    now = datetime.now(timezone.utc)
    for prev in KraConfiguration.query.filter_by(status=STATUS_PUBLISHED).all():
        prev.status = STATUS_SUPERSEDED

    published = KraConfiguration(
        guideline_label=guideline,
        status=STATUS_PUBLISHED,
        published_at=now,
        rank_weights=_rank_weights_from_settings(settings_json),
        settings_json=settings_json,
    )
    db.session.add(published)
    db.session.commit()
    return published


def get_version_by_id(config_id: int) -> KraConfiguration | None:
    return KraConfiguration.query.filter(
        KraConfiguration.id == config_id,
        KraConfiguration.status.in_((STATUS_PUBLISHED, STATUS_SUPERSEDED, STATUS_DRAFT)),
    ).first()
