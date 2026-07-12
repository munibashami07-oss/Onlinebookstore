"""JWT token creation, decoding, and verification utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT Access Token.

    Args:
        subject: Unique identifier for token subject (e.g. user_id).
        expires_delta: Optional custom expiration timedelta.

    Returns:
        Encoded JWT access token string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode: Dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT Refresh Token.

    Args:
        subject: Unique identifier for token subject (e.g. user_id).
        expires_delta: Optional custom expiration timedelta.

    Returns:
        Encoded JWT refresh token string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode: Dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str, secret_key: str) -> Optional[Dict[str, Any]]:
    """Decode and parse JWT payload using specified secret key.

    Args:
        token: Raw JWT token string.
        secret_key: Secret key used for signing verification.

    Returns:
        Decoded payload dict or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token, secret_key, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and validate a JWT token of specified type.

    Args:
        token: Raw JWT token string.
        token_type: Target token type ('access' or 'refresh').

    Returns:
        Validated payload dict or None if validation fails.
    """
    secret = (
        settings.SECRET_KEY
        if token_type == "access"
        else settings.REFRESH_SECRET_KEY
    )
    payload = decode_token(token, secret)
    if payload and payload.get("type") == token_type:
        return payload
    return None
