"""Verify KRA IV rank simulation aggregates approved QA docs on facultylink_qa only."""

from __future__ import annotations

import json
import os
import sys

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


def main() -> int:
    if os.environ.get("FACULTYLINK_KRA4_QA_RUN", "").strip() != "1":
        print("Set FACULTYLINK_KRA4_QA_RUN=1", file=sys.stderr)
        return 2
    from scripts.qa_db_guard import require_qa_test_database, qa_faculty_user

    require_qa_test_database()
    from config import Config
    from factory import create_app
    from documents.kra4_evidence.service import kra4_summary_for_faculty
    from faculty.rank_simulation_engine import compute_rank_simulation
    from kra_configuration.kra4_annex import CRITERION_A_ID, CRITERION_B_ID, CRITERION_C_ID, CRITERION_D_ID
    from models import Document

    app = create_app(Config)
    report: dict = {"checks": {}, "status": "FAIL"}
    with app.app_context():
        _, profile = qa_faculty_user()
        approved_qa = (
            Document.query.filter_by(faculty_profile_id=profile.id, criterion_id=CRITERION_A_ID)
            .filter(Document.title.ilike("%[KRA4-QA]%"))
            .filter(Document.deleted_at.is_(None))
            .all()
        )
        summaries = {}
        for cid in (CRITERION_A_ID, CRITERION_B_ID, CRITERION_C_ID, CRITERION_D_ID):
            summaries[cid] = kra4_summary_for_faculty(profile.id, criterion_id=cid)

        sim = compute_rank_simulation(profile)
        kra4 = next((r for r in (sim.get("kraScores") or []) if (r.get("kraId") or r.get("id")) == "kra4"), {})

        validated = float(kra4.get("validatedPoints") or 0)
        report["kra4Simulation"] = kra4
        report["criterionSummaries"] = {
            k: {"validatedPoints": v.get("validatedPoints"), "maxPoints": v.get("maxPoints")}
            for k, v in summaries.items()
        }
        report["checks"]["validated_nonzero"] = validated > 0
        report["checks"]["cap_ok"] = validated <= 100.0
        report["checks"]["qa_db_counts_qa"] = validated > 0 or len(approved_qa) == 0
        pending = Document.query.filter_by(faculty_profile_id=profile.id, status="pending_review").count()
        report["pendingDocCount"] = pending
        failed = [k for k, v in report["checks"].items() if not v]
        report["status"] = "PASS" if not failed else "FAIL"
        if failed:
            report["failedChecks"] = failed

    out = os.path.join(BACKEND, "..", "docs", "KRA4_RANK_SIM_QA.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
