"""Tests for Shopping Cart endpoints: /cart."""

import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _setup_book_and_stock(client: AsyncClient, admin_headers: dict, stock_qty: int = 10) -> int:
    """Helper to create genre, book, and increase stock for testing cart."""
    genre = await client.post("/genres", json={"name": "Cart Genre", "description": "Desc"}, headers=admin_headers)
    book = await client.post("/books", json={
        "title": "Cart Book",
        "author": "Cart Author",
        "isbn": "9781234567890",
        "price": 20.00,
        "genre_id": genre.json()["id"],
    }, headers=admin_headers)
    book_id = book.json()["id"]
    if stock_qty > 0:
        await client.post(f"/admin/inventory/{book_id}/increase?quantity={stock_qty}", headers=admin_headers)
    return book_id


# ── Cart Endpoints ────────────────────────────────────────────────────────────

class TestCartEndpoints:
    """Tests for /cart endpoints."""

    @pytest.mark.asyncio
    async def test_get_cart_empty(self, client: AsyncClient, user_auth_headers: dict):
        """GET /cart returns empty cart summary for user."""
        response = await client.get("/cart", headers=user_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["subtotal"] == 0.0
        assert data["tax"] == 0.0
        assert data["estimated_total"] == 0.0

    @pytest.mark.asyncio
    async def test_get_cart_unauthenticated(self, client: AsyncClient):
        """GET /cart without token returns 401."""
        response = await client.get("/cart")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_add_item_to_cart_success(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /cart/items adds book to user's cart."""
        book_id = await _setup_book_and_stock(client, admin_auth_headers, stock_qty=10)
        response = await client.post("/cart/items", json={
            "book_id": book_id,
            "quantity": 2,
        }, headers=user_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["quantity"] == 2
        assert data["price_at_add_time"] == 20.0

    @pytest.mark.asyncio
    async def test_add_item_insufficient_stock(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /cart/items with quantity > available stock returns 400."""
        book_id = await _setup_book_and_stock(client, admin_auth_headers, stock_qty=2)
        response = await client.post("/cart/items", json={
            "book_id": book_id,
            "quantity": 5,
        }, headers=user_auth_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_item_nonexistent_book(self, client: AsyncClient, user_auth_headers: dict):
        """POST /cart/items for non-existent book returns 404."""
        response = await client.post("/cart/items", json={
            "book_id": 99999,
            "quantity": 1,
        }, headers=user_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_cart_item_quantity(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """PUT /cart/items/{id} updates cart item quantity."""
        book_id = await _setup_book_and_stock(client, admin_auth_headers, stock_qty=10)
        add_res = await client.post("/cart/items", json={"book_id": book_id, "quantity": 1}, headers=user_auth_headers)
        item_id = add_res.json()["item_id"]

        response = await client.put(f"/cart/items/{item_id}", json={"quantity": 3}, headers=user_auth_headers)
        assert response.status_code == 200
        assert response.json()["quantity"] == 3

    @pytest.mark.asyncio
    async def test_remove_cart_item(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """DELETE /cart/items/{id} removes item from cart."""
        book_id = await _setup_book_and_stock(client, admin_auth_headers, stock_qty=10)
        add_res = await client.post("/cart/items", json={"book_id": book_id, "quantity": 1}, headers=user_auth_headers)
        item_id = add_res.json()["item_id"]

        response = await client.delete(f"/cart/items/{item_id}", headers=user_auth_headers)
        assert response.status_code == 204

        cart_res = await client.get("/cart", headers=user_auth_headers)
        assert cart_res.json()["items"] == []

    @pytest.mark.asyncio
    async def test_clear_cart(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """DELETE /cart/clear empties the entire cart."""
        book_id = await _setup_book_and_stock(client, admin_auth_headers, stock_qty=10)
        await client.post("/cart/items", json={"book_id": book_id, "quantity": 2}, headers=user_auth_headers)

        response = await client.delete("/cart/clear", headers=user_auth_headers)
        assert response.status_code == 204

        cart_res = await client.get("/cart", headers=user_auth_headers)
        assert cart_res.json()["items"] == []
