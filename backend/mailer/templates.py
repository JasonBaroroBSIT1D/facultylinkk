"""Email bodies (no secrets embedded)."""

from __future__ import annotations

from config import Config


def password_reset_otp_email(*, name: str, otp: str, minutes: int) -> tuple[str, str, str]:
    subject = "FacultyLink password reset code"
    text = (
        f"Hello {name},\n\n"
        f"Your FacultyLink password reset code is: {otp}\n"
        f"This code expires in {minutes} minutes.\n\n"
        "If you did not request this, you can ignore this email.\n"
    )
    html = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif;max-width:520px">
      <h2 style="color:#071429">FacultyLink</h2>
      <p>Hello {name},</p>
      <p>Use this one-time code to reset your password:</p>
      <p style="font-size:28px;letter-spacing:6px;font-weight:700">{otp}</p>
      <p>Expires in {minutes} minutes.</p>
      <p style="color:#666;font-size:13px">If you did not request this, ignore this email.</p>
    </div>
    """
    return subject, text, html


def account_credentials_email(
    *,
    name: str,
    role_label: str,
    email: str,
    temporary_password: str,
    portal_hint: str,
    portal_url: str,
) -> tuple[str, str, str]:
    subject = "Your FacultyLink sign-in credentials"
    portal_line = f"\nReviewer portal: {portal_url}\n" if portal_url else ""
    text = (
        f"Hello {name},\n\n"
        f"Your institution created a FacultyLink {role_label} account for you.\n\n"
        f"{portal_hint}\n"
        f"{portal_line}\n"
        f"Email: {email}\n"
        f"Temporary password: {temporary_password}\n\n"
        "You must change this password on first sign-in.\n"
        "If you did not expect this message, contact your institution administrator.\n"
    )
    portal_html = (
        f'<p><a href="{portal_url}">Open the Reviewer Web portal</a></p>' if portal_url else ""
    )
    html = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif;max-width:560px">
      <h2 style="color:#071429">Faculty<span style="color:#3b9eff">Link</span></h2>
      <p>Hello {name},</p>
      <p>Your institution created a <strong>{role_label}</strong> account for you.</p>
      <p>{portal_hint}</p>
      {portal_html}
      <p style="margin-top:16px"><strong>Email:</strong> {email}<br>
      <strong>Temporary password:</strong> {temporary_password}</p>
      <p style="font-size:13px;color:#666">Change this password immediately after your first sign-in.</p>
    </div>
    """
    return subject, text, html
