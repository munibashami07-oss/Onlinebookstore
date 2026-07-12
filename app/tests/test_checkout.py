"""Tests for Checkout endpoints: /checkout."""

import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _setup_cart_with_item(client: AsyncClient, admin_headers: dict, user_headers: dict, qty: int = 2) -> int:
    """Helper to create genre, book, stock, and add item to cart."""
    genre = await client.post("/genres", json={"name": "Checkout Genre", "description": "Desc"}, headers=admin_headers)
    book = await client.post("/books", json={
        "title": "Checkout Book",
        "author": "Author",
        "isbn": "9789999999999",
        "price": 25.00,
        "genre_id": genre.json()["id"],
    }, headers=admin_headers)
    book_id = book.json()["id"]
    await client.post(f"/admin/inventory/{book_id}/increase?quantity=10", headers=admin_headers)
    await client.post("/cart/items", json={"book_id": book_id, "quantity": qty}, headers=user_headers)
    return book_id


# ── Checkout Tests ────────────────────────────────────────────────────────────

class TestCheckout:
    """Tests for POST /checkout."""

    @pytest.mark.asyncio
    async def test_checkout_empty_cart(self, client: AsyncClient, user_auth_headers: dict):
        """POST /checkout with an empty cart returns 400 error."""
        response = await client.post("/checkout", json={
            "shipping_address": "123 Test Street, Test City, 12345",
            "payment_method": "stripe",
        }, headers=user_auth_headers)
        assert response.status_code == 400
        assert "empty cart" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_checkout_unauthenticated(self, client: AsyncClient):
        """POST /checkout without authentication returns 401."""
        response = await client.post("/checkout", json={
            "shipping_address": "123 Test Street",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_checkout_success(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /checkout with valid items creates order, clears cart, and returns order summary."""
        book_id = await _setup_cart_with_item(client, admin_auth_headers, user_auth_headers, qty=2)

        response = await client.post("/checkout", json={
            "shipping_address": "123 Main Street, Suite 400",
            "payment_method": "stripe",
        }, headers=user_auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert "order_id" in data
        assert data["order_number"].startswith("ORD-")
        assert data["status"] == "pending"
        assert len(data["purchased_items"]) == 1
        assert data["purchased_items"][0]["book_id"] == book_id
        assert data["grand_total"] > 0

        # Verify cart is cleared
        cart_res = await client.get("/cart", headers=user_auth_headers)
        assert cart_res.json()["items"] == []

    @pytest.mark.asyncio
    async def test_checkout_invalid_payload(self, client: AsyncClient, user_auth_headers: dict):
        """POST /checkout with short/missing address fails schema validation (422)."""
        response = await client.post("/checkout", json={
            "shipping_address": "12",  # Under 5 chars
        }, headers=user_auth_headers)
        assert response.status_code == 422
