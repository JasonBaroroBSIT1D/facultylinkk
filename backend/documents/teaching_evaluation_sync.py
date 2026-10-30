"""Sync OCR multi-SET/SEF parser output to document_teaching_evaluations."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

from extensions import db
from models import Document, DocumentTeachingEvaluation

from documents.ocr.set_sef_metadata import (
    SetSefEvaluationRecord,
    is_set_sef_indicator,
    parse_set_sef_metadata_multi,
    verify_record_indicator,
)
from documents.scoring.set_sef_aggregate import parse_rating_percent

_REVIEWER_PROTECTED_STATUSES = frozenset(
    {
        "approved",
        "verified",
        "confirmed",
        "valid",
        "rejected",
        "needs_revision",
    }
)


@dataclass
class ExistingEvalSnapshot:
    """In-memory view of a persisted row for sync planning (testable without DB)."""

    id: int
    evaluation_type: str
    academic_year: str | None
    semester: str | None
    source_section_ref: str | None
    extraction_source: str
    reviewer_validation_status: str | None = None
    reviewer_remarks: str | None = None
    correction_history: list[Any] = field(default_factory=list)


@dataclass
class SyncPlan:
    creates: list[dict[str, Any]] = field(default_factory=list)
    updates: list[dict[str, Any]] = field(default_factory=list)
    delete_ids: list[int] = field(default_factory=list)
    skipped_ambiguous_type: int = 0
    skipped_protected: int = 0


@dataclass
class TeachingEvaluationSyncResult:
    skipped: bool = False
    created: int = 0
    updated: int = 0
    removed: int = 0
    skipped_ambiguous_type: int = 0
    skipped_protected: int = 0
    linked_count: int = 0


def sync_key(
    *,
    evaluation_type: str | None,
    academic_year: str | None,
    semester: str | None,
    source_section_ref: str | None,
    fallback_index: int | None = None,
) -> tuple[str, ...]:
    et = (evaluation_type or "").strip().upper()
    year = (academic_year or "").strip()
    sem = (semester or "").strip()
    ref = (source_section_ref or "").strip()
    if et and year and sem:
        return ("period", et, year, sem)
    if et and ref:
        return ("section", et, ref)
    if et:
        return ("section", et, f"idx:{fallback_index if fallback_index is not None else 0}")
    return ("invalid", ref or str(fallback_index or 0))


def is_reviewer_protected(snapshot: ExistingEvalSnapshot) -> bool:
    if snapshot.correction_history:
        return True
    if (snapshot.reviewer_remarks or "").strip():
        return True
    status = (snapshot.reviewer_validation_status or "").strip().lower()
    return status in _REVIEWER_PROTECTED_STATUSES


def _record_metadata(
    record: SetSefEvaluationRecord,
    *,
    ocr_confidence: float | None,
    upload_indicator_id: str | None,
) -> dict[str, Any]:
    return {
        "missingFields": list(record.missing_fields),
        "ambiguousFields": list(record.ambiguous_fields),
        "uncertaintyNotes": list(record.uncertainty_notes),
        "extractionStatus": record.extraction_status,
        "documentTitle": record.document_title,
        "facultyName": record.faculty_name,
        "uploadIndicatorId": upload_indicator_id,
        "ocrConfidence": ocr_confidence,
        "syncedAt": datetime.now(timezone.utc).isoformat(),
    }


def _draft_from_record(
    record: SetSefEvaluationRecord,
    *,
    index: int,
    ocr_confidence: float | None,
    upload_indicator_id: str | None,
) -> dict[str, Any] | None:
    et = (record.evaluation_type or "").strip().upper()
    if et not in (
        DocumentTeachingEvaluation.EVALUATION_TYPE_SET,
        DocumentTeachingEvaluation.EVALUATION_TYPE_SEF,
    ):
        return None
    rating_pct, scale_used = parse_rating_percent(record.overall_rating)
    scale_float = None
    if record.rating_scale:
        try:
            scale_float = float(record.rating_scale)
        except ValueError:
            scale_float = scale_used
    elif scale_used:
        scale_float = scale_used
    return {
        "key": sync_key(
            evaluation_type=et,
            academic_year=record.academic_year,
            semester=record.semester,
            source_section_ref=record.source_section_ref,
            fallback_index=index,
        ),
        "evaluation_type": et,
        "indicator_id": DocumentTeachingEvaluation.INDICATOR_BY_TYPE[et],
        "academic_year": record.academic_year,
        "semester": record.semester,
        "rating_raw": record.overall_rating,
        "rating_scale": scale_float,
        "rating_percent": rating_pct,
        "source_section_ref": (record.source_section_ref or "")[:120] or None,
        "ocr_verification_status": verify_record_indicator(upload_indicator_id, record),
        "extracted_metadata": _record_metadata(
            record,
            ocr_confidence=ocr_confidence,
            upload_indicator_id=upload_indicator_id,
        ),
    }


def dedupe_parsed_drafts(drafts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep first draft per sync key; later duplicates are dropped (DB unique constraint)."""
    seen: set[tuple[str, ...]] = set()
    unique: list[dict[str, Any]] = []
    for draft in drafts:
        key = draft["key"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(draft)
    return unique


def build_sync_plan(
    parsed_records: list[SetSefEvaluationRecord],
    existing: list[ExistingEvalSnapshot],
    *,
    ocr_confidence: float | None = None,
    upload_indicator_id: str | None = None,
) -> SyncPlan:
    plan = SyncPlan()
    drafts: list[dict[str, Any]] = []
    skipped_type = 0
    for index, record in enumerate(parsed_records):
        draft = _draft_from_record(
            record,
            index=index,
            ocr_confidence=ocr_confidence,
            upload_indicator_id=upload_indicator_id,
        )
        if draft is None:
            skipped_type += 1
            continue
        drafts.append(draft)
    plan.skipped_ambiguous_type = skipped_type
    drafts = dedupe_parsed_drafts(drafts)

    existing_by_key: dict[tuple[str, ...], ExistingEvalSnapshot] = {}
    for row in existing:
        existing_by_key[
            sync_key(
                evaluation_type=row.evaluation_type,
                academic_year=row.academic_year,
                semester=row.semester,
                source_section_ref=row.source_section_ref,
            )
        ] = row

    desired_keys = {d["key"] for d in drafts}
    for draft in drafts:
        key = draft["key"]
        prev = existing_by_key.get(key)
        if prev and is_reviewer_protected(prev):
            plan.skipped_protected += 1
            continue
        payload = {k: v for k, v in draft.items() if k != "key"}
        if prev:
            plan.updates.append({"id": prev.id, **payload})
        else:
            plan.creates.append(payload)

    for row in existing:
        row_key = sync_key(
            evaluation_type=row.evaluation_type,
            academic_year=row.academic_year,
            semester=row.semester,
            source_section_ref=row.source_section_ref,
        )
        if row_key in desired_keys:
            continue
        if is_reviewer_protected(row):
            plan.skipped_protected += 1
            continue
        if (row.extraction_source or "ocr").lower() != "ocr":
            continue
        plan.delete_ids.append(row.id)

    return plan


def _snapshot_from_model(row: DocumentTeachingEvaluation) -> ExistingEvalSnapshot:
    history = row.correction_history_json if isinstance(row.correction_history_json, list) else []
    return ExistingEvalSnapshot(
        id=row.id,
        evaluation_type=row.evaluation_type,
        academic_year=row.academic_year,
        semester=row.semester,
        source_section_ref=row.source_section_ref,
        extraction_source=row.extraction_source or "ocr",
        reviewer_validation_status=row.reviewer_validation_status,
        reviewer_remarks=row.reviewer_remarks,
        correction_history=history,
    )


def _apply_plan_to_document(doc: Document, plan: SyncPlan) -> TeachingEvaluationSyncResult:
    result = TeachingEvaluationSyncResult(
        skipped_ambiguous_type=plan.skipped_ambiguous_type,
        skipped_protected=plan.skipped_protected,
    )
    for payload in plan.creates:
        row = DocumentTeachingEvaluation(document_id=doc.id, extraction_source="ocr", **payload)
        db.session.add(row)
        result.created += 1
    for item in plan.updates:
        row_id = item.pop("id")
        row = db.session.get(DocumentTeachingEvaluation, row_id)
        if not row or row.document_id != doc.id:
            continue
        for key, value in item.items():
            setattr(row, key, value)
        row.extraction_source = "ocr"
        result.updated += 1
    for row_id in plan.delete_ids:
        row = db.session.get(DocumentTeachingEvaluation, row_id)
        if not row or row.document_id != doc.id:
            continue
        if is_reviewer_protected(_snapshot_from_model(row)):
            result.skipped_protected += 1
            continue
        db.session.delete(row)
        result.removed += 1
    db.session.flush()
    result.linked_count = DocumentTeachingEvaluation.query.filter_by(document_id=doc.id).count()
    return result


def merge_sync_summary_into_extracted_info(
    info: dict,
    *,
    sync_result: TeachingEvaluationSyncResult,
    parsed_count: int,
) -> dict:
    merged = dict(info or {})
    if sync_result.skipped:
        return merged
    merged["Teaching evaluation record count"] = str(sync_result.linked_count)
    merged["Teaching evaluation parsed sections"] = str(parsed_count)
    merged["Teaching evaluation sync at"] = datetime.now(timezone.utc).isoformat()
    if sync_result.skipped_ambiguous_type:
        merged["Teaching evaluation skipped ambiguous type"] = str(sync_result.skipped_ambiguous_type)
    if sync_result.skipped_protected:
        merged["Teaching evaluation protected rows preserved"] = str(sync_result.skipped_protected)
    return merged


def sync_teaching_evaluations_for_document(
    doc: Document,
    *,
    text: str,
    ocr_confidence: float | None = None,
    extraction_method: str | None = None,
) -> TeachingEvaluationSyncResult:
    """
    Idempotent OCR sync: link parsed SET/SEF rows to ``doc`` without duplicating periods.
    Uses a nested transaction so failures do not leave partial child rows.
    """
    if not is_set_sef_indicator(doc.indicator_id):
        return TeachingEvaluationSyncResult(skipped=True)

    parsed = parse_set_sef_metadata_multi(text or "")
    existing = [_snapshot_from_model(row) for row in doc.teaching_evaluations.all()]
    plan = build_sync_plan(
        parsed,
        existing,
        ocr_confidence=ocr_confidence,
        upload_indicator_id=doc.indicator_id,
    )

    try:
        with db.session.begin_nested():
            sync_result = _apply_plan_to_document(doc, plan)
            db.session.flush()
    except Exception:
        logger.exception("Teaching evaluation sync failed for document %s", doc.public_id)
        raise

    doc.extracted_info = merge_sync_summary_into_extracted_info(
        doc.extracted_info or {},
        sync_result=sync_result,
        parsed_count=len(parsed),
    )
    if extraction_method:
        info = dict(doc.extracted_info)
        info["Teaching evaluation extraction method"] = extraction_method
        doc.extracted_info = info
    return sync_result
