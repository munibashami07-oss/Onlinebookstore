"""Pydantic v2 schemas for Stationary products."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StationaryBase(BaseModel):
    """Base schema for Stationary product attributes."""

    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0, description="Price must be strictly positive")
    stock: int = Field(0, ge=0, description="Stock must be non-negative")
    cover_image_url: Optional[str] = Field(None, max_length=500)


class StationaryCreate(StationaryBase):
    """Schema for creating a new Stationary product."""

    pass


class StationaryUpdate(BaseModel):
    """Schema for updating a Stationary product."""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    cover_image_url: Optional[str] = Field(None, max_length=500)


class StationaryResponse(StationaryBase):
    """Schema for Stationary API responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
