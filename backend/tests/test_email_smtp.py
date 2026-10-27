from unittest.mock import patch

from auth.email_delivery import deliver_password_reset_otp
from mailer.smtp import EmailDeliveryError
from config import Config


@patch("auth.email_delivery.find_user_by_email", return_value=None)
@patch("auth.email_delivery.send_email")
@patch.object(Config, "SMTP_USER", "user@gmail.com")
@patch.object(Config, "SMTP_PASSWORD", "secret")
@patch.object(Config, "SMTP_FROM", "FacultyLink <user@gmail.com>")
def test_deliver_password_reset_otp_calls_smtp(mock_send, _user_lookup):
    assert deliver_password_reset_otp("faculty@example.edu", "123456") is True
    mock_send.assert_called_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["to_address"] == "faculty@example.edu"
    assert "123456" in kwargs["text_body"]


@patch("auth.email_delivery.find_user_by_email", return_value=None)
@patch("auth.email_delivery.send_email", side_effect=EmailDeliveryError("down"))
@patch.object(Config, "SMTP_USER", "user@gmail.com")
@patch.object(Config, "SMTP_PASSWORD", "secret")
@patch.object(Config, "SMTP_FROM", "FacultyLink <user@gmail.com>")
def test_deliver_password_reset_otp_handles_failure(mock_send, _user_lookup):
    assert deliver_password_reset_otp("faculty@example.edu", "123456") is False
