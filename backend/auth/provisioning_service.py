"""Administrator-provisioned faculty/reviewer accounts with emailed temporary passwords."""

from __future__ import annotations

import secrets
import string

from auth.permissions import ROLE_FACULTY, ROLE_REVIEWER
from auth.rate_limit import allow_credential_resend, record_credential_resend
from auth.services import EMAIL_PATTERN, normalize_email
from config import Config
from mailer.smtp import EmailDeliveryError, send_email
from mailer.templates import account_credentials_email
from extensions import db
from models import FacultyProfile, User, new_public_id

_TEMP_ALPHABET = string.ascii_letters + string.digits


def generate_temporary_password(length: int = 14) -> str:
    """Cryptographically secure password meeting minimum length."""
    while True:
        chars = [secrets.choice(_TEMP_ALPHABET) for _ in range(length)]
        password = "".join(chars)
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
        ):
            return password


def _send_credentials_email(user: User, temporary_password: str) -> None:
    if user.role == ROLE_FACULTY:
        portal_hint = "Open the FacultyLink mobile app on your device and sign in with the credentials below."
        portal_url = ""
    else:
        portal_url = f"{Config.WEB_PUBLIC_URL}/pages/public/login.html"
        portal_hint = "Open the FacultyLink Reviewer Web portal and sign in with the credentials below."

    subject, text, html = account_credentials_email(
        name=user.full_name,
        role_label="Faculty" if user.role == ROLE_FACULTY else "Reviewer",
        email=user.email,
        temporary_password=temporary_password,
        portal_hint=portal_hint,
        portal_url=portal_url,
    )
    send_email(to_address=user.email, subject=subject, html_body=html, text_body=text)


def create_reviewer_account(*, full_name: str, email: str, office: str) -> tuple[User, str]:
    normalized = normalize_email(email)
    if not normalized or not EMAIL_PATTERN.match(normalized):
        raise ValueError("invalid_email")
    if User.query.filter(db.func.lower(User.email) == normalized).first():
        raise ValueError("duplicate_email")

    temporary_password = generate_temporary_password()
    user = User(
        email=normalized,
        role=ROLE_REVIEWER,
        full_name=full_name.strip(),
        office=(office or "").strip() or "Institutional Review",
        is_active=True,
        must_change_password=True,
    )
    user.set_password(temporary_password)
    db.session.add(user)
    db.session.flush()
    return user, temporary_password


def _next_employee_no() -> str:
    for _ in range(8):
        candidate = f"EMP-{secrets.randbelow(900000) + 100000}"
        if not FacultyProfile.query.filter_by(employee_no=candidate).first():
            return candidate
    return new_public_id("emp_")


def create_faculty_account(
    *,
    full_name: str,
    email: str,
    department: str,
    rank: str,
    education: str,
    reviewer_public_id: str | None,
) -> tuple[User, str]:
    normalized = normalize_email(email)
    if not normalized or not EMAIL_PATTERN.match(normalized):
        raise ValueError("invalid_email")
    if User.query.filter(db.func.lower(User.email) == normalized).first():
        raise ValueError("duplicate_email")

    reviewer_user_id = None
    if reviewer_public_id:
        reviewer = User.query.filter_by(public_id=reviewer_public_id.strip(), role=ROLE_REVIEWER).first()
        if not reviewer:
            raise ValueError("invalid_reviewer")
        reviewer_user_id = reviewer.id

    temporary_password = generate_temporary_password()
    user = User(
        email=normalized,
        role=ROLE_FACULTY,
        full_name=full_name.strip(),
        specialization=(education or "").strip(),
        is_active=True,
        must_change_password=True,
    )
    user.set_password(temporary_password)
    db.session.add(user)
    db.session.flush()

    profile = FacultyProfile(
        user_id=user.id,
        employee_no=_next_employee_no(),
        current_rank=(rank or "Instructor I").strip(),
        department=department.strip(),
        college=department.strip(),
        reviewer_user_id=reviewer_user_id,
    )
    db.session.add(profile)
    db.session.flush()
    return user, temporary_password


def provision_account_with_credentials(user: User, temporary_password: str) -> tuple[bool, str | None]:
    """Persist account and email temporary password. Plaintext exists only in memory until SMTP accepts."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    try:
        _send_credentials_email(user, temporary_password)
        return True, None
    except EmailDeliveryError as error:
        return False, str(error)


def _credential_resend_eligible(user: User | None) -> bool:
    if not user or user.role not in (ROLE_FACULTY, ROLE_REVIEWER):
        return False
    if user.must_change_password:
        return True
    return not user.is_active


def resend_credentials(public_id: str) -> tuple[bool, str | None]:
    user = User.query.filter_by(public_id=public_id).first()
    if not _credential_resend_eligible(user):
        raise ValueError("not_eligible")
    if not allow_credential_resend(user.public_id):
        raise ValueError("rate_limited")

    temporary_password = generate_temporary_password()
    user.set_password(temporary_password)
    user.is_active = True
    user.must_change_password = True
    user.auth_epoch += 1
    db.session.commit()
    record_credential_resend(user.public_id)

    try:
        _send_credentials_email(user, temporary_password)
        return True, None
    except EmailDeliveryError as error:
        return False, str(error)
