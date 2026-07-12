"""API Router for Checkout operations."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.order import OrderCreate
from app.services.checkout_service import CheckoutService, CheckoutServiceError

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Process checkout and generate order summary",
)
async def checkout(
    payload: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Execute atomic checkout:
    1. Validates user authentication.
    2. Validates shopping cart is not empty.
    3. Validates inventory stock availability (prevents overselling).
    4. Creates Order and OrderItems.
    5. Reserves inventory / decreases stock levels.
    6. Empties shopping cart.
    7. Returns complete Order Summary prepared for payment.
    """
    checkout_service = CheckoutService(db)
    try:
        order_summary = await checkout_service.process_checkout(current_user.id, payload)
        return order_summary
    except CheckoutServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
