"""Service layer for promotional deals and discount calculations."""

from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deal import Deal
from app.repositories.deal_repository import DealRepository


class DealServiceError(Exception):
    """Base exception for DealService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DealService:
    """Business logic for deals and price discount calculations."""

    def __init__(self, db: AsyncSession) -> None:
        self.deal_repo = DealRepository(db)

    async def get_active_deals(self, skip: int = 0, limit: int = 100) -> List[Deal]:
        """Fetch all currently active promotional deals.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of active Deal ORM instances.
        """
        all_active = await self.deal_repo.list_active(skip=skip, limit=limit)
        now = datetime.now(timezone.utc)
        
        # Filter deals active by date range
        valid_deals = [
            deal for deal in all_active
            if deal.start_date <= now <= deal.end_date
        ]
        return valid_deals

    async def calculate_discount(self, original_price: float, deal_id: int) -> Dict[str, Any]:
        """Calculate discounted price for a product under a specific deal.

        Args:
            original_price: Base price of the product.
            deal_id: Primary key of the deal.

        Returns:
            Dict containing original_price, discount_percentage, discount_amount, and final_price.

        Raises:
            DealServiceError: If deal is not found or expired.
        """
        deal = await self.deal_repo.get_by_id(deal_id)
        if not deal:
            raise DealServiceError("Deal not found.", status_code=404)

        now = datetime.now(timezone.utc)
        if not deal.is_active or not (deal.start_date <= now <= deal.end_date):
            raise DealServiceError("The requested deal is not currently active.", status_code=400)

        discount_pct = float(deal.discount_percentage)
        discount_amount = round((original_price * discount_pct) / 100.0, 2)
        final_price = max(0.0, round(original_price - discount_amount, 2))

        return {
            "deal_id": deal.id,
            "deal_title": deal.title,
            "original_price": original_price,
            "discount_percentage": discount_pct,
            "discount_amount": discount_amount,
            "final_price": final_price,
        }
