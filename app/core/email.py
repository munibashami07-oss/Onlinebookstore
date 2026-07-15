"""Plain-text email sending via Gmail SMTP.

Gmail requires an App Password for SMTP auth (your normal account
password will be rejected): Google Account -> Security -> 2-Step
Verification -> App Passwords. Put that 16-character value in
GMAIL_APP_PASSWORD in your .env, not your login password.
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.email_verification import create_email_verification_token

logger = logging.getLogger(__name__)


def _send_email_sync(to_email: str, subject: str, body: str) -> None:
    """Blocking SMTP send — always call via asyncio.to_thread from async code."""
    message = EmailMessage()
    message["From"] = settings.GMAIL_ADDRESS
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.GMAIL_ADDRESS, settings.GMAIL_APP_PASSWORD)
        server.send_message(message)


async def send_email(to_email: str, subject: str, body: str) -> None:
    """Send a plain-text email without blocking the event loop.

    Failures are logged, not raised, so a broken mail server never blocks
    registration itself (login/registration must keep working either way).
    """
    try:
        await asyncio.to_thread(_send_email_sync, to_email, subject, body)
    except Exception:
        logger.exception("Failed to send email to %s", to_email)


async def send_verification_email(to_email: str, full_name: str) -> None:
    """Send the account confirmation email containing a verification link."""
    token = create_email_verification_token(to_email)
    verify_link = (
        f"{settings.BACKEND_BASE_URL}{settings.API_V1_STR}"
        f"/auth/verify-email?token={token}"
    )

    subject = "Confirm your BookHaven account"
    body = (
        f"Hi {full_name},\n\n"
        "Thanks for creating a BookHaven account. Please confirm your email "
        "address by opening the link below:\n\n"
        f"{verify_link}\n\n"
        f"This link expires in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours. "
        "You can still log in and use your account before confirming.\n\n"
        "If you did not create this account, you can ignore this email.\n\n"
        "— The BookHaven Team"
    )

    await send_email(to_email, subject, body)