"""KRA II per-accomplishment accumulation (published criterion maximum)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kra_configuration.kra2_annex import (
    CRITERION_A_ID,
    CRITERION_B_ID,
    CRITERION_C_ID,
    CRITERION_MAX_POINTS,
    criterion_id_for_indicator,
    is_kra2_indicator,
    published_kra2_criterion_max_points,
    published_kra2_indicator_points,
)
from kra_configuration.published_limits import published_kra_max_points
from documents.kra2_evidence.bundle import (
    REVIEW_APPROVED,
    REVIEW_REJECTED,
    bundle_from_document,
    is_supporting_evidence_document,
)
from documents.kra2_evidence.validation import validate_kra2_bundle
from documents.scoring.document_evidence_points import effective_document_points


@dataclass(frozen=True)
class Kra2AccomplishmentScore:
    document_public_id: str
    indicator_id: str
    criterion_id: str
    accomplishment_id: str | None
    eligible_points: float
    assessed_points: float | None
    counted_points: float
    included: bool
    reasons: tuple[str, ...]


def _annex_fallback_allowed(*, applicable_config_present: bool) -> bool:
    return not applicable_config_present


def estimated_points_for_bundle(
    bundle: dict[str, Any] | None,
    *,
    indicator_id: str,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> float | None:
    if not isinstance(bundle, dict):
        return None
    base = published_kra2_indicator_points(
        indicator_id,
        settings,
        allow_annex_fallback=_annex_fallback_allowed(applicable_config_present=applicable_config_present),
    )
    if base is None:
        return None
    contribution = (bundle.get("contribution") or "").strip().lower()
    if contribution == "declared":
        try:
            pct = float(bundle.get("declaredContributionPercent"))
        except (TypeError, ValueError):
            return round(float(base), 2)
        pct = max(0.0, min(100.0, pct))
        return round(float(base) * (pct / 100.0), 2)
    return round(float(base), 2)


def is_qa_sandbox_accomplishment(doc: Any) -> bool:
    """Automated QA uploads — excluded from rank simulation and criterion totals."""
    title = (getattr(doc, "title", None) or "").strip()
    return title.startswith("[KRA2-B-QA]")


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
) -> Kra2AccomplishmentScore | None:
    criterion_id = (getattr(doc, "criterion_id", None) or "").strip()
    indicator_id = (getattr(doc, "indicator_id", None) or "").strip()
    if not is_kra2_indicator(indicator_id):
        return None
    if is_supporting_evidence_document(doc):
        return None
    if is_qa_sandbox_accomplishment(doc):
        return Kra2AccomplishmentScore(
            document_public_id=(getattr(doc, "public_id", None) or "").strip(),
            indicator_id=indicator_id,
            criterion_id=criterion_id or (criterion_id_for_indicator(indicator_id) or ""),
            accomplishment_id=None,
            eligible_points=0.0,
            assessed_points=None,
            counted_points=0.0,
            included=False,
            reasons=("qa_sandbox_excluded",),
        )

    bundle = bundle_from_document(doc)
    if not bundle:
        return None

    validation = validate_kra2_bundle(bundle, indicator_id=indicator_id)
    allow_fb = _annex_fallback_allowed(applicable_config_present=applicable_config_present)
    eligible_raw = published_kra2_indicator_points(
        indicator_id,
        settings,
        allow_annex_fallback=allow_fb,
    )
    eligible = float(eligible_raw) if eligible_raw is not None else 0.0
    pub_id = (getattr(doc, "public_id", None) or "").strip()
    crit = criterion_id or (criterion_id_for_indicator(indicator_id) or "")

    if not validation.get("readyForScoring"):
        return Kra2AccomplishmentScore(
            document_public_id=pub_id,
            indicator_id=indicator_id,
            criterion_id=crit,
            accomplishment_id=bundle.get("accomplishmentId"),
            eligible_points=round(float(eligible), 2),
            assessed_points=None,
            counted_points=0.0,
            included=False,
            reasons=tuple(validation.get("flags") or ("not_ready_for_scoring",)),
        )

    assessment = bundle.get("reviewerAssessment") if isinstance(bundle.get("reviewerAssessment"), dict) else {}
    if (bundle.get("reviewStatus") or "") != REVIEW_APPROVED:
        return Kra2AccomplishmentScore(
            document_public_id=pub_id,
            indicator_id=indicator_id,
            criterion_id=crit,
            accomplishment_id=bundle.get("accomplishmentId"),
            eligible_points=round(float(eligible), 2),
            assessed_points=None,
            counted_points=0.0,
            included=False,
            reasons=("review_not_approved",),
        )

    assessed = assessment.get("approvedPoints")
    if assessed is None:
        assessed = assessment.get("assessedPoints")
    try:
        counted = round(float(assessed), 2) if assessed is not None else round(float(eligible), 2)
    except (TypeError, ValueError):
        counted = round(float(eligible), 2)

    return Kra2AccomplishmentScore(
        document_public_id=pub_id,
        indicator_id=indicator_id,
        criterion_id=crit,
        accomplishment_id=bundle.get("accomplishmentId"),
        eligible_points=round(float(eligible), 2),
        assessed_points=round(float(assessed), 2) if assessed is not None else None,
        counted_points=counted,
        included=True,
        reasons=(),
    )


def aggregate_kra2_criterion_from_documents(
    docs: list[Any],
    *,
    criterion_id: str,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> dict[str, Any]:
    cap = published_kra2_criterion_max_points(
        criterion_id,
        settings,
        allow_annex_fallback=_annex_fallback_allowed(applicable_config_present=applicable_config_present),
    )
    if cap is None:
        return {
            "criterionId": criterion_id,
            "estimatedPoints": None,
            "maxPoints": None,
            "assessed": False,
            "documentCount": len(docs),
            "scoringSource": "configuration_incomplete",
            "aggregationPolicy": "per_accomplishment_sum_cap",
            "accomplishments": [],
        }
    criterion_max = float(cap)

    bundle_docs = [
        d
        for d in docs
        if bundle_from_document(d) and not is_supporting_evidence_document(d)
    ]
    bundle_indicator_ids = {
        (getattr(d, "indicator_id", None) or "").strip()
        for d in bundle_docs
        if (getattr(d, "indicator_id", None) or "").strip()
    }
    legacy_docs = [
        d
        for d in docs
        if d not in bundle_docs
        and not is_supporting_evidence_document(d)
        and (getattr(d, "indicator_id", None) or "").strip() not in bundle_indicator_ids
    ]

    estimate_by_accomplishment: dict[str, float] = {}
    validated_by_accomplishment: dict[str, float] = {}
    accomplishment_rows: list[Kra2AccomplishmentScore] = []

    for doc in bundle_docs:
        if is_qa_sandbox_accomplishment(doc):
            continue
        bundle = bundle_from_document(doc)
        if not isinstance(bundle, dict):
            continue
        dedup_key = _accomplishment_dedup_key(bundle, doc)
        if not dedup_key:
            continue
        review_status = (bundle.get("reviewStatus") or "").strip().lower()
        if review_status == REVIEW_REJECTED:
            continue

        indicator_id = (getattr(doc, "indicator_id", None) or "").strip()
        if review_status == REVIEW_APPROVED:
            row = score_accomplishment_document(
                doc,
                settings=settings,
                applicable_config_present=applicable_config_present,
            )
            if row and row.included:
                accomplishment_rows.append(row)
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

    from documents.kra2_evidence.group_caps import apply_group_caps

    ind_by_key: dict[str, str] = {}
    bundle_by_key: dict[str, dict[str, Any]] = {}
    for doc in bundle_docs:
        bundle = bundle_from_document(doc)
        if not isinstance(bundle, dict):
            continue
        key = _accomplishment_dedup_key(bundle, doc)
        if key:
            ind_by_key[key] = (getattr(doc, "indicator_id", None) or "").strip()
            bundle_by_key[key] = bundle

    from documents.kra2_evidence.patent_deduplication import apply_patent_highest_stage_only

    validated_by_accomplishment = apply_patent_highest_stage_only(
        validated_by_accomplishment,
        bundle_by_key=bundle_by_key,
        indicator_by_key=ind_by_key,
    )
    estimate_by_accomplishment = apply_patent_highest_stage_only(
        estimate_by_accomplishment,
        bundle_by_key=bundle_by_key,
        indicator_by_key=ind_by_key,
    )

    validated_by_accomplishment = apply_group_caps(
        validated_by_accomplishment,
        indicator_by_accomplishment=ind_by_key,
    )
    estimate_by_accomplishment = apply_group_caps(
        estimate_by_accomplishment,
        indicator_by_accomplishment=ind_by_key,
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

    combined_estimate = raw_estimate + legacy_total
    combined_validated = raw_sum + legacy_total
    estimated_total = round(min(combined_estimate, criterion_max), 2)
    validated_total = round(min(combined_validated, criterion_max), 2)
    assessed = estimated_total > 0 or validated_total > 0

    return {
        "criterionId": criterion_id,
        "estimatedPoints": estimated_total if estimated_total > 0 else None,
        "validatedPoints": validated_total if validated_total > 0 else 0.0,
        "maxPoints": criterion_max,
        "assessed": assessed,
        "documentCount": len(docs),
        "scoringSource": "kra2_evidence_bundle",
        "aggregationPolicy": "per_accomplishment_sum_cap",
        "rawAccomplishmentSum": round(raw_sum, 2),
        "rawEstimatedSum": round(raw_estimate, 2),
        "legacyCompanionPoints": round(legacy_total, 2) if legacy_docs else None,
        "accomplishments": [
            {
                "documentId": r.document_public_id,
                "indicatorId": r.indicator_id,
                "accomplishmentId": r.accomplishment_id,
                "countedPoints": r.counted_points,
                "eligiblePoints": r.eligible_points,
            }
            for r in accomplishment_rows
        ],
    }


def aggregate_kra2_a_from_documents(
    docs: list[Any],
    *,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> dict[str, Any]:
    return aggregate_kra2_criterion_from_documents(
        docs,
        criterion_id=CRITERION_A_ID,
        settings=settings,
        applicable_config_present=applicable_config_present,
    )


def aggregate_kra2_kra_from_documents(
    docs: list[Any],
    *,
    settings: dict[str, Any] | None = None,
    applicable_config_present: bool = False,
) -> dict[str, Any]:
    """
    KRA II total: sum of criterion totals (A, B, C), each already capped at 100, then cap at KRA max (100).
    Estimated and validated totals remain separate.
    """
    kra_max_raw = published_kra_max_points("kra2", settings)
    kra_max = float(kra_max_raw) if kra_max_raw is not None else float(CRITERION_MAX_POINTS)

    by_criterion: dict[str, list[Any]] = {CRITERION_A_ID: [], CRITERION_B_ID: [], CRITERION_C_ID: []}
    for doc in docs:
        cid = (getattr(doc, "criterion_id", None) or "").strip()
        if cid in by_criterion:
            by_criterion[cid].append(doc)

    criterion_blocks: dict[str, dict[str, Any]] = {}
    est_sum = 0.0
    val_sum = 0.0
    for cid, subset in by_criterion.items():
        block = aggregate_kra2_criterion_from_documents(
            subset,
            criterion_id=cid,
            settings=settings,
            applicable_config_present=applicable_config_present,
        )
        criterion_blocks[cid] = block
        if block.get("estimatedPoints") is not None:
            est_sum += float(block["estimatedPoints"])
        val_sum += float(block.get("validatedPoints") or 0.0)

    est_total = round(min(est_sum, kra_max), 2)
    val_total = round(min(val_sum, kra_max), 2)
    assessed = est_total > 0 or val_total > 0

    return {
        "kraId": "kra2",
        "estimatedPoints": est_total if est_total > 0 else None,
        "validatedPoints": val_total if val_total > 0 else 0.0,
        "maxPoints": kra_max,
        "assessed": assessed,
        "documentCount": len(docs),
        "scoringSource": "kra2_evidence_bundle",
        "aggregationPolicy": "criteria_sum_cap_at_kra_max",
        "criterionTotals": {
            cid: {
                "estimatedPoints": criterion_blocks[cid].get("estimatedPoints"),
                "validatedPoints": criterion_blocks[cid].get("validatedPoints"),
                "maxPoints": criterion_blocks[cid].get("maxPoints"),
            }
            for cid in by_criterion
        },
    }
