"""Repository for Payment database operations."""

from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus


class PaymentRepository:
    """Data access layer for the Payment model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_payment(self, payment: Payment) -> Payment:
        """Insert a new payment transaction record."""
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """Fetch a payment record by primary key."""
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_order_id(self, order_id: int) -> Optional[Payment]:
        """Fetch a payment record by order foreign key."""
        stmt = select(Payment).where(Payment.order_id == order_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """Fetch a payment record by transaction_id."""
        stmt = select(Payment).where(Payment.transaction_id == transaction_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_payment_status(
        self, payment_id: int, status: PaymentStatus
    ) -> Optional[Payment]:
        """Update payment_status for a given payment record."""
        stmt = (
            update(Payment)
            .where(Payment.id == payment_id)
            .values(payment_status=status)
            .returning(Payment)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        row = result.scalars().first()
        if row:
            await self.db.refresh(row)
        return row
