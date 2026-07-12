"""Service layer for Admin dashboard metrics and analytics reporting."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from app.repositories.admin_repository import AdminRepository
from app.repositories.book_repository import BookRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository


class AdminServiceError(Exception):
    """Base exception for AdminService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AdminService:
    """Business logic for admin management and analytical reporting."""

    def __init__(self, db: AsyncSession) -> None:
        self.admin_repo = AdminRepository(db)
        self.book_repo = BookRepository(db)
        self.order_repo = OrderRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.user_repo = UserRepository(db)
        self.review_repo = ReviewRepository(db)

    async def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Aggregate comprehensive store metrics for admin dashboard.

        Returns:
            Dict containing detailed store metrics.
        """
        total_users = await self.admin_repo.count_users()
        total_books = await self.admin_repo.count_books()
        total_genres = await self.admin_repo.count_genres()
        total_stationary = await self.admin_repo.count_stationary()
        total_orders = await self.admin_repo.count_orders()
        total_revenue = await self.admin_repo.get_total_revenue()
        pending_orders = await self.admin_repo.count_orders_by_status(OrderStatus.PENDING)
        paid_orders = await self.admin_repo.count_orders_by_status(OrderStatus.PROCESSING) + await self.admin_repo.count_orders_by_status(OrderStatus.DELIVERED)
        failed_payments = await self.admin_repo.count_payments_by_status(PaymentStatus.FAILED)
        books_in_stock = await self.admin_repo.count_books_in_stock()
        low_stock_books = await self.admin_repo.count_books_low_stock()
        out_of_stock_books = await self.admin_repo.count_books_out_of_stock()
        active_deals = await self.admin_repo.count_active_deals()

        return {
            "total_users": total_users,
            "total_books": total_books,
            "total_genres": total_genres,
            "total_stationary": total_stationary,
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "pending_orders": pending_orders,
            "paid_orders": paid_orders,
            "failed_payments": failed_payments,
            "books_in_stock": books_in_stock,
            "low_stock_books": low_stock_books,
            "out_of_stock_books": out_of_stock_books,
            "active_deals": active_deals,
        }

    async def get_top_selling_books(
        self,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Return the top-selling books along with
        total units sold.
        """

        all_orders = await self.order_repo.list_all_orders(
            skip=0,
            limit=10000,
        )

        sales_counter: Dict[int, int] = {}

        for order in all_orders:
            for item in order.items:
                sales_counter[item.book_id] = (
                    sales_counter.get(item.book_id, 0)
                    + item.quantity
                )

        sorted_books = sorted(
            sales_counter.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:limit]

        results: List[Dict[str, Any]] = []

        for book_id, units_sold in sorted_books:

            book = await self.book_repo.get_book(book_id)

            if not book:
                continue

            results.append(
                {
                    "book_id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "units_sold": units_sold,
                }
            )

        return results
    async def get_top_rated_books(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Identify books with the highest average star ratings."""
        books = await self.book_repo.list_books(skip=0, limit=1000)
        rated_books = []

        for book in books:
            reviews = await self.review_repo.get_book_reviews(book.id, skip=0, limit=1000)
            if reviews:
                avg_rating = sum(r.rating for r in reviews) / float(len(reviews))
                rated_books.append({
                    "book_id": book.id,
                    "title": book.title,
                    "average_rating": round(avg_rating, 2),
                    "total_reviews": len(reviews),
                })

        sorted_books = sorted(rated_books, key=lambda x: (x["average_rating"], x["total_reviews"]), reverse=True)[:limit]
        return sorted_books

    async def get_most_purchased_genres(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Calculate sales volume aggregated by book genre."""
        all_orders = await self.order_repo.list_all_orders(skip=0, limit=1000)
        genre_sales: Dict[str, int] = {}

        for order in all_orders:
            for item in order.items:
                book = await self.book_repo.get_book(item.book_id)
                if book and book.genre:
                    genre_name = book.genre.name
                    genre_sales[genre_name] = genre_sales.get(genre_name, 0) + item.quantity

        sorted_genres = sorted(genre_sales.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"genre": g, "total_units_sold": qty} for g, qty in sorted_genres]

    async def get_revenue_report(self) -> Dict[str, Any]:
        """Calculate revenue broken down by daily, weekly, and monthly periods."""
        now = datetime.now(timezone.utc)
        one_day_ago = now - timedelta(days=1)
        one_week_ago = now - timedelta(days=7)
        one_month_ago = now - timedelta(days=30)

        all_orders = await self.order_repo.list_all_orders(skip=0, limit=5000)

        daily_rev = 0.0
        weekly_rev = 0.0
        monthly_rev = 0.0
        total_rev = 0.0

        for order in all_orders:
            amt = float(order.total_amount)
            total_rev += amt
            if order.created_at >= one_day_ago:
                daily_rev += amt
            if order.created_at >= one_week_ago:
                weekly_rev += amt
            if order.created_at >= one_month_ago:
                monthly_rev += amt

        return {
            "daily_revenue": round(daily_rev, 2),
            "weekly_revenue": round(weekly_rev, 2),
            "monthly_revenue": round(monthly_rev, 2),
            "total_revenue": round(total_rev, 2),
        }

    async def get_monthly_revenue(self) -> List[Dict[str, Any]]:
        """
        Return monthly revenue from July to December
        of the current year.
        """

        current_year = datetime.now(timezone.utc).year

        month_names = {
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dec",
        }

        monthly_revenue = {
            month: 0.0
            for month in month_names
        }

        all_orders = await self.order_repo.list_all_orders(
            skip=0,
            limit=10000
        )

        for order in all_orders:

            if order.created_at.year != current_year:
                continue

            month = order.created_at.month

            if month in monthly_revenue:
                monthly_revenue[month] += float(order.total_amount)

        return [
            {
                "month": month_names[m],
                "revenue": round(monthly_revenue[m], 2)
            }
            for m in sorted(monthly_revenue.keys())
        ]
    

    async def get_daily_sales(
        self,
        month: int,
    ) -> List[Dict[str, Any]]:
        """
        Return daily sales for a selected month
        of the current year.
        """

        current_year = datetime.now(timezone.utc).year

        all_orders = await self.order_repo.list_all_orders(
            skip=0,
            limit=10000
        )

        daily_sales: Dict[int, float] = {}

        for order in all_orders:

            if order.created_at.year != current_year:
                continue

            if order.created_at.month != month:
                continue

            day = order.created_at.day

            daily_sales[day] = (
                daily_sales.get(day, 0.0)
                + float(order.total_amount)
            )

        return [
            {
                "day": day,
                "sales": round(daily_sales[day], 2)
            }
            for day in sorted(daily_sales.keys())
        ]   