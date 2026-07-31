"""Simple SMTP email-sending utility (Gmail SMTP).

Uses the GMAIL_ADDRESS / GMAIL_APP_PASSWORD settings already defined in
app/core/config.py. GMAIL_APP_PASSWORD must be a Gmail *App Password*
(Google Account -> Security -> 2-Step Verification -> App Passwords),
not your normal Gmail login password -- Gmail blocks plain SMTP auth
with regular account passwords.

Sending runs in a threadpool (smtplib is blocking) so it never blocks
the async event loop -- same pattern already used for RAG warmup in
main.py (run_in_threadpool).
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from starlette.concurrency import run_in_threadpool

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_email_sync(to_email: str, subject: str, html_body: str) -> None:
    if not settings.GMAIL_ADDRESS or not settings.GMAIL_APP_PASSWORD:
        logger.warning(
            "GMAIL_ADDRESS / GMAIL_APP_PASSWORD not configured -- skipping email to %s",
            to_email,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.GMAIL_ADDRESS
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.GMAIL_ADDRESS, settings.GMAIL_APP_PASSWORD)
        server.sendmail(settings.GMAIL_ADDRESS, to_email, msg.as_string())


async def send_email(to_email: str, subject: str, html_body: str) -> None:
    """Send an email without blocking the event loop.

    Failures are logged, never raised -- a broken/unconfigured mail
    server should never break registration or any other request that
    happens to trigger a notification email.
    """
    try:
        await run_in_threadpool(_send_email_sync, to_email, subject, html_body)
    except Exception:
        logger.exception("Failed to send email to %s", to_email)


async def send_registration_confirmation_email(to_email: str, full_name: str) -> None:
    """Send a welcome / account-confirmation email right after signup."""
    subject = f"Welcome to {settings.PROJECT_NAME} — your account is confirmed"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; color: #1e293b;">
      <h2 style="color: #4f46e5;">Welcome, {full_name}!</h2>
      <p>Your account with <strong>{settings.PROJECT_NAME}</strong> has been created successfully.</p>
      <p>You can now sign in and start browsing our catalog.</p>
      <p style="margin-top: 24px; color: #64748b; font-size: 0.85rem;">
        If you didn't create this account, you can safely ignore this email.
      </p>
    </div>
    """
    await send_email(to_email, subject, html_body)