"""
KRA III — live integration QA (Flask app context + PostgreSQL).

Creates tagged [KRA3-QA] accomplishments only. Does not modify approved legacy rows.

Run:
  set FACULTYLINK_KRA3_QA_RUN=1
  cd backend && python scripts/kra3_live_qa.py

Optional HTTP (Flask on :5000):
  set FACULTYLINK_KRA3_QA_HTTP=1
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

OUT_JSON = REPO / "docs" / "KRA3_LIVE_QA_REPORT.json"

def _representative(run_id: str) -> tuple[tuple[str, str, dict[str, Any]], ...]:
    income_unique = 50000 + (int(run_id[-6:], 36) % 40000)
    return (
        (
            "kra3-a-linkage",
            "kra3-a",
            {
                "activityTitle": "QA Partnership",
                "organizationName": "Partner Org",
                "facultyRole": "Lead",
                "activityDate": "2026-01-15",
                "approvalReference": "BR-2026-001",
            },
        ),
        (
            "kra3-a-income-lead-100k",
            "kra3-a",
            {
                "activityTitle": "QA Income",
                "grossIncomeAmount": income_unique,
                "activityDate": "2026-02-01",
                "facultyRole": "Lead",
                "organizationName": "Finance Unit",
            },
        ),
        (
            "kra3-b-train-local",
            "kra3-b",
            {
                "activityTitle": "QA Training",
                "deliveryHours": 2,
                "activityDate": "2026-03-01",
                "facultyRole": "Resource person",
                "organizationName": "Barangay Hall",
            },
        ),
        (
            "kra3-c-satisfaction",
            "kra3-c",
            {
                "activityTitle": "QA CSR",
                "csrOverallRating": 85,
                "linkedExtensionProjectId": f"qa-ext-{run_id}",
            },
        ),
        (
            "kra3-d-president",
            "kra3-d",
            {
                "designationTitle": "QA President role",
                "approvalReference": "SO-2026-QA",
                "serviceStartDate": "2025-01-01",
                "serviceEndDate": "2026-01-01",
                "serviceDurationMonths": 12,
            },
        ),
    )

from werkzeug.datastructures import FileStorage  # noqa: E402


def _require_flag() -> None:
    if os.environ.get("FACULTYLINK_KRA3_QA_RUN", "").strip() != "1":
        print("Set FACULTYLINK_KRA3_QA_RUN=1 to run KRA III live QA.")
        sys.exit(2)


def _qa_title(indicator_id: str) -> str:
    return f"[KRA3-QA] {indicator_id} {datetime.now(timezone.utc).strftime('%Y%m%d')}"


def _make_png_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    seed = uuid.uuid4().int % 0xFFFFFF
    Image.new("RGB", (4, 4), color=((seed >> 16) & 255, (seed >> 8) & 255, seed & 255)).save(
        buf, format="PNG"
    )
    return buf.getvalue()


def _make_pdf(body: str) -> bytes:
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
    except urllib.error.HTTPError:
        return None


def _http_get_json(token: str, path: str) -> tuple[int, dict | None]:
    import urllib.error
    import urllib.request

    base = os.environ.get("FLASK_API_BASE", "http://127.0.0.1:5000").rstrip("/")
    req = urllib.request.Request(
        f"{base}{path}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, None


def _fill_evidence_slots(
    faculty_user,
    primary,
    *,
    indicator_id: str,
    criterion_id: str,
    body: str,
    run_id: str,
) -> None:
    from documents.kra3_evidence.bundle import bundle_from_document
    from documents.kra3_evidence.slots import required_slots
    from documents.service import create_upload
    from extensions import db

    slots = list(required_slots(indicator_id=indicator_id))
    for slot in slots:
        db.session.refresh(primary)
        bundle = bundle_from_document(primary)
        entry = (bundle or {}).get("checklist", {}).get(slot) or {}
        if entry.get("documentId"):
            continue
        if slot in ("primary_output", "partnership_approval", "csr_report", "special_order_designation"):
            slot_pdf = _make_pdf(body + f"\nEvidence slot: {slot}\n")
            fs = FileStorage(
                stream=io.BytesIO(slot_pdf),
                filename=f"kra3-{slot}-{run_id}.pdf",
                content_type="application/pdf",
            )
        else:
            fs = FileStorage(
                stream=io.BytesIO(_make_png_bytes()),
                filename=f"kra3-{slot}-{run_id}.png",
                content_type="image/png",
            )
        create_upload(
            faculty_user,
            file=fs,
            title=f"{_qa_title(indicator_id)} — {slot}",
            kra_id="kra3",
            criterion_id=criterion_id,
            indicator_id=indicator_id,
            bundle_primary_public_id=primary.public_id,
            evidence_slot=slot,
        )
        db.session.commit()


def run_indicator(
    *,
    faculty_user,
    reviewer_user,
    profile,
    indicator_id: str,
    criterion_id: str,
    metadata: dict[str, Any],
    run_id: str,
    report: dict[str, Any],
    http_token: str | None,
) -> None:
    from documents.kra3_evidence.bundle import bundle_from_document
    from documents.kra3_evidence.service import (
        bundle_api_payload,
        list_faculty_accomplishments,
        reviewer_update_kra3,
        update_bundle_metadata,
    )
    from documents.kra3_evidence.ocr_extraction import ensure_kra3_ocr_extraction
    from documents.kra3_evidence.slots import required_slots
    from documents.service import create_upload
    from extensions import db
    from kra_configuration.kra3_workflow import metadata_field_ids

    row: dict[str, Any] = {"indicatorId": indicator_id, "criterionId": criterion_id, "checks": {}, "status": "FAIL"}
    report["indicators"][indicator_id] = row

    try:
        gross = metadata.get("grossIncomeAmount")
        body = (
            f"KRA III QA run {run_id}\nIndicator: {indicator_id}\n"
            f"Gross income {gross}\nCSR rating 85\nHours 2\n"
        )
        pdf = _make_pdf(body)
        fs = FileStorage(
            stream=io.BytesIO(pdf),
            filename=f"kra3-qa-{indicator_id}-{run_id}.pdf",
            content_type="application/pdf",
        )
        primary = create_upload(
            faculty_user,
            file=fs,
            title=_qa_title(indicator_id),
            kra_id="kra3",
            criterion_id=criterion_id,
            indicator_id=indicator_id,
        )
        db.session.commit()
        db.session.refresh(primary)
        row["documentId"] = primary.public_id

        bundle = bundle_from_document(primary)
        row["checks"]["bundle_initialized"] = isinstance(bundle, dict) and bundle.get("indicatorId") == indicator_id

        slots = list(required_slots(indicator_id=indicator_id))
        row["checks"]["required_slots"] = len(slots) >= 1

        _fill_evidence_slots(
            faculty_user,
            primary,
            indicator_id=indicator_id,
            criterion_id=criterion_id,
            body=body,
            run_id=run_id,
        )
        ensure_kra3_ocr_extraction(primary)
        db.session.commit()

        field_ids = metadata_field_ids(indicator_id)
        payload_meta = {**metadata, "confirmMetadata": True}
        payload_meta["metadataConfirmed"] = {k: True for k in field_ids}
        if "activityTitle" in metadata:
            payload_meta["outputTitle"] = metadata["activityTitle"]
        _, val_draft = update_bundle_metadata(faculty_user, primary.public_id, payload_meta)
        row["checks"]["metadata_saved"] = val_draft.get("readyForSubmission") is True
        if not row["checks"]["metadata_saved"]:
            row["draftBlockers"] = val_draft.get("submissionBlockers")

        _, val_submit = update_bundle_metadata(
            faculty_user,
            primary.public_id,
            {"submitAccomplishment": True, **payload_meta},
        )
        row["checks"]["submit_ready"] = val_submit.get("readyForSubmission") is True
        row["checks"]["submitted_status"] = False
        db.session.refresh(primary)
        row["checks"]["submitted_status"] = primary.status == "pending_review"
        if not row["checks"]["submit_ready"]:
            row["submissionBlockers"] = val_submit.get("submissionBlockers")

        submitted_rows = list_faculty_accomplishments(
            profile.id, criterion_id=criterion_id, submitted_only=True
        )
        row["checks"]["reviewer_list_visible"] = any(
            r.get("documentId") == primary.public_id for r in submitted_rows
        )

        api = bundle_api_payload(primary)
        row["checks"]["api_required_slots"] = len(api.get("requiredEvidenceSlots") or []) >= 1
        est = (api.get("scoring") or {}).get("estimatedPoints")
        row["estimatedPoints"] = est
        official_base = (api.get("scoring") or {}).get("officialBasePoints")
        row["officialBasePoints"] = official_base
        if indicator_id.startswith("kra3-d-"):
            # Catalog fallback disabled for D; estimates may still reflect Admin-published points.
            row["checks"]["designation_scoring_policy"] = official_base is None or est is None or est == official_base
        else:
            row["checks"]["estimated_points_present"] = est is not None and est > 0

        db.session.refresh(primary)
        checklist = (bundle_from_document(primary) or {}).get("checklist") or {}
        for slot in slots:
            entry = checklist.get(slot) if isinstance(checklist.get(slot), dict) else {}
            if not entry.get("documentId"):
                continue
            reviewer_update_kra3(
                reviewer_user,
                primary.public_id,
                slot_id=slot,
                status="verified",
                reviewer_note="KRA3 QA verify",
            )
        db.session.commit()

        reviewer_update_kra3(
            reviewer_user,
            primary.public_id,
            slot_id=None,
            status=None,
            review_status="approved",
            remarks=f"KRA3 QA approval {indicator_id} automated",
        )
        db.session.commit()
        db.session.refresh(primary)
        bundle_final = bundle_from_document(primary)
        ra = (bundle_final or {}).get("reviewerAssessment") or {}
        row["checks"]["approved_persisted"] = (bundle_final or {}).get("reviewStatus") == "approved"
        row["approvedPoints"] = ra.get("assessedPoints")

        if http_token and criterion_id:
            crit_key = criterion_id
            status, summary = _http_get_json(
                http_token,
                f"/api/reviewer/me/faculty/{profile.public_id}/{crit_key}/summary",
            )
            row["checks"]["http_summary"] = status == 200 and isinstance(summary, dict)
            status2, acc = _http_get_json(
                http_token,
                f"/api/reviewer/me/faculty/{profile.public_id}/{crit_key}/accomplishments",
            )
            row["checks"]["http_accomplishments"] = status2 == 200 and isinstance(acc, dict)

        failed = [k for k, v in row["checks"].items() if v is False]
        row["status"] = "PASS" if not failed else "FAIL"
        if failed:
            row["failedChecks"] = failed
    except Exception as exc:
        row["status"] = "FAIL"
        row["error"] = str(exc)
        db.session.rollback()


def run_rank_sim(profile, report: dict) -> None:
    from faculty.rank_simulation_engine import compute_rank_simulation

    try:
        sim = compute_rank_simulation(profile)
        kra3 = next((r for r in (sim.get("kraScores") or []) if (r.get("kraId") or r.get("id")) == "kra3"), None)
        report["rankSimulation"] = {
            "status": "PASS" if kra3 else "FAIL",
            "estimatedPoints": (kra3 or {}).get("estimatedPoints"),
            "validatedPoints": (kra3 or {}).get("validatedPoints"),
            "maxPoints": (kra3 or {}).get("maxPoints"),
        }
        if kra3 and kra3.get("validatedPoints") is not None:
            report["rankSimulation"]["cap_ok"] = float(kra3["validatedPoints"]) <= 100.0
    except Exception as exc:
        report["rankSimulation"] = {"status": "FAIL", "error": str(exc)}


def main() -> int:
    _require_flag()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report: dict[str, Any] = {
        "runId": run_id,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "indicators": {},
        "environment": {"database": "facultylink (app DATABASE_URL)", "api": os.environ.get("FLASK_API_BASE", "http://127.0.0.1:5000")},
    }

    from config import Config
    from factory import create_app
    from models import FacultyProfile, User

    app = create_app(Config)
    with app.app_context():
        faculty_user = User.query.filter_by(role="faculty").order_by(User.id.asc()).first()
        if not faculty_user:
            print("No faculty user.")
            return 1
        profile = FacultyProfile.query.filter_by(user_id=faculty_user.id).first()
        reviewer = User.query.get(profile.reviewer_user_id) if profile else None
        if not reviewer:
            reviewer = User.query.filter_by(role="reviewer").first()
        if not profile or not reviewer:
            print("Missing profile/reviewer.")
            return 1

        report["facultyRole"] = "faculty"
        report["reviewerRole"] = "reviewer"
        report["facultyPublicId"] = profile.public_id

        http_token = None
        if os.environ.get("FACULTYLINK_KRA3_QA_HTTP", "").strip() == "1":
            pwd = os.environ.get("QA_REVIEWER_PASSWORD", "").strip()
            if pwd:
                http_token = _login_http(reviewer.email, pwd)

        for indicator_id, criterion_id, meta in _representative(run_id):
            run_indicator(
                faculty_user=faculty_user,
                reviewer_user=reviewer,
                profile=profile,
                indicator_id=indicator_id,
                criterion_id=criterion_id,
                metadata=meta,
                run_id=run_id,
                report=report,
                http_token=http_token,
            )

        run_rank_sim(profile, report)
        report["finishedAt"] = datetime.now(timezone.utc).isoformat()
        report["overallStatus"] = (
            "PASS"
            if all(r.get("status") == "PASS" for r in report["indicators"].values())
            and (report.get("rankSimulation") or {}).get("status") == "PASS"
            else "FAIL"
        )

        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote {OUT_JSON} overall={report['overallStatus']}")
        return 0 if report["overallStatus"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
