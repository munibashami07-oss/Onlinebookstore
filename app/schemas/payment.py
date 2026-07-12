"""Pydantic v2 schemas for Payment transaction safe view models."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentStatus


class PaymentResponse(BaseModel):
    """Safe payment response schema.
    
    SECURITY NOTE:
    Never expose CVV or full card numbers. last4 is strictly read-only metadata.
    """

    id: int
    order_id: int
    transaction_id: str
    amount: float = Field(..., gt=0)
    payment_status: PaymentStatus
    payment_method: str
    last4: str = Field(..., description="Read-only last 4 digits of payment card")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentStatusResponse(BaseModel):
    """Lightweight payment status check response."""

    transaction_id: str
    payment_status: PaymentStatus
    last4: str

    model_config = ConfigDict(from_attributes=True)
