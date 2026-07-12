"""Repository for Admin database operations and dashboard queries."""

from typing import List, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.models.book import Book
from app.models.deal import Deal
from app.models.genre import Genre
from app.models.inventory import Inventory
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.stationary import Stationary
from app.models.user import User


class AdminRepository:
    """Data access layer for the Admin model and dashboard aggregations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---- CRUD ----

    async def create(self, admin: Admin) -> Admin:
        """Insert a new admin record."""
        self.db.add(admin)
        await self.db.flush()
        await self.db.refresh(admin)
        return admin

    async def get_by_id(self, admin_id: int) -> Optional[Admin]:
        """Fetch a single admin by primary key."""
        stmt = select(Admin).where(Admin.id == admin_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[Admin]:
        """Fetch a single admin by email."""
        stmt = select(Admin).where(Admin.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[Admin]:
        """Fetch a single admin by username."""
        stmt = select(Admin).where(Admin.username == username)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_all(
        self, skip: int = 0, limit: int = 100
    ) -> List[Admin]:
        """Fetch a paginated list of admins."""
        stmt = select(Admin).offset(skip).limit(limit).order_by(Admin.id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, admin: Admin) -> Admin:
        """Persist changes to an existing admin."""
        await self.db.flush()
        await self.db.refresh(admin)
        return admin

    async def delete(self, admin_id: int) -> None:
        """Delete an admin by primary key."""
        stmt = delete(Admin).where(Admin.id == admin_id)
        await self.db.execute(stmt)
        await self.db.flush()

    # ---- Dashboard Aggregations ----

    async def count_users(self) -> int:
        """Return total number of registered users."""
        stmt = select(func.count()).select_from(User)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_books(self) -> int:
        """Return total number of books in catalogue."""
        stmt = select(func.count()).select_from(Book)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_genres(self) -> int:
        """Return total number of genres."""
        stmt = select(func.count()).select_from(Genre)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_stationary(self) -> int:
        """Return total number of stationary products."""
        stmt = select(func.count()).select_from(Stationary)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_orders(self) -> int:
        """Return total number of orders placed."""
        stmt = select(func.count()).select_from(Order)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_orders_by_status(self, status: OrderStatus) -> int:
        """Return total orders matching a specific status."""
        stmt = select(func.count()).select_from(Order).where(Order.status == status)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_payments_by_status(self, status: PaymentStatus) -> int:
        """Return total payments matching a specific status."""
        stmt = select(func.count()).select_from(Payment).where(Payment.payment_status == status)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_total_revenue(self) -> float:
        """Return sum of all order totals."""
        stmt = select(func.coalesce(func.sum(Order.total_amount), 0))
        result = await self.db.execute(stmt)
        return float(result.scalar_one())

    async def count_books_in_stock(self) -> int:
        """Count books with stock > low_stock_threshold."""
        stmt = select(func.count()).select_from(Inventory).where(Inventory.stock_quantity > Inventory.low_stock_threshold)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_books_low_stock(self) -> int:
        """Count books with stock > 0 and stock <= low_stock_threshold."""
        stmt = select(func.count()).select_from(Inventory).where(
            Inventory.stock_quantity > 0,
            Inventory.stock_quantity <= Inventory.low_stock_threshold,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_books_out_of_stock(self) -> int:
        """Count books with stock == 0."""
        stmt = select(func.count()).select_from(Inventory).where(Inventory.stock_quantity == 0)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_active_deals(self) -> int:
        """Count active deals."""
        stmt = select(func.count()).select_from(Deal).where(Deal.is_active.is_(True))
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_low_stock_inventory(self, skip: int = 0, limit: int = 100) -> List[Inventory]:
        """Fetch list of inventory records with stock <= low_stock_threshold."""
        stmt = select(Inventory).where(Inventory.stock_quantity <= Inventory.low_stock_threshold).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
