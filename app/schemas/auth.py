"""Pydantic v2 schemas for Authentication workflows."""

import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Registration request payload."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength (min 8 chars, 1 uppercase, 1 lowercase, 1 digit)."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class LoginRequest(BaseModel):
    """User login request payload."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """JWT Token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    """Refresh token request payload."""

    refresh_token: str = Field(..., min_length=1)


class RefreshTokenResponse(BaseModel):
    """Refreshed access token response."""

    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    """Decoded JWT payload structure."""

    sub: Optional[str] = None
    type: Optional[str] = None
    exp: Optional[int] = None
