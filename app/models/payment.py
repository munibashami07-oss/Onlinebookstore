"""Payment ORM model strictly adhering to PCI DSS security guidelines."""

import enum
from typing import TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class PaymentStatus(str, enum.Enum):
    """Enumeration of payment transaction statuses."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Payment(Base, TimestampMixin):
    """Payment record model mapping to 'payments' table.
    
    SECURITY WARNING:
    Never store CVV, full credit card numbers, or expiration dates.
    Only store safe metadata: transaction_id, amount, payment_status, payment_method, currency, and last4.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    transaction_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    last4: Mapped[str] = mapped_column(String(4), nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="payment")

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} order_id={self.order_id} "
            f"tx_id='{self.transaction_id}' status='{self.payment_status}' last4='{self.last4}'>"
        )
