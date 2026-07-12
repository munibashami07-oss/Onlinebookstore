"""Tests for Authentication endpoints: /auth/register, /auth/login, /auth/refresh, /auth/logout, /auth/me."""

import pytest
from httpx import AsyncClient


# ─── Registration ────────────────────────────────────────────────────────────

class TestRegister:
    """Tests for POST /auth/register."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Successful registration returns 201 and user data."""
        payload = {
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "StrongPass1",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "hashed_password" not in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Duplicate email returns 409 conflict."""
        payload = {
            "email": "dup@example.com",
            "full_name": "Dup User",
            "password": "StrongPass1",
        }
        await client.post("/auth/register", json=payload)
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Password without uppercase/digit fails validation."""
        payload = {
            "email": "weak@example.com",
            "full_name": "Weak Pass",
            "password": "nocaps123",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Password under 8 characters fails validation."""
        payload = {
            "email": "short@example.com",
            "full_name": "Short",
            "password": "Aa1",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Invalid email format fails validation."""
        payload = {
            "email": "not-an-email",
            "full_name": "Bad Email",
            "password": "GoodPass1",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_full_name(self, client: AsyncClient):
        """Missing full_name fails validation."""
        payload = {"email": "noname@example.com", "password": "GoodPass1"}
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422


# ─── Login ───────────────────────────────────────────────────────────────────

class TestLogin:
    """Tests for POST /auth/login (OAuth2 form data)."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Valid credentials return access and refresh tokens."""
        await client.post("/auth/register", json={
            "email": "login@example.com",
            "full_name": "Login User",
            "password": "LoginPass1",
        })
        response = await client.post("/auth/login", data={
            "username": "login@example.com",
            "password": "LoginPass1",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Wrong password returns 401."""
        await client.post("/auth/register", json={
            "email": "wrong@example.com",
            "full_name": "Wrong",
            "password": "RightPass1",
        })
        response = await client.post("/auth/login", data={
            "username": "wrong@example.com",
            "password": "WrongPass1",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: AsyncClient):
        """Non-existent email returns 401."""
        response = await client.post("/auth/login", data={
            "username": "nobody@example.com",
            "password": "Whatever1",
        })
        assert response.status_code == 401


# ─── Refresh Token ───────────────────────────────────────────────────────────

class TestRefreshToken:
    """Tests for POST /auth/refresh."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, client: AsyncClient):
        """Valid refresh token returns new access token."""
        await client.post("/auth/register", json={
            "email": "refresh@example.com",
            "full_name": "Refresh",
            "password": "RefreshPass1",
        })
        login_res = await client.post("/auth/login", data={
            "username": "refresh@example.com",
            "password": "RefreshPass1",
        })
        refresh_token = login_res.json()["refresh_token"]
        response = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Invalid refresh token returns 401."""
        response = await client.post("/auth/refresh", json={
            "refresh_token": "invalid.token.here",
        })
        assert response.status_code == 401


# ─── Logout ──────────────────────────────────────────────────────────────────

class TestLogout:
    """Tests for POST /auth/logout."""

    @pytest.mark.asyncio
    async def test_logout_requires_auth(self, client: AsyncClient):
        """Logout without token returns 401."""
        response = await client.post("/auth/logout")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient):
        """Authenticated logout returns 200."""
        await client.post("/auth/register", json={
            "email": "logout@example.com",
            "full_name": "Logout",
            "password": "LogoutPass1",
        })
        login_res = await client.post("/auth/login", data={
            "username": "logout@example.com",
            "password": "LogoutPass1",
        })
        token = login_res.json()["access_token"]
        response = await client.post("/auth/logout", headers={
            "Authorization": f"Bearer {token}",
        })
        assert response.status_code == 200


# ─── Me ──────────────────────────────────────────────────────────────────────

class TestMe:
    """Tests for GET /auth/me."""

    @pytest.mark.asyncio
    async def test_me_success(self, client: AsyncClient):
        """Authenticated user gets profile data."""
        await client.post("/auth/register", json={
            "email": "me@example.com",
            "full_name": "Me User",
            "password": "MeUserPass1",
        })
        login_res = await client.post("/auth/login", data={
            "username": "me@example.com",
            "password": "MeUserPass1",
        })
        token = login_res.json()["access_token"]
        response = await client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_me_no_auth(self, client: AsyncClient):
        """Unauthenticated request returns 401."""
        response = await client.get("/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_token(self, client: AsyncClient):
        """Invalid bearer token returns 401."""
        response = await client.get("/auth/me", headers={
            "Authorization": "Bearer invalidtoken",
        })
        assert response.status_code == 401
