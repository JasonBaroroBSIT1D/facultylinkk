from __future__ import annotations

import re
import secrets
from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from auth.permissions import ROLE_FACULTY, STAFF_ROLES
from auth_models import PasswordResetRequest
from extensions import db
from models import User, utcnow

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
OTP_TTL = timedelta(minutes=15)
RESET_TOKEN_TTL = timedelta(minutes=10)
MAX_OTP_ATTEMPTS = 5
RESEND_COOLDOWN = timedelta(seconds=60)

GENERIC_AUTH_FAILURE = "The email or password is incorrect."
def generic_forgot_message() -> str:
    from config import Config

    if Config.smtp_enabled():
        return "If that address is registered, a 6-digit code was sent to your email."
    return (
        "If that address is registered, password reset instructions will be sent when email delivery is configured."
    )


def normalize_email(value: str) -> str:
    return value.strip().lower()


def validate_password_strength(password: str) -> str | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Use at least {MIN_PASSWORD_LENGTH} characters."
    return None


def find_user_by_identity(identity: str) -> User | None:
    raw = (identity or "").strip()
    if not raw:
        return None
    lowered = raw.lower()
    if "@" in lowered:
        return User.query.filter(db.func.lower(User.email) == lowered).first()
    return User.query.filter_by(public_id=raw).first()


def find_user_by_email(email: str) -> User | None:
    normalized = normalize_email(email)
    if not normalized:
        return None
    return User.query.filter(db.func.lower(User.email) == normalized).first()


def authenticate_user(identity: str, password: str) -> User | None:
    user = find_user_by_identity(identity)
    if not user or not user.is_active:
        return None
    if not user.check_password(password):
        return None
    return user


def assert_client_role_allowed(user: User, client: str | None) -> str | None:
    """Return an error message if client channel forbids this role."""
    if not client:
        return None
    channel = client.strip().lower()
    if channel == "web" and user.role == ROLE_FACULTY:
        return "Faculty accounts must use the mobile application."
    if channel == "mobile" and user.role in STAFF_ROLES:
        return "Administrator and reviewer accounts must use the web portal."
    return None


def session_payload(user: User) -> dict:
    return {
        "userId": user.public_id,
        "role": user.role,
        "mustChangePassword": user.must_change_password,
    }


def invalidate_prior_reset_requests(user_id: int) -> None:
    now = utcnow()
    (
        PasswordResetRequest.query.filter(
            PasswordResetRequest.user_id == user_id,
            PasswordResetRequest.used_at.is_(None),
        ).update({"used_at": now}, synchronize_session=False)
    )


def _generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_value(value: str) -> str:
    return generate_password_hash(value)


def _check_hash(stored_hash: str, value: str) -> bool:
    return check_password_hash(stored_hash, value)


def start_password_reset(email: str, *, client_ip: str | None = None) -> tuple[dict, str | None]:
    """
    Create reset request. Returns (public_response, otp_for_delivery).
    otp_for_delivery is only for email/logging — never include in HTTP responses.
    """
    message = generic_forgot_message()
    normalized = normalize_email(email)
    if not normalized or not EMAIL_PATTERN.match(normalized):
        return {"ok": True, "message": message}, None

    from auth.rate_limit import allow_forgot_password, record_forgot_password

    ip_bucket = f"ip:{client_ip or 'unknown'}"
    email_bucket = f"email:{normalized}"
    if not allow_forgot_password(email_bucket=email_bucket, ip_bucket=ip_bucket):
        return {
            "ok": True,
            "message": message,
            "resendAfterSeconds": 60,
        }, None

    user = find_user_by_email(normalized)
    if not user or not user.is_active:
        return {"ok": True, "message": message}, None

    latest = (
        PasswordResetRequest.query.filter_by(user_id=user.id, used_at=None)
        .order_by(PasswordResetRequest.created_at.desc())
        .first()
    )
    if latest and not latest.is_expired:
        elapsed = utcnow() - latest.created_at
        if elapsed < RESEND_COOLDOWN:
            wait = int((RESEND_COOLDOWN - elapsed).total_seconds())
            return {
                "ok": True,
                "message": message,
                "resendAfterSeconds": max(wait, 1),
                "expiresInSeconds": max(int((latest.expires_at - utcnow()).total_seconds()), 0),
            }, None

    invalidate_prior_reset_requests(user.id)
    otp = _generate_otp()
    record = PasswordResetRequest(
        user_id=user.id,
        otp_hash=_hash_value(otp),
        expires_at=utcnow() + OTP_TTL,
    )
    db.session.add(record)
    record_forgot_password(email_bucket=email_bucket, ip_bucket=ip_bucket)
    db.session.commit()

    return {
        "ok": True,
        "message": message,
        "resendAfterSeconds": int(RESEND_COOLDOWN.total_seconds()),
        "expiresInSeconds": int(OTP_TTL.total_seconds()),
    }, otp


def verify_reset_otp(email: str, code: str) -> str:
    user = find_user_by_email(email)
    if not user:
        raise ValueError("invalid")

    record = (
        PasswordResetRequest.query.filter_by(user_id=user.id, used_at=None)
        .order_by(PasswordResetRequest.created_at.desc())
        .first()
    )
    if not record or record.is_expired or record.is_consumed:
        raise ValueError("invalid")

    if record.failed_attempts >= MAX_OTP_ATTEMPTS:
        raise ValueError("invalid")

    if not _check_hash(record.otp_hash, code.strip()):
        record.failed_attempts += 1
        db.session.commit()
        raise ValueError("invalid")

    reset_token = secrets.token_urlsafe(32)
    record.otp_verified_at = utcnow()
    record.reset_token_hash = _hash_value(reset_token)
    record.expires_at = utcnow() + RESET_TOKEN_TTL
    db.session.commit()
    return reset_token


def complete_password_reset(email: str, reset_token: str, new_password: str) -> None:
    strength = validate_password_strength(new_password)
    if strength:
        raise ValueError(strength)

    user = find_user_by_email(email)
    if not user:
        raise ValueError("invalid")

    record = (
        PasswordResetRequest.query.filter_by(user_id=user.id, used_at=None)
        .order_by(PasswordResetRequest.created_at.desc())
        .first()
    )
    if (
        not record
        or not record.reset_token_hash
        or record.is_expired
        or record.is_consumed
        or not _check_hash(record.reset_token_hash, reset_token.strip())
    ):
        raise ValueError("invalid")

    user.set_password(new_password)
    user.must_change_password = False
    user.auth_epoch += 1
    record.used_at = utcnow()
    invalidate_prior_reset_requests(user.id)
    db.session.commit()
