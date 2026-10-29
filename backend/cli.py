"""Flask CLI commands."""

from __future__ import annotations

import getpass
import sys

import click
from flask.cli import with_appcontext

from auth.services import validate_password_strength
from extensions import db
from models import User


@click.command("create-administrator")
@click.option("--email", prompt=True, help="Administrator email address")
@click.option("--full-name", prompt="Full name", help="Display name")
@with_appcontext
def create_administrator(email: str, full_name: str) -> None:
    """
    Create the first (or additional) administrator account interactively.
    Password is read from the terminal and never stored in source control.
    """
    normalized = email.strip().lower()
    if User.query.filter_by(role="administrator").first():
        click.echo(
            "An administrator account already exists. "
            "Use that account after staff-management APIs are available.",
            err=True,
        )
        sys.exit(1)

    duplicate = User.query.filter(db.func.lower(User.email) == normalized).first()
    if duplicate:
        click.echo("A user with that email already exists.", err=True)
        sys.exit(1)

    while True:
        password = getpass.getpass("Administrator password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            click.echo("Passwords do not match. Try again.", err=True)
            continue
        strength = validate_password_strength(password)
        if strength:
            click.echo(strength, err=True)
            continue
        break

    user = User(
        email=normalized,
        role="administrator",
        full_name=full_name.strip(),
        is_active=True,
        must_change_password=False,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Administrator created: {user.public_id} ({user.email})")


@click.command("ocr-worker")
@click.option("--once", is_flag=True, help="Process pending jobs once and exit.")
@with_appcontext
def ocr_worker(once: bool) -> None:
    """Run the persistent OCR job worker (recommended for production)."""
    import time

    from flask import current_app

    from documents.ocr.queue import process_pending_jobs

    poll = current_app.config.get("OCR_WORKER_POLL_SECONDS", 3)
    click.echo(f"OCR worker started (poll={poll}s). Press Ctrl+C to stop.")
    while True:
        count = process_pending_jobs(limit=5)
        if count:
            click.echo(f"Processed {count} OCR job(s).")
        if once:
            break
        time.sleep(poll)


@click.command("ocr-enqueue-stale")
@with_appcontext
def ocr_enqueue_stale() -> None:
    """Enqueue OCR for uploaded documents still pending OCR (no active job)."""
    from models import Document

    from documents.ocr.queue import enqueue_document_ocr

    pending = Document.query.filter(
        Document.deleted_at.is_(None),
        Document.ocr_status.in_(("pending", "failed", None)),
        Document.file_path.isnot(None),
    ).all()
    created = 0
    for doc in pending:
        if enqueue_document_ocr(doc):
            created += 1
    click.echo(f"Enqueued OCR for {created} document(s).")


def _legacy_uploaded_drafts():
    from models import Document

    from documents.status_map import is_legacy_uploaded_draft

    rows = Document.query.filter(
        Document.deleted_at.is_(None),
        Document.status == "draft",
        Document.file_path.isnot(None),
    ).order_by(Document.id)
    return [d for d in rows.all() if is_legacy_uploaded_draft(d)]


@click.command("documents-list-legacy-drafts")
@with_appcontext
def documents_list_legacy_drafts() -> None:
    """List uploaded documents still stored with status=draft (read-only)."""
    rows = _legacy_uploaded_drafts()
    click.echo(f"Found {len(rows)} legacy uploaded draft document(s):")
    for doc in rows:
        profile = doc.faculty_profile
        faculty = profile.public_id if profile else "?"
        click.echo(
            f"  {doc.public_id}  file={doc.file_name!r}  faculty={faculty}  "
            f"submitted_at={doc.submitted_at}  reviewed_at={doc.reviewed_at}"
        )


@click.command("documents-promote-legacy-drafts")
@click.option(
    "--apply",
    is_flag=True,
    help="Persist pending_review on listed rows (default: dry run only).",
)
@with_appcontext
def documents_promote_legacy_drafts(apply: bool) -> None:
    """Promote legacy uploaded drafts to pending_review (requires --apply)."""
    from documents.service import utcnow

    rows = _legacy_uploaded_drafts()
    if not rows:
        click.echo("No legacy uploaded draft documents to promote.")
        return
    click.echo(f"{'Applying' if apply else 'Dry run'}: {len(rows)} document(s)")
    for doc in rows:
        click.echo(f"  {doc.public_id} ({doc.file_name})")
    if not apply:
        click.echo("No changes written. Re-run with --apply to update PostgreSQL.")
        return
    now = utcnow()
    for doc in rows:
        doc.status = "pending_review"
        if not doc.submitted_at:
            doc.submitted_at = now
    db.session.commit()
    click.echo(f"Updated {len(rows)} document(s) to pending_review.")


@click.command("documents-refresh-set-sef-extraction")
@click.option("--apply", is_flag=True, help="Persist parsed SET/SEF metadata from stored OCR text.")
@with_appcontext
def documents_refresh_set_sef_extraction(apply: bool) -> None:
    """Re-parse SET/SEF metadata from documents.extracted_text (no file re-OCR)."""
    from models import Document

    from documents.ocr.set_sef_metadata import apply_set_sef_to_extracted_info, is_set_sef_indicator

    docs = Document.query.filter(
        Document.deleted_at.is_(None),
        Document.indicator_id.in_(("kra1-a-student", "kra1-a-supervisor")),
    ).all()
    targets = [d for d in docs if is_set_sef_indicator(d.indicator_id) and (d.extracted_text or "").strip()]
    click.echo(f"Found {len(targets)} SET/SEF document(s) with stored text.")
    for doc in targets:
        click.echo(f"  {doc.public_id}  indicator={doc.indicator_id}  ocr={doc.ocr_status}")
    if not apply:
        click.echo("Dry run only. Re-run with --apply to update extracted_info.")
        return
    updated = 0
    for doc in targets:
        info = dict(doc.extracted_info or {})
        method = info.get("OCR method") or info.get("Extraction method")
        doc.extracted_info = apply_set_sef_to_extracted_info(
            info,
            text=(doc.extracted_text or "").strip(),
            indicator_id=doc.indicator_id,
            extraction_method=method,
        )
        updated += 1
    db.session.commit()
    click.echo(f"Updated extracted_info on {updated} document(s).")


@click.command("documents-purge-set-sef")
@click.option(
    "--apply",
    is_flag=True,
    help="Backup selected rows/PDFs and permanently delete (default: dry-run only).",
)
@click.option(
    "--confirm",
    default="",
    help="Required with --apply. Must be exactly: DELETE-SET-SEF-12",
)
@click.option(
    "--faculty",
    "faculty_public_id",
    default="",
    help="Optional faculty public_id scope (e.g. fac_a727f9d39571).",
)
@with_appcontext
def documents_purge_set_sef(apply: bool, confirm: str, faculty_public_id: str) -> None:
    """
    Remove all active SET/SEF documents (kra1-a-student / kra1-a-supervisor) and OCR jobs.
    Does not remove other indicators or whole upload directories.
    """
    from documents.purge_set_sef import CONFIRM_PHRASE, dry_run_report, execute_purge

    scope = faculty_public_id.strip() or None
    if not apply:
        click.echo(dry_run_report(faculty_public_id=scope))
        return
    if confirm != CONFIRM_PHRASE:
        click.echo(
            f"Refusing apply: pass --confirm {CONFIRM_PHRASE} after reviewing the dry-run.",
            err=True,
        )
        sys.exit(1)
    try:
        backup = execute_purge(faculty_public_id=scope, confirm=confirm)
    except ValueError as err:
        click.echo(str(err), err=True)
        sys.exit(1)
    click.echo(f"Purge complete. Backup written to: {backup}")
    click.echo("Re-upload the same PDFs from Flutter; duplicate detection uses file_hash per indicator.")


REASSESS_CONFIRM = "REASSESS-SET-SEF-SIMULATION"


@click.command("documents-reassess-set-sef-simulation")
@click.option("--apply", is_flag=True, help="Apply auto-accept to eligible pending SET/SEF rows.")
@click.option(
    "--confirm",
    default="",
    help=f"Required with --apply. Must be exactly: {REASSESS_CONFIRM}",
)
@click.option(
    "--faculty",
    "faculty_public_id",
    default="",
    help="Optional faculty public_id scope.",
)
@with_appcontext
def documents_reassess_set_sef_simulation(apply: bool, confirm: str, faculty_public_id: str) -> None:
    """Re-run simulation auto-accept for OCR-complete SET/SEF documents (no re-OCR)."""
    from documents.ocr.set_sef_metadata import is_set_sef_indicator
    from documents.set_sef_auto_approval.apply import reassess_set_sef_simulation_accept
    from documents.set_sef_auto_approval.assess import assess_document
    from documents.set_sef_auto_approval.policy import is_auto_approval_active
    from models import Document, FacultyProfile

    if not is_auto_approval_active():
        click.echo(
            "Simulation auto-accept policy is inactive. Enable it in Admin (or env) before reassessing.",
            err=True,
        )
        sys.exit(1)

    q = Document.query.filter(Document.deleted_at.is_(None), Document.status == "pending_review")
    if faculty_public_id.strip():
        profile = FacultyProfile.query.filter_by(public_id=faculty_public_id.strip()).first()
        if not profile:
            click.echo("Faculty not found.", err=True)
            sys.exit(1)
        q = q.filter(Document.faculty_profile_id == profile.id)
    candidates = [d for d in q.all() if is_set_sef_indicator(d.indicator_id)]
    if not candidates:
        click.echo("No pending SET/SEF documents in scope.")
        return

    would: list[str] = []
    skip: list[str] = []
    for doc in candidates:
        result = assess_document(doc)
        if result.eligible:
            would.append(doc.public_id)
        else:
            skip.append(f"{doc.public_id}: {result.withheld_reasons[0] if result.withheld_reasons else 'not eligible'}")

    click.echo(f"Pending SET/SEF in scope: {len(candidates)}")
    click.echo(f"Would auto-accept ({len(would)}): " + (", ".join(would) if would else "—"))
    if skip:
        click.echo("Would remain pending:")
        for line in skip:
            click.echo(f"  {line}")

    if not apply:
        click.echo("Dry-run only. Pass --apply --confirm to update statuses and audit logs.")
        return
    if confirm != REASSESS_CONFIRM:
        click.echo(f"Refusing apply: pass --confirm {REASSESS_CONFIRM}", err=True)
        sys.exit(1)

    approved = 0
    for doc in candidates:
        before = doc.status
        reassess_set_sef_simulation_accept(doc)
        if doc.status == "approved" and before != "approved":
            approved += 1
    db.session.commit()
    click.echo(f"Applied simulation auto-accept to {approved} document(s).")
