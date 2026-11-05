"""Safe admin KRA configuration checks on facultylink_qa (no production publish)."""

from __future__ import annotations

import json
import os
import sys

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


def _kra4_ids(kra_settings: dict) -> list[str]:
    indicators = (kra_settings or {}).get("indicators") if isinstance(kra_settings, dict) else {}
    if not isinstance(indicators, dict):
        return []
    return sorted(iid for iid in indicators if str(iid).startswith("kra4-"))


def main() -> int:
    if os.environ.get("FACULTYLINK_KRA4_QA_RUN", "").strip() != "1":
        print("Set FACULTYLINK_KRA4_QA_RUN=1", file=sys.stderr)
        return 2
    from scripts.qa_db_guard import require_qa_test_database

    require_qa_test_database()
    from config import Config
    from factory import create_app
    from auth.permissions import ROLE_ADMINISTRATOR
    from models import User
    from kra_configuration.kra4_indicator_registry import all_indicators
    from kra_configuration.service import get_draft_row, list_history_rows, preview_publish_validation, save_draft

    app = create_app(Config)
    report: dict = {"status": "FAIL", "checks": {}}
    with app.app_context():
        admin = User.query.filter_by(role=ROLE_ADMINISTRATOR, is_active=True).first()
        if not admin:
            report["status"] = "BLOCKED"
            report["reason"] = "no_active_admin_on_qa_db"
            out = os.path.join(BACKEND, "..", "docs", "KRA4_ADMIN_CONFIG_QA.json")
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2)
            print(json.dumps(report, indent=2))
            return 3

        catalog_ids = [row["id"] for row in all_indicators() if row.get("id")]
        report["catalogKra4IndicatorCount"] = len(catalog_ids)
        report["checks"]["catalog_nineteen_indicators"] = len(catalog_ids) == 19

        draft = get_draft_row()
        if not draft:
            save_draft(admin, {"kraSettings": {"indicators": {}, "criteria": {}, "kras": {}}})
            draft = get_draft_row()
        sj = draft.settings_json if draft and isinstance(draft.settings_json, dict) else {}
        indicators = dict(sj.get("indicators") or {})
        for row in all_indicators():
            iid = row.get("id")
            if not iid or iid in indicators:
                continue
            indicators[iid] = {
                "points": row.get("points"),
                "maxPoints": row.get("maxPoints"),
                "officialPoints": row.get("points"),
                "criterionId": row.get("criterionId"),
                "label": row.get("name"),
            }
        save_draft(admin, {"kraSettings": {"indicators": indicators}})
        report["checks"]["save_draft"] = True
        ids = _kra4_ids({"indicators": indicators})
        report["kra4IndicatorCountInDraft"] = len(ids)
        report["checks"]["draft_nineteen_kra4_indicators"] = len(ids) == 19

        history = list_history_rows()
        report["publishedVersionCount"] = len(history)
        report["checks"]["version_history_readable"] = isinstance(history, list)

        validation = preview_publish_validation({"metadata": {"effectiveFrom": "2026-01-01"}})
        report["checks"]["validate_publish_runs"] = isinstance(validation, dict)
        report["validatePublishReady"] = validation.get("ready")
        report["checks"]["publish_not_required_for_qa"] = validation.get("ready") is False
        report["validatePublish"] = {
            k: validation.get(k) for k in ("ready", "errors", "checks") if k in validation
        }
        report["status"] = "PASS" if all(report["checks"].values()) else "FAIL"

    out = os.path.join(BACKEND, "..", "docs", "KRA4_ADMIN_CONFIG_QA.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
