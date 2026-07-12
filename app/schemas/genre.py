"""Pydantic v2 schemas for Genre management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class GenreBase(BaseModel):
    """Base schema for Genre attributes."""

    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GenreCreate(GenreBase):
    """Schema for creating a new Genre."""

    pass


class GenreUpdate(BaseModel):
    """Schema for updating an existing Genre."""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GenreResponse(GenreBase):
    """Schema for Genre API responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
