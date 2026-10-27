"""Authentication-related persistence (tokens, revocation)."""

from __future__ import annotations

from datetime import datetime, timezone

from extensions import db
from models import utcnow


class RevokedToken(db.Model):
    __tablename__ = "revoked_tokens"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(16), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)


class PasswordResetRequest(db.Model):
    """Single active reset flow per user: hashed OTP, then hashed reset token after verify."""

    __tablename__ = "password_reset_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    otp_hash = db.Column(db.String(255), nullable=False)
    reset_token_hash = db.Column(db.String(255))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    otp_verified_at = db.Column(db.DateTime(timezone=True))
    used_at = db.Column(db.DateTime(timezone=True))
    failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("password_reset_requests", lazy="dynamic"))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.used_at is not None


class AccountActivationToken(db.Model):
    __tablename__ = "account_activation_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("activation_tokens", lazy="dynamic"))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.used_at is not None


class AuthRateLimitEvent(db.Model):
    __tablename__ = "auth_rate_limit_events"

    id = db.Column(db.Integer, primary_key=True)
    bucket = db.Column(db.String(200), nullable=False, index=True)
    action = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
