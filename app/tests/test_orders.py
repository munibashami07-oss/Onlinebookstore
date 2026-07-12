"""Tests for Order management endpoints and OrderService: /admin/orders."""

import pytest
from httpx import AsyncClient

from app.models.order import OrderStatus


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _create_test_order(client: AsyncClient, admin_headers: dict, user_headers: dict) -> int:
    """Helper to create an order via checkout."""
    genre = await client.post("/genres", json={"name": "Order Genre", "description": "Desc"}, headers=admin_headers)
    book = await client.post("/books", json={
        "title": "Order Book",
        "author": "Author",
        "isbn": "9781111222333",
        "price": 30.00,
        "genre_id": genre.json()["id"],
    }, headers=admin_headers)
    book_id = book.json()["id"]
    await client.post(f"/admin/inventory/{book_id}/increase?quantity=5", headers=admin_headers)
    await client.post("/cart/items", json={"book_id": book_id, "quantity": 1}, headers=user_headers)
    checkout_res = await client.post("/checkout", json={
        "shipping_address": "100 Order Street, City",
        "payment_method": "stripe",
    }, headers=user_headers)
    return checkout_res.json()["order_id"]


# ── Admin Orders Endpoints ───────────────────────────────────────────────────

class TestAdminOrders:
    """Tests for admin order management endpoints."""

    @pytest.mark.asyncio
    async def test_list_all_orders_as_admin(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """GET /admin/orders lists all orders for admin."""
        await _create_test_order(client, admin_auth_headers, user_auth_headers)
        response = await client.get("/admin/orders", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_all_orders_as_customer(self, client: AsyncClient, user_auth_headers: dict):
        """GET /admin/orders returns 403 for non-admin user."""
        response = await client.get("/admin/orders", headers=user_auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_order_details_as_admin(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """GET /admin/orders/{id} returns detailed order info."""
        order_id = await _create_test_order(client, admin_auth_headers, user_auth_headers)
        response = await client.get(f"/admin/orders/{order_id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_order_details_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /admin/orders/{id} for non-existent order returns 404."""
        response = await client.get("/admin/orders/99999", headers=admin_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_order_status_as_admin(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """PUT /admin/orders/{id}/status updates order processing status."""
        order_id = await _create_test_order(client, admin_auth_headers, user_auth_headers)
        response = await client.put(
            f"/admin/orders/{order_id}/status?order_status=shipped",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "shipped"

    @pytest.mark.asyncio
    async def test_update_order_status_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """PUT /admin/orders/{id}/status for non-existent order returns 404."""
        response = await client.put(
            "/admin/orders/99999/status?order_status=delivered",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404
