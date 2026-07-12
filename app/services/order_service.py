"""Service layer for order management operations."""

from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.repositories.order_repository import OrderRepository


class OrderServiceError(Exception):
    """Base exception for OrderService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class OrderService:
    """Business logic for customer orders and admin order management."""

    def __init__(self, db: AsyncSession) -> None:
        self.order_repo = OrderRepository(db)

    async def get_order_details(self, order_id: int) -> Order:
        """Fetch details of an order by ID.

        Args:
            order_id: Primary key of the order.

        Returns:
            Order ORM instance.

        Raises:
            OrderServiceError: If order is not found.
        """
        order = await self.order_repo.get_order(order_id)
        if not order:
            raise OrderServiceError("Order not found.", status_code=404)
        return order

    async def get_user_orders(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Fetch paginated orders for a user.

        Args:
            user_id: Primary key of the user.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of Order ORM instances.
        """
        return await self.order_repo.get_user_orders(user_id, skip=skip, limit=limit)

    async def list_all_orders(
        self, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Fetch paginated list of all orders (Admin only)."""
        return await self.order_repo.list_all_orders(skip=skip, limit=limit)

    async def update_order_status(
        self, order_id: int, new_status: OrderStatus
    ) -> Order:
        """Update processing status of an order (Admin only).

        Args:
            order_id: Primary key of the order.
            new_status: Target OrderStatus enum value.

        Returns:
            Updated Order ORM instance.

        Raises:
            OrderServiceError: If order is not found, or the order has
                already been cancelled and can no longer be modified.
        """
        order = await self.order_repo.get_order(order_id)
        if not order:
            raise OrderServiceError("Order not found.", status_code=404)

        if order.status == OrderStatus.CANCELLED:
            raise OrderServiceError(
                "This order has been cancelled and its status can no longer be changed.",
                status_code=400,
            )

        # Stamp delivered_at exactly once, the first time the order reaches
        # DELIVERED. Re-saving/updating afterwards must not overwrite it.
        if new_status == OrderStatus.DELIVERED and order.delivered_at is None:
            order.delivered_at = datetime.now(timezone.utc)

        order.status = new_status
        return await self.order_repo.update_order(order)

    async def cancel_user_order(self, order_id: int, user_id: int) -> Order:
        """Cancel an order owned by a customer if eligible.

        Args:
            order_id: Primary key of the order.
            user_id: Primary key of the requesting authenticated user.

        Returns:
            Updated Order instance with status CANCELLED.

        Raises:
            OrderServiceError: If order not found, not owned by user, or
                the order is not currently pending (only pending orders
                are eligible for customer-initiated cancellation).
        """
        order = await self.order_repo.get_order(order_id)
        if not order:
            raise OrderServiceError("Order not found.", status_code=404)
        if order.user_id != user_id:
            raise OrderServiceError("Unauthorized access to order.", status_code=403)

        if order.status != OrderStatus.PENDING:
            raise OrderServiceError(
                "Only pending orders can be cancelled.", status_code=400
            )

        order.status = OrderStatus.CANCELLED
        return await self.order_repo.update_order(order)