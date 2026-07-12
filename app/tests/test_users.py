"""Tests for User profile endpoints: /users/me, /users, /users/{id}."""

import pytest
from httpx import AsyncClient


class TestUserProfile:
    """Tests for user profile CRUD."""

    @pytest.mark.asyncio
    async def test_get_my_profile(self, client: AsyncClient, user_auth_headers: dict):
        """GET /users/me returns authenticated user profile."""
        response = await client.get("/users/me", headers=user_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_get_my_profile_no_auth(self, client: AsyncClient):
        """GET /users/me without auth returns 401."""
        response = await client.get("/users/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_my_profile(self, client: AsyncClient, user_auth_headers: dict):
        """PUT /users/me updates user profile fields."""
        response = await client.put("/users/me", json={
            "full_name": "Updated Name",
        }, headers=user_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_profile_duplicate_email(self, client: AsyncClient, user_auth_headers: dict):
        """PUT /users/me with already-taken email returns 409."""
        # Register a second user first
        await client.post("/auth/register", json={
            "email": "other@example.com",
            "full_name": "Other",
            "password": "OtherPass1",
        })
        response = await client.put("/users/me", json={
            "email": "other@example.com",
        }, headers=user_auth_headers)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_delete_my_account(self, client: AsyncClient):
        """DELETE /users/me deletes authenticated user account."""
        await client.post("/auth/register", json={
            "email": "todelete@example.com",
            "full_name": "Delete Me",
            "password": "DeletePass1",
        })
        login_res = await client.post("/auth/login", data={
            "username": "todelete@example.com",
            "password": "DeletePass1",
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.delete("/users/me", headers=headers)
        assert response.status_code == 204


class TestAdminUserManagement:
    """Tests for admin-only user management endpoints."""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /users returns user list for admin."""
        response = await client.get("/users", headers=admin_auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_list_users_as_customer(self, client: AsyncClient, user_auth_headers: dict):
        """GET /users returns 403 for regular customers."""
        response = await client.get("/users", headers=user_auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_users_no_auth(self, client: AsyncClient):
        """GET /users without auth returns 401."""
        response = await client.get("/users")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_by_id_as_admin(self, client: AsyncClient, admin_auth_headers: dict, test_user):
        """GET /users/{id} returns user detail for admin."""
        response = await client.get(f"/users/{test_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /users/{id} with non-existent ID returns 404."""
        response = await client.get("/users/99999", headers=admin_auth_headers)
        assert response.status_code == 404
