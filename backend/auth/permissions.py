from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from models import User

ROLE_ADMINISTRATOR = "administrator"
ROLE_REVIEWER = "reviewer"
ROLE_FACULTY = "faculty"

STAFF_ROLES = {ROLE_ADMINISTRATOR, ROLE_REVIEWER}
ALL_ROLES = STAFF_ROLES | {ROLE_FACULTY}

PASSWORD_CHANGE_REQUIRED_MESSAGE = "Change your temporary password before continuing."


def _password_change_block_response():
    return jsonify(
        {
            "message": PASSWORD_CHANGE_REQUIRED_MESSAGE,
            "code": "PASSWORD_CHANGE_REQUIRED",
        }
    ), 403


def ensure_password_changed():
    """Return a Flask response if the signed-in user must change a temporary password."""
    public_id = get_jwt_identity()
    if not public_id:
        return None
    user = User.query.filter_by(public_id=public_id, is_active=True).first()
    if user and user.must_change_password:
        return _password_change_block_response()
    return None


def roles_required(*allowed_roles: str):
    allowed = set(allowed_roles)

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            blocked = ensure_password_changed()
            if blocked:
                return blocked
            role = get_jwt().get("role")
            if role not in allowed:
                return jsonify({"message": "You do not have permission to perform this action."}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
