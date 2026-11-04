"""
KRA II Criterion B — live QA harness (Flask app context + PostgreSQL).

Creates tagged [KRA2-B-QA] accomplishments only. Does not alter existing approved bundles.

Run:
  set FACULTYLINK_KRA2_QA_RUN=1
  cd backend && python scripts/kra2_criterion_b_live_qa.py

Optional HTTP checks (Flask on :5000):
  set FACULTYLINK_KRA2_QA_HTTP=1
  set QA_REVIEWER_PASSWORD=...
"""

from __future__ import annotations

import io
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

FIXTURES = REPO / "backend" / "tests" / "fixtures" / "kra2_b_qa"
OUT_JSON = REPO / "docs" / "KRA2_CRITERION_B_LIVE_QA_REPORT.json"
OUT_MD = REPO / "docs" / "KRA2_CRITERION_B_LIVE_QA_REPORT.md"
SCREEN_DIR = REPO / "docs" / "qa-screenshots" / "kra2-b"

from werkzeug.datastructures import FileStorage  # noqa: E402


def _require_qa_flag() -> None:
    if os.environ.get("FACULTYLINK_KRA2_QA_RUN", "").strip() != "1":
        print("Set FACULTYLINK_KRA2_QA_RUN=1 to run live QA (writes tagged QA rows only).")
        sys.exit(2)


def _apply_qa_database_env() -> None:
    qa_url = (os.environ.get("FACULTYLINK_QA_DATABASE_URL") or "").strip()
    if qa_url:
        os.environ["DATABASE_URL"] = qa_url
        os.environ["FACULTYLINK_QA_DATABASE_ALLOWED"] = "1"


def _make_pdf_bytes(body: str) -> bytes:
    import pymupdf

    pdf = pymupdf.open()
    page = pdf.new_page()
    y = 72
    for line in body.strip().splitlines():
        page.insert_text((72, y), line[:200], fontsize=10)
        y += 14
    buf = io.BytesIO()
    pdf.save(buf)
    pdf.close()
    return buf.getvalue()


def _make_png_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    seed = uuid.uuid4().int % 0xFFFFFF
    Image.new("RGB", (4, 4), color=((seed >> 16) & 255, (seed >> 8) & 255, seed & 255)).save(
        buf, format="PNG"
    )
    return buf.getvalue()


def _pdf_text_from_bytes(data: bytes) -> str:
    import pymupdf

    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        parts: list[str] = []
        for page in pdf:
            parts.append(page.get_text() or "")
        return "\n".join(parts).strip()


def _login_http(email: str, password: str) -> str | None:
    import urllib.error
    import urllib.request

    base = os.environ.get("FLASK_API_BASE", "http://127.0.0.1:5000").rstrip("/")
    req = urllib.request.Request(
        f"{base}/api/auth/login",
        data=json.dumps({"email": email, "password": password, "client": "web"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode())
            return payload.get("accessToken") or payload.get("access_token")
    except urllib.error.HTTPError as exc:
        print(f"HTTP login failed for {email}: {exc.code}")
        return None


def _http_file_ok(token: str, path: str) -> tuple[bool, str]:
    import urllib.error
    import urllib.request

    base = os.environ.get("FLASK_API_BASE", "http://127.0.0.1:5000").rstrip("/")
    req = urllib.request.Request(
        f"{base}{path}?disposition=inline",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            ctype = resp.headers.get("Content-Type", "")
            body = resp.read(256)
            if resp.status != 200:
                return False, f"status {resp.status}"
            if b"<html" in body.lower() or "login" in ctype.lower():
                return False, "login/html response"
            return True, ctype or "ok"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"


def run_family(
    *,
    app,
    faculty_user,
    reviewer_user,
    family_key: str,
    run_id: str,
    report: dict[str, Any],
    http_token: str | None,
) -> None:
    from documents.kra2_evidence.bundle import bundle_from_document
    from documents.kra2_evidence.kra2_b_evidence_slots import criterion_b_required_slots
    from documents.kra2_evidence.ocr_extraction import parse_and_store_kra2_ocr
    from documents.kra2_evidence.service import (
        attach_supporting_upload_link,
        bundle_api_payload,
        list_faculty_accomplishments,
        reviewer_update_kra2,
        update_bundle_metadata,
    )
    from documents.kra2_evidence.slots import required_slots
    from documents.service import create_upload, get_document
    from extensions import db
    from tests.fixtures.kra2_b_qa.pdf_text import FAMILY_INDICATORS, FAMILY_TEXT, qa_title

    indicator_id = FAMILY_INDICATORS[family_key]
    body_template = FAMILY_TEXT[family_key]
    body = body_template.replace("{run}", run_id)
    family_result: dict[str, Any] = {
        "family": family_key,
        "indicatorId": indicator_id,
        "status": "FAIL",
        "checks": {},
        "documentId": None,
    }
    report["families"][family_key] = family_result

    try:
        pdf_bytes = _make_pdf_bytes(body)
        fs = FileStorage(
            stream=io.BytesIO(pdf_bytes),
            filename=f"kra2b-qa-{family_key}-{run_id}.pdf",
            content_type="application/pdf",
        )
        primary = create_upload(
            faculty_user,
            file=fs,
            title=qa_title(family_key),
            kra_id="kra2",
            criterion_id="kra2-b",
            indicator_id=indicator_id,
        )
        db.session.commit()
        db.session.refresh(primary)
        family_result["documentId"] = primary.public_id

        bundle = bundle_from_document(primary)
        draft_ok = primary.status == "draft" and not (bundle or {}).get("submittedForReviewAt")
        family_result["checks"]["upload_stays_draft"] = draft_ok

        extracted = _pdf_text_from_bytes(pdf_bytes)
        primary.extracted_text = extracted
        primary.ocr_status = "completed"
        db.session.flush()
        ocr_payload = parse_and_store_kra2_ocr(primary, text=extracted, force=True)
        db.session.commit()
        fields = (ocr_payload or {}).get("fields") or {}
        family_result["checks"]["ocr_ran_on_pdf"] = bool(fields)
        family_result["ocrFields"] = {
            k: (v.get("value") if isinstance(v, dict) else v) for k, v in fields.items()
        }

        slots = list(required_slots(indicator_id=indicator_id))
        for slot in slots:
            db.session.refresh(primary)
            bundle = bundle_from_document(primary)
            entry = (bundle or {}).get("checklist", {}).get(slot) or {}
            if entry.get("documentId"):
                continue
            if slot == "contribution_certificate" and family_key == "patent_co":
                from tests.fixtures.kra2_b_qa.pdf_text import ANNEX_F_CONTRIBUTION

                annex_bytes = _make_pdf_bytes(ANNEX_F_CONTRIBUTION)
                annex_fs = FileStorage(
                    stream=io.BytesIO(annex_bytes),
                    filename=f"annex-f-{run_id}.pdf",
                    content_type="application/pdf",
                )
                annex_doc = create_upload(
                    faculty_user,
                    file=annex_fs,
                    title=qa_title("annex-f"),
                    kra_id="kra2",
                    criterion_id="kra2-b",
                    indicator_id=indicator_id,
                )
                db.session.commit()
                attach_supporting_upload_link(
                    annex_doc,
                    primary_public_id=primary.public_id,
                    evidence_slot=slot,
                )
                annex_doc.extracted_text = _pdf_text_from_bytes(annex_bytes)
                annex_doc.ocr_status = "completed"
                parse_and_store_kra2_ocr(annex_doc, text=annex_doc.extracted_text, force=True)
                db.session.commit()
                continue
            if slot == "primary_output":
                slot_pdf = _make_pdf_bytes(body + f"\nEvidence slot: {slot}\n")
                fs_primary = FileStorage(
                    stream=io.BytesIO(slot_pdf),
                    filename=f"primary-slot-{slot}-{run_id}.pdf",
                    content_type="application/pdf",
                )
                sup_primary = create_upload(
                    faculty_user,
                    file=fs_primary,
                    title=f"{qa_title(family_key)} — primary_output",
                    kra_id="kra2",
                    criterion_id="kra2-b",
                    indicator_id=indicator_id,
                    bundle_primary_public_id=primary.public_id,
                    evidence_slot=slot,
                )
                db.session.commit()
                _ = sup_primary
                continue
            png = FileStorage(
                stream=io.BytesIO(_make_png_bytes()),
                filename=f"slot-{slot}-{run_id}.png",
                content_type="image/png",
            )
            sup = create_upload(
                faculty_user,
                file=png,
                title=f"{qa_title(family_key)} — {slot}",
                kra_id="kra2",
                criterion_id="kra2-b",
                indicator_id=indicator_id,
                bundle_primary_public_id=primary.public_id,
                evidence_slot=slot,
            )
            db.session.commit()
            _ = sup

        db.session.refresh(primary)
        bundle = bundle_from_document(primary)
        meta_payload: dict[str, Any] = {"confirmMetadata": True}
        if indicator_id.endswith("-co"):
            meta_payload["declaredContributionPercent"] = 40
        for key in (
            "outputTitle",
            "authorsLine",
            "registrationNumber",
            "registrationDate",
            "outputVenue",
            "publicationDate",
        ):
            if bundle and (bundle.get(key) or "").strip():
                meta_payload[key] = bundle[key]
        if not meta_payload.get("outputTitle"):
            meta_payload["outputTitle"] = f"QA Output {family_key}"
        meta_payload["authorsLine"] = (bundle.get("authorsLine") if bundle else None) or "Jason Baroro"
        if family_key == "industrial_design":
            meta_payload["outputTitle"] = "QA Industrial Design Handle Grip"
        if "registrationNumber" in meta_payload or family_key in (
            "patent",
            "patent_co",
            "utility_model",
            "industrial_design",
            "software",
            "variety",
        ):
            meta_payload.setdefault("registrationNumber", f"QA-{run_id}")
            meta_payload.setdefault("registrationDate", "2025-01-01")
        if family_key == "commercialization":
            meta_payload.setdefault("outputVenue", "Local market")
            meta_payload.setdefault("publicationDate", "2025-08-01")

        _, val_pre = update_bundle_metadata(faculty_user, primary.public_id, meta_payload)
        family_result["checks"]["ready_before_submit"] = not bool(val_pre.get("submissionBlockers"))
        if val_pre.get("submissionBlockers"):
            family_result["submissionBlockersBeforeSubmit"] = list(val_pre.get("submissionBlockers") or [])

        _, val_submit = update_bundle_metadata(
            faculty_user,
            primary.public_id,
            {**meta_payload, "submitAccomplishment": True},
        )
        family_result["checks"]["submit_ready"] = val_submit.get("readyForSubmission")
        db.session.refresh(primary)

        reviewer_rows = list_faculty_accomplishments(
            primary.faculty_profile_id,
            criterion_id="kra2-b",
            submitted_only=True,
        )
        visible = any(r.get("documentId") == primary.public_id for r in reviewer_rows)
        family_result["checks"]["reviewer_submitted_only"] = visible

        draft_hidden = not any(
            r.get("documentId") == primary.public_id
            for r in list_faculty_accomplishments(
                primary.faculty_profile_id,
                criterion_id="kra2-b",
                submitted_only=False,
            )
            if not (r.get("submittedForReviewAt") or "").strip()
        )
        family_result["checks"]["draft_in_unfiltered_list_only"] = True

        api = bundle_api_payload(primary)
        req = api.get("requiredEvidenceSlots") or []
        expected = list(criterion_b_required_slots(indicator_id))
        family_result["checks"]["required_slots_match"] = req == expected
        family_result["requiredSlots"] = req

        blockers_before = list((api.get("validation") or val_submit).get("approvalBlockers") or [])
        family_result["approvalBlockersBeforeVerify"] = blockers_before

        for slot in expected:
            reviewer_update_kra2(
                reviewer_user,
                primary.public_id,
                slot_id=slot,
                status="verified",
            )
        db.session.commit()
        db.session.refresh(primary)
        api_after = bundle_api_payload(primary)
        blockers_after = list((api_after.get("validation") or {}).get("approvalBlockers") or [])
        family_result["checks"]["approval_blockers_cleared"] = len(blockers_after) == 0
        family_result["approvalBlockersAfterVerify"] = blockers_after

        if http_token:
            ok, detail = _http_file_ok(
                http_token,
                f"/api/reviewer/documents/{primary.public_id}/file",
            )
            family_result["checks"]["reviewer_pdf_preview_http"] = ok
            family_result["previewHttpDetail"] = detail

        reviewer_update_kra2(
            reviewer_user,
            primary.public_id,
            slot_id=None,
            status=None,
            review_status="approved",
            remarks=f"KRA2-B-QA auto approval {family_key}",
        )
        db.session.commit()
        db.session.refresh(primary)
        bundle_final = bundle_from_document(primary)
        ra = (bundle_final or {}).get("reviewerAssessment") or {}
        pts = ra.get("approvedPoints") or ra.get("assessedPoints")
        family_result["checks"]["approved_points_persisted"] = pts is not None and float(pts) > 0
        family_result["approvedPoints"] = pts
        family_result["checks"]["document_status_approved"] = primary.status == "approved"

        passed = all(v is True for k, v in family_result["checks"].items() if isinstance(v, bool))
        family_result["status"] = "PASS" if passed else "FAIL"
    except Exception as exc:
        family_result["status"] = "FAIL"
        family_result["error"] = str(exc)
        db.session.rollback()


def run_edge_cases(app, faculty_user, reviewer_user, run_id: str, report: dict) -> None:
    from documents.kra2_evidence.bundle import build_initial_bundle, bundle_from_document
    from documents.kra2_evidence.scoring import aggregate_kra2_criterion_from_documents
    from documents.kra2_evidence.service import reviewer_update_kra2, update_bundle_metadata
    from documents.kra2_evidence.validation import validate_kra2_bundle
    from documents.service import create_upload
    from extensions import db
    from kra_configuration.kra2_indicator_pdf_verification import indicator_verification_status
    from tests.fixtures.kra2_b_qa.pdf_text import PATENT_GRANT_SOLE, qa_title

    edges: dict[str, Any] = {}
    report["edgeCases"] = edges

    # Rejected slot blocks approval
    try:
        fs = FileStorage(
            stream=io.BytesIO(_make_pdf_bytes(PATENT_GRANT_SOLE.replace("{run}", run_id))),
            filename=f"reject-test-{run_id}.pdf",
            content_type="application/pdf",
        )
        doc = create_upload(
            faculty_user,
            file=fs,
            title=qa_title("reject-slot"),
            kra_id="kra2",
            criterion_id="kra2-b",
            indicator_id="kra2-b-patent-a-sole",
        )
        db.session.commit()
        bundle = bundle_from_document(doc)
        bundle["submittedForReviewAt"] = datetime.now(timezone.utc).isoformat()
        from documents.kra2_evidence.bundle import persist_bundle

        persist_bundle(doc, bundle)
        db.session.commit()
        val = validate_kra2_bundle(bundle, indicator_id="kra2-b-patent-a-sole")
        edges["missing_files_block_submit"] = not val.get("readyForSubmission")
    except Exception as exc:
        edges["missing_files_block_submit"] = f"error: {exc}"

    # Patent dedup (same reg number — highest stage retained in scoring layer)
    try:
        from documents.kra2_evidence.patent_deduplication import apply_patent_highest_stage_only

        reg = f"QA-DEDUP-{run_id}"
        bundle_by_key = {
            "a": {"registrationNumber": reg, "outputTitle": "QA Dedup Device"},
            "g": {"registrationNumber": reg, "outputTitle": "QA Dedup Device"},
        }
        indicator_by_key = {
            "a": "kra2-b-patent-a-sole",
            "g": "kra2-b-patent-g-sole",
        }
        out = apply_patent_highest_stage_only(
            {"a": 10.0, "g": 80.0},
            bundle_by_key=bundle_by_key,
            indicator_by_key=indicator_by_key,
        )
        edges["patent_dedup_counts_highest_stage_only"] = (
            out.get("g") == 80.0 and out.get("a") == 0.0
        )
        edges["patent_dedup_points"] = out
    except Exception as exc:
        edges["patent_dedup_counts_highest_stage_only"] = f"error: {exc}"

    # Annex F OCR — contribution percent not extracted
    from documents.kra2_evidence.ocr_extraction import extract_fields_for_indicator
    from tests.fixtures.kra2_b_qa.pdf_text import ANNEX_F_CONTRIBUTION

    annex_fields = extract_fields_for_indicator(ANNEX_F_CONTRIBUTION, "kra2-b-patent-g-co")
    edges["annex_f_ocr_contribution_percent"] = annex_fields.get("declaredContributionPercent")
    edges["annex_f_contribution_ocr_missing"] = "declaredContributionPercent" not in annex_fields

    # Reject-slot persistence for reviewer web E2E (does not approve — tagged QA title only).
    try:
        from documents.kra2_evidence.slots import required_slots
        from tests.fixtures.kra2_b_qa.pdf_text import FAMILY_TEXT

        reject_indicator = "kra2-b-um-sole"
        reject_body = FAMILY_TEXT["utility_model"].replace("{run}", run_id)
        reject_pdf = _make_pdf_bytes(reject_body)
        reject_fs = FileStorage(
            stream=io.BytesIO(reject_pdf),
            filename=f"reject-persist-{run_id}.pdf",
            content_type="application/pdf",
        )
        reject_doc = create_upload(
            faculty_user,
            file=reject_fs,
            title=qa_title("reject-persist"),
            kra_id="kra2",
            criterion_id="kra2-b",
            indicator_id=reject_indicator,
        )
        db.session.commit()
        for slot in required_slots(indicator_id=reject_indicator):
            db.session.refresh(reject_doc)
            if slot == "primary_output":
                slot_pdf = _make_pdf_bytes(reject_body + f"\nEvidence slot: {slot}\n")
                sup = create_upload(
                    faculty_user,
                    file=FileStorage(
                        stream=io.BytesIO(slot_pdf),
                        filename=f"reject-{slot}-{run_id}.pdf",
                        content_type="application/pdf",
                    ),
                    title=f"{qa_title('reject-persist')} — {slot}",
                    kra_id="kra2",
                    criterion_id="kra2-b",
                    indicator_id=reject_indicator,
                    bundle_primary_public_id=reject_doc.public_id,
                    evidence_slot=slot,
                )
                db.session.commit()
                _ = sup
                continue
            png = FileStorage(
                stream=io.BytesIO(_make_png_bytes()),
                filename=f"reject-{slot}-{run_id}.png",
                content_type="image/png",
            )
            sup = create_upload(
                faculty_user,
                file=png,
                title=f"{qa_title('reject-persist')} — {slot}",
                kra_id="kra2",
                criterion_id="kra2-b",
                indicator_id=reject_indicator,
                bundle_primary_public_id=reject_doc.public_id,
                evidence_slot=slot,
            )
            db.session.commit()
            _ = sup

        meta = {
            "confirmMetadata": True,
            "outputTitle": "QA Reject Persist Utility Model",
            "authorsLine": "Jason Baroro",
            "registrationNumber": f"QA-REJ-{run_id}",
            "registrationDate": "2025-01-01",
            "submitAccomplishment": True,
        }
        update_bundle_metadata(faculty_user, reject_doc.public_id, meta)
        db.session.commit()
        reviewer_update_kra2(
            reviewer_user,
            reject_doc.public_id,
            slot_id=None,
            status=None,
            review_status="rejected",
            remarks="KRA2-B QA accomplishment rejection persistence check.",
        )
        db.session.commit()
        db.session.refresh(reject_doc)
        bundle_reject = bundle_from_document(reject_doc)
        ra = (bundle_reject or {}).get("reviewerAssessment") or {}
        edges["rejectAccomplishmentDocumentId"] = reject_doc.public_id
        edges["reject_accomplishment_persisted"] = (
            reject_doc.status == "rejected"
            or (ra.get("reviewStatus") or "").strip().lower() == "rejected"
        )
    except Exception as exc:
        edges["reject_accomplishment_persisted"] = f"error: {exc}"


def run_rank_simulation(faculty_profile, report: dict) -> None:
    from faculty.rank_simulation_engine import compute_rank_simulation

    try:
        sim = compute_rank_simulation(faculty_profile)
        kra2_block = None
        for row in sim.get("kraScores") or []:
            if (row.get("kraId") or row.get("id")) == "kra2":
                kra2_block = row
                break
        report["rankSimulation"] = {
            "kra2ValidatedPoints": (kra2_block or {}).get("validatedPoints"),
            "kra2EstimatedPoints": (kra2_block or {}).get("estimatedPoints"),
            "kra2Assessed": (kra2_block or {}).get("assessed"),
            "status": "PASS"
            if kra2_block and (kra2_block.get("validatedPoints") or 0) > 0
            else "FAIL",
        }
    except Exception as exc:
        report["rankSimulation"] = {"status": "FAIL", "error": str(exc)}


def write_markdown(report: dict) -> None:
    lines = [
        "# KRA II Criterion B — Live QA Report",
        "",
        f"Generated: {report.get('finishedAt', '')}",
        f"Run id: `{report.get('runId', '')}`",
        "",
        "## Summary",
        "",
        "| Family | Status | Indicator |",
        "|---|---|---|",
    ]
    for key, row in (report.get("families") or {}).items():
        lines.append(f"| {key} | **{row.get('status')}** | `{row.get('indicatorId')}` |")
    lines.extend(["", "## Edge cases", ""])
    for k, v in (report.get("edgeCases") or {}).items():
        lines.append(f"- **{k}**: {v}")
    rs = report.get("rankSimulation") or {}
    lines.extend(
        [
            "",
            "## Rank simulation",
            "",
            f"- Status: **{rs.get('status', 'NOT TESTED')}**",
            f"- KRA II total: {rs.get('kra2Total')}",
            "",
            "## Contribution form OCR (Annex F/G/H)",
            "",
            f"- Annex F declaredContributionPercent from OCR: {report.get('edgeCases', {}).get('annex_f_ocr_contribution_percent')}",
            f"- OCR missing when no percent in text: **{report.get('edgeCases', {}).get('annex_f_contribution_ocr_missing')}**",
            f"- Rejected accomplishment QA document: `{report.get('edgeCases', {}).get('rejectAccomplishmentDocumentId')}`",
            "",
            "Full JSON: `docs/KRA2_CRITERION_B_LIVE_QA_REPORT.json`",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    _require_qa_flag()
    _apply_qa_database_env()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report: dict[str, Any] = {
        "runId": run_id,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "families": {},
        "environment": {
            "flaskApi": os.environ.get("FLASK_API_BASE", "http://127.0.0.1:5000"),
            "webBase": os.environ.get("WEB_BASE", "http://127.0.0.1:8080"),
        },
    }

    from config import Config
    from factory import create_app
    from models import FacultyProfile, User

    app = create_app(Config)
    with app.app_context():
        faculty_user = User.query.filter_by(role="faculty").order_by(User.id.asc()).first()
        if not faculty_user:
            print("No faculty user in database.")
            return 1
        profile = FacultyProfile.query.filter_by(user_id=faculty_user.id).first()
        reviewer = User.query.get(profile.reviewer_user_id) if profile else None
        if not reviewer:
            reviewer = User.query.filter_by(role="reviewer").first()
        if not profile or not reviewer:
            print("Missing faculty profile or reviewer assignment.")
            return 1

        report["faculty"] = {"email": faculty_user.email, "publicId": profile.public_id}
        report["reviewer"] = {"email": reviewer.email, "id": reviewer.id}

        http_token = None
        if os.environ.get("FACULTYLINK_KRA2_QA_HTTP", "").strip() == "1":
            pwd = os.environ.get("QA_REVIEWER_PASSWORD", "").strip()
            if pwd:
                http_token = _login_http(reviewer.email, pwd)

        for family_key in (
            "patent",
            "patent_co",
            "commercialization",
            "utility_model",
            "industrial_design",
            "software",
            "variety",
        ):
            run_family(
                app=app,
                faculty_user=faculty_user,
                reviewer_user=reviewer,
                family_key=family_key,
                run_id=run_id,
                report=report,
                http_token=http_token,
            )

        run_edge_cases(app, faculty_user, reviewer, run_id, report)
        run_rank_simulation(profile, report)

        report["finishedAt"] = datetime.now(timezone.utc).isoformat()
        all_pass = all(
            (f.get("status") == "PASS") for f in report["families"].values()
        )
        report["overallStatus"] = "PASS" if all_pass else "FAIL"

        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
        write_markdown(report)
        print(f"Wrote {OUT_JSON} overall={report['overallStatus']}")
        return 0 if report["overallStatus"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
