"""
KRA IV — live integration QA (Flask app context + isolated PostgreSQL).

Creates tagged [KRA4-QA] accomplishments only. Requires facultylink_qa database.

Run:
  set FACULTYLINK_KRA4_QA_RUN=1
  set FACULTYLINK_QA_DATABASE_URL=postgresql+psycopg://postgres:...@127.0.0.1:5432/facultylink_qa
  set FACULTYLINK_QA_DATABASE_ALLOWED=1
  set QA_FACULTY_EMAIL=...   (recommended)
  cd backend && python scripts/kra4_live_qa.py
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

OUT_JSON = REPO / "docs" / "KRA4_LIVE_QA_REPORT.json"

from werkzeug.datastructures import FileStorage  # noqa: E402


def _require_flag() -> None:
    if os.environ.get("FACULTYLINK_KRA4_QA_RUN", "").strip() != "1":
        print("Set FACULTYLINK_KRA4_QA_RUN=1 to run KRA IV live QA.")
        sys.exit(2)


def _qa_title(indicator_id: str) -> str:
    return f"[KRA4-QA] {indicator_id} {datetime.now(timezone.utc).strftime('%Y%m%d')}"


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


def _pdf_ocr_body(indicator_id: str, metadata: dict[str, Any], run_id: str) -> str:
    lines = [f"KRA IV QA run {run_id}", f"Indicator: {indicator_id}"]
    for key, val in metadata.items():
        lines.append(f"{key}: {val}")
    lines.extend(
        [
            "Organization: QA Professional Society",
            "Degree: Master of Science",
            "University: QA State University",
            "Training hours: 8 hours",
            "Award: QA Excellence Award",
            "Employer: QA Prior Employer",
            "Position: Faculty Member",
            "Experience: 2 years",
            "Period: 2018-01-01 to 2020-01-01",
        ]
    )
    return "\n".join(lines)


def _fill_evidence_slots(
    faculty_user,
    primary,
    *,
    indicator_id: str,
    criterion_id: str,
    body: str,
    run_id: str,
) -> None:
    from documents.kra4_evidence.bundle import bundle_from_document
    from documents.kra4_evidence.slots import primary_evidence_slot, required_slots
    from documents.service import create_upload
    from extensions import db

    primary_slot = primary_evidence_slot(indicator_id=indicator_id)
    slots = list(required_slots(indicator_id=indicator_id))
    for slot in slots:
        db.session.refresh(primary)
        bundle = bundle_from_document(primary)
        entry = (bundle or {}).get("checklist", {}).get(slot) or {}
        if entry.get("documentId"):
            continue
        if slot == primary_slot:
            continue
        slot_pdf = _make_pdf(body + f"\nEvidence slot: {slot}\n")
        fs = FileStorage(
            stream=io.BytesIO(slot_pdf),
            filename=f"kra4-{slot}-{run_id}.pdf",
            content_type="application/pdf",
        )
        create_upload(
            faculty_user,
            file=fs,
            title=f"{_qa_title(indicator_id)} — {slot}",
            kra_id="kra4",
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
    mode: str = "approve",
) -> None:
    from documents.kra4_evidence.bundle import bundle_from_document
    from documents.kra4_evidence.service import (
        bundle_api_payload,
        kra4_summary_for_faculty,
        list_faculty_accomplishments,
        reviewer_update_kra4,
        update_bundle_metadata,
    )
    from documents.kra4_evidence.ocr_extraction import OCR_EXTRACTION_KEY, ensure_kra4_ocr_extraction
    from documents.kra4_evidence.slots import required_slots
    from documents.service import create_upload
    from extensions import db
    from kra_configuration.kra4_indicator_registry import metadata_field_ids

    row: dict[str, Any] = {
        "indicatorId": indicator_id,
        "criterionId": criterion_id,
        "mode": mode,
        "checks": {},
        "status": "FAIL",
    }
    report["indicators"][f"{indicator_id}:{mode}"] = row

    try:
        body = _pdf_ocr_body(indicator_id, metadata, run_id)
        pdf = _make_pdf(body)
        fs = FileStorage(
            stream=io.BytesIO(pdf),
            filename=f"kra4-qa-{indicator_id}-{run_id}.pdf",
            content_type="application/pdf",
        )
        primary = create_upload(
            faculty_user,
            file=fs,
            title=_qa_title(indicator_id) + (f" ({mode})" if mode != "approve" else ""),
            kra_id="kra4",
            criterion_id=criterion_id,
            indicator_id=indicator_id,
        )
        db.session.commit()
        db.session.refresh(primary)
        row["documentId"] = primary.public_id
        row["checks"]["kra_id"] = primary.kra_id == "kra4"
        row["checks"]["criterion_match"] = primary.criterion_id == criterion_id

        bundle = bundle_from_document(primary)
        row["checks"]["bundle_initialized"] = isinstance(bundle, dict) and bundle.get("indicatorId") == indicator_id

        _fill_evidence_slots(
            faculty_user,
            primary,
            indicator_id=indicator_id,
            criterion_id=criterion_id,
            body=body,
            run_id=run_id,
        )
        primary.ocr_text = body
        primary.ocr_status = "completed"
        ensure_kra4_ocr_extraction(primary)
        db.session.commit()

        extraction = (primary.extracted_info or {}).get(OCR_EXTRACTION_KEY)
        row["checks"]["ocr_extraction"] = isinstance(extraction, dict) and isinstance(
            extraction.get("hints"), dict
        )

        field_ids = metadata_field_ids(indicator_id)
        payload_meta = {**metadata, "confirmMetadata": True}
        payload_meta["metadataConfirmed"] = {k: True for k in field_ids}
        if metadata.get("activityTitle"):
            payload_meta["outputTitle"] = metadata["activityTitle"]
        _, val_draft = update_bundle_metadata(faculty_user, primary.public_id, payload_meta)
        row["checks"]["draft_metadata"] = val_draft.get("readyForSubmission") is True
        if not row["checks"]["draft_metadata"]:
            row["draftBlockers"] = val_draft.get("submissionBlockers")

        _, val_submit = update_bundle_metadata(
            faculty_user,
            primary.public_id,
            {"submitAccomplishment": True, **payload_meta},
        )
        row["checks"]["submit_ready"] = val_submit.get("readyForSubmission") is True
        db.session.refresh(primary)
        row["checks"]["submitted_status"] = primary.status == "pending_review"

        slots = list(required_slots(indicator_id=indicator_id))
        for slot in slots:
            entry = (bundle_from_document(primary) or {}).get("checklist", {}).get(slot) or {}
            if not entry.get("documentId"):
                continue
            reviewer_update_kra4(
                reviewer_user,
                primary.public_id,
                slot_id=slot,
                status="verified",
                reviewer_note="KRA4 QA verify",
            )
        db.session.commit()

        api = bundle_api_payload(primary)
        scoring = api.get("scoring") or {}
        est = scoring.get("estimatedPoints")
        row["estimatedPoints"] = est
        row["officialBasePoints"] = scoring.get("officialBasePoints")
        if indicator_id.startswith("kra4-d-"):
            row["checks"]["experience_formula"] = est is not None and float(est) > 0
        else:
            row["checks"]["estimated_points_present"] = est is not None and float(est) > 0

        assessed = scoring.get("reviewerEligiblePoints") or scoring.get("eligiblePoints") or est
        reviewer_update_kra4(
            reviewer_user,
            primary.public_id,
            slot_id=None,
            status=None,
            remarks=f"[KRA4-QA] save assessment {indicator_id}",
            assessed_points=assessed,
        )
        db.session.commit()
        row["checks"]["save_assessment_pending"] = True

        if mode == "reject":
            reviewer_update_kra4(
                reviewer_user,
                primary.public_id,
                slot_id=None,
                status=None,
                review_status="rejected",
                remarks=f"[KRA4-QA] rejection {indicator_id}",
            )
            db.session.commit()
            bundle_final = bundle_from_document(primary) or {}
            row["checks"]["rejected_persisted"] = bundle_final.get("reviewStatus") == "rejected"
        elif mode == "approve":
            reviewer_update_kra4(
                reviewer_user,
                primary.public_id,
                slot_id=None,
                status=None,
                review_status="approved",
                remarks=f"[KRA4-QA] approval {indicator_id}",
                assessed_points=assessed,
            )
            db.session.commit()
            bundle_final = bundle_from_document(primary) or {}
            ra = bundle_final.get("reviewerAssessment") or {}
            row["checks"]["approved_persisted"] = bundle_final.get("reviewStatus") == "approved"
            row["approvedPoints"] = ra.get("assessedPoints") or scoring.get("approvedPoints")

        summary = kra4_summary_for_faculty(profile.id, criterion_id=criterion_id)
        row["checks"]["criterion_summary"] = isinstance(summary, dict)
        row["criterionValidatedPoints"] = summary.get("validatedPoints")

        submitted_rows = list_faculty_accomplishments(
            profile.id, criterion_id=criterion_id, submitted_only=True
        )
        row["checks"]["reviewer_list_visible"] = any(
            r.get("documentId") == primary.public_id for r in submitted_rows
        )

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
        kra4 = next((r for r in (sim.get("kraScores") or []) if (r.get("kraId") or r.get("id")) == "kra4"), None)
        report["rankSimulation"] = {
            "status": "PASS" if kra4 else "FAIL",
            "estimatedPoints": (kra4 or {}).get("estimatedPoints"),
            "validatedPoints": (kra4 or {}).get("validatedPoints"),
            "maxPoints": (kra4 or {}).get("maxPoints"),
        }
        if kra4 and kra4.get("validatedPoints") is not None:
            report["rankSimulation"]["cap_ok"] = float(kra4["validatedPoints"]) <= 100.0
    except Exception as exc:
        report["rankSimulation"] = {"status": "FAIL", "error": str(exc)}


def main() -> int:
    _require_flag()
    from scripts.qa_db_guard import require_qa_test_database, qa_faculty_user, qa_reviewer_for_profile

    db_name = require_qa_test_database()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report: dict[str, Any] = {
        "runId": run_id,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "indicators": {},
        "environment": {"database": db_name, "tag": "[KRA4-QA]"},
    }

    from config import Config
    from factory import create_app

    from scripts.kra4_qa_metadata import all_qa_indicators, qa_metadata_for

    app = create_app(Config)
    with app.app_context():
        faculty_user, profile = qa_faculty_user()
        reviewer = qa_reviewer_for_profile(profile)
        report["facultyEmail"] = faculty_user.email
        report["reviewerEmail"] = reviewer.email
        report["facultyPublicId"] = profile.public_id

        reject_only = {
            "kra4-a-member",
            "kra4-b-part-local",
            "kra4-c-inst",
            "kra4-d-faculty",
        }

        for indicator_id, criterion_id, _row in all_qa_indicators():
            meta = qa_metadata_for(indicator_id, run_id=run_id)
            run_indicator(
                faculty_user=faculty_user,
                reviewer_user=reviewer,
                profile=profile,
                indicator_id=indicator_id,
                criterion_id=criterion_id,
                metadata=meta,
                run_id=run_id,
                report=report,
                mode="approve",
            )

        for indicator_id in reject_only:
            row = next((r for r in all_qa_indicators() if r[0] == indicator_id), None)
            if not row:
                continue
            iid, cid, _ = row
            meta = qa_metadata_for(iid, run_id=run_id)
            run_indicator(
                faculty_user=faculty_user,
                reviewer_user=reviewer,
                profile=profile,
                indicator_id=iid,
                criterion_id=cid,
                metadata=meta,
                run_id=f"{run_id}-rej",
                report=report,
                mode="reject",
            )

        run_rank_sim(profile, report)
        report["finishedAt"] = datetime.now(timezone.utc).isoformat()
        passed = [r for r in report["indicators"].values() if r.get("status") == "PASS"]
        report["overallStatus"] = "PASS" if len(passed) == len(report["indicators"]) else "FAIL"
        report["passCount"] = len(passed)
        report["totalCount"] = len(report["indicators"])

        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote {OUT_JSON} overall={report['overallStatus']} ({report['passCount']}/{report['totalCount']})")
        return 0 if report["overallStatus"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
