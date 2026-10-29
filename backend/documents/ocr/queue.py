"""Persistent OCR job queue and processing."""

from __future__ import annotations

import os
import socket
import uuid
from datetime import datetime, timedelta, timezone

from flask import current_app

from extensions import db
from models import Document, DocumentOcrJob
from documents.ocr.config import (
    ocr_excerpt_max_chars,
    ocr_max_attempts,
    ocr_runtime_status,
    ocr_stale_processing_minutes,
    refresh_tesseract_availability,
)
from documents.ocr.engine import run_ocr_on_file
from documents.ocr.result import OcrProcessingError
from documents.ocr.set_sef_metadata import (
    apply_set_sef_to_extracted_info,
    mark_set_sef_processing_failed,
)
from documents.set_sef_auto_approval.apply import maybe_auto_approve_after_ocr
from documents.storage import resolve_path

WORKER_ID = f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_ocr_status(raw: str | None) -> str:
    value = (raw or "pending").strip().lower()
    if value in ("complete", "done", "success"):
        return "completed"
    if value in ("error",):
        return "failed"
    if value in ("pending", "processing", "completed", "failed"):
        return value
    return "pending"


def _quality_label(confidence: float | None) -> str:
    if confidence is None:
        return "Unknown"
    if confidence >= 85:
        return "Good"
    if confidence >= 65:
        return "Fair"
    return "Poor"


def enqueue_document_ocr(doc: Document, *, force: bool = False) -> DocumentOcrJob | None:
    """Create a pending OCR job unless one is already queued for this file version."""
    file_hash = (doc.file_hash or "").strip()
    if not file_hash or not doc.file_path:
        return None
    active = (
        DocumentOcrJob.query.filter_by(document_id=doc.id, file_hash=file_hash)
        .filter(DocumentOcrJob.status.in_(("pending", "running")))
        .first()
    )
    if active and not force:
        return active
    if force and active:
        active.status = "cancelled"
    job = DocumentOcrJob(
        document_id=doc.id,
        status="pending",
        attempts=0,
        max_attempts=ocr_max_attempts(),
        file_hash=file_hash,
    )
    doc.ocr_status = "pending"
    db.session.add(job)
    db.session.commit()
    return job


def recover_stale_jobs() -> int:
    """Reset jobs/documents stuck in processing after worker loss."""
    cutoff = utcnow() - timedelta(minutes=ocr_stale_processing_minutes())
    stale_jobs = DocumentOcrJob.query.filter(
        DocumentOcrJob.status == "running",
        DocumentOcrJob.locked_at.isnot(None),
        DocumentOcrJob.locked_at < cutoff,
    ).all()
    count = 0
    for job in stale_jobs:
        job.status = "pending"
        job.locked_at = None
        job.locked_by = None
        job.last_error = "Processing timed out; job requeued."
        doc = job.document
        if doc and doc.ocr_status == "processing":
            doc.ocr_status = "pending"
        count += 1
    if count:
        db.session.commit()
    return count


def _apply_success(doc: Document, result, job: DocumentOcrJob) -> None:
    text = (result.text or "").strip()
    excerpt_cap = ocr_excerpt_max_chars()
    excerpt = text[:excerpt_cap] if text else ""
    info = dict(doc.extracted_info or {})
    info["Extraction mode"] = "Tesseract OCR / PDF text extraction"
    info["OCR method"] = result.method
    info["OCR excerpt"] = excerpt
    if result.confidence is not None:
        info["OCR confidence"] = f"{result.confidence:.1f}%"
    else:
        info.pop("OCR confidence", None)
    info["OCR quality"] = _quality_label(result.confidence)
    info["OCR completed at"] = utcnow().isoformat()
    info.pop("OCR error", None)
    if result.warnings:
        info["OCR warnings"] = "; ".join(result.warnings)
    doc.extracted_text = text or None
    doc.ocr_confidence = result.confidence
    doc.extracted_info = apply_set_sef_to_extracted_info(
        info,
        text=text,
        indicator_id=doc.indicator_id,
        extraction_method=result.method,
    )
    doc.ocr_status = "completed"
    job.status = "succeeded"
    job.last_error = None
    job.locked_at = None
    job.locked_by = None
    try:
        maybe_auto_approve_after_ocr(doc, job)
    except Exception:  # noqa: BLE001 — auto-approval must not fail OCR completion
        current_app.logger.exception(
            "SET/SEF auto-approval after OCR failed for document %s",
            doc.public_id,
        )


def _apply_failure(doc: Document, job: DocumentOcrJob, *, code: str, message: str) -> None:
    info = dict(doc.extracted_info or {})
    info["OCR error"] = message
    info["OCR failed at"] = utcnow().isoformat()
    info["Extraction mode"] = "OCR failed"
    doc.extracted_info = mark_set_sef_processing_failed(
        info,
        indicator_id=doc.indicator_id,
        message=message,
    )
    doc.extracted_text = doc.extracted_text
    doc.ocr_confidence = None
    doc.ocr_status = "failed"
    job.status = "failed"
    job.last_error = f"{code}: {message}"[:2000]
    job.locked_at = None
    job.locked_by = None


def process_job(job_id: int) -> bool:
    """Process one OCR job. Returns True if processed."""
    job = DocumentOcrJob.query.get(job_id)
    if not job or job.status not in ("pending", "running"):
        return False
    doc = job.document
    if not doc or doc.deleted_at is not None:
        job.status = "cancelled"
        db.session.commit()
        return False
    if (doc.file_hash or "") != job.file_hash:
        job.status = "cancelled"
        job.last_error = "File version changed; job cancelled."
        db.session.commit()
        return False

    job.status = "running"
    job.attempts = (job.attempts or 0) + 1
    job.locked_at = utcnow()
    job.locked_by = WORKER_ID
    doc.ocr_status = "processing"
    db.session.commit()

    refresh_tesseract_availability()
    runtime = ocr_runtime_status()
    if not runtime.available:
        if job.attempts < job.max_attempts:
            job.status = "pending"
            job.locked_at = None
            job.locked_by = None
            doc.ocr_status = "pending"
            job.last_error = runtime.message
            db.session.commit()
            return True
        _apply_failure(doc, job, code="tesseract_unavailable", message=runtime.message)
        db.session.commit()
        return True

    path = resolve_path(doc.file_path or "")
    if not path:
        _apply_failure(doc, job, code="file_missing", message="The stored file is not available.")
        db.session.commit()
        return True

    try:
        result = run_ocr_on_file(path=path, mime_type=doc.mime_type or "")
        _apply_success(doc, result, job)
    except OcrProcessingError as err:
        if job.attempts < job.max_attempts and err.code in (
            "tesseract_unavailable",
            "read_failed",
        ):
            job.status = "pending"
            doc.ocr_status = "pending"
            job.last_error = err.message
            job.locked_at = None
            job.locked_by = None
        else:
            _apply_failure(doc, job, code=err.code, message=err.message)
    except Exception:  # noqa: BLE001 — persist safe failure, no paths in client message
        current_app.logger.exception("OCR failed for document %s", doc.public_id)
        _apply_failure(
            doc,
            job,
            code="processing_error",
            message="Text extraction failed due to an internal error.",
        )
    db.session.commit()
    return True


def process_pending_jobs(*, limit: int = 5) -> int:
    recover_stale_jobs()
    pending = (
        DocumentOcrJob.query.filter_by(status="pending")
        .order_by(DocumentOcrJob.created_at.asc())
        .limit(limit)
        .all()
    )
    processed = 0
    for job in pending:
        if process_job(job.id):
            processed += 1
    return processed


def retry_document_ocr(doc: Document) -> DocumentOcrJob | None:
    """Requeue OCR for the current file version (faculty/reviewer/admin)."""
    info = dict(doc.extracted_info or {})
    info.pop("OCR error", None)
    doc.extracted_info = info
    doc.ocr_status = "pending"
    db.session.commit()
    return enqueue_document_ocr(doc, force=True)
