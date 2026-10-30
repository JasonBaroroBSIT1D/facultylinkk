from __future__ import annotations

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

from auth import assignment_queries as aq
from auth import permissions as perm
from auth.permissions import ROLE_REVIEWER
from kra_configuration import service as kra_svc

reviewer_bp = Blueprint("reviewer_api", __name__, url_prefix="/api/reviewer")


@reviewer_bp.get("/me/faculty")
@perm.roles_required(ROLE_REVIEWER)
def my_assigned_faculty():
    public_id = get_jwt_identity()
    user = aq.current_reviewer_user(public_id)
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    faculty = aq.list_assigned_faculty_for_reviewer(user)
    return jsonify({"faculty": faculty, "count": len(faculty)}), 200


@reviewer_bp.get("/kra-configuration")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_get_published_kra_configuration():
    row = kra_svc.get_published_row()
    if not row:
        return jsonify({"published": None, "message": "No published configuration."}), 200
    payload = kra_svc.configuration_to_api(row)
    return jsonify({"published": payload, "kraSettings": payload["kraSettings"]}), 200


@reviewer_bp.get("/evaluation-periods")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_get_evaluation_periods():
    from evaluation_periods import service as eval_periods

    return jsonify({"evaluationPeriods": eval_periods.list_published_periods_api()}), 200
