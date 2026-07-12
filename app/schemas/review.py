"""Pydantic v2 schemas for Review management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReviewBase(BaseModel):
    """Base schema for Review attributes."""

    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
    review_text: Optional[str] = Field(None, max_length=2000)


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""

    book_id: int = Field(..., gt=0)


class ReviewUpdate(BaseModel):
    """Schema for updating an existing review."""

    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = Field(None, max_length=2000)


class ReviewResponse(ReviewBase):
    """Schema for Review API responses."""

    id: int
    user_id: int
    book_id: int
    reviewer_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
