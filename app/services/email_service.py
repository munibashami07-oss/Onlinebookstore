"""Email sending via Gmail SMTP.

Uses the standard library `smtplib` over STARTTLS on port 587, which is
what a Gmail "app password" (Google Account -> Security -> 2-Step
Verification -> App passwords) is for -- your normal Gmail password won't
work here, Google blocks plain SMTP auth with it.

Required environment variables (set these in Railway's dashboard for the
backend service, not committed to source):
    SMTP_USERNAME     - the full Gmail address sending the email
    SMTP_PASSWORD     - the 16-character Gmail app password (not your login password)
    MAIL_FROM_EMAIL   - usually the same as SMTP_USERNAME
    MAIL_FROM_NAME    - display name, e.g. "BookHaven"

`smtplib` is synchronous/blocking, so sends are run in FastAPI's
threadpool via `run_in_threadpool` rather than blocking the event loop.
"""

import logging
import smtplib
from email.message import EmailMessage

from starlette.concurrency import run_in_threadpool

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_sync(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    """Blocking SMTP send -- always call via run_in_threadpool from async code."""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM_EMAIL}>"
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


async def send_password_reset_email(to_email: str, reset_url: str) -> None:
    """Send the password reset email with the given reset link.

    Best-effort: raises on failure so the caller can decide how to react
    (e.g. log it), but a send failure should never reveal to the client
    whether the account exists -- see AuthService.forgot_password.
    """
    subject = "Reset your BookHaven password"
    text_body = (
        "We received a request to reset your BookHaven password.\n\n"
        f"Reset it here: {reset_url}\n\n"
        f"This link expires in {settings.RESET_TOKEN_EXPIRE_MINUTES} minutes.\n"
        "If you didn't request this, you can safely ignore this email."
    )
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color: #0f172a;">Reset your password</h2>
      <p>We received a request to reset your BookHaven account password.</p>
      <p>
        <a href="{reset_url}"
           style="display: inline-block; padding: 12px 24px; background: #d97706;
                  color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold;">
          Reset Password
        </a>
      </p>
      <p style="color: #64748b; font-size: 0.9em;">
        This link expires in {settings.RESET_TOKEN_EXPIRE_MINUTES} minutes.
        If you didn't request this, you can safely ignore this email.
      </p>
    </div>
    """

    try:
        await run_in_threadpool(_send_sync, to_email, subject, html_body, text_body)
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)
        raise


async def send_verification_email(to_email: str, full_name: str, verify_url: str) -> None:
    """Send the account confirmation email with the given verification link.

    Best-effort: raises on failure so the caller (AuthService.register) can
    decide how to react -- registration itself should still succeed even if
    this fails, so the caller catches and logs rather than propagating.
    """
    subject = "Confirm your BookHaven account"
    text_body = (
        f"Hi {full_name},\n\n"
        "Thanks for creating a BookHaven account. Please confirm your email "
        "address by opening the link below:\n\n"
        f"{verify_url}\n\n"
        f"This link expires in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours. "
        "You can still log in and use your account before confirming.\n\n"
        "If you did not create this account, you can ignore this email."
    )
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color: #0f172a;">Confirm your email</h2>
      <p>Hi {full_name}, thanks for creating a BookHaven account.</p>
      <p>
        <a href="{verify_url}"
           style="display: inline-block; padding: 12px 24px; background: #d97706;
                  color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold;">
          Confirm Email
        </a>
      </p>
      <p style="color: #64748b; font-size: 0.9em;">
        This link expires in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours.
        You can still log in and use your account before confirming.
        If you didn't create this account, you can safely ignore this email.
      </p>
    </div>
    """

    try:
        await run_in_threadpool(_send_sync, to_email, subject, html_body, text_body)
    except Exception:
        logger.exception("Failed to send verification email to %s", to_email)
        raise