"""Gmail SMTP delivery (STARTTLS on port 587)."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """SMTP rejected or misconfigured."""


def send_email(*, to_address: str, subject: str, html_body: str, text_body: str) -> None:
    if not Config.smtp_enabled():
        raise EmailDeliveryError("SMTP is not configured.")

    to_address = to_address.strip()
    if not to_address:
        raise EmailDeliveryError("Missing recipient.")

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = Config.SMTP_FROM
    message["To"] = to_address
    message.attach(MIMEText(text_body, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.sendmail(Config.SMTP_FROM, [to_address], message.as_string())
    except Exception as exc:
        logger.warning("SMTP delivery failed for recipient (details not logged): %s", type(exc).__name__)
        raise EmailDeliveryError("Email could not be delivered.") from exc
