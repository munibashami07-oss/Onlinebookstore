"""Receipt generation utility for completed payment transactions."""

from datetime import datetime, timezone
from typing import Any, Dict


class ReceiptGenerator:
    """Utility class for formatting and generating digital payment receipts."""

    @staticmethod
    def generate_receipt(
        transaction_id: str,
        order_id: int,
        amount: float,
        currency: str,
        payment_method: str,
        last4: str,
    ) -> Dict[str, Any]:
        """Generate structured digital receipt metadata dictionary.

        Args:
            transaction_id: Payment transaction ID.
            order_id: Associated order ID.
            amount: Total payment amount.
            currency: ISO currency code.
            payment_method: Payment gateway/method.
            last4: Last 4 digits of card.

        Returns:
            Dict containing full digital receipt payload.
        """
        issued_at = datetime.now(timezone.utc).isoformat()
        receipt_number = f"RCP-{order_id:06d}-{transaction_id[:8].upper()}"

        return {
            "receipt_number": receipt_number,
            "transaction_id": transaction_id,
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "card_last4": last4,
            "status": "PAID",
            "issued_at": issued_at,
            "merchant_name": "Online Book Store",
            "support_email": "support@onlinebookstore.com",
        }
