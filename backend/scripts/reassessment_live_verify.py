"""Live reassessment workflow against the running app database (no PostgreSQL reset)."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TARGET_DOC = os.environ.get("REASSESSMENT_QA_DOC", "doc_af42ab28e9f7")
REASON = (
    "Hourly training approval used legacy flat points; correcting to published hourly eligible amount."
)


def main() -> int:
    from app import create_app
    from documents.kra3_evidence.bundle import bundle_from_document
    from documents.kra3_evidence.service import bundle_api_payload, reviewer_update_kra3
    from models import Document, User

    app = create_app()
    results: dict = {"docId": TARGET_DOC, "steps": []}

    def step(name: str, ok: bool, detail: dict | None = None) -> None:
        results["steps"].append({"step": name, "ok": ok, "detail": detail or {}})

    with app.app_context():
        doc = Document.query.filter_by(public_id=TARGET_DOC).first()
        if not doc:
            step("load_document", False, {"error": "not_found"})
            print(json.dumps(results, indent=2))
            return 1

        reviewer = User.query.filter_by(role="reviewer", is_active=True).first()
        admin = User.query.filter_by(role="administrator", is_active=True).first()
        if not reviewer or not admin:
            step("load_users", False)
            print(json.dumps(results, indent=2))
            return 1

        payload = bundle_api_payload(doc, viewer_user=reviewer)
        caps = payload.get("reassessmentCapabilities") or {}
        step(
            "reviewer_capabilities",
            bool(caps.get("canRequestReassessment")),
            caps,
        )

        bundle = bundle_from_document(doc)
        session = (bundle or {}).get("reassessmentSession") if isinstance(bundle, dict) else None
        if isinstance(session, dict) and session.get("active"):
            reviewer_update_kra3(
                reviewer,
                TARGET_DOC,
                slot_id=None,
                status=None,
                reassessment_action="cancel",
            )
            doc = Document.query.filter_by(public_id=TARGET_DOC).first()

        try:
            reviewer_update_kra3(
                reviewer,
                TARGET_DOC,
                slot_id=None,
                status=None,
                reassessment_action="open",
                reassessment_reason=REASON,
            )
            step("open_reassessment", True, {})
        except Exception as exc:
            step("open_reassessment", False, {"error": str(exc)})

        fresh = Document.query.filter_by(public_id=TARGET_DOC).first()
        b2 = bundle_from_document(fresh)
        ra_before = (b2.get("reviewerAssessment") or {}).get("assessedPoints")
        system_now = (bundle_api_payload(fresh, viewer_user=reviewer).get("scoring") or {}).get(
            "systemCalculatedPoints"
        )

        adjust_reason = (
            "Legacy approval stored flat base without hourly multiplier; "
            "correcting to published hourly eligible amount."
        )
        try:
            from documents.kra3_evidence.reviewer_assessment import propose_assessed_points
            from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

            score_settings, _ = resolve_settings_for_faculty_simulation()
            # Use system eligible when valid; otherwise keep official cap (legacy 4 vs 2 often means hourly > per-output max).
            try:
                target_pts, _ = propose_assessed_points(
                    b2,
                    assessed_points=system_now,
                    score_adjustment_reason=adjust_reason,
                    indicator_id=fresh.indicator_id,
                    settings=score_settings,
                )
            except ValueError:
                target_pts, _ = propose_assessed_points(
                    b2,
                    assessed_points=ra_before,
                    score_adjustment_reason=adjust_reason,
                    indicator_id=fresh.indicator_id,
                    settings=score_settings,
                )
            reviewer_update_kra3(
                reviewer,
                TARGET_DOC,
                slot_id=None,
                status=None,
                reassessment_action="save_draft",
                assessed_points=target_pts,
                remarks="Corrected hourly training points after reassessment audit.",
                score_adjustment_reason=adjust_reason,
            )
            step("save_draft", True, {"targetPoints": target_pts, "systemEligible": system_now})
        except Exception as exc:
            step("save_draft", False, {"error": str(exc)})

        from documents.kra3_evidence.service import Kra3EvidenceError

        try:
            reviewer_update_kra3(
                reviewer,
                TARGET_DOC,
                slot_id=None,
                status=None,
                reassessment_action="finalize",
                confirm_reassessment=True,
                remarks="Corrected hourly training points after reassessment audit.",
            )
            step("reviewer_finalize_blocked", False, {"error": "unexpected_success"})
        except Kra3EvidenceError as exc:
            step(
                "reviewer_finalize_blocked",
                exc.code == "reassessment_finalize_requires_administrator",
                {"code": exc.code},
            )
        except Exception as exc:
            step("reviewer_finalize_blocked", False, {"error": str(exc)})

        try:
            reviewer_update_kra3(
                admin,
                TARGET_DOC,
                slot_id=None,
                status=None,
                reassessment_action="finalize",
                confirm_reassessment=True,
                remarks="Administrator finalized corrected hourly training points.",
                score_adjustment_reason=adjust_reason,
                actor_is_administrator=True,
            )
            final_doc = Document.query.filter_by(public_id=TARGET_DOC).first()
            b3 = bundle_from_document(final_doc)
            ra_after = (b3.get("reviewerAssessment") or {}).get("assessedPoints")
            hist = b3.get("reassessmentHistory") or []
            last = hist[-1] if hist else {}
            step(
                "admin_finalize",
                ra_after is not None and len(hist) >= 1 and last.get("originalApprovedPoints") == ra_before,
                {
                    "pointsBefore": ra_before,
                    "pointsAfter": ra_after,
                    "historyEntries": len(hist),
                    "auditOriginalPoints": last.get("originalApprovedPoints"),
                },
            )
        except Exception as exc:
            step("admin_finalize", False, {"error": str(exc)})

    results["pass"] = all(s["ok"] for s in results["steps"])
    print(json.dumps(results, indent=2))
    return 0 if results["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
