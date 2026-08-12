"""Repository for PasswordResetToken database operations."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken


class PasswordResetRepository:
    """Data access layer for the PasswordResetToken model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_token(self, token: PasswordResetToken) -> PasswordResetToken:
        """Insert a new password reset token record."""
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token

    async def get_valid_token(self, token_hash: str) -> Optional[PasswordResetToken]:
        """Fetch a reset token by its hash, only if unused and unexpired."""
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def mark_used(self, token: PasswordResetToken) -> None:
        """Mark a token as used so it can't be redeemed again."""
        token.used_at = datetime.now(timezone.utc)
        await self.db.flush()