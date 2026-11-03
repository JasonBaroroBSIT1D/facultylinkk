"""Read-only applicable scoring configuration (Phase C5 — C6/C7 clients)."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from auth import permissions as perm
from auth.permissions import ROLE_FACULTY, ROLE_REVIEWER
from kra_configuration.read_api import applicable_scoring_configuration_payload

scoring_read_bp = Blueprint("scoring_read", __name__)


def _parse_as_of_query() -> date | None:
    raw = (request.args.get("asOf") or request.args.get("as_of") or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


@scoring_read_bp.get("/scoring-configuration/applicable")
@perm.roles_required(ROLE_FACULTY, ROLE_REVIEWER)
def read_applicable_scoring_configuration():
    """Faculty and reviewer read-only access to the applicable official scoring configuration."""
    public_id = get_jwt_identity()
    if not public_id:
        return jsonify({"message": "Authentication is required."}), 401
    config_id = request.args.get("configurationId") or request.args.get("configuration_id")
    kra_configuration_id = None
    if config_id:
        try:
            kra_configuration_id = int(config_id)
        except (TypeError, ValueError):
            return jsonify({"message": "configurationId must be a numeric id."}), 400
    payload = applicable_scoring_configuration_payload(
        as_of=_parse_as_of_query(),
        kra_configuration_id=kra_configuration_id,
    )
    resp = jsonify(payload)
    resp.headers["Cache-Control"] = "no-store"
    return resp, 200
