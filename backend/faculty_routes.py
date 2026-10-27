from __future__ import annotations

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

from auth import assignment_queries as aq
from auth import permissions as perm
from auth.permissions import ROLE_FACULTY

faculty_bp = Blueprint("faculty_api", __name__, url_prefix="/api/faculty")


@faculty_bp.get("/me/reviewer")
@perm.roles_required(ROLE_FACULTY)
def my_assigned_reviewer():
    public_id = get_jwt_identity()
    user = aq.current_faculty_user(public_id)
    if not user:
        return jsonify({"message": "Faculty account was not found."}), 404
    try:
        payload = aq.faculty_assigned_reviewer(user)
    except ValueError as error:
        if str(error) == "no_profile":
            return jsonify({"message": "Faculty profile was not found."}), 404
        return jsonify({"message": "Reviewer assignment could not be loaded."}), 400
    return jsonify(payload), 200
