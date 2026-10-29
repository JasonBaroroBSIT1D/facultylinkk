"""HTTP routes for Official Scoring Configuration."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from auth import permissions as perm
from auth.permissions import ROLE_ADMINISTRATOR
from kra_configuration import service as kra_svc
from models import User

kra_config_admin_bp = Blueprint("kra_config_admin", __name__)


def _admin_user() -> User | None:
    public_id = get_jwt_identity()
    if not public_id:
        return None
    return User.query.filter_by(public_id=public_id, role=ROLE_ADMINISTRATOR, is_active=True).first()


def _json_body() -> dict:
    return request.get_json(silent=True) or {}


@kra_config_admin_bp.get("/kra-configuration/draft")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_get_draft():
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    draft = kra_svc.get_draft_row()
    published = kra_svc.get_published_row()
    return jsonify(
        {
            "draft": kra_svc.configuration_to_api(draft) if draft else None,
            "publishedSummary": kra_svc.version_summary(published) if published else None,
        }
    ), 200


@kra_config_admin_bp.put("/kra-configuration/draft")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_save_draft():
    admin = _admin_user()
    if not admin:
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    body = _json_body()
    if not body.get("kraSettings") and not body.get("settings"):
        return jsonify({"message": "kraSettings payload is required."}), 400
    try:
        row = kra_svc.save_draft(admin, body)
    except Exception:
        return jsonify({"message": "Draft configuration was not saved."}), 500
    payload = kra_svc.configuration_to_api(row)
    return jsonify({"draft": payload, "kraSettings": payload["kraSettings"]}), 200


@kra_config_admin_bp.post("/kra-configuration/validate-publish")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_validate_publish():
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    body = _json_body()
    return jsonify(kra_svc.preview_publish_validation(body)), 200


@kra_config_admin_bp.post("/kra-configuration/publish")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_publish():
    admin = _admin_user()
    if not admin:
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    body = _json_body()
    try:
        row = kra_svc.publish_draft(admin, body)
    except ValueError as error:
        code = str(error)
        messages = {
            "draft_required": "Save a draft configuration before publishing.",
            "effective_from_required": "Effective date is required to publish.",
            "effective_from_invalid": "Effective date must be a valid calendar date (YYYY-MM-DD).",
            "set_indicator_incomplete": (
                "Student Evaluation of Teaching (SET) maximum points must be configured before publishing."
            ),
            "sef_indicator_incomplete": (
                "Supervisor Evaluation of Faculty (SEF) maximum points must be configured before publishing."
            ),
            "evaluation_coverage_invalid": "Evaluation coverage rules are incomplete or invalid.",
            "criterion_a_inconsistent": (
                "Criterion A maximum points cannot be less than the combined SET and SEF maxima."
            ),
            "publish_validation_failed": "Configuration did not pass publish validation.",
        }
        return jsonify({"message": messages.get(code, "Configuration was not published.")}), 400
    except Exception:
        return jsonify({"message": "Configuration was not published."}), 500
    payload = kra_svc.configuration_to_api(row)
    return jsonify({"published": payload, "kraSettings": payload["kraSettings"]}), 200


@kra_config_admin_bp.get("/kra-configuration/published")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_get_published():
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    row = kra_svc.get_published_row()
    if not row:
        return jsonify({"published": None, "message": "No published configuration."}), 200
    payload = kra_svc.configuration_to_api(row)
    return jsonify({"published": payload, "kraSettings": payload["kraSettings"]}), 200


@kra_config_admin_bp.get("/kra-configuration/versions")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_list_versions():
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    rows = kra_svc.list_history_rows()
    return jsonify({"versions": [kra_svc.version_summary(r) for r in rows]}), 200


@kra_config_admin_bp.get("/kra-configuration/versions/<int:config_id>")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_get_version(config_id: int):
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    row = kra_svc.get_version_by_id(config_id)
    if not row or row.status == kra_svc.STATUS_DRAFT:
        return jsonify({"message": "Configuration version was not found."}), 404
    payload = kra_svc.configuration_to_api(row)
    return jsonify({"configuration": payload, "kraSettings": payload["kraSettings"]}), 200

