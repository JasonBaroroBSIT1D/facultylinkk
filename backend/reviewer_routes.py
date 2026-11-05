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
    from kra_configuration.read_api import applicable_scoring_configuration_payload

    payload = applicable_scoring_configuration_payload()
    if not payload.get("configuration"):
        return jsonify({"published": None, "message": "No published configuration.", **payload}), 200
    return jsonify(
        {
            "published": payload["configuration"],
            "kraSettings": payload["kraSettings"],
            "metadata": payload.get("metadata"),
            "rankWeightsPolicy": payload.get("rankWeightsPolicy"),
        }
    ), 200


@reviewer_bp.get("/evaluation-periods")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_get_evaluation_periods():
    from evaluation_periods import service as eval_periods

    return jsonify({"evaluationPeriods": eval_periods.list_published_periods_api()}), 200


@reviewer_bp.get("/faculty/<faculty_public_id>/estimated-assessment")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_faculty_estimated_assessment(faculty_public_id: str):
    from auth import assignment_queries as aq
    from faculty.estimated_score_service import estimated_assessment_payload
    from models import FacultyProfile

    reviewer_public = get_jwt_identity()
    reviewer = aq.current_reviewer_user(reviewer_public)
    if not reviewer:
        return jsonify({"message": "Reviewer account was not found."}), 404
    profile = FacultyProfile.query.filter_by(public_id=faculty_public_id).first()
    if not profile or not profile.user:
        return jsonify({"message": "Faculty member was not found."}), 404
    assigned = aq.list_assigned_faculty_for_reviewer(reviewer)
    if not any(row.get("id") == faculty_public_id for row in assigned):
        return jsonify({"message": "You do not have permission to view this faculty member."}), 403
    payload = estimated_assessment_payload(profile)
    resp = jsonify(payload)
    resp.headers["Cache-Control"] = "no-store"
    return resp, 200


@reviewer_bp.get("/me/dashboard")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_dashboard():
    public_id = get_jwt_identity()
    user = aq.current_reviewer_user(public_id)
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    from portal.dashboard_service import reviewer_dashboard_payload

    resp = jsonify(reviewer_dashboard_payload(user))
    resp.headers["Cache-Control"] = "no-store"
    return resp, 200


@reviewer_bp.get("/me/sync-health")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_sync_health():
    public_id = get_jwt_identity()
    user = aq.current_reviewer_user(public_id)
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    from portal.sync_health import reviewer_sync_health_payload

    resp = jsonify(reviewer_sync_health_payload(user))
    resp.headers["Cache-Control"] = "no-store"
    return resp, 200


@reviewer_bp.get("/me/notifications")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_notifications_list():
    public_id = get_jwt_identity()
    user = aq.current_reviewer_user(public_id)
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    from portal.dashboard_service import notifications_payload

    return jsonify(notifications_payload(user)), 200


@reviewer_bp.patch("/me/notifications/<public_id>")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_notification_patch(public_id: str):
    from extensions import db
    from flask import request
    from models import Notification

    reviewer_public = get_jwt_identity()
    user = aq.current_reviewer_user(reviewer_public)
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    note = Notification.query.filter_by(public_id=public_id, user_id=user.id).first()
    if not note:
        return jsonify({"message": "Notification was not found."}), 404
    body = request.get_json(silent=True) or {}
    if "read" in body:
        note.read = bool(body.get("read"))
        db.session.commit()
    return jsonify({"id": note.public_id, "read": note.read}), 200


@reviewer_bp.patch("/me/notifications")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_notifications_mark_all():
    from extensions import db
    from flask import request
    from models import Notification

    reviewer_public = get_jwt_identity()
    user = aq.current_reviewer_user(reviewer_public)
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    body = request.get_json(silent=True) or {}
    read = bool(body.get("read", True))
    ids = body.get("ids") if isinstance(body.get("ids"), list) else None
    q = Notification.query.filter_by(user_id=user.id, read=not read)
    if ids:
        q = q.filter(Notification.public_id.in_(ids))
    for note in q.all():
        note.read = read
    db.session.commit()
    return jsonify({"updated": True}), 200
