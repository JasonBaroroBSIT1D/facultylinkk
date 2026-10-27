from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from auth import permissions as perm
from auth.email_delivery import deliver_password_reset_otp
from auth.permissions import ensure_password_changed
from auth.services import (
    GENERIC_AUTH_FAILURE,
    authenticate_user,
    assert_client_role_allowed,
    complete_password_reset,
    session_payload,
    start_password_reset,
    validate_password_strength,
    verify_reset_otp,
)
from auth_models import RevokedToken
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _json_body() -> dict:
    return request.get_json(silent=True) or {}


def _login_identity(body: dict) -> str:
    return (body.get("email") or body.get("identity") or "").strip()


def _token_response(user: User):
    claims = {
        "role": user.role,
        "epoch": user.auth_epoch,
        "mustChangePassword": user.must_change_password,
    }
    access = create_access_token(identity=user.public_id, additional_claims=claims)
    refresh = create_refresh_token(identity=user.public_id, additional_claims=claims)
    return {
        "accessToken": access,
        "refreshToken": refresh,
        "user": user.to_session_user(),
        "session": session_payload(user),
    }


def _current_user() -> User | None:
    public_id = get_jwt_identity()
    if not public_id:
        return None
    return User.query.filter_by(public_id=public_id, is_active=True).first()


@auth_bp.post("/login")
def login():
    body = _json_body()
    identity = _login_identity(body)
    password = body.get("password") or ""
    client = body.get("client")

    if not identity or not password:
        return jsonify({"message": GENERIC_AUTH_FAILURE}), 401

    user = authenticate_user(identity, password)
    if not user:
        return jsonify({"message": GENERIC_AUTH_FAILURE}), 401

    channel_error = assert_client_role_allowed(user, client)
    if channel_error:
        return jsonify({"message": channel_error}), 403

    return jsonify(_token_response(user)), 200


@auth_bp.get("/session")
@jwt_required()
def session():
    user = _current_user()
    if not user:
        return jsonify({"message": "Sign in required."}), 401
    return jsonify({"user": user.to_session_user(), "session": session_payload(user)}), 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user = _current_user()
    if not user:
        return jsonify({"message": "Sign in required."}), 401
    claims = {
        "role": user.role,
        "epoch": user.auth_epoch,
        "mustChangePassword": user.must_change_password,
    }
    access = create_access_token(identity=user.public_id, additional_claims=claims)
    return jsonify({"accessToken": access}), 200


@auth_bp.post("/logout")
@jwt_required()
def logout():
    jwt_data = get_jwt()
    jti = jwt_data.get("jti")
    token_type = jwt_data.get("type", "access")
    exp = jwt_data.get("exp")
    if jti and exp:
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        db.session.add(
            RevokedToken(jti=jti, token_type=token_type, expires_at=expires_at)
        )
        db.session.commit()
    return jsonify({"ok": True}), 200


@auth_bp.post("/logout-all")
@jwt_required(refresh=True)
def logout_all():
    """Revoke the refresh token used for this call (client should discard access token locally)."""
    jwt_data = get_jwt()
    jti = jwt_data.get("jti")
    token_type = jwt_data.get("type", "refresh")
    exp = jwt_data.get("exp")
    if jti and exp:
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        db.session.add(
            RevokedToken(jti=jti, token_type=token_type, expires_at=expires_at)
        )
        db.session.commit()
    return jsonify({"ok": True}), 200


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    user = _current_user()
    if not user:
        return jsonify({"message": "Sign in required."}), 401

    body = _json_body()
    current = body.get("currentPassword") or body.get("current_password") or ""
    new_password = body.get("newPassword") or body.get("new_password") or ""

    if not user.check_password(current):
        return jsonify({"message": "The current password is incorrect."}), 400

    strength = validate_password_strength(new_password)
    if strength:
        return jsonify({"message": strength}), 400

    if user.check_password(new_password):
        return jsonify({"message": "Choose a password that is different from your current password."}), 400

    required_first_login = user.must_change_password
    user.set_password(new_password)
    user.must_change_password = False
    user.auth_epoch += 1
    db.session.commit()
    if required_first_login:
        return jsonify(_token_response(user)), 200
    return jsonify({"ok": True}), 200


@auth_bp.post("/forgot-password")
def forgot_password():
    body = _json_body()
    email = (body.get("email") or "").strip()
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    payload, otp = start_password_reset(email, client_ip=client_ip)
    if otp:
        deliver_password_reset_otp(email, otp)
    return jsonify(payload), 200


@auth_bp.post("/forgot-password/verify")
def forgot_password_verify():
    body = _json_body()
    email = (body.get("email") or "").strip()
    code = (body.get("code") or body.get("otp") or "").strip()
    if not email or not code:
        return jsonify({"message": "The code is invalid or has expired. Request a new code."}), 400
    try:
        reset_token = verify_reset_otp(email, code)
    except ValueError:
        return jsonify({"message": "The code is invalid or has expired. Request a new code."}), 400
    return jsonify({"resetToken": reset_token}), 200


@auth_bp.post("/forgot-password/reset")
def forgot_password_reset():
    body = _json_body()
    email = (body.get("email") or "").strip()
    reset_token = (body.get("resetToken") or body.get("reset_token") or "").strip()
    new_password = body.get("newPassword") or body.get("new_password") or ""
    if not email or not reset_token or not new_password:
        return jsonify({"message": "Reset session expired. Start again."}), 400
    try:
        complete_password_reset(email, reset_token, new_password)
    except ValueError as error:
        message = str(error)
        if message == "invalid":
            return jsonify({"message": "Reset session expired. Start again."}), 400
        return jsonify({"message": message}), 400
    return jsonify({"ok": True, "message": "Your password has been updated. Sign in with your new password."}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    blocked = ensure_password_changed()
    if blocked:
        return blocked
    user = _current_user()
    if not user:
        return jsonify({"message": "Sign in required."}), 401
    return jsonify({"user": user.to_session_user()}), 200


# Role-guarded probes for integration tests (no domain data).
@auth_bp.get("/probe/administrator")
@perm.roles_required(perm.ROLE_ADMINISTRATOR)
def probe_administrator():
    return jsonify({"role": perm.ROLE_ADMINISTRATOR, "ok": True}), 200


@auth_bp.get("/probe/reviewer")
@perm.roles_required(perm.ROLE_REVIEWER)
def probe_reviewer():
    return jsonify({"role": perm.ROLE_REVIEWER, "ok": True}), 200


@auth_bp.get("/probe/faculty")
@perm.roles_required(perm.ROLE_FACULTY)
def probe_faculty():
    return jsonify({"role": perm.ROLE_FACULTY, "ok": True}), 200
