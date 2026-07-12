"""Pydantic v2 schemas for Shopping Cart management."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.book import BookResponse


class CartItemBase(BaseModel):
    """Base schema for CartItem."""

    book_id: int = Field(..., gt=0)
    quantity: int = Field(1, ge=1, description="Quantity must be at least 1")


class CartItemCreate(CartItemBase):
    """Schema for adding an item to the shopping cart."""

    pass


class CartItemUpdate(BaseModel):
    """Schema for updating cart item quantity."""

    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")


class CartItemResponse(CartItemBase):
    """Schema for CartItem response."""

    id: int
    cart_id: int
    price_at_add_time: float
    total_price: Optional[float] = None
    book: Optional[BookResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Schema for complete Cart API response."""

    id: int
    user_id: int
    items: List[CartItemResponse] = []
    total_amount: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
