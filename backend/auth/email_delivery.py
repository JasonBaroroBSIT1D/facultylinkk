"""Password-reset and account emails via SMTP."""

from __future__ import annotations

import logging
import os

from auth.services import find_user_by_email
from config import Config
from mailer.smtp import EmailDeliveryError, send_email
from mailer.templates import password_reset_otp_email

logger = logging.getLogger(__name__)


def deliver_password_reset_otp(email: str, otp: str) -> bool:
    """
    Send OTP to the user. Returns True when SMTP accepted the message.
    Never log OTP values.
    """
    if os.getenv("AUTH_LOG_RESET_OTP", "").strip() == "1":
        logger.warning("Password reset OTP generated (dev flag AUTH_LOG_RESET_OTP=1; disable in production).")

    if not Config.smtp_enabled():
        return False

    user = find_user_by_email(email)
    name = user.full_name if user else "FacultyLink user"
    subject, text, html = password_reset_otp_email(name=name, otp=otp, minutes=15)
    try:
        send_email(to_address=email, subject=subject, html_body=html, text_body=text)
        return True
    except EmailDeliveryError:
        return False
