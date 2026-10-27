from __future__ import annotations

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

from auth import assignment_queries as aq
from auth import permissions as perm
from auth.permissions import ROLE_REVIEWER

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
