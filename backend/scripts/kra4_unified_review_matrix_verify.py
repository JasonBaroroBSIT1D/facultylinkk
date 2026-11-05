"""API matrix: pending / approved / rejected KRA IV docs per criterion + Save Assessment checks."""

from __future__ import annotations

import json
import os
import sys

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


def _pick_docs(session, criterion_id: str, *, review_status: str | None = None, limit: int = 60):
    from models import Document

    q = (
        session.query(Document)
        .filter(Document.criterion_id == criterion_id)
        .filter(Document.title.ilike("%[KRA4-QA]%"))
        .order_by(Document.updated_at.desc())
        .limit(limit)
    )
    return list(q)


def _review_state(doc, payload: dict) -> str:
    bundle = payload.get("bundle") or {}
    ra = bundle.get("reviewerAssessment") or {}
    status = (ra.get("reviewStatus") or bundle.get("reviewStatus") or "").strip().lower()
    if status == "approved":
        return "approved"
    if status == "rejected":
        return "rejected"
    if bundle.get("submittedForReviewAt"):
        return "pending"
    return "draft"


def _ui_flags(payload: dict) -> dict:
    scoring = payload.get("scoring") or {}
    v = payload.get("validation") or {}
    return {
        "allowsPointAdjustment": scoring.get("allowsPointAdjustment"),
        "numericScoringBlocked": scoring.get("numericScoringBlocked"),
        "systemCalculatedPoints": scoring.get("systemCalculatedPoints"),
        "eligiblePoints": scoring.get("eligiblePoints"),
        "reviewerAssessedPoints": scoring.get("reviewerAssessedPoints"),
        "approvedPoints": scoring.get("approvedPoints"),
        "approvalBlockerCount": len(v.get("approvalBlockers") or []),
        "reviewerBlockerCount": len(v.get("reviewerBlockers") or []),
    }


def _assessed_for_save(scoring: dict) -> float | None:
    assessed = scoring.get("reviewerEligiblePoints")
    if assessed is None:
        assessed = scoring.get("maxAssessedPoints")
    if assessed is None:
        assessed = scoring.get("eligiblePoints")
    if assessed is None:
        assessed = scoring.get("systemCalculatedPoints")
    if scoring.get("numericScoringBlocked"):
        return None
    return assessed


def _save_assessment(reviewer, doc, *, note: str, assessed) -> tuple[bool, str | None, dict]:
    from documents.kra4_evidence.service import reviewer_update_kra4, bundle_api_payload
    from extensions import db

    try:
        reviewer_update_kra4(
            reviewer,
            doc.public_id,
            slot_id=None,
            status=None,
            remarks=note,
            assessed_points=assessed,
            score_adjustment_reason=None,
        )
        db.session.commit()
        db.session.refresh(doc)
        fresh = bundle_api_payload(doc, viewer_user=reviewer)
        bundle = fresh.get("bundle") or {}
        ra = bundle.get("reviewerAssessment") or {}
        remarks = (
            bundle.get("reviewerRemarks")
            or ra.get("draftRemarks")
            or ra.get("remarks")
            or ""
        ).strip()
        ok = remarks == note.strip()
        return ok, None, fresh
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return False, str(exc), {}


def main() -> int:
    if os.environ.get("FACULTYLINK_KRA4_QA_RUN", "").strip() != "1":
        print("Set FACULTYLINK_KRA4_QA_RUN=1 to run KRA IV matrix verify.", file=sys.stderr)
        return 2

    from scripts.qa_db_guard import require_qa_test_database, qa_faculty_user, qa_reviewer_for_profile

    db_name = require_qa_test_database()
    from config import Config
    from factory import create_app

    app = create_app(Config)
    criteria = ["kra4-a", "kra4-b", "kra4-c", "kra4-d"]
    rows = []
    with app.app_context():
        from documents.kra4_evidence.service import bundle_api_payload
        from extensions import db

        _, profile = qa_faculty_user()
        reviewer = qa_reviewer_for_profile(profile)

        for crit in criteria:
            docs = _pick_docs(db.session, crit)
            buckets: dict[str, tuple] = {}
            for doc in docs:
                payload = bundle_api_payload(doc, viewer_user=reviewer)
                st = _review_state(doc, payload)
                if st in ("pending", "approved", "rejected") and st not in buckets:
                    buckets[st] = (doc, payload)

            row: dict = {"criterion": crit, "database": db_name}
            for status in ("pending", "approved", "rejected"):
                entry = buckets.get(status)
                if not entry:
                    row[status] = None
                    continue
                doc, payload = entry
                scoring = payload.get("scoring") or {}
                note = f"[KRA4-QA matrix] save on {status}"
                ok, err, fresh = _save_assessment(
                    reviewer, doc, note=note, assessed=_assessed_for_save(scoring)
                )
                approved_before = scoring.get("approvedPoints")
                approved_after = (fresh.get("scoring") or {}).get("approvedPoints")
                row[status] = {
                    "documentId": doc.public_id,
                    "indicatorId": doc.indicator_id,
                    "flags": _ui_flags(payload),
                    "saveAssessmentOk": ok,
                    "saveAssessmentError": err,
                    "approvedPointsUnchanged": status != "approved"
                    or approved_before == approved_after,
                }
            rows.append(row)

    print(json.dumps(rows, indent=2))
    missing = []
    for r in rows:
        for st in ("pending", "approved", "rejected"):
            if not r.get(st):
                missing.append(f"{r['criterion']}:{st}")
            elif not r[st].get("saveAssessmentOk"):
                missing.append(f"{r['criterion']}:{st}:save")
            elif st == "approved" and not r[st].get("approvedPointsUnchanged"):
                missing.append(f"{r['criterion']}:approved:points_changed")
    if missing:
        print("\nFAIL:", ", ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
