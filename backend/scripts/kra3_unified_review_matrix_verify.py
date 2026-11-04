"""API-level matrix check: one pending + one approved KRA III doc per criterion (A–D)."""

from __future__ import annotations

import json
import os
import sys

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from app import create_app  # noqa: E402
from models import Document, User  # noqa: E402
from documents.kra3_evidence.service import bundle_api_payload, reviewer_update_kra3  # noqa: E402


def _pick_docs(session, criterion_id: str, limit: int = 40):
    q = (
        session.query(Document)
        .filter(Document.criterion_id == criterion_id)
        .filter(Document.title.ilike("%KRA3-QA%"))
        .order_by(Document.updated_at.desc())
        .limit(limit)
    )
    return list(q)


def _review_state(doc: Document, payload: dict) -> str:
    bundle = payload.get("bundle") or {}
    ra = bundle.get("reviewerAssessment") or {}
    status = (
        (ra.get("reviewStatus") or bundle.get("reviewStatus") or "").strip().lower()
    )
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
        "approvalBlockerCount": len(v.get("approvalBlockers") or []),
        "reviewerBlockerCount": len(v.get("reviewerBlockers") or []),
    }


def main() -> int:
    app = create_app()
    criteria = ["kra3-a", "kra3-b", "kra3-c", "kra3-d"]
    rows = []
    with app.app_context():
        from extensions import db

        reviewer = User.query.filter(User.email == "jaso.jary@gmail.com").first()
        viewer = reviewer
        for crit in criteria:
            docs = _pick_docs(db.session, crit)
            pending = approved = None
            for doc in docs:
                payload = bundle_api_payload(doc, viewer_user=viewer)
                st = _review_state(doc, payload)
                if st == "pending" and not pending:
                    pending = (doc, payload)
                if st == "approved" and not approved:
                    approved = (doc, payload)
                if pending and approved:
                    break
            pending_row = None
            if pending:
                doc, payload = pending
                draft_note = "[KRA3-QA unified verify] save assessment draft"
                scoring = payload.get("scoring") or {}
                assessed = scoring.get("reviewerEligiblePoints")
                if assessed is None:
                    assessed = scoring.get("maxAssessedPoints")
                if assessed is None:
                    assessed = scoring.get("eligiblePoints")
                if assessed is None:
                    assessed = scoring.get("systemCalculatedPoints")
                if scoring.get("numericScoringBlocked"):
                    assessed = None
                save_ok = True
                save_err = None
                try:
                    reviewer_update_kra3(
                        viewer,
                        doc.public_id,
                        slot_id=None,
                        status=None,
                        remarks=draft_note,
                        assessed_points=assessed,
                        score_adjustment_reason=None,
                    )
                    db.session.commit()
                    fresh = bundle_api_payload(doc, viewer_user=viewer)
                    bundle = fresh.get("bundle") or {}
                    ra = bundle.get("reviewerAssessment") or {}
                    save_ok = (bundle.get("reviewerRemarks") or ra.get("remarks") or "").strip() == draft_note
                except Exception as exc:  # noqa: BLE001
                    save_ok = False
                    save_err = str(exc)
                    db.session.rollback()
                pending_row = {
                    "id": doc.public_id,
                    "indicator": doc.indicator_id,
                    "flags": _ui_flags(payload),
                    "saveAssessmentDraftOk": save_ok,
                    "saveAssessmentError": save_err,
                }
            approved_row = None
            if approved:
                adoc, apayload = approved
                caps = apayload.get("reassessmentCapabilities") or {}
                approved_save_ok = True
                approved_save_err = None
                approved_before = (
                    (apayload.get("scoring") or {}).get("approvedPoints")
                )
                try:
                    reviewer_update_kra3(
                        viewer,
                        adoc.public_id,
                        slot_id=None,
                        status=None,
                        remarks="[KRA3-QA] approved revision save verify",
                        assessed_points=approved_before,
                        score_adjustment_reason=None,
                    )
                    db.session.commit()
                    fresh_a = bundle_api_payload(adoc, viewer_user=viewer)
                    sc = fresh_a.get("scoring") or {}
                    approved_save_ok = sc.get("approvedPoints") == approved_before
                except Exception as exc:  # noqa: BLE001
                    approved_save_ok = False
                    approved_save_err = str(exc)
                    db.session.rollback()
                approved_row = {
                    "id": adoc.public_id,
                    "indicator": adoc.indicator_id,
                    "flags": _ui_flags(apayload),
                    "canRequestReassessment": caps.get("canRequestReassessment"),
                    "saveAssessmentOnApprovedOk": approved_save_ok,
                    "saveAssessmentOnApprovedError": approved_save_err,
                }
            rows.append(
                {
                    "criterion": crit,
                    "pending": pending_row,
                    "approved": approved_row,
                }
            )
    print(json.dumps(rows, indent=2))
    missing = [r["criterion"] for r in rows if not r["pending"] or not r["approved"]]
    if missing:
        print("\nWARN: missing pending or approved QA doc for:", ", ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
