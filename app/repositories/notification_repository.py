"""Repository for Notification database operations."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    """Data access layer for the Notification model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_notification(self, notification: Notification) -> Notification:
        """Insert a new notification record."""
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def get_user_notifications(
        self, user_id: int, skip: int = 0, limit: int = 50
    ) -> List[Notification]:
        """Fetch a paginated list of notifications for a user, newest first."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: int) -> int:
        """Count all unread notifications for a user."""
        stmt = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        """Mark a single notification as read, scoped to its owning user.

        The `user_id` filter prevents one user from marking another user's
        notification as read even if they guess the ID.
        """
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
            .returning(Notification)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.scalars().first()

    async def mark_all_as_read(self, user_id: int) -> None:
        """Mark every unread notification for a user as read."""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.flush()
