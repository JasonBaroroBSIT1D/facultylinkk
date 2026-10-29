from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from auth import permissions as perm
from auth.admin_directory import faculty_row, list_faculty_rows, list_reviewer_rows, reviewer_row
from auth import admin_management as mgmt
from auth.provisioning_service import (
    create_faculty_account,
    create_reviewer_account,
    provision_account_with_credentials,
    resend_credentials,
)
from auth.permissions import ROLE_ADMINISTRATOR
from extensions import db
from models import User

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _json_body() -> dict:
    return request.get_json(silent=True) or {}


def _admin_user() -> User | None:
    public_id = get_jwt_identity()
    if not public_id:
        return None
    return User.query.filter_by(public_id=public_id, role=ROLE_ADMINISTRATOR, is_active=True).first()


@admin_bp.get("/faculty")
@perm.roles_required(ROLE_ADMINISTRATOR)
def list_faculty():
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    return jsonify({"faculty": list_faculty_rows()}), 200


@admin_bp.get("/reviewers")
@perm.roles_required(ROLE_ADMINISTRATOR)
def list_reviewers():
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    return jsonify({"reviewers": list_reviewer_rows()}), 200


@admin_bp.post("/reviewers")
@perm.roles_required(ROLE_ADMINISTRATOR)
def create_reviewer():
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403

    body = _json_body()
    full_name = (body.get("fullName") or body.get("full_name") or "").strip()
    email = (body.get("email") or "").strip()
    department = (body.get("department") or body.get("office") or "").strip()

    if not full_name or not email:
        return jsonify({"message": "Enter the reviewer’s name and email."}), 400

    try:
        user, temporary_password = create_reviewer_account(
            full_name=full_name, email=email, office=department
        )
        email_sent, email_error = provision_account_with_credentials(user, temporary_password)
    except ValueError as error:
        code = str(error)
        if code == "duplicate_email":
            return jsonify({"message": "That email address is already registered."}), 409
        if code == "invalid_email":
            return jsonify({"message": "Enter a valid email address."}), 400
        return jsonify({"message": "Reviewer was not created."}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Reviewer was not created."}), 500

    return jsonify(
        {
            "reviewer": reviewer_row(user),
            "emailSent": email_sent,
            "emailError": email_error,
        }
    ), 201


@admin_bp.post("/faculty")
@perm.roles_required(ROLE_ADMINISTRATOR)
def create_faculty():
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403

    body = _json_body()
    full_name = (body.get("fullName") or body.get("full_name") or "").strip()
    email = (body.get("email") or "").strip()
    department = (body.get("department") or "").strip()
    rank = (body.get("rank") or "Instructor I").strip()
    education = (body.get("education") or "").strip()
    reviewer_id = (body.get("reviewerId") or body.get("reviewer_id") or "").strip() or None

    if not full_name or not email or not department:
        return jsonify({"message": "Fill in name, email, and department."}), 400

    try:
        user, temporary_password = create_faculty_account(
            full_name=full_name,
            email=email,
            department=department,
            rank=rank,
            education=education,
            reviewer_public_id=reviewer_id,
        )
        email_sent, email_error = provision_account_with_credentials(user, temporary_password)
    except ValueError as error:
        code = str(error)
        if code == "duplicate_email":
            return jsonify({"message": "That email address is already registered."}), 409
        if code == "invalid_email":
            return jsonify({"message": "Enter a valid email address."}), 400
        if code == "invalid_reviewer":
            return jsonify({"message": "Selected reviewer was not found."}), 400
        return jsonify({"message": "Faculty was not created."}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Faculty was not created."}), 500

    faculty = faculty_row(user.faculty_profile) if user.faculty_profile else None
    return jsonify(
        {
            "faculty": faculty,
            "emailSent": email_sent,
            "emailError": email_error,
        }
    ), 201


def _resend_credentials_handler(public_id: str):
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403

    try:
        email_sent, email_error = resend_credentials(public_id)
    except ValueError as error:
        code = str(error)
        if code == "rate_limited":
            return jsonify({"message": "Wait before requesting another credential email."}), 429
        if code == "not_eligible":
            return jsonify({"message": "This account is not eligible for credential email."}), 400
        return jsonify({"message": "Credential email was not sent."}), 400

    return jsonify({"emailSent": email_sent, "emailError": email_error}), 200


@admin_bp.post("/users/<public_id>/resend-credentials")
@perm.roles_required(ROLE_ADMINISTRATOR)
def resend_credentials_email(public_id: str):
    return _resend_credentials_handler(public_id)


@admin_bp.post("/users/<public_id>/resend-activation")
@perm.roles_required(ROLE_ADMINISTRATOR)
def resend_activation_email_legacy(public_id: str):
    """Deprecated alias for resend-credentials."""
    return _resend_credentials_handler(public_id)


@admin_bp.get("/faculty/<faculty_id>")
@perm.roles_required(ROLE_ADMINISTRATOR)
def get_faculty_detail(faculty_id: str):
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    try:
        return jsonify({"faculty": mgmt.faculty_detail(faculty_id)}), 200
    except ValueError as error:
        if str(error) == "not_found":
            return jsonify({"message": "Faculty record was not found."}), 404
        return jsonify({"message": "Faculty record was not found."}), 404


@admin_bp.patch("/faculty/<faculty_id>/reviewer")
@perm.roles_required(ROLE_ADMINISTRATOR)
def patch_faculty_reviewer(faculty_id: str):
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    body = _json_body()
    reviewer_id = (body.get("reviewerId") or body.get("reviewer_id") or "").strip() or None
    try:
        result = mgmt.set_faculty_reviewer(faculty_id, reviewer_id)
    except ValueError as error:
        code = str(error)
        if code == "not_found":
            return jsonify({"message": "Faculty record was not found."}), 404
        if code == "invalid_reviewer":
            return jsonify({"message": "Selected reviewer was not found or is inactive."}), 400
        if code == "inactive_faculty":
            return jsonify({"message": "Inactive faculty accounts cannot be reassigned."}), 400
        return jsonify({"message": "Reviewer assignment was not saved."}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Reviewer assignment was not saved."}), 500
    return jsonify(result), 200


@admin_bp.put("/reviewers/<reviewer_id>/faculty-assignments")
@perm.roles_required(ROLE_ADMINISTRATOR)
def put_reviewer_faculty_assignments(reviewer_id: str):
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    body = _json_body()
    faculty_ids = body.get("facultyIds") or body.get("faculty_ids") or []
    if not isinstance(faculty_ids, list):
        return jsonify({"message": "Invalid faculty list."}), 400
    confirm = bool(body.get("confirmReassign") or body.get("confirm_reassign"))
    try:
        result = mgmt.sync_reviewer_faculty_assignments(
            reviewer_id, [str(item) for item in faculty_ids], confirm_reassign=confirm
        )
    except ValueError as error:
        code = str(error)
        if code == "invalid_reviewer":
            return jsonify({"message": "Reviewer was not found or is inactive."}), 404
        if code == "invalid_faculty":
            return jsonify({"message": "One or more faculty records were not found."}), 400
        if code == "reassign_confirmation_required":
            return jsonify(
                {
                    "message": "Some faculty are assigned to another reviewer. Confirm reassignment to continue.",
                    "code": code,
                }
            ), 409
        return jsonify({"message": "Assignments were not saved."}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Assignments were not saved."}), 500
    return jsonify(result), 200


@admin_bp.get("/reviewers/<reviewer_id>/work")
@perm.roles_required(ROLE_ADMINISTRATOR)
def get_reviewer_work(reviewer_id: str):
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    try:
        return jsonify(mgmt.reviewer_work_detail(reviewer_id)), 200
    except ValueError as error:
        if str(error) == "not_found":
            return jsonify({"message": "Reviewer was not found."}), 404
        return jsonify({"message": "Reviewer was not found."}), 404


@admin_bp.post("/users/<public_id>/deactivate")
@perm.roles_required(ROLE_ADMINISTRATOR)
def deactivate_account(public_id: str):
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    try:
        result = mgmt.deactivate_user(public_id)
    except ValueError as error:
        if str(error) == "not_found":
            return jsonify({"message": "Account was not found."}), 404
        if str(error) == "reviewer_has_assignments":
            return jsonify(
                {
                    "message": "Reassign or remove faculty assignments and resolve pending reviews before deactivating this reviewer.",
                    "code": "reviewer_has_assignments",
                }
            ), 409
        return jsonify({"message": "Account was not deactivated."}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Account was not deactivated."}), 500
    return jsonify(result), 200


@admin_bp.post("/users/<public_id>/reactivate")
@perm.roles_required(ROLE_ADMINISTRATOR)
def reactivate_account(public_id: str):
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    try:
        result = mgmt.reactivate_user(public_id)
    except ValueError as error:
        if str(error) == "not_found":
            return jsonify({"message": "Account was not found."}), 404
        return jsonify({"message": "Account was not reactivated."}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Account was not reactivated."}), 500
    return jsonify(result), 200


@admin_bp.get("/policies/set-sef-auto-approval")
@perm.roles_required(ROLE_ADMINISTRATOR)
def get_set_sef_auto_approval_policy():
    if not _admin_user():
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    from documents.set_sef_auto_approval.policy import policy_state_for_api

    return jsonify({"policy": policy_state_for_api()}), 200


@admin_bp.put("/policies/set-sef-auto-approval")
@perm.roles_required(ROLE_ADMINISTRATOR)
def put_set_sef_auto_approval_policy():
    admin = _admin_user()
    if not admin:
        return jsonify({"message": "You do not have permission to perform this action."}), 403
    from documents.set_sef_auto_approval.policy import set_admin_policy_enabled

    body = _json_body()
    enabled = body.get("enabled") is True
    try:
        state = set_admin_policy_enabled(enabled=enabled, admin_public_id=admin.public_id)
    except ValueError as error:
        if str(error) == "policy_toggle_not_allowed":
            return jsonify(
                {
                    "message": (
                        "SET/SEF simulation auto-accept cannot be enabled until the server "
                        "allows Admin toggling (SET_SEF_AUTO_APPROVAL_ALLOW_ADMIN_TOGGLE)."
                    )
                }
            ), 403
        return jsonify({"message": "Policy was not updated."}), 400
    return jsonify({"policy": state}), 200
