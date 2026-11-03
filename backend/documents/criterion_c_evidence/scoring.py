"""Criterion C per-service accumulation (published criterion maximum)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kra_configuration.criterion_c_annex import (
    CRITERION_C_ID,
    CRITERION_C_MAX_POINTS,
    published_criterion_c_max_points,
    published_points_for_indicator,
)
from documents.criterion_c_evidence.bundle import (
    REVIEW_APPROVED,
    REVIEW_REJECTED,
    bundle_from_document,
    is_supporting_evidence_document,
)
from documents.criterion_c_evidence.validation import validate_criterion_c_bundle
from documents.scoring.document_evidence_points import effective_document_points


@dataclass(frozen=True)
class CriterionCServiceScore:
    document_public_id: str
    indicator_id: str
    accomplishment_id: str | None
    eligible_points: float
    assessed_points: float | None
    counted_points: float
    included: bool
    reasons: tuple[str, ...]


def _annex_fallback_allowed(*, applicable_config_present: bool) -> bool:
    return not applicable_config_present


def _resolve_criterion_cap(
    settings: dict[str, Any] | None,
    *,
    applicable_config_present: bool,
) -> float | None:
    return published_criterion_c_max_points(
        settings,
        allow_annex_fallback=_annex_fallback_allowed(applicable_config_present=applicable_config_present),
    )


def estimated_points_for_bundle(
    bundle: dict[str, Any] | None,
    *,
    indicator_id: str,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> float | None:
    if not isinstance(bundle, dict):
        return None
    pts = published_points_for_indicator(
        indicator_id,
        settings,
        allow_annex_fallback=_annex_fallback_allowed(applicable_config_present=applicable_config_present),
    )
    return round(float(pts), 2) if pts is not None else None


def _accomplishment_dedup_key(bundle: dict[str, Any], doc: Any) -> str:
    aid = (bundle.get("accomplishmentId") or "").strip()
    if aid:
        return aid
    return (getattr(doc, "public_id", None) or "").strip()


def score_accomplishment_document(
    doc: Any,
    *,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> CriterionCServiceScore | None:
    if (getattr(doc, "criterion_id", None) or "").strip() != CRITERION_C_ID:
        return None
    if is_supporting_evidence_document(doc):
        return None

    indicator_id = (getattr(doc, "indicator_id", None) or "").strip()
    bundle = bundle_from_document(doc)
    if not bundle:
        return None

    validation = validate_criterion_c_bundle(bundle)
    allow_fb = _annex_fallback_allowed(applicable_config_present=applicable_config_present)
    eligible_raw = published_points_for_indicator(indicator_id, settings, allow_annex_fallback=allow_fb)
    eligible = float(eligible_raw) if eligible_raw is not None else 0.0
    pub_id = (getattr(doc, "public_id", None) or "").strip()

    if not validation.get("readyForScoring"):
        return CriterionCServiceScore(
            document_public_id=pub_id,
            indicator_id=indicator_id,
            accomplishment_id=bundle.get("accomplishmentId"),
            eligible_points=round(float(eligible), 2),
            assessed_points=None,
            counted_points=0.0,
            included=False,
            reasons=tuple(validation.get("flags") or ("not_ready_for_scoring",)),
        )

    assessment = bundle.get("reviewerAssessment") if isinstance(bundle.get("reviewerAssessment"), dict) else {}
    if (bundle.get("reviewStatus") or "") != REVIEW_APPROVED:
        return CriterionCServiceScore(
            document_public_id=pub_id,
            indicator_id=indicator_id,
            accomplishment_id=bundle.get("accomplishmentId"),
            eligible_points=round(float(eligible), 2),
            assessed_points=None,
            counted_points=0.0,
            included=False,
            reasons=("review_not_approved",),
        )

    assessed = assessment.get("assessedPoints")
    try:
        counted = round(float(assessed), 2) if assessed is not None else round(float(eligible), 2)
    except (TypeError, ValueError):
        counted = round(float(eligible), 2)

    return CriterionCServiceScore(
        document_public_id=pub_id,
        indicator_id=indicator_id,
        accomplishment_id=bundle.get("accomplishmentId"),
        eligible_points=round(float(eligible), 2),
        assessed_points=round(float(assessed), 2) if assessed is not None else None,
        counted_points=counted,
        included=True,
        reasons=(),
    )


def aggregate_criterion_c_from_documents(
    docs: list[Any],
    *,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> dict[str, Any]:
    """
    Sum eligible distinct services (bundle-backed), cap at published Criterion C maximum.
    Legacy documents without bundles use best-per-indicator fallback (historical).
    """
    cap = _resolve_criterion_cap(settings, applicable_config_present=applicable_config_present)
    if cap is None:
        return {
            "criterionId": CRITERION_C_ID,
            "estimatedPoints": None,
            "maxPoints": None,
            "assessed": False,
            "documentCount": len(docs),
            "scoringSource": "configuration_incomplete",
            "aggregationPolicy": "per_service_sum_cap",
            "services": [],
        }
    criterion_max = float(cap)

    bundle_docs = [
        d
        for d in docs
        if bundle_from_document(d) and not is_supporting_evidence_document(d)
    ]
    legacy_docs = [
        d
        for d in docs
        if d not in bundle_docs and not is_supporting_evidence_document(d)
    ]

    service_rows: list[CriterionCServiceScore] = []
    estimate_by_accomplishment: dict[str, float] = {}
    validated_by_accomplishment: dict[str, float] = {}

    for doc in bundle_docs:
        bundle = bundle_from_document(doc)
        if not isinstance(bundle, dict):
            continue
        dedup_key = _accomplishment_dedup_key(bundle, doc)
        if not dedup_key:
            continue
        review_status = (bundle.get("reviewStatus") or "").strip().lower()
        if review_status == REVIEW_REJECTED:
            continue
        if "duplicate_service_suspected" in (bundle.get("duplicateFlags") or []):
            continue

        indicator_id = (getattr(doc, "indicator_id", None) or "").strip()
        if review_status == REVIEW_APPROVED:
            row = score_accomplishment_document(
                doc,
                settings=settings,
                applicable_config_present=applicable_config_present,
            )
            if row and row.included:
                service_rows.append(row)
                validated_by_accomplishment[dedup_key] = max(
                    validated_by_accomplishment.get(dedup_key, 0.0),
                    row.counted_points,
                )
                estimate_by_accomplishment[dedup_key] = validated_by_accomplishment[dedup_key]
            continue

        est = estimated_points_for_bundle(
            bundle,
            indicator_id=indicator_id,
            settings=settings,
            applicable_config_present=applicable_config_present,
        )
        if est is not None and est > 0:
            estimate_by_accomplishment[dedup_key] = max(
                estimate_by_accomplishment.get(dedup_key, 0.0),
                float(est),
            )

    raw_sum = sum(validated_by_accomplishment.values())
    raw_estimate = sum(estimate_by_accomplishment.values())

    legacy_total = 0.0
    if legacy_docs:
        best_by_indicator: dict[str, float] = {}
        for doc in legacy_docs:
            pts = effective_document_points(doc)
            if pts is None:
                continue
            key = (getattr(doc, "indicator_id", None) or getattr(doc, "public_id", "") or "").strip()
            prev = best_by_indicator.get(key)
            if prev is None or pts > prev:
                best_by_indicator[key] = pts
        legacy_total = sum(best_by_indicator.values())
        legacy_total = min(legacy_total, criterion_max)

    has_bundle_path = bool(bundle_docs)
    if has_bundle_path or estimate_by_accomplishment or validated_by_accomplishment or service_rows:
        combined_estimate = raw_estimate + legacy_total
        combined_validated = raw_sum + legacy_total
        estimated_total = round(min(combined_estimate, criterion_max), 2)
        validated_total = round(min(combined_validated, criterion_max), 2)
        assessed = estimated_total > 0 or validated_total > 0
        policy = "per_service_sum_cap"
        if legacy_docs and service_rows:
            policy = "hybrid_per_service_plus_legacy_cap"
        elif legacy_docs and not service_rows:
            policy = "legacy_best_per_indicator_with_bundle_primaries_pending"
        return {
            "criterionId": CRITERION_C_ID,
            "estimatedPoints": estimated_total if estimated_total > 0 else None,
            "validatedPoints": validated_total if validated_total > 0 else 0.0,
            "maxPoints": criterion_max,
            "assessed": assessed,
            "documentCount": len(docs),
            "scoringSource": "criterion_c_per_service",
            "aggregationPolicy": policy,
            "rawServiceSum": round(raw_sum, 2),
            "rawEstimatedSum": round(raw_estimate, 2),
            "legacyCompanionPoints": round(legacy_total, 2) if legacy_docs else None,
            "services": [
                {
                    "documentId": r.document_public_id,
                    "indicatorId": r.indicator_id,
                    "accomplishmentId": r.accomplishment_id,
                    "countedPoints": r.counted_points,
                    "eligiblePoints": r.eligible_points,
                }
                for r in service_rows
            ],
        }

    if legacy_docs:
        total = round(min(legacy_total, criterion_max), 2)
        has_evidence = any(effective_document_points(d) is not None for d in legacy_docs)
        return {
            "criterionId": CRITERION_C_ID,
            "estimatedPoints": total if has_evidence and total > 0 else None,
            "validatedPoints": total if has_evidence and total > 0 else 0.0,
            "maxPoints": criterion_max,
            "assessed": has_evidence and total > 0,
            "documentCount": len(docs),
            "scoringSource": "legacy_document_points",
            "aggregationPolicy": "legacy_best_per_indicator",
            "services": [],
        }

    return {
        "criterionId": CRITERION_C_ID,
        "estimatedPoints": None,
        "maxPoints": criterion_max,
        "assessed": False,
        "documentCount": len(docs),
        "scoringSource": "none",
        "aggregationPolicy": "per_service_sum_cap",
        "services": [],
    }
