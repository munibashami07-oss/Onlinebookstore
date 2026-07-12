"""API Router for Payment Gateway operations and receipts."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.payment import PaymentResponse
from app.services.payment_service import PaymentService, PaymentServiceError

router = APIRouter(prefix="/payments", tags=["Payments"])


class CreatePaymentRequest(BaseModel):
    """Payload for creating a payment transaction."""

    order_id: int = Field(..., gt=0)
    payment_method: str = Field("stripe", min_length=2, max_length=50)
    card_number: Optional[str] = Field(None, max_length=19, description="Raw card for last4 extraction only - NEVER stored")


class PaymentActionRequest(BaseModel):
    """Payload for confirming or canceling a transaction."""

    transaction_id: str = Field(..., min_length=5, max_length=255)


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    summary="Create pending payment transaction",
)
async def create_payment(
    payload: CreatePaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Initialize a pending payment transaction for an order."""
    payment_service = PaymentService(db)
    try:
        return await payment_service.create_payment(
            order_id=payload.order_id,
            payment_method=payload.payment_method,
            card_number=payload.card_number,
        )
    except PaymentServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/confirm",
    summary="Confirm pending payment transaction",
)
async def confirm_payment(
    payload: PaymentActionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Confirm a pending payment transaction and generate digital receipt."""
    payment_service = PaymentService(db)
    try:
        return await payment_service.confirm_payment(payload.transaction_id)
    except PaymentServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/cancel",
    summary="Cancel pending payment transaction",
)
async def cancel_payment(
    payload: PaymentActionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Cancel a pending payment transaction."""
    payment_service = PaymentService(db)
    try:
        return await payment_service.cancel_payment(payload.transaction_id)
    except PaymentServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/{transaction_id}",
    response_model=PaymentResponse,
    summary="Get payment details by transaction ID",
)
async def get_payment_details(
    transaction_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    """Retrieve details of a payment transaction by transaction ID."""
    payment_service = PaymentService(db)
    try:
        payment = await payment_service.get_payment_details(transaction_id)
        return payment
    except PaymentServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
