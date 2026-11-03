"""
Read-only post-activation checks against the running Flask API (port 5000).

Uses reviewer credentials from environment (never printed):
  ACTIVATION_VERIFY_REVIEWER_EMAIL
  ACTIVATION_VERIFY_REVIEWER_PASSWORD

If unset, skips HTTP estimated-assessment and reports NOT TESTED for that step.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

BASE = (os.environ.get("ACTIVATION_VERIFY_API_BASE") or "http://127.0.0.1:5000").rstrip("/")


def _http_json(method: str, path: str, *, body: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    url = f"{BASE}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {"message": exc.reason}
        except json.JSONDecodeError:
            payload = {"message": raw or exc.reason}
        return exc.code, payload


def _find_jason_public_id() -> str | None:
    from factory import create_app
    from config import Config
    from models import FacultyProfile, User

    app = create_app(Config)
    with app.app_context():
        user = User.query.filter(User.full_name.ilike("%Jason Baroro%")).first()
        if not user:
            return None
        profile = FacultyProfile.query.filter_by(user_id=user.id).first()
        return profile.public_id if profile else None


def main() -> int:
    report: dict = {"baseUrl": BASE, "steps": []}

    status, health = _http_json("GET", "/api/health")
    report["health"] = {"statusCode": status, "body": health}
    if status != 200 or health.get("status") != "ok":
        print(json.dumps({"ok": False, "report": report}, indent=2))
        return 1

    faculty_id = _find_jason_public_id()
    report["jasonFacultyPublicId"] = faculty_id

    email = (os.environ.get("ACTIVATION_VERIFY_REVIEWER_EMAIL") or "").strip()
    password = os.environ.get("ACTIVATION_VERIFY_REVIEWER_PASSWORD") or ""
    if not email or not password:
        report["estimatedAssessment"] = {
            "result": "NOT TESTED",
            "reason": "Set ACTIVATION_VERIFY_REVIEWER_EMAIL and ACTIVATION_VERIFY_REVIEWER_PASSWORD for live HTTP auth.",
        }
    elif not faculty_id:
        report["estimatedAssessment"] = {"result": "FAIL", "reason": "Jason Baroro faculty public id not found."}
    else:
        status, login = _http_json(
            "POST",
            "/api/auth/login",
            body={"email": email, "password": password, "client": "web"},
        )
        if status != 200 or not login.get("accessToken"):
            report["estimatedAssessment"] = {
                "result": "FAIL",
                "statusCode": status,
                "message": login.get("message", "login failed"),
            }
        else:
            token = login["accessToken"]
            status, payload = _http_json(
                "GET",
                f"/api/reviewer/faculty/{faculty_id}/estimated-assessment",
                token=token,
            )
            est = payload.get("estimatedAssessment") or payload
            kra_scores = est.get("kraScores") or []
            kra1 = next((k for k in kra_scores if k.get("kraId") == "kra1"), {})
            crit_b = next(
                (c for c in (kra1.get("criteriaScores") or []) if c.get("criterionId") == "kra1-b"),
                {},
            )
            report["estimatedAssessment"] = {
                "result": "PASS" if status == 200 and crit_b.get("estimatedPoints") == 14 else "FAIL",
                "statusCode": status,
                "kra1EstimatedPoints": kra1.get("estimatedPoints"),
                "criterionBEstimatedPoints": crit_b.get("estimatedPoints"),
                "simulationTotal": est.get("estimatedTotalKraPoints"),
                "simulationAdapterEnabled": crit_b.get("simulationAdapterEnabled"),
            }

    # In-process parity (same DB + .env as backend code)
    from factory import create_app
    from config import Config
    from faculty.estimated_score_service import estimated_assessment_payload
    from models import FacultyProfile

    import importlib
    import documents.scoring.criterion_b_simulation_adapter as adapter_mod

    importlib.reload(adapter_mod)
    report["adapterEnabledInFreshProcess"] = adapter_mod.CRITERION_B_SIMULATION_ADAPTER_ENABLED

    app = create_app(Config)
    with app.app_context():
        if faculty_id:
            profile = FacultyProfile.query.filter_by(public_id=faculty_id).first()
            if profile:
                est = estimated_assessment_payload(profile).get("estimatedAssessment") or {}
                kra1 = next((k for k in est.get("kraScores") or [] if k.get("kraId") == "kra1"), {})
                crit_b = next(
                    (c for c in (kra1.get("criteriaScores") or []) if c.get("criterionId") == "kra1-b"),
                    {},
                )
                report["inProcessEstimatedAssessment"] = {
                    "kra1EstimatedPoints": kra1.get("estimatedPoints"),
                    "criterionBEstimatedPoints": crit_b.get("estimatedPoints"),
                    "simulationTotal": est.get("estimatedTotalKraPoints"),
                }

    ok = (
        report.get("health", {}).get("statusCode") == 200
        and report.get("inProcessEstimatedAssessment", {}).get("criterionBEstimatedPoints") == 14
    )
    print(json.dumps({"ok": ok, "report": report}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
