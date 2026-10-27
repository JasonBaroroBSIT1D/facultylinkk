from __future__ import annotations

from datetime import timedelta

from auth_models import AuthRateLimitEvent
from config import Config
from extensions import db
from models import utcnow


def _count_recent(bucket: str, action: str, window: timedelta) -> int:
    since = utcnow() - window
    return (
        AuthRateLimitEvent.query.filter(
            AuthRateLimitEvent.bucket == bucket,
            AuthRateLimitEvent.action == action,
            AuthRateLimitEvent.created_at >= since,
        ).count()
    )


def record_event(*, bucket: str, action: str) -> None:
    db.session.add(AuthRateLimitEvent(bucket=bucket, action=action))
    db.session.commit()


def allow_forgot_password(*, email_bucket: str, ip_bucket: str) -> bool:
    window = timedelta(seconds=Config.FORGOT_PASSWORD_RATE_WINDOW_SECONDS)
    limit = Config.FORGOT_PASSWORD_RATE_LIMIT
    if _count_recent(email_bucket, "forgot_password", window) >= limit:
        return False
    if _count_recent(ip_bucket, "forgot_password_ip", window) >= limit:
        return False
    return True


def record_forgot_password(*, email_bucket: str, ip_bucket: str) -> None:
    db.session.add(AuthRateLimitEvent(bucket=email_bucket, action="forgot_password"))
    db.session.add(AuthRateLimitEvent(bucket=ip_bucket, action="forgot_password_ip"))


CREDENTIAL_RESEND_COOLDOWN = timedelta(seconds=120)
CREDENTIAL_RESEND_LIMIT = 5
CREDENTIAL_RESEND_WINDOW = timedelta(hours=1)


def allow_credential_resend(user_public_id: str) -> bool:
    bucket = f"user:{user_public_id}"
    if _count_recent(bucket, "credential_resend", CREDENTIAL_RESEND_WINDOW) >= CREDENTIAL_RESEND_LIMIT:
        return False
    latest = (
        AuthRateLimitEvent.query.filter_by(bucket=bucket, action="credential_resend")
        .order_by(AuthRateLimitEvent.created_at.desc())
        .first()
    )
    if latest and utcnow() - latest.created_at < CREDENTIAL_RESEND_COOLDOWN:
        return False
    return True


def record_credential_resend(user_public_id: str) -> None:
    db.session.add(
        AuthRateLimitEvent(bucket=f"user:{user_public_id}", action="credential_resend")
    )
    db.session.commit()
