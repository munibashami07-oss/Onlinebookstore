"""Fraud detection stub for basic payment risk assessment."""

from typing import Any, Dict


class FraudDetector:
    """Fraud detection engine stub for evaluating transaction risk."""

    HIGH_RISK_AMOUNT_THRESHOLD = 5000.00  # Transactions > $5,000 flagged for manual review

    def evaluate_transaction(self, amount: float, payment_method: str) -> Dict[str, Any]:
        """Assess risk level for a proposed transaction.

        Args:
            amount: Transaction amount.
            payment_method: Selected payment method.

        Returns:
            Dict containing risk_score, is_approved, and risk_flag.
        """
        risk_score = 0.05  # Low baseline risk score

        if amount >= self.HIGH_RISK_AMOUNT_THRESHOLD:
            risk_score = 0.75
            return {
                "is_approved": True,
                "risk_score": risk_score,
                "risk_flag": "HIGH_VALUE_TRANSACTION",
                "recommendation": "FLAG_FOR_REVIEW",
            }

        return {
            "is_approved": True,
            "risk_score": risk_score,
            "risk_flag": "PASSED",
            "recommendation": "ALLOW",
        }
