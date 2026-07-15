"""Main API Router assembly including Payment Module endpoints."""

from fastapi import APIRouter

from app.api import (
    admin,
    auth,
    books,
    cart,
    chat,
    checkout,
    email_verification,
    genres,
    orders,
    payment,
    reviews,
    stationary,
    users,
    chatbot,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(books.router)
api_router.include_router(genres.router)
api_router.include_router(stationary.router)
api_router.include_router(reviews.router)
api_router.include_router(admin.router)
api_router.include_router(cart.router)
api_router.include_router(checkout.router)
api_router.include_router(orders.router)
api_router.include_router(payment.router)
api_router.include_router(chatbot.router)
api_router.include_router(chat.router)
api_router.include_router(chat.rest_router)
api_router.include_router(email_verification.router)