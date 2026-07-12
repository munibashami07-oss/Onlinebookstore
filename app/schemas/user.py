"""Pydantic v2 schemas for User management."""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base schema for User models."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    is_active: Optional[bool] = True
    role: Optional[UserRole] = UserRole.CUSTOMER


class UserCreate(UserBase):
    """User creation schema with password strength validation."""

    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password contains uppercase, lowercase, and numeric characters."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class UserUpdate(BaseModel):
    """User profile update schema."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format if provided."""
        if v is not None:
            cleaned = re.sub(r"[\s\-\(\)\+]", "", v)
            if not cleaned.isdigit() or len(cleaned) < 7 or len(cleaned) > 15:
                raise ValueError("Invalid phone number format.")
        return v


class UserResponse(UserBase):
    """User API response model excluding sensitive password hashes."""

    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    """Publicly safe user attributes for embedded responses."""

    id: int
    full_name: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
