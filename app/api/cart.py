"""API Router for Shopping Cart operations."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate
from app.services.cart_service import CartService, CartServiceError

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


@router.get(
    "",
    summary="Get current user shopping cart with subtotal, tax, and estimated total",
)
async def get_my_cart(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve current user's shopping cart and summary metrics."""
    cart_service = CartService(db)
    return await cart_service.get_cart_summary(current_user.id)


@router.post(
    "/items",
    status_code=status.HTTP_201_CREATED,
    summary="Add item to shopping cart",
)
async def add_item_to_cart(
    payload: CartItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Add a book to shopping cart after validating stock availability."""
    cart_service = CartService(db)
    try:
        item = await cart_service.add_item(current_user.id, payload)
        return {
            "status": "success",
            "message": "Item added to cart successfully.",
            "item_id": item.id,
            "book_id": item.book_id,
            "quantity": item.quantity,
            "price_at_add_time": float(item.price_at_add_time),
        }
    except CartServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put(
    "/items/{item_id}",
    summary="Update quantity of an item in shopping cart",
)
async def update_cart_item_quantity(
    item_id: int,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Update item quantity in user cart after validating inventory."""
    cart_service = CartService(db)
    try:
        item = await cart_service.update_quantity(current_user.id, item_id, payload)
        return {
            "status": "success",
            "message": "Cart item quantity updated.",
            "item_id": item.id,
            "quantity": item.quantity,
        }
    except CartServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an item from shopping cart",
)
async def remove_item_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a specific item from shopping cart."""
    cart_service = CartService(db)
    try:
        await cart_service.remove_item(current_user.id, item_id)
    except CartServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete(
    "/clear",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear all items from shopping cart",
)
async def clear_shopping_cart(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Clear all items from current user's cart."""
    cart_service = CartService(db)
    await cart_service.clear_cart(current_user.id)
