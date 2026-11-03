"""
Read-only Criterion B simulation adapter staging verification.

Does NOT insert/update/delete rows, send email, or enable production code paths.
Staging adapter is enabled in-process only (or via env on the staging host).

Usage (staging DB recommended):
  set FACULTYLINK_STAGING_VERIFY=1
  set DATABASE_URL=postgresql://.../facultylink_staging
  set CRITERION_B_SIMULATION_ADAPTER_ENABLED=1
  cd backend && python scripts/criterion_b_staging_activation_verify.py

Optional read-only check against a local facultylink *copy* (not recommended for production hosts):
  set FACULTYLINK_STAGING_VERIFY=1
  set FACULTYLINK_STAGING_READONLY_FACULTYLINK=1
  cd backend && python scripts/criterion_b_staging_activation_verify.py

Report: backend/backups/criterion_b_staging_activation_report.json
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import Config
from factory import create_app

TAG = "CRITERION-B-STAGING-VERIFY"
JASON_NAME_HINT = "Jason Baroro"
TEXTBOOK_TITLE_HINT = "Introduction to Data Literacy"


def _db_name() -> str:
    url = Config.database_url().replace("postgresql+psycopg", "postgresql")
    return urlparse(url).path.lstrip("/").split("?")[0]


def _staging_allowed(db_name: str) -> tuple[bool, str]:
    if os.environ.get("FACULTYLINK_STAGING_VERIFY") != "1":
        return False, "Set FACULTYLINK_STAGING_VERIFY=1 to run this script."
    if "staging" in db_name.lower():
        return True, "staging database name"
    if db_name == "facultylink" and os.environ.get("FACULTYLINK_STAGING_READONLY_FACULTYLINK") == "1":
        return True, "read-only facultylink (local copy only — not for production hosts)"
    return False, (
        f"Refusing database {db_name!r}. Use a staging DB (name contains 'staging') "
        "or FACULTYLINK_STAGING_READONLY_FACULTYLINK=1 for read-only local copy."
    )


def _enable_adapter_in_process() -> None:
    import documents.scoring.criterion_b_simulation_adapter as adapter_mod

    adapter_mod.CRITERION_B_SIMULATION_ADAPTER_ENABLED = True


def _adapter_flag() -> bool:
    from documents.scoring.criterion_b_simulation_adapter import CRITERION_B_SIMULATION_ADAPTER_ENABLED

    return CRITERION_B_SIMULATION_ADAPTER_ENABLED


def _find_jason_primary_docs(session) -> list[Any]:
    from models import Document, FacultyProfile, User

    from documents.criterion_b_evidence.bundle import is_supporting_evidence_document

    users = User.query.filter(User.full_name.ilike(f"%{JASON_NAME_HINT}%")).all()
    profiles = []
    for user in users:
        profile = FacultyProfile.query.filter_by(user_id=user.id).first()
        if profile:
            profiles.append((user, profile))
    if not profiles:
        return []

    docs: list[Any] = []
    for user, profile in profiles:
        rows = (
            Document.query.filter_by(
                faculty_profile_id=profile.id,
                criterion_id="kra1-b",
            )
            .filter(Document.deleted_at.is_(None))
            .all()
        )
        for doc in rows:
            if is_supporting_evidence_document(doc):
                continue
            title = (doc.title or "").lower()
            if TEXTBOOK_TITLE_HINT.lower() in title or "data literacy" in title:
                docs.append({"user": user, "profile": profile, "document": doc})
    if not docs and profiles:
        _, profile = profiles[0]
        for doc in Document.query.filter_by(faculty_profile_id=profile.id, criterion_id="kra1-b").filter(
            Document.deleted_at.is_(None)
        ):
            if not is_supporting_evidence_document(doc):
                docs.append({"user": profiles[0][0], "profile": profile, "document": doc})
    return docs


def _accomplishment_snapshot(doc) -> dict[str, Any]:
    from documents.criterion_b_evidence.scoring_context import build_criterion_b_scoring_context
    from documents.criterion_b_evidence.service import bundle_api_payload

    payload = bundle_api_payload(doc)
    bundle = payload.get("bundle") or {}
    validation = payload.get("validation") or {}
    scoring = build_criterion_b_scoring_context(doc, bundle, validation)
    display = scoring.get("displayScore") or {}
    current = scoring.get("currentScore") or display
    return {
        "documentId": doc.public_id,
        "title": doc.title,
        "status": doc.status,
        "indicatorId": doc.indicator_id,
        "validationStatus": validation.get("validationStatus"),
        "readyForScoring": validation.get("readyForScoring"),
        "systemEstimatePoints": scoring.get("systemEstimatePoints"),
        "guidelineCompliantVerifiedPoints": scoring.get("guidelineCompliantVerifiedPoints"),
        "reviewerProposedPoints": (scoring.get("reviewerProposedAssessment") or {}).get("points"),
        "currentScoreLabel": current.get("label"),
        "currentScorePoints": current.get("points"),
        "currentScoreSource": current.get("source"),
    }


def _kra1_sim_block(profile, *, adapter_on: bool) -> dict[str, Any]:
    import documents.scoring.criterion_b_simulation_adapter as adapter_mod
    from faculty.kra_document_aggregate import aggregate_criterion_documents
    from faculty.rank_simulation_engine import compute_rank_simulation

    prev = adapter_mod.CRITERION_B_SIMULATION_ADAPTER_ENABLED
    adapter_mod.CRITERION_B_SIMULATION_ADAPTER_ENABLED = adapter_on
    try:
        b_block = aggregate_criterion_documents(profile, "kra1", "kra1-b")
        sim = compute_rank_simulation(profile)
    finally:
        adapter_mod.CRITERION_B_SIMULATION_ADAPTER_ENABLED = prev

    kra1 = next((k for k in sim.get("kraScores") or [] if k.get("kraId") == "kra1"), {})
    crit_b = next(
        (c for c in (kra1.get("criteriaScores") or []) if c.get("criterionId") == "kra1-b"),
        {},
    )
    return {
        "adapterOn": adapter_on,
        "criterionBEstimatedPoints": b_block.get("estimatedPoints"),
        "criterionBPreviewPoints": b_block.get("accomplishmentPreviewPoints"),
        "criterionBIntegrationState": b_block.get("integrationState"),
        "criterionBScoringSource": b_block.get("scoringSource"),
        "kra1EstimatedPoints": kra1.get("estimatedPoints"),
        "kra1CriteriaBPoints": crit_b.get("estimatedPoints"),
        "simulationEstimatedTotal": sim.get("estimatedTotalKraPoints"),
        "simulationAdapterEnabledField": crit_b.get("simulationAdapterEnabled"),
    }


def _write_report(report: dict) -> Path:
    out_dir = ROOT / "backups"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"criterion_b_staging_activation_report_{stamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def main() -> int:
    report: dict[str, Any] = {
        "tag": TAG,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "checks": [],
        "defects": [],
        "warnings": [],
        "goRecommendation": None,
    }

    db_name = _db_name()
    report["database"] = db_name
    report["adapterEnv"] = os.environ.get("CRITERION_B_SIMULATION_ADAPTER_ENABLED")
    report["adapterAtImport"] = _adapter_flag()

    ok, reason = _staging_allowed(db_name)
    if not ok:
        report["defects"].append(reason)
        path = _write_report(report)
        print(f"ABORT: {reason}\nReport: {path}")
        return 2

    report["stagingMode"] = reason
    _enable_adapter_in_process()
    report["adapterInProcess"] = _adapter_flag()

    app = create_app(Config)
    with app.app_context():
        from documents.criterion_b_evidence.bundle import is_supporting_evidence_document
        from faculty.kra_document_aggregate import aggregate_criterion_documents_from_list
        from models import Document, FacultyProfile

        hits = _find_jason_primary_docs(None)
        if not hits:
            report["defects"].append(f"No Criterion B primary found for {JASON_NAME_HINT!r}.")
        else:
            for hit in hits:
                doc = hit["document"]
                profile = hit["profile"]
                snap = _accomplishment_snapshot(doc)
                report.setdefault("jasonAccomplishments", []).append(snap)

                before = _kra1_sim_block(profile, adapter_on=False)
                after = _kra1_sim_block(profile, adapter_on=True)
                report.setdefault("scoreComparison", []).append(
                    {
                        "documentId": doc.public_id,
                        "beforeAdapterOff": before,
                        "afterAdapterOn": after,
                    }
                )

                checks = []
                if snap.get("currentScoreSource") == "reviewer_assessment":
                    pts = snap.get("currentScorePoints")
                    if pts is not None:
                        checks.append(("current_score_reviewer_assessed", float(pts)))
                if after.get("criterionBEstimatedPoints") is not None:
                    checks.append(
                        (
                            "criterion_b_aggregated",
                            float(after["criterionBEstimatedPoints"]),
                        )
                    )
                if (
                    snap.get("currentScorePoints") is not None
                    and after.get("criterionBEstimatedPoints") is not None
                    and abs(
                        float(snap["currentScorePoints"])
                        - float(after["criterionBEstimatedPoints"])
                    )
                    > 0.01
                ):
                    report["defects"].append(
                        f"Aggregate {after['criterionBEstimatedPoints']} != current "
                        f"{snap['currentScorePoints']} for {doc.public_id}"
                    )
                elif snap.get("currentScorePoints") is not None and after.get("criterionBEstimatedPoints") is not None:
                    report["checks"].append(
                        {
                            "name": "current_score_matches_criterion_b_aggregate",
                            "documentId": doc.public_id,
                            "points": float(snap["currentScorePoints"]),
                        }
                    )

                if snap.get("systemEstimatePoints") is not None:
                    report["checks"].append(
                        {
                            "name": "audit_system_estimate_preserved",
                            "documentId": doc.public_id,
                            "systemEstimatePoints": snap["systemEstimatePoints"],
                        }
                    )

                report["checks"].append({"name": "jason_scenario_row", "documentId": doc.public_id, "checks": checks})

        # Supporting docs must not aggregate as primaries
        if hits:
            profile = hits[0]["profile"]
            all_b = (
                Document.query.filter_by(faculty_profile_id=profile.id, criterion_id="kra1-b")
                .filter(Document.deleted_at.is_(None))
                .all()
            )
            supporting = [d for d in all_b if is_supporting_evidence_document(d)]
            primaries = [d for d in all_b if not is_supporting_evidence_document(d)]
            import documents.scoring.criterion_b_simulation_adapter as adapter_mod
            from kra_configuration.published_limits import published_settings_blob

            adapter_mod.CRITERION_B_SIMULATION_ADAPTER_ENABLED = True
            block = aggregate_criterion_documents_from_list(
                all_b,
                kra_key="kra1",
                criterion_id="kra1-b",
                settings=published_settings_blob(),
            )
            report["supportingExclusion"] = {
                "primaryCount": len(primaries),
                "supportingCount": len(supporting),
                "aggregatedDocumentCount": block.get("documentCount"),
                "estimatedPoints": block.get("estimatedPoints"),
            }
            if block.get("documentCount") != len(primaries):
                report["defects"].append(
                    "Aggregation documentCount includes supporting evidence rows."
                )

        # Legacy-only docs on profile (behavior note)
        if hits:
            profile = hits[0]["profile"]
            legacy = []
            for doc in Document.query.filter_by(faculty_profile_id=profile.id, criterion_id="kra1-b").filter(
                Document.deleted_at.is_(None)
            ):
                if is_supporting_evidence_document(doc):
                    continue
                info = doc.extracted_info if isinstance(doc.extracted_info, dict) else {}
                if not info.get("criterionBEvidenceBundle"):
                    legacy.append(
                        {
                            "documentId": doc.public_id,
                            "verifiedPoints": doc.verified_points,
                            "estimatedPoints": doc.estimated_points,
                        }
                    )
            if legacy:
                report["warnings"].append(
                    "Legacy-only Criterion B primaries present; adapter prefers bundles — see legacy fallback in kra_document_aggregate."
                )
                report["legacyPrimaries"] = legacy

    report["finishedAt"] = datetime.now(timezone.utc).isoformat()
    report["automatedTestCommand"] = (
        "cd backend && python -m pytest tests/staging/test_criterion_b_activation_scenarios.py -q"
    )

    if report["defects"]:
        report["goRecommendation"] = "NO-GO"
    elif not report.get("jasonAccomplishments"):
        report["goRecommendation"] = "NO-GO"
    else:
        report["goRecommendation"] = "GO (staging read-only checks passed — confirm UI manually on staging host)"

    path = _write_report(report)
    print(json.dumps({"recommendation": report["goRecommendation"], "report": str(path)}, indent=2))
    return 0 if report["goRecommendation"].startswith("GO") else 1


if __name__ == "__main__":
    raise SystemExit(main())
