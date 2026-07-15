"""Stateless JWT helpers for email verification links.

Assumes `python-jose` (jose.jwt) is already used elsewhere in
app/core/security.py, since that's the most common choice for
FastAPI + JWT projects. If this project instead uses PyJWT, swap
`from jose import jwt, JWTError` for `import jwt` and
`jwt.decode(..., algorithms=[...])` stays the same, but catch
`jwt.PyJWTError` instead of `JWTError`.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings

EMAIL_VERIFICATION_PURPOSE = "email_verification"


def create_email_verification_token(email: str) -> str:
    """Create a short-lived, stateless JWT used to confirm an email address.

    No database storage needed — the token itself is validated (signature +
    expiry + purpose claim) when the user clicks the link.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
    )
    payload = {
        "sub": email,
        "purpose": EMAIL_VERIFICATION_PURPOSE,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_email_verification_token(token: str) -> Optional[str]:
    """Validate a verification token and return the email it was issued for.

    Returns None if the token is invalid, expired, or issued for a different
    purpose (defense against reusing an access/refresh token here).
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        return None

    if payload.get("purpose") != EMAIL_VERIFICATION_PURPOSE:
        return None

    return payload.get("sub")