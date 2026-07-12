"""Service layer for inventory management and stock checking."""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.repositories.book_repository import BookRepository
from app.repositories.inventory_repository import InventoryRepository


class InventoryServiceError(Exception):
    """Base exception for InventoryService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class InventoryService:
    """Business logic for inventory tracking, stock adjustments, and availability checks."""

    def __init__(self, db: AsyncSession) -> None:
        self.inventory_repo = InventoryRepository(db)
        self.book_repo = BookRepository(db)

    async def get_stock(self, book_id: int) -> Inventory:
        """Fetch stock record for a given book.

        Args:
            book_id: Primary key of the book.

        Returns:
            Inventory ORM instance.

        Raises:
            InventoryServiceError: If book or inventory record not found.
        """
        book = await self.book_repo.get_book(book_id)
        if not book:
            raise InventoryServiceError("Book not found.", status_code=404)

        inventory = await self.inventory_repo.get_stock(book_id)
        if not inventory:
            # Auto-create initial zero stock inventory if missing
            inventory = Inventory(book_id=book_id, stock_quantity=0, low_stock_threshold=5)
            inventory = await self.inventory_repo.create(inventory)
        return inventory

    async def check_availability(self, book_id: int, requested_quantity: int) -> Dict[str, Any]:
        """Check if requested quantity of a book is available in stock.

        Args:
            book_id: Primary key of the book.
            requested_quantity: Quantity to check.

        Returns:
            Dict containing availability status, current stock, and low stock warning.
        """
        inventory = await self.get_stock(book_id)
        available = inventory.stock_quantity >= requested_quantity
        is_low_stock = inventory.stock_quantity <= inventory.low_stock_threshold

        return {
            "book_id": book_id,
            "requested_quantity": requested_quantity,
            "current_stock": inventory.stock_quantity,
            "available": available,
            "is_low_stock": is_low_stock,
        }

    async def increase_stock(self, book_id: int, quantity: int) -> Inventory:
        """Increase stock level for a book.

        Args:
            book_id: Primary key of the book.
            quantity: Quantity to add (must be > 0).

        Returns:
            Updated Inventory ORM instance.

        Raises:
            InventoryServiceError: If quantity is non-positive or book not found.
        """
        if quantity <= 0:
            raise InventoryServiceError("Quantity to add must be greater than zero.", status_code=400)

        inventory = await self.get_stock(book_id)
        updated = await self.inventory_repo.increase_stock(book_id, quantity)
        return updated or inventory

    async def decrease_stock(self, book_id: int, quantity: int) -> Inventory:
        """Decrease stock level for a book.

        Args:
            book_id: Primary key of the book.
            quantity: Quantity to subtract (must be > 0).

        Returns:
            Updated Inventory ORM instance.

        Raises:
            InventoryServiceError: If stock is insufficient or quantity non-positive.
        """
        if quantity <= 0:
            raise InventoryServiceError("Quantity to subtract must be greater than zero.", status_code=400)

        inventory = await self.get_stock(book_id)
        if inventory.stock_quantity < quantity:
            raise InventoryServiceError(
                f"Insufficient stock. Available: {inventory.stock_quantity}, Requested: {quantity}.",
                status_code=400,
            )

        updated = await self.inventory_repo.decrease_stock(book_id, quantity)
        return updated or inventory
