"""Payment Gateway abstraction interface and Stripe integration placeholder."""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict


class PaymentGateway(ABC):
    """Abstract Base Class interface for external Payment Gateways."""

    @abstractmethod
    async def create_payment_intent(
        self, amount: float, currency: str = "USD", metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a payment intent / token with external provider."""
        pass

    @abstractmethod
    async def confirm_payment_intent(self, transaction_id: str) -> Dict[str, Any]:
        """Confirm a pending payment intent."""
        pass

    @abstractmethod
    async def cancel_payment_intent(self, transaction_id: str) -> Dict[str, Any]:
        """Cancel a pending payment intent."""
        pass


class StripePaymentGateway(PaymentGateway):
    """Production-ready Stripe Payment Gateway placeholder integration."""

    def __init__(self, secret_key: str = "sk_test_placeholder") -> None:
        self.secret_key = secret_key

    async def create_payment_intent(
        self, amount: float, currency: str = "USD", metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Simulate creating a Stripe PaymentIntent (pi_...) object."""
        intent_id = f"pi_stripe_{uuid.uuid4().hex[:16]}"
        client_secret = f"{intent_id}_secret_{uuid.uuid4().hex[:8]}"

        return {
            "gateway": "stripe",
            "transaction_id": intent_id,
            "client_secret": client_secret,
            "amount": amount,
            "currency": currency,
            "status": "pending",
        }

    async def confirm_payment_intent(self, transaction_id: str) -> Dict[str, Any]:
        """Simulate Stripe webhook/confirmation handler."""
        return {
            "gateway": "stripe",
            "transaction_id": transaction_id,
            "status": "succeeded",
        }

    async def cancel_payment_intent(self, transaction_id: str) -> Dict[str, Any]:
        """Simulate canceling a Stripe PaymentIntent."""
        return {
            "gateway": "stripe",
            "transaction_id": transaction_id,
            "status": "cancelled",
        }
