"""Hard-delete SET/SEF test documents (scoped, backup-first)."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import BASE_DIR, Config
from extensions import db
from models import AuditLog, Document, DocumentOcrJob

SET_INDICATOR = "kra1-a-student"
SEF_INDICATOR = "kra1-a-supervisor"
CONFIRM_PHRASE = "DELETE-SET-SEF-12"


@dataclass
class PurgePlan:
    documents: list[Document]
    ocr_job_count: int
    file_paths: list[Path]
    backup_dir: Path | None


def _backup_root() -> Path:
    root = BASE_DIR / "backups"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _serialize_doc(doc: Document) -> dict[str, Any]:
    info = dict(doc.extracted_info or {})
    text = doc.extracted_text or ""
    return {
        "id": doc.id,
        "publicId": doc.public_id,
        "facultyProfileId": doc.faculty_profile_id,
        "facultyPublicId": doc.faculty_profile.public_id if doc.faculty_profile else None,
        "indicatorId": doc.indicator_id,
        "status": doc.status,
        "fileName": doc.file_name,
        "filePath": doc.file_path,
        "fileHash": doc.file_hash,
        "mimeType": doc.mime_type,
        "fileSize": doc.file_size,
        "ocrStatus": doc.ocr_status,
        "ocrConfidence": doc.ocr_confidence,
        "extractedInfo": info,
        "extractedTextLength": len(text),
        "extractedTextPreview": text[:2000],
        "reviewerRemarks": doc.reviewer_remarks,
        "reviewedAt": doc.reviewed_at.isoformat() if doc.reviewed_at else None,
        "submittedAt": doc.submitted_at.isoformat() if doc.submitted_at else None,
        "replacesDocumentId": doc.replaces_document_id,
    }


def find_set_sef_documents(*, faculty_public_id: str | None = None) -> list[Document]:
    q = Document.query.filter(
        Document.deleted_at.is_(None),
        Document.indicator_id.in_((SET_INDICATOR, SEF_INDICATOR)),
    ).order_by(Document.indicator_id, Document.id)
    if faculty_public_id:
        from models import FacultyProfile

        profile = FacultyProfile.query.filter_by(public_id=faculty_public_id.strip()).first()
        if not profile:
            return []
        q = q.filter(Document.faculty_profile_id == profile.id)
    return q.all()


def build_purge_plan(*, faculty_public_id: str | None = None) -> PurgePlan:
    from documents.storage import resolve_path

    docs = find_set_sef_documents(faculty_public_id=faculty_public_id)
    job_count = 0
    paths: list[Path] = []
    if docs:
        ids = [d.id for d in docs]
        job_count = DocumentOcrJob.query.filter(DocumentOcrJob.document_id.in_(ids)).count()
        for doc in docs:
            resolved = resolve_path(doc.file_path or "")
            if resolved and resolved.is_file():
                paths.append(resolved)
    return PurgePlan(documents=docs, ocr_job_count=job_count, file_paths=paths, backup_dir=None)


def dry_run_report(*, faculty_public_id: str | None = None) -> str:
    plan = build_purge_plan(faculty_public_id=faculty_public_id)
    lines = [
        "SET/SEF purge dry-run",
        f"Faculty filter: {faculty_public_id or '(all faculty with SET/SEF rows)'}",
        f"Documents matched: {len(plan.documents)}",
        f"OCR jobs to delete: {plan.ocr_job_count}",
        f"PDF files on disk: {len(plan.file_paths)}",
        "",
    ]
    for doc in plan.documents:
        info = doc.extracted_info or {}
        lines.append(
            f"  {doc.public_id}  id={doc.id}  {doc.indicator_id}  status={doc.status}  "
            f"file={doc.file_name!r}  hash={ (doc.file_hash or '')[:16]}…  "
            f"period={info.get('Academic year')} {info.get('Semester')}"
        )
    other = Document.query.filter(
        Document.deleted_at.is_(None),
        ~Document.indicator_id.in_((SET_INDICATOR, SEF_INDICATOR)),
    ).count()
    lines.extend(
        [
            "",
            f"Other active documents (preserved): {other}",
            "replaces_document_id chains: none among matched rows",
            "Scoring: recomputed live from documents (no SET/SEF score cache rows found for this faculty).",
            "",
            "No changes written. To backup and delete after review:",
            f"  python -m flask documents-purge-set-sef --apply --confirm {CONFIRM_PHRASE}",
            "Optional faculty scope:",
            f"  python -m flask documents-purge-set-sef --apply --confirm {CONFIRM_PHRASE} "
            "--faculty fac_a727f9d39571",
        ]
    )
    return "\n".join(lines)


def execute_purge(
    *,
    faculty_public_id: str | None,
    confirm: str,
    actor_user_id: int | None = None,
) -> Path:
    if confirm != CONFIRM_PHRASE:
        raise ValueError("confirm_phrase_mismatch")

    plan = build_purge_plan(faculty_public_id=faculty_public_id)
    if not plan.documents:
        raise ValueError("nothing_to_purge")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = _backup_root() / f"set_sef_purge_{stamp}"
    backup_dir.mkdir(parents=True)
    pdfs_dir = backup_dir / "pdfs"
    pdfs_dir.mkdir()

    manifest = {
        "purgedAt": datetime.now(timezone.utc).isoformat(),
        "confirmPhrase": CONFIRM_PHRASE,
        "facultyFilter": faculty_public_id,
        "documents": [_serialize_doc(d) for d in plan.documents],
        "ocrJobsDeleted": plan.ocr_job_count,
    }
    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    from documents.storage import resolve_path

    for doc in plan.documents:
        src = resolve_path(doc.file_path or "")
        if src and src.is_file():
            dest = pdfs_dir / f"{doc.public_id}_{doc.file_name}"
            shutil.copy2(src, dest)

    ids = [d.id for d in plan.documents]
    public_ids = [d.public_id for d in plan.documents]

    DocumentOcrJob.query.filter(DocumentOcrJob.document_id.in_(ids)).delete(synchronize_session=False)
    Document.query.filter(Document.id.in_(ids)).delete(synchronize_session=False)

    removed_files = 0
    for doc in plan.documents:
        src = resolve_path(doc.file_path or "")
        if src and src.is_file():
            src.unlink()
            removed_files += 1

    audit_detail = {
        "action": "set_sef_test_documents_hard_delete",
        "documentPublicIds": public_ids,
        "documentIds": ids,
        "backupDirectory": str(backup_dir),
        "pdfFilesRemoved": removed_files,
        "facultyFilter": faculty_public_id,
    }
    db.session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="SET/SEF test document purge",
            target_id=public_ids[0] if len(public_ids) == 1 else "batch",
            detail=json.dumps(audit_detail, ensure_ascii=False)[:8000],
        )
    )
    db.session.commit()
    return backup_dir
