"""
Phase 6B — Controlled Criterion B workflow exercise (facultylink DB).

Uses Flask app context + service layer (same code paths as HTTP).
Does not send email, drop tables, or delete records.
Run: cd backend && python scripts/phase6b_criterion_b_e2e.py
"""

from __future__ import annotations

import io
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from werkzeug.datastructures import FileStorage

from config import Config
from factory import create_app


TAG = "PHASE6B-E2E"


def _unique_png_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    seed = uuid.uuid4().int % 0xFFFFFF
    r, g, b = (seed >> 16) & 255, (seed >> 8) & 255, seed & 255
    Image.new("RGB", (3, 3), color=(r, g, b)).save(buf, format="PNG")
    return buf.getvalue()


def main() -> int:
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
        bundle_api_payload,
        link_existing_supporting_document,
        reviewer_update_checklist_slot,
        update_bundle_metadata,
    )
    from documents.service import get_document
    from documents.scoring.criterion_b_simulation_adapter import CRITERION_B_SIMULATION_ADAPTER_ENABLED
    from documents.scoring.document_evidence_points import effective_document_points
    from documents.service import create_upload, reviewer_can_access
    from extensions import db
    from faculty.rank_simulation_engine import compute_rank_simulation
    from kra_configuration.published_limits import (
        published_criterion_max_points,
        published_kra_max_points,
        published_settings_blob,
    )
    from models import FacultyProfile, User

    def _upload(
        faculty_user: User,
        *,
        title: str,
        indicator_id: str,
        primary_public_id: str | None = None,
        evidence_slot: str | None = None,
    ):
        data = io.BytesIO(_unique_png_bytes())
        fs = FileStorage(stream=data, filename=f"{TAG}-{title[:40]}.png", content_type="image/png")
        return create_upload(
            faculty_user,
            file=fs,
            title=f"{TAG} {title}",
            kra_id="kra1",
            criterion_id="kra1-b",
            indicator_id=indicator_id,
            bundle_primary_public_id=primary_public_id,
            evidence_slot=evidence_slot,
        )

    report: dict = {
        "tag": TAG,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "adapterEnabled": CRITERION_B_SIMULATION_ADAPTER_ENABLED,
        "recordsCreated": [],
        "steps": [],
        "defects": [],
        "knownDefects": [
            "Primary bundle checklist slots may be cleared when inline OCR completes after "
            "supporting upload-with-link; relink step mitigates for this script only.",
        ],
    }

    def _relink_supporting(faculty_user: User, primary_public_id: str) -> None:
        primary = get_document(primary_public_id)
        if not primary:
            return
        checklist = (bundle_api_payload(primary).get("bundle") or {}).get("checklist") or {}
        for rec in report["recordsCreated"]:
            if (
                rec.get("primaryPublicId") == primary_public_id
                and rec.get("role", "").startswith("supporting")
                and rec.get("slot")
            ):
                slot = rec["slot"]
                entry = checklist.get(slot) if isinstance(checklist, dict) else None
                if isinstance(entry, dict) and entry.get("documentId"):
                    continue
                link_existing_supporting_document(
                    faculty_user,
                    primary_public_id=primary_public_id,
                    supporting_public_id=rec["publicId"],
                    evidence_slot=slot,
                )
                primary = get_document(primary_public_id)
                checklist = (bundle_api_payload(primary).get("bundle") or {}).get("checklist") or {}

    app = create_app(Config)
    with app.app_context():
        from urllib.parse import urlparse

        db_name = urlparse(Config.database_url().replace("postgresql+psycopg", "postgresql")).path.lstrip("/")
        report["database"] = db_name
        report["smtpEnabled"] = Config.smtp_enabled()
        report["uploadFolder"] = str(app.config.get("UPLOAD_FOLDER"))

        if db_name != "facultylink":
            report["defects"].append("DATABASE_URL is not facultylink — aborted before writes.")
            _write_report(report)
            return 2

        if CRITERION_B_SIMULATION_ADAPTER_ENABLED:
            report["defects"].append("CRITERION_B_SIMULATION_ADAPTER_ENABLED is True — aborted.")
            _write_report(report)
            return 3

        faculty_user = User.query.filter_by(role="faculty", is_active=True).first()
        reviewer_user = User.query.filter_by(role="reviewer", is_active=True).first()
        if not faculty_user or not reviewer_user:
            report["defects"].append("Missing active faculty or reviewer user.")
            _write_report(report)
            return 4

        profile = FacultyProfile.query.filter_by(user_id=faculty_user.id).first()
        if not profile:
            report["defects"].append("Faculty profile missing.")
            _write_report(report)
            return 5

        report["testFacultyEmail"] = faculty_user.email
        report["testReviewerEmail"] = reviewer_user.email

        sim_before = compute_rank_simulation(profile)
        report["rankSimulationBaseline"] = _sim_snapshot(sim_before)

        # --- IM primary ---
        im_primary = _upload(faculty_user, title="IM Module Primary", indicator_id="kra1-b-module-sole")
        report["recordsCreated"].append({"role": "primary_im", "publicId": im_primary.public_id})
        payload = bundle_api_payload(im_primary)
        b = payload.get("bundle") or {}
        v = payload.get("validation") or {}
        report["steps"].append(
            {
                "step": "im_bundle_init",
                "claimType": b.get("claimType"),
                "hasChecklist": bool(b.get("checklist")),
                "validationStatus": v.get("validationStatus"),
                "readyForScoring": v.get("readyForScoring"),
            }
        )
        if b.get("claimType") != "instructional_material" or not b.get("checklist"):
            report["defects"].append("IM bundle failed to initialize.")

        update_bundle_metadata(
            faculty_user,
            im_primary.public_id,
            {
                "materialTitle": f"{TAG} Calculus Module Sample",
                "completeSetDeclared": True,
                "specializationAligned": True,
            },
        )
        im_primary = db.session.get(type(im_primary), im_primary.id)
        v2 = bundle_api_payload(im_primary)["validation"]
        report["steps"].append(
            {
                "step": "im_metadata_patch",
                "validationStatus": v2.get("validationStatus"),
                "flags": v2.get("flags", [])[:12],
            }
        )

        for slot in (SLOT_IMDC_APPROVAL, SLOT_LIBRARY_CERTIFICATION, SLOT_COMPLETE_SET):
            sup = _upload(
                faculty_user,
                title=f"IM support {slot}",
                indicator_id="kra1-b-module-sole",
                primary_public_id=im_primary.public_id,
                evidence_slot=slot,
            )
            report["recordsCreated"].append(
                {
                    "role": "supporting_im",
                    "slot": slot,
                    "publicId": sup.public_id,
                    "primaryPublicId": im_primary.public_id,
                }
            )

        _relink_supporting(faculty_user, im_primary.public_id)
        im_primary = get_document(im_primary.public_id)
        v3 = bundle_api_payload(im_primary)["validation"]
        report["steps"].append(
            {
                "step": "im_supporting_linked",
                "validationStatus": v3.get("validationStatus"),
                "readyForScoring": v3.get("readyForScoring"),
            }
        )
        if v3.get("validationStatus") not in ("incomplete", "reviewer_required"):
            report["defects"].append(f"Unexpected IM status after partial evidence: {v3.get('validationStatus')}")

        sup_doc = None
        for rec in report["recordsCreated"]:
            if rec.get("slot") == SLOT_IMDC_APPROVAL and rec.get("role") == "supporting_im":
                sup_doc = get_document(rec["publicId"])
                break
        if sup_doc and effective_document_points(sup_doc) is not None:
            report["defects"].append("Supporting IM document returned independent points.")

        im_primary = db.session.get(type(im_primary), im_primary.id)
        checklist = (bundle_api_payload(im_primary).get("bundle") or {}).get("checklist") or {}
        imdc_entry = checklist.get(SLOT_IMDC_APPROVAL) if isinstance(checklist, dict) else {}
        if not (isinstance(imdc_entry, dict) and imdc_entry.get("documentId")):
            report["defects"].append("IMDC slot missing documentId before reviewer verify.")
        else:
            _, rv = reviewer_update_checklist_slot(
                reviewer_user,
                im_primary.public_id,
                slot_id=SLOT_IMDC_APPROVAL,
                status="verified",
                reviewer_note=f"{TAG} verified IMDC slot.",
                remarks=f"{TAG} reviewer bundle remarks for IM.",
            )
            report["steps"].append({"step": "im_reviewer_verify_slot", "validationStatus": rv.get("validationStatus")})
        im_primary = db.session.get(type(im_primary), im_primary.id)
        if (im_primary.extracted_info or {}).get("criterionBEvidenceBundle", {}).get("reviewerRemarks") != f"{TAG} reviewer bundle remarks for IM.":
            report["defects"].append("Reviewer remarks did not persist on IM bundle.")

        # --- Program primary ---
        prog_primary = _upload(faculty_user, title="Program Lead Primary", indicator_id="kra1-b-program-lead")
        report["recordsCreated"].append({"role": "primary_program", "publicId": prog_primary.public_id})
        update_bundle_metadata(
            faculty_user,
            prog_primary.public_id,
            {
                "programName": f"{TAG} BS Sample Program",
                "programDevelopmentKind": "new_program",
                "contributionDescription": f"{TAG} led feasibility and curriculum design.",
            },
        )
        prog_primary = db.session.get(type(prog_primary), prog_primary.id)
        for slot in (
            SLOT_DEAN_CERTIFICATION,
            SLOT_ACADEMIC_COUNCIL,
            SLOT_GOVERNING_BOARD,
            SLOT_IMPLEMENTATION,
            SLOT_FEASIBILITY_STUDY,
        ):
            sup = _upload(
                faculty_user,
                title=f"Program {slot}",
                indicator_id="kra1-b-program-lead",
                primary_public_id=prog_primary.public_id,
                evidence_slot=slot,
            )
            report["recordsCreated"].append(
                {
                    "role": "supporting_program",
                    "slot": slot,
                    "publicId": sup.public_id,
                    "primaryPublicId": prog_primary.public_id,
                }
            )

        _relink_supporting(faculty_user, prog_primary.public_id)
        prog_primary = get_document(prog_primary.public_id)
        v_unknown = bundle_api_payload(prog_primary)["validation"]
        report["steps"].append(
            {
                "step": "program_rrpa_unknown",
                "rrpaCopcApplicability": v_unknown.get("rrpaCopcApplicability"),
                "readyForScoring": v_unknown.get("readyForScoring"),
                "flags": [f for f in v_unknown.get("flags", []) if "rrpa" in f],
            }
        )
        if v_unknown.get("readyForScoring"):
            report["defects"].append("Program readyForScoring true while RRPA applicability unknown.")
        if "rrpa_copc_applicability_undetermined" not in v_unknown.get("flags", []):
            report["defects"].append("Expected rrpa_copc_applicability_undetermined flag.")

        reviewer_update_checklist_slot(
            reviewer_user,
            prog_primary.public_id,
            slot_id=None,
            status=None,
            rrpa_copc_applicability="applicable",
            rrpa_copc_applicability_note="",
            remarks=f"{TAG} RRPA applicable.",
        )
        prog_primary = db.session.get(type(prog_primary), prog_primary.id)
        v_app = bundle_api_payload(prog_primary)["validation"]
        report["steps"].append(
            {
                "step": "program_rrpa_applicable_missing_doc",
                "readyForScoring": v_app.get("readyForScoring"),
                "flags": [f for f in v_app.get("flags", []) if "rrpa" in f or "missing" in f],
            }
        )
        if v_app.get("readyForScoring") or "missing_rrpa_or_copc" not in v_app.get("flags", []):
            report["defects"].append("Applicable RRPA without document should block scoring.")

        rrpa_sup = _upload(
            faculty_user,
            title="RRPA doc",
            indicator_id="kra1-b-program-lead",
            primary_public_id=prog_primary.public_id,
            evidence_slot=SLOT_RRPA_COPC,
        )
        report["recordsCreated"].append(
            {
                "role": "supporting_program",
                "slot": SLOT_RRPA_COPC,
                "publicId": rrpa_sup.public_id,
                "primaryPublicId": prog_primary.public_id,
            }
        )
        _relink_supporting(faculty_user, prog_primary.public_id)
        prog_primary = get_document(prog_primary.public_id)

        for slot in (
            SLOT_PRIMARY_CONTRIBUTION,
            SLOT_DEAN_CERTIFICATION,
            SLOT_ACADEMIC_COUNCIL,
            SLOT_GOVERNING_BOARD,
            SLOT_IMPLEMENTATION,
            SLOT_FEASIBILITY_STUDY,
            SLOT_RRPA_COPC,
        ):
            entry = ((bundle_api_payload(prog_primary).get("bundle") or {}).get("checklist") or {}).get(slot)
            if not (isinstance(entry, dict) and entry.get("documentId")):
                report["defects"].append(f"Program slot missing before verify: {slot}")
                continue
            reviewer_update_checklist_slot(
                reviewer_user,
                prog_primary.public_id,
                slot_id=slot,
                status="verified",
                reviewer_note=f"{TAG} verified {slot}",
            )
        prog_primary = db.session.get(type(prog_primary), prog_primary.id)
        v_ready = bundle_api_payload(prog_primary)["validation"]
        report["steps"].append(
            {
                "step": "program_rrpa_applicable_verified",
                "validationStatus": v_ready.get("validationStatus"),
                "readyForScoring": v_ready.get("readyForScoring"),
            }
        )

        reviewer_update_checklist_slot(
            reviewer_user,
            prog_primary.public_id,
            slot_id=None,
            status=None,
            rrpa_copc_applicability="not_applicable",
            rrpa_copc_applicability_note=f"{TAG} COPC exempt per controlled test memo.",
        )
        prog_primary = db.session.get(type(prog_primary), prog_primary.id)
        v_na = bundle_api_payload(prog_primary)["validation"]
        report["steps"].append(
            {
                "step": "program_rrpa_not_applicable",
                "rrpaCopcApplicability": v_na.get("rrpaCopcApplicability"),
                "readyForScoring": v_na.get("readyForScoring"),
            }
        )

        # Authorization: faculty cannot access reviewer_can_access as faculty role user
        if reviewer_can_access(faculty_user, prog_primary):
            report["defects"].append("Faculty user incorrectly passed reviewer_can_access.")

        admin = User.query.filter_by(role="administrator", is_active=True).first()
        if admin and reviewer_can_access(admin, prog_primary):
            report["steps"].append({"step": "admin_not_assigned_reviewer_access", "access": False, "note": "ok if False"})
        if not reviewer_can_access(reviewer_user, prog_primary):
            report["defects"].append("Assigned reviewer cannot access program primary.")

        blob = published_settings_blob()
        report["publishedCaps"] = {
            "kra1Max": published_kra_max_points("kra1", blob),
            "criterionBMax": published_criterion_max_points("kra1-b", blob),
        }

        sim_after = compute_rank_simulation(profile)
        report["rankSimulationAfter"] = _sim_snapshot(sim_after)

        te = sim_after.get("teachingEffectiveness") or {}
        report["criterionAUnchanged"] = {
            "setCombinedValidated": (te.get("set") or {}).get("combinedValidatedPoints"),
            "sefCombinedValidated": (te.get("sef") or {}).get("combinedValidatedPoints"),
        }

    report["finishedAt"] = datetime.now(timezone.utc).isoformat()
    report["success"] = not report["defects"]
    _write_report(report)
    print(json.dumps({"success": report["success"], "defects": report["defects"], "records": len(report["recordsCreated"])}, indent=2))
    return 0 if report["success"] else 1


def _sim_snapshot(sim: dict) -> dict:
    kra1 = next((k for k in sim.get("kraScores") or [] if k.get("kraKey") == "kra1" or k.get("kraId") == "kra1"), None)
    if not kra1:
        for k in sim.get("kraScores") or []:
            if "kra1" in str(k.get("kraKey", "")):
                kra1 = k
                break
    criteria = (kra1 or {}).get("criteriaScores") or []
    b_row = next((c for c in criteria if c.get("criterionId") == "kra1-b"), {})
    return {
        "estimatedTotalKraPoints": sim.get("estimatedTotalKraPoints"),
        "kra1Estimated": (kra1 or {}).get("estimatedPoints"),
        "kra1-b": {
            "estimatedPoints": b_row.get("estimatedPoints"),
            "maxPoints": b_row.get("maxPoints"),
        },
        "configurationComplete": sim.get("configurationComplete"),
    }


def _write_report(report: dict) -> None:
    out_dir = ROOT / "backups"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"phase6b_e2e_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "LATEST_PHASE6B_E2E_REPORT.txt").write_text(path.name + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
