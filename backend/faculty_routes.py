from __future__ import annotations

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

from auth import assignment_queries as aq
from auth import permissions as perm
from auth.permissions import ROLE_FACULTY
from faculty.faculty_payloads import faculty_dashboard_payload, faculty_profile_payload
from faculty.rank_simulation_engine import compute_rank_simulation
from documents.teaching_effectiveness import teaching_effectiveness_payload

faculty_bp = Blueprint("faculty_api", __name__, url_prefix="/api/faculty")


@faculty_bp.get("/me")
@perm.roles_required(ROLE_FACULTY)
def faculty_me():
    public_id = get_jwt_identity()
    user = aq.current_faculty_user(public_id)
    if not user:
        return jsonify({"message": "Faculty account was not found."}), 404
    profile = user.faculty_profile
    return jsonify(
        {
            "user": user.to_session_user(),
            "profile": faculty_profile_payload(user, profile),
        }
    ), 200


@faculty_bp.get("/me/dashboard")
@perm.roles_required(ROLE_FACULTY)
def faculty_dashboard():
    public_id = get_jwt_identity()
    user = aq.current_faculty_user(public_id)
    if not user:
        return jsonify({"message": "Faculty account was not found."}), 404
    profile = user.faculty_profile
    if not profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    return jsonify(faculty_dashboard_payload(user, profile)), 200


@faculty_bp.get("/me/rank-simulation")
@perm.roles_required(ROLE_FACULTY)
def faculty_rank_simulation():
    public_id = get_jwt_identity()
    user = aq.current_faculty_user(public_id)
    if not user or not user.faculty_profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    payload = compute_rank_simulation(user.faculty_profile)
    resp = jsonify({"simulation": payload})
    resp.headers["Cache-Control"] = "no-store"
    return resp, 200


@faculty_bp.get("/me/teaching-effectiveness")
@perm.roles_required(ROLE_FACULTY)
def faculty_teaching_effectiveness():
    public_id = get_jwt_identity()
    user = aq.current_faculty_user(public_id)
    if not user or not user.faculty_profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    return jsonify(teaching_effectiveness_payload(user.faculty_profile)), 200


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
