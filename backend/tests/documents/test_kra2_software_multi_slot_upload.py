"""Regression: KRA II software indicator allows one file per checklist slot (same indicator_id)."""

from __future__ import annotations

import io
import uuid

import pytest
from werkzeug.datastructures import FileStorage

from documents.kra2_evidence.bundle import bundle_from_document
from documents.kra2_evidence.slots import required_slots
from documents.service import create_upload
from extensions import db
from models import User

pytestmark = pytest.mark.db_write


def _png(unique: str) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    seed = int(uuid.uuid5(uuid.NAMESPACE_DNS, unique).hex[:8], 16) % 0xFFFFFF
    Image.new("RGB", (5, 5), color=((seed >> 16) & 255, (seed >> 8) & 255, seed & 255)).save(
        buf, format="PNG"
    )
    return buf.getvalue()


def _pdf(unique: str) -> bytes:
    import pymupdf

    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), f"Software slot test {unique}", fontsize=11)
    buf = io.BytesIO()
    pdf.save(buf)
    pdf.close()
    return buf.getvalue()


def test_sw_new_sole_multi_slot_uploads_same_indicator(app):
    """Reproduce multi-slot flow: duplicate hash in different slots must not block."""
    with app.app_context():
        faculty_user = User.query.filter_by(role="faculty").order_by(User.id.asc()).first()
        if not faculty_user:
            pytest.skip("No faculty user in database")
        _run_sw_multi_slot(faculty_user)


def _run_sw_multi_slot(faculty_user: User) -> None:

    indicator_id = "kra2-b-sw-new-sole"
    run = uuid.uuid4().hex[:8]
    primary_fs = FileStorage(
        stream=io.BytesIO(_pdf(f"primary-{run}")),
        filename=f"sw-primary-{run}.pdf",
        content_type="application/pdf",
    )
    primary = create_upload(
        faculty_user,
        file=primary_fs,
        title=f"[KRA2-B-QA] sw multi-slot primary {run}",
        kra_id="kra2",
        criterion_id="kra2-b",
        indicator_id=indicator_id,
    )
    db.session.commit()

    shared_png = _png(f"shared-{run}")
    slots = list(required_slots(indicator_id=indicator_id))
    filled = 0
    for slot in slots:
        bundle = bundle_from_document(primary)
        entry = (bundle or {}).get("checklist", {}).get(slot) or {}
        if entry.get("documentId"):
            filled += 1
            continue
        if slot == "primary_output":
            fs = FileStorage(
                stream=io.BytesIO(_pdf(f"slot-{slot}-{run}")),
                filename=f"{slot}-{run}.pdf",
                content_type="application/pdf",
            )
        else:
            fs = FileStorage(
                stream=io.BytesIO(shared_png),
                filename=f"{slot}-{run}.png",
                content_type="image/png",
            )
        create_upload(
            faculty_user,
            file=fs,
            title=f"[KRA2-B-QA] sw slot {slot} {run}",
            kra_id="kra2",
            criterion_id="kra2-b",
            indicator_id=indicator_id,
            bundle_primary_public_id=primary.public_id,
            evidence_slot=slot,
        )
        db.session.commit()
        filled += 1

    db.session.refresh(primary)
    bundle = bundle_from_document(primary)
    assert bundle is not None
    for slot in slots:
        doc_id = (bundle.get("checklist", {}).get(slot) or {}).get("documentId")
        assert doc_id, f"missing slot {slot}"


def test_shared_png_allowed_in_two_slots_on_same_bundle(app):
    """Same PNG bytes in two checklist slots should succeed (KRA II supporting uploads)."""
    with app.app_context():
        faculty_user = User.query.filter_by(role="faculty").order_by(User.id.asc()).first()
        if not faculty_user:
            pytest.skip("No faculty user in database")
        run = uuid.uuid4().hex[:8]
        indicator_id = "kra2-b-sw-new-sole"
        primary = create_upload(
            faculty_user,
            file=FileStorage(
                stream=io.BytesIO(_pdf(f"p-{run}")),
                filename=f"p-{run}.pdf",
                content_type="application/pdf",
            ),
            title=f"[KRA2-B-QA] sw dup png primary {run}",
            kra_id="kra2",
            criterion_id="kra2-b",
            indicator_id=indicator_id,
        )
        db.session.commit()
        png = _png(f"same-{run}")
        for slot in ("project_summary", "software_documentation"):
            create_upload(
                faculty_user,
                file=FileStorage(
                    stream=io.BytesIO(png),
                    filename=f"{slot}-{run}.png",
                    content_type="image/png",
                ),
                title=f"[KRA2-B-QA] sw dup {slot} {run}",
                kra_id="kra2",
                criterion_id="kra2-b",
                indicator_id=indicator_id,
                bundle_primary_public_id=primary.public_id,
                evidence_slot=slot,
            )
            db.session.commit()
        bundle = bundle_from_document(primary)
        assert (bundle["checklist"]["project_summary"]["documentId"])
        assert (bundle["checklist"]["software_documentation"]["documentId"])
