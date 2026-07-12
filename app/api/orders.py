"""API Router for Customer Order History and Cancellation."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.order import OrderResponse
from app.services.order_service import OrderService, OrderServiceError

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get(
    "/me",
    response_model=List[OrderResponse],
    summary="Get current user's order history",
)
async def get_my_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[OrderResponse]:
    """Retrieve order history for the authenticated user only."""
    order_service = OrderService(db)
    skip = (page - 1) * page_size
    orders = await order_service.get_user_orders(current_user.id, skip=skip, limit=page_size)
    return orders


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel an order if not out for delivery or delivered",
)
async def cancel_my_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """Cancel an active order owned by the logged-in customer."""
    order_service = OrderService(db)
    try:
        updated_order = await order_service.cancel_user_order(order_id, current_user.id)
        return updated_order
    except OrderServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
