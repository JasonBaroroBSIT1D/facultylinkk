"""
Phase 6B.2 — Live Criterion B regression on facultylink (no relink workaround).

Run: cd backend && python scripts/phase6b2_criterion_b_live_regression.py
"""

from __future__ import annotations

import io
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from werkzeug.datastructures import FileStorage

from config import Config
from factory import create_app

TAG = "PHASE6B2"


def _unique_png_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    seed = uuid.uuid4().int % 0xFFFFFF
    r, g, b = (seed >> 16) & 255, (seed >> 8) & 255, seed & 255
    Image.new("RGB", (4, 4), color=(r, g, b)).save(buf, format="PNG")
    return buf.getvalue()


def _wait_ocr(app, public_id: str, *, timeout_sec: float = 45.0) -> str:
    from documents.service import get_document
    from documents.ocr.queue import process_pending_jobs
    from extensions import db

    deadline = time.monotonic() + timeout_sec
    last = "pending"
    with app.app_context():
        while time.monotonic() < deadline:
            process_pending_jobs(limit=3)
            db.session.expire_all()
            doc = get_document(public_id)
            last = (doc.ocr_status or "pending") if doc else "missing"
            if last in ("completed", "failed"):
                return last
            time.sleep(0.35)
    return last


def _reload_primary(public_id: str):
    from documents.service import get_document
    from extensions import db
    from models import Document

    db.session.expire_all()
    return Document.query.filter_by(public_id=public_id).first() or get_document(public_id)


def _checklist_entry(primary, slot: str) -> dict:
    from documents.criterion_b_evidence.service import bundle_api_payload

    payload = bundle_api_payload(primary)
    cl = (payload.get("bundle") or {}).get("checklist") or {}
    entry = cl.get(slot) if isinstance(cl, dict) else {}
    return entry if isinstance(entry, dict) else {}


def main() -> int:
    from documents.criterion_b_evidence.bundle import CLAIM_TYPE_INSTRUCTIONAL_MATERIAL
    from documents.criterion_b_evidence.checklist import (
        SLOT_COMPLETE_SET,
        SLOT_IMDC_APPROVAL,
        SLOT_LIBRARY_CERTIFICATION,
    )
    from documents.criterion_b_evidence.program_checklist import (
        SLOT_ACADEMIC_COUNCIL,
        SLOT_DEAN_CERTIFICATION,
        SLOT_FEASIBILITY_STUDY,
        SLOT_GOVERNING_BOARD,
        SLOT_IMPLEMENTATION,
        SLOT_PRIMARY_CONTRIBUTION,
        SLOT_RRPA_COPC,
    )
    from documents.criterion_b_evidence.service import (
        attach_supporting_upload_link,
        bundle_api_payload,
        reviewer_update_checklist_slot,
        update_bundle_metadata,
    )
    from documents.ocr.queue import process_pending_jobs, retry_document_ocr
    from documents.scoring.criterion_b_simulation_adapter import CRITERION_B_SIMULATION_ADAPTER_ENABLED
    from documents.scoring.document_evidence_points import effective_document_points
    from documents.service import create_upload, get_document, reviewer_can_access
    from extensions import db
    from faculty.rank_simulation_engine import compute_rank_simulation
    from kra_configuration.published_limits import (
        published_criterion_max_points,
        published_kra_max_points,
        published_settings_blob,
    )
    from models import Document, FacultyProfile, User
    from urllib.parse import urlparse

    report: dict = {
        "tag": TAG,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "adapterEnabled": CRITERION_B_SIMULATION_ADAPTER_ENABLED,
        "recordsCreated": [],
        "steps": [],
        "ocrScenarios": [],
        "defects": [],
    }

    app = create_app(Config)
    with app.app_context():
        db_name = urlparse(Config.database_url().replace("postgresql+psycopg", "postgresql")).path.lstrip("/")
        report["database"] = db_name
        if db_name != "facultylink":
            report["defects"].append("DATABASE_URL is not facultylink")
            _write(report)
            return 2
        if CRITERION_B_SIMULATION_ADAPTER_ENABLED:
            report["defects"].append("Simulation adapter enabled")
            _write(report)
            return 3

        faculty_user = User.query.filter_by(role="faculty", is_active=True).first()
        reviewer_user = User.query.filter_by(role="reviewer", is_active=True).first()
        profile = FacultyProfile.query.filter_by(user_id=faculty_user.id).first() if faculty_user else None
        if not faculty_user or not reviewer_user or not profile:
            report["defects"].append("Missing faculty/reviewer/profile")
            _write(report)
            return 4

        report["facultyEmail"] = faculty_user.email
        report["reviewerEmail"] = reviewer_user.email
        sim_before = compute_rank_simulation(profile)
        report["simBaseline"] = _sim_kra1_b(sim_before)

        def upload(
            *,
            title: str,
            indicator_id: str,
            primary_public_id: str | None = None,
            evidence_slot: str | None = None,
        ) -> Document:
            data = io.BytesIO(_unique_png_bytes())
            fs = FileStorage(stream=data, filename=f"{TAG}-{title[:36]}.png", content_type="image/png")
            doc = create_upload(
                faculty_user,
                file=fs,
                title=f"{TAG} {title}",
                kra_id="kra1",
                criterion_id="kra1-b",
                indicator_id=indicator_id,
                bundle_primary_public_id=primary_public_id,
                evidence_slot=evidence_slot,
            )
            rec = {
                "publicId": doc.public_id,
                "title": doc.title,
                "indicatorId": indicator_id,
                "primaryPublicId": primary_public_id,
                "evidenceSlot": evidence_slot,
            }
            report["recordsCreated"].append(rec)
            return doc

        # --- IM: overlap OCR + supporting (no relink) ---
        im_primary = upload(title="IM Primary overlap", indicator_id="kra1-b-module-sole")
        update_bundle_metadata(
            faculty_user,
            im_primary.public_id,
            {
                "materialTitle": f"{TAG} Overlap Module",
                "completeSetDeclared": True,
                "specializationAligned": True,
            },
        )
        im_support = upload(
            title="IM IMDC overlap",
            indicator_id="kra1-b-module-sole",
            primary_public_id=im_primary.public_id,
            evidence_slot=SLOT_IMDC_APPROVAL,
        )
        ocr_primary = _wait_ocr(app, im_primary.public_id)
        ocr_support = _wait_ocr(app, im_support.public_id)
        report["ocrScenarios"].append(
            {
                "name": "overlap_primary_and_supporting",
                "primaryOcr": ocr_primary,
                "supportingOcr": ocr_support,
            }
        )

        im_primary = _reload_primary(im_primary.public_id)
        payload = bundle_api_payload(im_primary)
        bundle = payload.get("bundle") or {}
        validation = payload.get("validation") or {}
        imdc = _checklist_entry(im_primary, SLOT_IMDC_APPROVAL)
        report["steps"].append(
            {
                "step": "im_after_overlap_ocr",
                "claimType": bundle.get("claimType"),
                "materialTitle": bundle.get("materialTitle"),
                "imdcDocumentId": imdc.get("documentId"),
                "validationStatus": validation.get("validationStatus"),
            }
        )
        if bundle.get("claimType") != CLAIM_TYPE_INSTRUCTIONAL_MATERIAL:
            report["defects"].append("IM claimType not instructional_material after OCR")
        if imdc.get("documentId") != im_support.public_id:
            report["defects"].append("IM supporting not on primary checklist without relink")

        remarks = f"{TAG} reviewer IM remarks"
        reviewer_update_checklist_slot(
            reviewer_user,
            im_primary.public_id,
            slot_id=SLOT_IMDC_APPROVAL,
            status="verified",
            reviewer_note=f"{TAG} IMDC verified",
            remarks=remarks,
        )
        process_pending_jobs(limit=2)
        _wait_ocr(app, im_primary.public_id, timeout_sec=5.0)
        retry_document_ocr(im_primary)
        ocr_after_verify = _wait_ocr(app, im_primary.public_id)
        report["ocrScenarios"].append({"name": "ocr_retry_after_reviewer_verify", "status": ocr_after_verify})

        im_primary = _reload_primary(im_primary.public_id)
        bundle2 = bundle_api_payload(im_primary).get("bundle") or {}
        imdc2 = _checklist_entry(im_primary, SLOT_IMDC_APPROVAL)
        if bundle2.get("reviewerRemarks") != remarks:
            report["defects"].append("Reviewer remarks lost after OCR retry")
        if imdc2.get("status") != "verified":
            report["defects"].append("Verified IMDC slot lost after OCR retry")
        if bundle2.get("claimType") != CLAIM_TYPE_INSTRUCTIONAL_MATERIAL:
            report["defects"].append("claimType lost after OCR retry")

        supporting = get_document(im_support.public_id)
        if effective_document_points(supporting) is not None:
            report["defects"].append("Supporting IM has independent points")

        # Idempotent attach (service layer, same as second upload would hit duplicate hash)
        try:
            attach_supporting_upload_link(
                supporting,
                primary_public_id=im_primary.public_id,
                evidence_slot=SLOT_IMDC_APPROVAL,
            )
            attach_supporting_upload_link(
                supporting,
                primary_public_id=im_primary.public_id,
                evidence_slot=SLOT_IMDC_APPROVAL,
            )
        except Exception as exc:  # noqa: BLE001
            report["defects"].append(f"Idempotent attach failed: {exc}")
        ids = [
            (bundle_api_payload(im_primary).get("bundle") or {})
            .get("checklist", {})
            .get(SLOT_IMDC_APPROVAL, {})
            .get("documentId")
        ]
        if ids.count(im_support.public_id) != 1:
            report["defects"].append("Duplicate checklist entries after idempotent attach")

        # OCR before supporting (sequential)
        im_seq = upload(title="IM Primary sequential", indicator_id="kra1-b-module-sole")
        _wait_ocr(app, im_seq.public_id)
        lib = upload(
            title="IM Library sequential",
            indicator_id="kra1-b-module-sole",
            primary_public_id=im_seq.public_id,
            evidence_slot=SLOT_LIBRARY_CERTIFICATION,
        )
        _wait_ocr(app, lib.public_id)
        _wait_ocr(app, im_seq.public_id, timeout_sec=10.0)
        im_seq = _reload_primary(im_seq.public_id)
        lib_entry = _checklist_entry(im_seq, SLOT_LIBRARY_CERTIFICATION)
        report["ocrScenarios"].append(
            {
                "name": "ocr_before_then_after_supporting",
                "libraryLinked": lib_entry.get("documentId") == lib.public_id,
            }
        )
        if lib_entry.get("documentId") != lib.public_id:
            report["defects"].append("Sequential OCR: library slot not linked")

        # --- Program (RRPA + implementation) ---
        prog = upload(title="Program Lead", indicator_id="kra1-b-program-lead")
        update_bundle_metadata(
            faculty_user,
            prog.public_id,
            {
                "programName": f"{TAG} BS Verification Program",
                "programDevelopmentKind": "new_program",
                "contributionDescription": f"{TAG} program contribution narrative.",
            },
        )
        for slot in (
            SLOT_DEAN_CERTIFICATION,
            SLOT_ACADEMIC_COUNCIL,
            SLOT_GOVERNING_BOARD,
            SLOT_IMPLEMENTATION,
            SLOT_FEASIBILITY_STUDY,
        ):
            upload(
                title=f"Prog {slot[:20]}",
                indicator_id="kra1-b-program-lead",
                primary_public_id=prog.public_id,
                evidence_slot=slot,
            )
        process_pending_jobs(limit=5)
        prog = _reload_primary(prog.public_id)
        v0 = bundle_api_payload(prog)["validation"]
        report["steps"].append(
            {
                "step": "program_rrpa_unknown",
                "readyForScoring": v0.get("readyForScoring"),
                "flags": [f for f in v0.get("flags", []) if "rrpa" in f],
            }
        )
        if v0.get("readyForScoring"):
            report["defects"].append("Program ready with RRPA unknown")

        reviewer_update_checklist_slot(
            reviewer_user,
            prog.public_id,
            slot_id=None,
            status=None,
            rrpa_copc_applicability="applicable",
            rrpa_copc_applicability_note="",
        )
        prog = _reload_primary(prog.public_id)
        v1 = bundle_api_payload(prog)["validation"]
        if v1.get("readyForScoring") or "missing_rrpa_or_copc" not in v1.get("flags", []):
            report["defects"].append("Applicable RRPA without doc should block scoring")

        rrpa_doc = upload(
            title="RRPA doc",
            indicator_id="kra1-b-program-lead",
            primary_public_id=prog.public_id,
            evidence_slot=SLOT_RRPA_COPC,
        )
        _wait_ocr(app, prog.public_id)
        _wait_ocr(app, rrpa_doc.public_id)
        prog = _reload_primary(prog.public_id)
        if _checklist_entry(prog, SLOT_IMPLEMENTATION).get("documentId") is None:
            report["defects"].append("Implementation evidence missing from checklist after OCR")

        prog_remarks = f"{TAG} program reviewer remarks"
        for slot in (
            SLOT_PRIMARY_CONTRIBUTION,
            SLOT_DEAN_CERTIFICATION,
            SLOT_ACADEMIC_COUNCIL,
            SLOT_GOVERNING_BOARD,
            SLOT_IMPLEMENTATION,
            SLOT_FEASIBILITY_STUDY,
            SLOT_RRPA_COPC,
        ):
            entry = _checklist_entry(prog, slot)
            if not entry.get("documentId"):
                report["defects"].append(f"Cannot verify missing slot {slot}")
                continue
            reviewer_update_checklist_slot(
                reviewer_user,
                prog.public_id,
                slot_id=slot,
                status="verified",
                reviewer_note=f"{TAG} ok",
            )
        reviewer_update_checklist_slot(
            reviewer_user,
            prog.public_id,
            slot_id=None,
            status=None,
            remarks=prog_remarks,
        )
        _wait_ocr(app, prog.public_id, timeout_sec=15.0)
        prog = _reload_primary(prog.public_id)
        v2 = bundle_api_payload(prog)["validation"]
        b2 = bundle_api_payload(prog).get("bundle") or {}
        report["steps"].append(
            {
                "step": "program_all_verified",
                "readyForScoring": v2.get("readyForScoring"),
                "validationStatus": v2.get("validationStatus"),
            }
        )
        if not v2.get("readyForScoring"):
            report["defects"].append("Program should be ready after full verification")

        reviewer_update_checklist_slot(
            reviewer_user,
            prog.public_id,
            slot_id=None,
            status=None,
            rrpa_copc_applicability="not_applicable",
            rrpa_copc_applicability_note=f"{TAG} documented exemption for controlled test.",
        )
        prog = _reload_primary(prog.public_id)
        v3 = bundle_api_payload(prog)["validation"]
        report["steps"].append(
            {
                "step": "program_rrpa_not_applicable",
                "rrpaCopcApplicability": v3.get("rrpaCopcApplicability"),
                "readyForScoring": v3.get("readyForScoring"),
            }
        )

        if not reviewer_can_access(reviewer_user, prog):
            report["defects"].append("Assigned reviewer lost access")
        if reviewer_can_access(faculty_user, prog):
            report["defects"].append("Faculty incorrectly has reviewer access")

        blob = published_settings_blob()
        report["caps"] = {
            "kra1": published_kra_max_points("kra1", blob),
            "criterionB": published_criterion_max_points("kra1-b", blob),
        }
        sim_after = compute_rank_simulation(profile)
        report["simAfter"] = _sim_kra1_b(sim_after)
        if report["simBaseline"] != report["simAfter"]:
            report["steps"].append(
                {"step": "sim_changed", "before": report["simBaseline"], "after": report["simAfter"]}
            )

    report["success"] = not report["defects"]
    report["finishedAt"] = datetime.now(timezone.utc).isoformat()
    _write(report)
    print(json.dumps({"success": report["success"], "defects": report["defects"]}, indent=2))
    return 0 if report["success"] else 1


def _sim_kra1_b(sim: dict) -> dict:
    kra1 = next((k for k in sim.get("kraScores") or [] if k.get("kraKey") == "kra1"), None)
    criteria = (kra1 or {}).get("criteriaScores") or []
    b = next((c for c in criteria if c.get("criterionId") == "kra1-b"), {})
    return {"estimatedPoints": b.get("estimatedPoints"), "maxPoints": b.get("maxPoints")}


def _write(report: dict) -> None:
    out_dir = ROOT / "backups"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"phase6b2_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "LATEST_PHASE6B2_REPORT.txt").write_text(path.name + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
