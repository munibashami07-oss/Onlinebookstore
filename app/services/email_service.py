"""Email sending via the Resend HTTP API.

Switched from Gmail SMTP because Railway blocks outbound SMTP ports
(25/465/587) on Free/Trial/Hobby plans -- connections just hang until
they time out. Resend sends over plain HTTPS, so this works on any
Railway plan with no networking changes needed.

Required environment variables:
    RESEND_API_KEY    - from https://resend.com/api-keys
    MAIL_FROM_EMAIL    - must be on a domain you've verified with Resend
                          (Resend's onboarding@resend.dev works for testing
                          without a verified domain, but only delivers to
                          your own Resend account email until you verify one)
    MAIL_FROM_NAME     - display name, e.g. "BookHaven"

Since this is a plain HTTPS call, it runs natively as an async request --
no threadpool needed (unlike the old smtplib-based version).
"""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


async def _send_via_resend(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    """POST a single email to the Resend API. Raises on non-2xx responses."""
    payload = {
        "from": f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM_EMAIL}>",
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }
    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(RESEND_API_URL, json=payload, headers=headers)
        response.raise_for_status()


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
        await _send_via_resend(to_email, subject, html_body, text_body)
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
        await _send_via_resend(to_email, subject, html_body, text_body)
    except Exception:
        logger.exception("Failed to send verification email to %s", to_email)
        raise