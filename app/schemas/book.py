"""Pydantic v2 schemas for Book catalog management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class InventoryResponse(BaseModel):
    """Minimal inventory info nested inside Book responses."""

    stock_quantity: int
    low_stock_threshold: int

    model_config = ConfigDict(from_attributes=True)


class BookBase(BaseModel):
    """Base schema for Book attributes."""

    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=10, max_length=20)
    price: float = Field(..., gt=0, description="Book price must be strictly positive")
    description: Optional[str] = None
    cover_image_url: Optional[str] = Field(None, max_length=500)
    genre_id: int = Field(..., gt=0)


class BookCreate(BookBase):
    """Schema for creating a new Book record."""

    pass


class BookUpdate(BaseModel):
    """Schema for updating an existing Book record."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, min_length=10, max_length=20)
    price: Optional[float] = Field(None, gt=0, description="Price must be positive if updated")
    description: Optional[str] = None
    cover_image_url: Optional[str] = Field(None, max_length=500)
    genre_id: Optional[int] = Field(None, gt=0)


class BookResponse(BookBase):
    """Schema for Book API responses."""

    id: int
    created_at: datetime
    updated_at: datetime
    inventory: Optional[InventoryResponse] = None

    model_config = ConfigDict(from_attributes=True)