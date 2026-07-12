"""Tests for Payment module endpoints: /payments."""

import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _create_test_order_id(client: AsyncClient, admin_headers: dict, user_headers: dict) -> int:
    """Helper to create an order ready for payment."""
    genre = await client.post("/genres", json={"name": "Payment Genre", "description": "Desc"}, headers=admin_headers)
    book = await client.post("/books", json={
        "title": "Payment Book",
        "author": "Author",
        "isbn": "9788888777666",
        "price": 40.00,
        "genre_id": genre.json()["id"],
    }, headers=admin_headers)
    book_id = book.json()["id"]
    await client.post(f"/admin/inventory/{book_id}/increase?quantity=5", headers=admin_headers)
    await client.post("/cart/items", json={"book_id": book_id, "quantity": 1}, headers=user_headers)
    checkout_res = await client.post("/checkout", json={
        "shipping_address": "500 Payment Ave",
        "payment_method": "stripe",
    }, headers=user_headers)
    return checkout_res.json()["order_id"]


# ── Payment Tests ────────────────────────────────────────────────────────────

class TestPayments:
    """Tests for /payments endpoints."""

    @pytest.mark.asyncio
    async def test_create_payment_success(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /payments/create creates pending transaction and extracts last4."""
        order_id = await _create_test_order_id(client, admin_auth_headers, user_auth_headers)

        response = await client.post("/payments/create", json={
            "order_id": order_id,
            "payment_method": "stripe",
            "card_number": "4111111111111111",
        }, headers=user_auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["order_id"] == order_id
        assert data["payment_status"] == "pending"
        assert data["last4"] == "1111"
        assert "transaction_id" in data
        # Security: full card number must NOT be in response
        assert "4111111111111111" not in str(data)

    @pytest.mark.asyncio
    async def test_create_payment_nonexistent_order(self, client: AsyncClient, user_auth_headers: dict):
        """POST /payments/create for non-existent order returns 404."""
        response = await client.post("/payments/create", json={
            "order_id": 99999,
            "payment_method": "stripe",
        }, headers=user_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_duplicate_payment(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /payments/create twice for same order returns 409."""
        order_id = await _create_test_order_id(client, admin_auth_headers, user_auth_headers)
        await client.post("/payments/create", json={"order_id": order_id, "payment_method": "stripe"}, headers=user_auth_headers)

        response = await client.post("/payments/create", json={"order_id": order_id, "payment_method": "stripe"}, headers=user_auth_headers)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_confirm_payment_success(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /payments/confirm confirms transaction and generates receipt."""
        order_id = await _create_test_order_id(client, admin_auth_headers, user_auth_headers)
        create_res = await client.post("/payments/create", json={"order_id": order_id, "payment_method": "stripe"}, headers=user_auth_headers)
        tx_id = create_res.json()["transaction_id"]

        response = await client.post("/payments/confirm", json={"transaction_id": tx_id}, headers=user_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["payment_status"] == "succeeded"
        assert data["order_status"] == "processing"
        assert "receipt" in data

    @pytest.mark.asyncio
    async def test_confirm_payment_already_confirmed(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /payments/confirm on already confirmed transaction returns 400."""
        order_id = await _create_test_order_id(client, admin_auth_headers, user_auth_headers)
        create_res = await client.post("/payments/create", json={"order_id": order_id, "payment_method": "stripe"}, headers=user_auth_headers)
        tx_id = create_res.json()["transaction_id"]

        await client.post("/payments/confirm", json={"transaction_id": tx_id}, headers=user_auth_headers)
        response = await client.post("/payments/confirm", json={"transaction_id": tx_id}, headers=user_auth_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_confirm_payment_not_found(self, client: AsyncClient, user_auth_headers: dict):
        """POST /payments/confirm for invalid transaction ID returns 404."""
        response = await client.post("/payments/confirm", json={"transaction_id": "tx_nonexistent_999"}, headers=user_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_payment(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /payments/cancel cancels pending transaction."""
        order_id = await _create_test_order_id(client, admin_auth_headers, user_auth_headers)
        create_res = await client.post("/payments/create", json={"order_id": order_id, "payment_method": "stripe"}, headers=user_auth_headers)
        tx_id = create_res.json()["transaction_id"]

        response = await client.post("/payments/cancel", json={"transaction_id": tx_id}, headers=user_auth_headers)
        assert response.status_code == 200
        assert response.json()["payment_status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_get_payment_details(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """GET /payments/{transaction_id} returns payment metadata."""
        order_id = await _create_test_order_id(client, admin_auth_headers, user_auth_headers)
        create_res = await client.post("/payments/create", json={"order_id": order_id, "payment_method": "stripe"}, headers=user_auth_headers)
        tx_id = create_res.json()["transaction_id"]

        response = await client.get(f"/payments/{tx_id}", headers=user_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == tx_id
        assert data["order_id"] == order_id
