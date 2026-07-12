"""Pydantic v2 schemas for Order management."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus
from app.schemas.book import BookResponse
from app.schemas.payment import PaymentResponse


class OrderItemCreate(BaseModel):
    """Schema for individual order line items on creation."""

    book_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1)


class OrderItemResponse(BaseModel):
    """Schema for OrderItem API response."""

    id: int
    order_id: int
    book_id: int
    quantity: int = Field(..., ge=1)
    purchase_price: float = Field(..., gt=0)
    total_price: Optional[float] = None
    book: Optional[BookResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """Schema for creating a new checkout order."""

    shipping_address: str = Field(..., min_length=5, max_length=500)
    payment_method: str = Field("stripe", min_length=2, max_length=50)


class OrderResponse(BaseModel):
    """Schema for complete Order API response."""

    id: int
    user_id: int
    total_amount: float
    status: OrderStatus
    shipping_address: Optional[str] = None
    items: List[OrderItemResponse] = []
    payment: Optional[PaymentResponse] = None
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)