"""SET/SEF semester aggregation using published Admin scoring configuration."""

from __future__ import annotations

import re
from typing import Any

from models import Document, DocumentTeachingEvaluation

from documents.scoring.circular_formula import (
    indicator_points_from_overall_rating,
    is_supported_aggregation,
    overall_rating_from_semesters,
    provisional_average,
)
from documents.scoring.config_loader import (
    CRITERION_A_ID,
    SET_INDICATOR,
    SEF_INDICATOR,
    criterion_a_max_points,
    indicator_scoring_config,
    published_settings_root,
)
from documents.scoring.section10 import resolve_divisor
from documents.review_display import review_display_status
from documents.status_map import document_status_to_web

_RATING_FRACTION = re.compile(
    r"(\d{1,3}(?:\.\d+)?)\s*(?:/|\s+out\s+of\s+)\s*(\d{1,3}(?:\.\d+)?)",
    re.IGNORECASE,
)
_RATING_PERCENT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%", re.IGNORECASE)

_APPROVED = frozenset({"approved", "valid"})
_PENDING = frozenset({"pending_review", "reviewer_required", "needs_revision"})
_REJECTED = frozenset({"rejected"})


def parse_rating_percent(raw: str | None, default_scale: float = 100.0) -> tuple[float | None, float | None]:
    text = (raw or "").strip()
    if not text:
        return None, None
    match = _RATING_FRACTION.search(text)
    if match:
        num, denom = float(match.group(1)), float(match.group(2))
        if denom <= 0:
            return None, None
        return round(num / denom * 100.0, 4), denom
    pct = _RATING_PERCENT.search(text)
    if pct:
        return round(float(pct.group(1)), 4), default_scale
    try:
        val = float(text)
        if val <= default_scale and val > 0:
            return round(val / default_scale * 100.0, 4) if default_scale else val, default_scale
    except ValueError:
        pass
    return None, None


def _effective_fields(doc: Document) -> dict:
    info = dict(doc.extracted_info or {})
    return {
        "academicYear": (info.get("Academic year") or "").strip(),
        "semester": (info.get("Semester") or "").strip(),
        "ratingRaw": (info.get("Extracted rating") or "").strip(),
        "ratingScaleRaw": (info.get("Rating scale") or "").strip(),
        "facultyName": (info.get("Faculty name") or info.get("Extracted names") or "").strip(),
        "evaluationType": (info.get("Evaluation type") or "").strip(),
        "verification": (info.get("Indicator verification status") or "").strip(),
    }


def _review_bucket(status: str | None) -> str:
    """Map stored document status to scoring inclusion bucket.

    ``approved`` / ``valid`` count as *accepted* for SET/SEF simulation scoring only —
    not as official certification of uploaded PDFs.
    """
    st = (status or "").strip().lower()
    if st in _APPROVED:
        return "accepted"
    if st in _REJECTED:
        return "rejected"
    if st == "needs_revision":
        return "revision"
    if st in _PENDING or st == "draft":
        return "pending"
    return "pending"


def _period_rank(bucket: str) -> int:
    return {"accepted": 4, "pending": 3, "revision": 2, "rejected": 1, "incomplete": 0}.get(bucket, 0)


def _iter_teaching_evaluations(doc: Document) -> list[Any]:
    rel = getattr(doc, "teaching_evaluations", None)
    if rel is None:
        return []
    try:
        return list(rel.all())
    except AttributeError:
        try:
            return list(rel)
        except TypeError:
            return []


def _tev_review_bucket(reviewer_status: str | None, *, incomplete: bool) -> str:
    if incomplete:
        return "incomplete"
    st = (reviewer_status or "").strip().lower().replace("-", "_")
    if st in _APPROVED:
        return "accepted"
    if st in _REJECTED:
        return "rejected"
    if st == "needs_revision":
        return "revision"
    if st in _PENDING or not st:
        return "pending"
    return "pending"


def _tev_incomplete(meta: dict) -> bool:
    if not isinstance(meta, dict):
        return False
    if meta.get("missingFields"):
        return True
    return meta.get("extractionStatus") in ("partial", "ambiguous")


def teaching_evaluation_period_row(
    tev: DocumentTeachingEvaluation | Any,
    doc: Document,
    *,
    default_scale: float = 100.0,
) -> dict:
    meta = dict(getattr(tev, "extracted_metadata", None) or {})
    incomplete = _tev_incomplete(meta)
    scale = getattr(tev, "rating_scale", None) or default_scale
    try:
        scale = float(scale)
    except (TypeError, ValueError):
        scale = default_scale
    rating_pct = getattr(tev, "rating_percent", None)
    scale_used = scale
    rating_raw = (getattr(tev, "rating_raw", None) or "").strip()
    if rating_pct is None and rating_raw:
        rating_pct, scale_used = parse_rating_percent(rating_raw, default_scale=scale)
    bucket = _tev_review_bucket(getattr(tev, "reviewer_validation_status", None), incomplete=incomplete)
    return {
        "teachingEvaluationId": getattr(tev, "public_id", None),
        "documentId": doc.public_id,
        "fileName": doc.file_name,
        "academicYear": getattr(tev, "academic_year", None) or None,
        "semester": getattr(tev, "semester", None) or None,
        "ratingRaw": rating_raw or None,
        "ratingPercent": rating_pct,
        "ratingScale": scale_used,
        "facultyName": (meta.get("facultyName") or meta.get("Faculty name") or None),
        "evaluationType": getattr(tev, "evaluation_type", None),
        "ocrVerificationStatus": getattr(tev, "ocr_verification_status", None),
        "reviewStatus": document_status_to_web_from_tev(getattr(tev, "reviewer_validation_status", None)),
        "reviewerValidationStatus": document_status_to_web_from_tev(
            getattr(tev, "reviewer_validation_status", None)
        ),
        "reviewDisplayStatus": document_status_to_web_from_tev(getattr(tev, "reviewer_validation_status", None)),
        "approvalDecisionSource": None,
        "autoValidation": None,
        "reviewBucket": bucket,
        "ocrStatus": doc.ocr_status,
        "submittedAt": doc.submitted_at.isoformat() if doc.submitted_at else None,
        "sourceSectionRef": getattr(tev, "source_section_ref", None),
        "incompleteExtraction": incomplete,
    }


def document_status_to_web_from_tev(reviewer_status: str | None) -> str:
    st = (reviewer_status or "").strip().lower().replace("-", "_")
    if not st:
        return "pending-review"
    from documents.status_map import DB_TO_WEB

    return DB_TO_WEB.get(st, st.replace("_", "-"))


def collect_period_rows(
    docs: list[Document],
    indicator_id: str,
    *,
    default_scale: float = 100.0,
) -> list[dict]:
    """Build semester rows from linked evaluations, with legacy document fallback."""
    rows: list[dict] = []
    for doc in docs:
        children = [
            tev
            for tev in _iter_teaching_evaluations(doc)
            if getattr(tev, "indicator_id", None) == indicator_id
        ]
        if children:
            for tev in sorted(
                children,
                key=lambda t: (
                    getattr(t, "academic_year", None) or "",
                    getattr(t, "semester", None) or "",
                    getattr(t, "public_id", None) or "",
                ),
            ):
                rows.append(
                    teaching_evaluation_period_row(tev, doc, default_scale=default_scale)
                )
        elif doc.indicator_id == indicator_id:
            rows.append(document_period_row(doc, default_scale=default_scale))
    return rows


def document_period_row(doc: Document, *, default_scale: float = 100.0) -> dict:
    fields = _effective_fields(doc)
    scale = default_scale
    if fields["ratingScaleRaw"]:
        try:
            scale = float(fields["ratingScaleRaw"])
        except ValueError:
            pass
    rating_pct, scale_used = parse_rating_percent(fields["ratingRaw"], default_scale=scale)
    bucket = _review_bucket(doc.status)
    return {
        "documentId": doc.public_id,
        "fileName": doc.file_name,
        "academicYear": fields["academicYear"] or None,
        "semester": fields["semester"] or None,
        "ratingRaw": fields["ratingRaw"] or None,
        "ratingPercent": rating_pct,
        "ratingScale": scale_used,
        "facultyName": fields["facultyName"] or None,
        "evaluationType": fields["evaluationType"] or None,
        "ocrVerificationStatus": fields["verification"] or None,
        "reviewStatus": document_status_to_web(doc),
        "reviewerValidationStatus": document_status_to_web(doc),
        "reviewDisplayStatus": review_display_status(doc),
        "approvalDecisionSource": (dict(doc.extracted_info or {}).get("Approval decision source") or None),
        "autoValidation": dict(doc.extracted_info or {}).get("autoValidation"),
        "reviewBucket": bucket,
        "ocrStatus": doc.ocr_status,
        "submittedAt": doc.submitted_at.isoformat() if doc.submitted_at else None,
    }


def _dedupe_periods(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """One record per (academic year, semester); track excluded duplicates."""
    by_key: dict[tuple[str, str], dict] = {}
    excluded: list[dict] = []
    for row in rows:
        year = row.get("academicYear") or ""
        sem = row.get("semester") or ""
        if not year and not sem:
            row["exclusionReason"] = "Missing academic year or semester"
            row["includedInAverage"] = False
            excluded.append(row)
            continue
        key = (year, sem)
        prev = by_key.get(key)
        if not prev:
            by_key[key] = row
            continue
        prev_bucket = prev["reviewBucket"]
        row_bucket = row["reviewBucket"]
        if _period_rank(row_bucket) > _period_rank(prev_bucket):
            prev["exclusionReason"] = "Duplicate period — superseded by higher-priority record"
            prev["includedInAverage"] = False
            excluded.append(prev)
            by_key[key] = row
        elif prev_bucket == "accepted" and row_bucket == "accepted":
            reason = "Conflict: multiple reviewer-approved records for this period"
            for record in (prev, row):
                record["exclusionReason"] = reason
                record["includedInAverage"] = False
                excluded.append(record)
            by_key.pop(key, None)
        else:
            row["exclusionReason"] = "Duplicate period — another document covers this semester"
            row["includedInAverage"] = False
            excluded.append(row)
    chosen = []
    for row in by_key.values():
        if row["reviewBucket"] == "rejected":
            row["includedInAverage"] = False
            row["exclusionReason"] = row.get("exclusionReason") or "Rejected evidence"
        elif row["reviewBucket"] == "incomplete":
            row["includedInAverage"] = False
            row["exclusionReason"] = row.get("exclusionReason") or "Incomplete or ambiguous OCR extraction"
        elif row.get("ratingPercent") is None:
            row["includedInAverage"] = False
            row["exclusionReason"] = row.get("exclusionReason") or "Rating not available"
        else:
            row["includedInAverage"] = True
            row["exclusionReason"] = None
        chosen.append(row)
    return chosen, excluded


def _record_status_counts(
    rows: list[dict],
    excluded: list[dict],
    periods: list[dict],
) -> dict[str, int]:
    duplicate_excluded = sum(
        1
        for item in excluded
        if item.get("exclusionReason")
        and (
            "Duplicate period" in item["exclusionReason"]
            or "Conflict:" in item["exclusionReason"]
        )
    )
    return {
        "detectedEvaluationRecords": len(rows),
        "verifiedEligibleRecords": sum(
            1
            for p in periods
            if p.get("includedInAverage") and p.get("reviewBucket") == "accepted"
        ),
        "pendingRecords": sum(1 for r in rows if r.get("reviewBucket") == "pending"),
        "rejectedOrRevisionRecords": sum(
            1 for r in rows if r.get("reviewBucket") in ("rejected", "revision")
        ),
        "incompleteRecords": sum(1 for r in rows if r.get("reviewBucket") == "incomplete"),
        "excludedDuplicateRecords": duplicate_excluded,
    }


def _ratings_from_periods(periods: list[dict]) -> list[float]:
    return [
        float(p["ratingPercent"])
        for p in periods
        if p.get("includedInAverage") and p.get("ratingPercent") is not None
    ]


def aggregate_indicator(
    docs: list[Document],
    indicator_id: str,
    *,
    faculty_eligibility: dict | None = None,
) -> dict:
    config = indicator_scoring_config(indicator_id)
    scale = config.get("ratingScale") or 100.0
    rows = collect_period_rows(docs, indicator_id, default_scale=scale)
    periods, excluded = _dedupe_periods(rows)
    record_counts = _record_status_counts(rows, excluded, periods)
    included = [p for p in periods if p.get("includedInAverage")]
    accepted = [p for p in included if p.get("reviewBucket") == "accepted"]

    settings = published_settings_root() or {}
    coverage = config.get("evaluationCoverage") or settings.get("evaluationCoverage")
    divisor_info = resolve_divisor(coverage, faculty_eligibility)

    all_ratings = _ratings_from_periods(included)
    validated_ratings = _ratings_from_periods(accepted)

    provisional_oetr = provisional_average(all_ratings)
    validated_oetr = None
    provisional_points = None
    validated_points = None
    scoring_note = config.get("reason")
    aggregation_method = config.get("aggregationMethod")

    if config.get("complete"):
        mult = config["multiplier"]
        max_pts = config["maxPoints"]
        rounding = config.get("roundingRule")
        divisor = divisor_info.eligible_divisor

        if not is_supported_aggregation(aggregation_method):
            scoring_note = (
                "Published aggregation method is missing or not supported for official SET/SEF scoring."
            )
            config = {**config, "complete": False}
        elif divisor is None:
            scoring_note = divisor_info.incomplete_reason or "Applicable semester divisor could not be resolved."
            config = {**config, "complete": False}
        else:
            if all_ratings and provisional_oetr is not None:
                if len(all_ratings) >= divisor:
                    official_prov = overall_rating_from_semesters(all_ratings, divisor=divisor)
                    if official_prov is not None:
                        provisional_points = indicator_points_from_overall_rating(
                            official_prov,
                            multiplier=mult,
                            max_points=max_pts,
                            rounding_rule=rounding,
                        )
                else:
                    scoring_note = (
                        scoring_note
                        or f"Incomplete coverage: {len(all_ratings)} of {divisor} required semester(s) evidenced."
                    )

            if validated_ratings:
                if len(validated_ratings) >= divisor:
                    validated_oetr = overall_rating_from_semesters(validated_ratings, divisor=divisor)
                    if validated_oetr is not None:
                        validated_points = indicator_points_from_overall_rating(
                            validated_oetr,
                            multiplier=mult,
                            max_points=max_pts,
                            rounding_rule=rounding,
                        )
    elif not scoring_note:
        scoring_note = "Scoring configuration incomplete"

    missing_periods: list[str] = []
    if divisor_info.eligible_divisor:
        need = divisor_info.eligible_divisor
        have = len(all_ratings)
        if have < need:
            missing_periods.append(f"{need - have} semester(s) missing for divisor {need}")

    return {
        "indicatorId": indicator_id,
        "configuration": config,
        "documents": rows,
        "periods": periods,
        "excludedPeriods": excluded,
        "averageRatingPercent": provisional_oetr,
        "validatedAverageRatingPercent": validated_oetr,
        "overallRatingPercent": provisional_oetr if len(all_ratings) >= (divisor_info.eligible_divisor or 0) else None,
        "validatedOverallRatingPercent": validated_oetr,
        "provisionalPoints": provisional_points,
        "validatedPoints": validated_points,
        "scoringStatus": "complete"
        if config.get("complete") and provisional_points is not None
        else "incomplete",
        "scoringNote": scoring_note,
        "missingPeriods": missing_periods,
        "eligibility": {
            "standardRequiredSemesters": divisor_info.standard_required_semesters,
            "eligibleDivisor": divisor_info.eligible_divisor,
            "section10Code": divisor_info.section10_code,
            "section10Verified": divisor_info.section10_verified,
            "audit": divisor_info.audit,
            "incompleteReason": divisor_info.incomplete_reason,
        },
        "coverageSummary": {
            "includedPeriods": len(included),
            "acceptedPeriods": len(accepted),
            "totalUploads": len(rows),
            "requiredPeriods": divisor_info.eligible_divisor,
            "evidencedRatings": len(all_ratings),
            **record_counts,
        },
        "recordCounts": record_counts,
        "aggregationMethod": aggregation_method,
        "ratingsUsed": all_ratings,
        "validatedRatingsUsed": validated_ratings,
    }


def build_criterion_a_summary(
    docs: list[Document],
    *,
    faculty_eligibility: dict | None = None,
) -> dict:
    set_block = aggregate_indicator(docs, SET_INDICATOR, faculty_eligibility=faculty_eligibility)
    sef_block = aggregate_indicator(docs, SEF_INDICATOR, faculty_eligibility=faculty_eligibility)
    crit_max = criterion_a_max_points()
    combined_provisional = None
    combined_validated = None
    if set_block.get("provisionalPoints") is not None and sef_block.get("provisionalPoints") is not None:
        combined_provisional = round(set_block["provisionalPoints"] + sef_block["provisionalPoints"], 2)
    if set_block.get("validatedPoints") is not None and sef_block.get("validatedPoints") is not None:
        combined_validated = round(set_block["validatedPoints"] + sef_block["validatedPoints"], 2)
    config_complete = set_block["configuration"].get("complete") and sef_block["configuration"].get("complete")
    return {
        "criterionId": CRITERION_A_ID,
        "criterionName": "Criterion A — Teaching Effectiveness",
        "set": set_block,
        "sef": sef_block,
        "combinedProvisionalPoints": combined_provisional,
        "combinedValidatedPoints": combined_validated,
        "criterionMaxPoints": crit_max,
        "configurationComplete": config_complete,
        "summaryNote": None
        if config_complete
        else "Scoring configuration incomplete for SET and/or SEF — publish applicable Admin settings.",
        "teachingEffectivenessFormula": "Teaching Effectiveness Points = SET Points + SEF Points (JC 01 s. 2026)",
    }
