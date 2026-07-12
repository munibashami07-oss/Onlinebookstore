"""Pydantic v2 schemas for Inventory management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class InventoryBase(BaseModel):
    """Base schema for Inventory."""

    book_id: int = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0, description="Stock quantity must be non-negative")
    low_stock_threshold: int = Field(5, ge=0)


class InventoryCreate(InventoryBase):
    """Schema for initializing inventory for a book."""

    pass


class InventoryUpdate(BaseModel):
    """Schema for updating inventory stock levels."""

    stock_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)


class InventoryResponse(InventoryBase):
    """Schema for Inventory API responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
