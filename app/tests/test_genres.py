"""Tests for Genre catalog endpoints: /genres."""

import pytest
from httpx import AsyncClient


# ── Public Read Endpoints ────────────────────────────────────────────────────

class TestGenresPublic:
    """Tests for public genre browsing."""

    @pytest.mark.asyncio
    async def test_list_genres_empty(self, client: AsyncClient):
        """GET /genres on empty catalog returns empty list."""
        response = await client.get("/genres")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_genres_with_data(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /genres returns created genres."""
        await client.post("/genres", json={"name": "Sci-Fi", "description": "Science Fiction"}, headers=admin_auth_headers)
        response = await client.get("/genres")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Sci-Fi"

    @pytest.mark.asyncio
    async def test_get_genre_by_id(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /genres/{id} returns genre details."""
        res = await client.post("/genres", json={"name": "Fantasy", "description": "Fantasy novels"}, headers=admin_auth_headers)
        genre = res.json()
        response = await client.get(f"/genres/{genre['id']}")
        assert response.status_code == 200
        assert response.json()["name"] == "Fantasy"

    @pytest.mark.asyncio
    async def test_get_genre_not_found(self, client: AsyncClient):
        """GET /genres/{id} for invalid ID returns 404."""
        response = await client.get("/genres/99999")
        assert response.status_code == 404


# ── Admin CRUD ───────────────────────────────────────────────────────────────

class TestGenresAdmin:
    """Tests for admin genre CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_genre_as_admin(self, client: AsyncClient, admin_auth_headers: dict):
        """POST /genres as admin returns 201."""
        response = await client.post("/genres", json={
            "name": "Horror",
            "description": "Horror novels",
        }, headers=admin_auth_headers)
        assert response.status_code == 201
        assert response.json()["name"] == "Horror"

    @pytest.mark.asyncio
    async def test_create_genre_as_customer(self, client: AsyncClient, user_auth_headers: dict):
        """POST /genres as customer returns 403."""
        response = await client.post("/genres", json={
            "name": "Fail",
            "description": "Should fail",
        }, headers=user_auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_genre_no_auth(self, client: AsyncClient):
        """POST /genres without auth returns 401."""
        response = await client.post("/genres", json={
            "name": "NoAuth",
            "description": "No auth",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_genre_duplicate_name(self, client: AsyncClient, admin_auth_headers: dict):
        """POST /genres with duplicate name returns 409."""
        await client.post("/genres", json={"name": "Romance", "description": "Romance"}, headers=admin_auth_headers)
        response = await client.post("/genres", json={"name": "Romance", "description": "Again"}, headers=admin_auth_headers)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_genre_missing_name(self, client: AsyncClient, admin_auth_headers: dict):
        """POST /genres without name returns 422."""
        response = await client.post("/genres", json={"description": "No name"}, headers=admin_auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_genre_as_admin(self, client: AsyncClient, admin_auth_headers: dict):
        """PUT /genres/{id} as admin returns updated genre."""
        res = await client.post("/genres", json={"name": "Old", "description": "Old genre"}, headers=admin_auth_headers)
        genre = res.json()
        response = await client.put(f"/genres/{genre['id']}", json={"name": "New Name"}, headers=admin_auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_genre_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """PUT /genres/{id} for non-existent ID returns 404."""
        response = await client.put("/genres/99999", json={"name": "Ghost"}, headers=admin_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_genre_as_admin(self, client: AsyncClient, admin_auth_headers: dict):
        """DELETE /genres/{id} as admin returns 204."""
        res = await client.post("/genres", json={"name": "ToDelete", "description": "Gone"}, headers=admin_auth_headers)
        genre = res.json()
        response = await client.delete(f"/genres/{genre['id']}", headers=admin_auth_headers)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_genre_as_customer(self, client: AsyncClient, user_auth_headers: dict, admin_auth_headers: dict):
        """DELETE /genres/{id} as customer returns 403."""
        res = await client.post("/genres", json={"name": "NoDelete", "description": "Nope"}, headers=admin_auth_headers)
        genre = res.json()
        response = await client.delete(f"/genres/{genre['id']}", headers=user_auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_genre_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """DELETE /genres/{id} for non-existent ID returns 404."""
        response = await client.delete("/genres/99999", headers=admin_auth_headers)
        assert response.status_code == 404
