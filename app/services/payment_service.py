"""Service layer for payment processing and payment gateway integration architecture."""

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.payments.card_validation import CardValidator
from app.payments.fraud_detection import FraudDetector
from app.payments.paypal import PayPalPaymentGateway
from app.payments.receipts import ReceiptGenerator
from app.payments.stripe import StripePaymentGateway
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository


class PaymentServiceError(Exception):
    """Base exception for PaymentService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class PaymentService:
    """Business logic for payment gateway interactions and receipt generation."""

    def __init__(self, db: AsyncSession) -> None:
        self.payment_repo = PaymentRepository(db)
        self.order_repo = OrderRepository(db)
        self.stripe_gateway = StripePaymentGateway()
        self.paypal_gateway = PayPalPaymentGateway()
        self.fraud_detector = FraudDetector()

    async def create_payment(
        self,
        order_id: int,
        payment_method: str = "stripe",
        card_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a pending payment transaction.

        SECURITY CONSTRAINTS:
        - NEVER store CVV, expiry date, or full card number.
        - Safely extract last4 digits using CardValidator.
        """
        order = await self.order_repo.get_order(order_id)
        if not order:
            raise PaymentServiceError("Order not found.", status_code=404)

        existing_payment = await self.payment_repo.get_by_order_id(order_id)
        if existing_payment:
            raise PaymentServiceError(
                "A payment transaction already exists for this order.", status_code=409
            )

        # Evaluate transaction risk using FraudDetector
        fraud_analysis = self.fraud_detector.evaluate_transaction(
            amount=float(order.total_amount), payment_method=payment_method
        )

       # Validate card number for card-based payment methods (skip for PayPal,
        # which never collects a card number here).
        if payment_method.lower() != "paypal":
            if not card_number or not CardValidator.validate_luhn(card_number):
                raise PaymentServiceError(
                    "Invalid card number. Please check the digits and try again.",
                    status_code=422,
                )

        # Safely extract last4 without keeping raw card data
        last4 = CardValidator.extract_last4(card_number) if card_number else "4242"

        # Select Gateway Provider
        if payment_method.lower() == "paypal":
            gateway_res = await self.paypal_gateway.create_payment_intent(
                amount=float(order.total_amount)
            )
        else:
            gateway_res = await self.stripe_gateway.create_payment_intent(
                amount=float(order.total_amount)
            )

        transaction_id = gateway_res["transaction_id"]

        # Persist ONLY safe metadata to database
        payment = Payment(
            order_id=order_id,
            transaction_id=transaction_id,
            amount=order.total_amount,
            currency="USD",
            payment_status=PaymentStatus.PENDING,
            payment_method=payment_method,
            last4=last4,
        )
        saved_payment = await self.payment_repo.create_payment(payment)

        return {
            "payment_id": saved_payment.id,
            "order_id": order_id,
            "transaction_id": transaction_id,
            "amount": float(saved_payment.amount),
            "currency": saved_payment.currency,
            "payment_status": saved_payment.payment_status.value,
            "payment_method": payment_method,
            "last4": last4,
            "gateway_details": gateway_res,
            "fraud_risk": fraud_analysis,
        }

    async def confirm_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Confirm a pending payment, update order status to PROCESSING, and generate receipt."""
        payment = await self.payment_repo.get_by_transaction_id(transaction_id)
        if not payment:
            raise PaymentServiceError("Payment transaction not found.", status_code=404)

        if payment.payment_status in (PaymentStatus.SUCCEEDED, PaymentStatus.COMPLETED):
            raise PaymentServiceError("Payment is already confirmed.", status_code=400)

        # Update payment status
        updated_payment = await self.payment_repo.update_payment_status(
            payment.id, PaymentStatus.SUCCEEDED
        )

        # Update Order status
        order = await self.order_repo.get_order(payment.order_id)
        if order:
            order.status = OrderStatus.PROCESSING
            await self.order_repo.update_order(order)

        # Generate Receipt
        receipt = ReceiptGenerator.generate_receipt(
            transaction_id=transaction_id,
            order_id=payment.order_id,
            amount=float(payment.amount),
            currency=payment.currency,
            payment_method=payment.payment_method,
            last4=payment.last4,
        )

        return {
            "status": "success",
            "message": "Payment confirmed successfully.",
            "transaction_id": transaction_id,
            "payment_status": PaymentStatus.SUCCEEDED.value,
            "order_status": OrderStatus.PROCESSING.value,
            "receipt": receipt,
        }

    async def cancel_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Cancel a pending payment transaction."""
        payment = await self.payment_repo.get_by_transaction_id(transaction_id)
        if not payment:
            raise PaymentServiceError("Payment transaction not found.", status_code=404)

        updated_payment = await self.payment_repo.update_payment_status(
            payment.id, PaymentStatus.CANCELLED
        )

        # Update Order status
        order = await self.order_repo.get_order(payment.order_id)
        if order:
            order.status = OrderStatus.CANCELLED
            await self.order_repo.update_order(order)

        return {
            "status": "cancelled",
            "message": "Payment transaction cancelled.",
            "transaction_id": transaction_id,
            "payment_status": PaymentStatus.CANCELLED.value,
            "order_status": OrderStatus.CANCELLED.value,
        }

    async def get_payment_details(self, transaction_id: str) -> Payment:
        """Fetch payment record by transaction ID."""
        payment = await self.payment_repo.get_by_transaction_id(transaction_id)
        if not payment:
            raise PaymentServiceError("Payment transaction not found.", status_code=404)
        return payment
