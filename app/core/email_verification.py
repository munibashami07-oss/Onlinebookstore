"""Endpoint for confirming a user's email address via a signed link."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.core.email_verification import decode_email_verification_token
from app.repositories.user_repository import UserRepository

router = APIRouter()


@router.get("/verify-email", response_class=PlainTextResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Validate a verification token and mark the corresponding user verified."""
    email = decode_email_verification_token(token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has expired.",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found for this verification link.",
        )

    if not user.is_verified:
        user.is_verified = True
        await user_repo.update_user(user)

    return "Your email has been confirmed. You can close this tab."