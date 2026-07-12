"""Tests for Admin Dashboard, CRUD, Inventory, Reports, and Security RBAC: /admin."""

import pytest
from httpx import AsyncClient


# ── Security & RBAC ──────────────────────────────────────────────────────────

class TestAdminRBAC:
    """Tests ensuring RBAC enforcement across admin endpoints."""

    @pytest.mark.asyncio
    async def test_dashboard_unauthenticated(self, client: AsyncClient):
        """GET /admin/dashboard without auth returns 401."""
        response = await client.get("/admin/dashboard")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_dashboard_customer_denied(self, client: AsyncClient, user_auth_headers: dict):
        """GET /admin/dashboard as customer returns 403."""
        response = await client.get("/admin/dashboard", headers=user_auth_headers)
        assert response.status_code == 403


# ── Dashboard & Analytics ───────────────────────────────────────────────────

class TestAdminDashboard:
    """Tests for GET /admin/dashboard."""

    @pytest.mark.asyncio
    async def test_get_dashboard_metrics(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /admin/dashboard as admin returns system metrics."""
        response = await client.get("/admin/dashboard", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_books" in data
        assert "total_orders" in data
        assert "total_revenue" in data


# ── Stationery Admin CRUD ───────────────────────────────────────────────────

class TestAdminStationery:
    """Tests for admin stationery endpoints."""

    @pytest.mark.asyncio
    async def test_create_stationery(self, client: AsyncClient, admin_auth_headers: dict):
        """POST /admin/stationery creates stationery item."""
        response = await client.post("/admin/stationery", json={
            "name": "Luxury Fountain Pen",
            "description": "Fine nib pen",
            "price": 45.00,
            "stock": 50,
        }, headers=admin_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Luxury Fountain Pen"
        assert data["price"] == 45.00

    @pytest.mark.asyncio
    async def test_list_stationery(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /admin/stationery lists all stationery items."""
        await client.post("/admin/stationery", json={
            "name": "Notebook A5",
            "price": 12.00,
            "stock": 20,
        }, headers=admin_auth_headers)
        response = await client.get("/admin/stationery", headers=admin_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    @pytest.mark.asyncio
    async def test_update_stationery(self, client: AsyncClient, admin_auth_headers: dict):
        """PUT /admin/stationery/{id} updates stationery item."""
        create_res = await client.post("/admin/stationery", json={
            "name": "Eraser",
            "price": 2.00,
            "stock": 100,
        }, headers=admin_auth_headers)
        item_id = create_res.json()["id"]

        response = await client.put(f"/admin/stationery/{item_id}", json={
            "price": 2.50,
        }, headers=admin_auth_headers)
        assert response.status_code == 200
        assert response.json()["price"] == 2.50

    @pytest.mark.asyncio
    async def test_delete_stationery(self, client: AsyncClient, admin_auth_headers: dict):
        """DELETE /admin/stationery/{id} deletes item."""
        create_res = await client.post("/admin/stationery", json={
            "name": "Ruler",
            "price": 1.50,
            "stock": 30,
        }, headers=admin_auth_headers)
        item_id = create_res.json()["id"]

        response = await client.delete(f"/admin/stationery/{item_id}", headers=admin_auth_headers)
        assert response.status_code == 204


# ── Deals ────────────────────────────────────────────────────────────────────

class TestAdminDeals:
    """Tests for GET /admin/deals."""

    @pytest.mark.asyncio
    async def test_list_deals(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /admin/deals returns active/inactive deals list."""
        response = await client.get("/admin/deals", headers=admin_auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ── Inventory Stock Management ──────────────────────────────────────────────

class TestAdminInventory:
    """Tests for stock adjustments and low stock report."""

    @pytest.mark.asyncio
    async def test_increase_and_decrease_stock(self, client: AsyncClient, admin_auth_headers: dict):
        """POST /admin/inventory/{book_id}/increase and decrease stock."""
        genre = await client.post("/genres", json={"name": "Inv Genre", "description": "D"}, headers=admin_auth_headers)
        book = await client.post("/books", json={
            "title": "Inv Book",
            "author": "Author",
            "isbn": "9781112223334",
            "price": 10.00,
            "genre_id": genre.json()["id"],
        }, headers=admin_auth_headers)
        book_id = book.json()["id"]

        # Increase
        inc_res = await client.post(f"/admin/inventory/{book_id}/increase?quantity=20", headers=admin_auth_headers)
        assert inc_res.status_code == 200
        assert inc_res.json()["stock_quantity"] == 20

        # Decrease
        dec_res = await client.post(f"/admin/inventory/{book_id}/decrease?quantity=5", headers=admin_auth_headers)
        assert dec_res.status_code == 200
        assert dec_res.json()["stock_quantity"] == 15

    @pytest.mark.asyncio
    async def test_low_stock_report(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /admin/inventory/low-stock returns low stock items."""
        response = await client.get("/admin/inventory/low-stock", headers=admin_auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ── Reports ──────────────────────────────────────────────────────────────────

class TestAdminReports:
    """Tests for admin analytical reports."""

    @pytest.mark.asyncio
    async def test_top_selling_books_report(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /admin/reports/top-selling-books returns sales report."""
        response = await client.get("/admin/reports/top-selling-books", headers=admin_auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_top_rated_books_report(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /admin/reports/top-rated-books returns ratings report."""
        response = await client.get("/admin/reports/top-rated-books", headers=admin_auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_most_purchased_genres_report(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /admin/reports/most-purchased-genres returns genre popularity report."""
        response = await client.get("/admin/reports/most-purchased-genres", headers=admin_auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_revenue_report(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /admin/reports/revenue returns revenue statistics."""
        response = await client.get("/admin/reports/revenue", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "daily_revenue" in data
        assert "weekly_revenue" in data
        assert "monthly_revenue" in data
