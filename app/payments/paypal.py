"""PayPal Payment Gateway integration placeholder."""

import uuid
from typing import Any, Dict

from app.payments.stripe import PaymentGateway


class PayPalPaymentGateway(PaymentGateway):
    """PayPal Payment Gateway placeholder implementation."""

    def __init__(self, client_id: str = "paypal_client_placeholder") -> None:
        self.client_id = client_id

    async def create_payment_intent(
        self, amount: float, currency: str = "USD", metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Simulate creating a PayPal order token."""
        order_id = f"PAYPAL-ORDER-{uuid.uuid4().hex[:12].upper()}"
        return {
            "gateway": "paypal",
            "transaction_id": order_id,
            "approval_url": f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}",
            "amount": amount,
            "currency": currency,
            "status": "pending",
        }

    async def confirm_payment_intent(self, transaction_id: str) -> Dict[str, Any]:
        """Simulate capturing PayPal order payment."""
        return {
            "gateway": "paypal",
            "transaction_id": transaction_id,
            "status": "succeeded",
        }

    async def cancel_payment_intent(self, transaction_id: str) -> Dict[str, Any]:
        """Simulate canceling a PayPal order."""
        return {
            "gateway": "paypal",
            "transaction_id": transaction_id,
            "status": "cancelled",
        }
