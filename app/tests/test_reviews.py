"""Tests for Review endpoints: /reviews."""

import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _setup_book(client: AsyncClient, admin_headers: dict) -> int:
    """Create genre + book, return book id."""
    genre = await client.post("/genres", json={"name": "Fiction", "description": "Fiction"}, headers=admin_headers)
    book = await client.post("/books", json={
        "title": "Review Target",
        "author": "Author X",
        "isbn": "1234567890",
        "price": 15.99,
        "genre_id": genre.json()["id"],
    }, headers=admin_headers)
    return book.json()["id"]


# ── Review CRUD ──────────────────────────────────────────────────────────────

class TestReviewsCRUD:
    """Tests for review create, read, update, delete."""

    @pytest.mark.asyncio
    async def test_create_review(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /reviews creates a review for authenticated user."""
        book_id = await _setup_book(client, admin_auth_headers)
        response = await client.post("/reviews", json={
            "book_id": book_id,
            "rating": 5,
            "comment": "Excellent book!",
        }, headers=user_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Excellent book!"

    @pytest.mark.asyncio
    async def test_create_review_no_auth(self, client: AsyncClient, admin_auth_headers: dict):
        """POST /reviews without auth returns 401."""
        book_id = await _setup_book(client, admin_auth_headers)
        response = await client.post("/reviews", json={
            "book_id": book_id,
            "rating": 3,
            "comment": "Good",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_review_invalid_rating(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /reviews with rating > 5 returns 422."""
        book_id = await _setup_book(client, admin_auth_headers)
        response = await client.post("/reviews", json={
            "book_id": book_id,
            "rating": 6,
            "comment": "Too high",
        }, headers=user_auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_review_invalid_rating_zero(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /reviews with rating 0 returns 422."""
        book_id = await _setup_book(client, admin_auth_headers)
        response = await client.post("/reviews", json={
            "book_id": book_id,
            "rating": 0,
            "comment": "Zero stars?",
        }, headers=user_auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_review_nonexistent_book(self, client: AsyncClient, user_auth_headers: dict):
        """POST /reviews for non-existent book returns 404."""
        response = await client.post("/reviews", json={
            "book_id": 99999,
            "rating": 3,
            "comment": "Ghost book",
        }, headers=user_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_reviews_for_book(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """GET /reviews/book/{book_id} returns reviews list."""
        book_id = await _setup_book(client, admin_auth_headers)
        await client.post("/reviews", json={
            "book_id": book_id,
            "rating": 4,
            "comment": "Nice read",
        }, headers=user_auth_headers)
        response = await client.get(f"/reviews/book/{book_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["rating"] == 4

    @pytest.mark.asyncio
    async def test_get_reviews_for_book_empty(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /reviews/book/{book_id} with no reviews returns empty list."""
        book_id = await _setup_book(client, admin_auth_headers)
        response = await client.get(f"/reviews/book/{book_id}")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_update_own_review(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """PUT /reviews/{id} by review owner updates the review."""
        book_id = await _setup_book(client, admin_auth_headers)
        create_res = await client.post("/reviews", json={
            "book_id": book_id,
            "rating": 2,
            "comment": "Meh",
        }, headers=user_auth_headers)
        review_id = create_res.json()["id"]
        response = await client.put(f"/reviews/{review_id}", json={
            "rating": 4,
            "comment": "Actually quite good!",
        }, headers=user_auth_headers)
        assert response.status_code == 200
        assert response.json()["rating"] == 4

    @pytest.mark.asyncio
    async def test_delete_own_review(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """DELETE /reviews/{id} by review owner returns 204."""
        book_id = await _setup_book(client, admin_auth_headers)
        create_res = await client.post("/reviews", json={
            "book_id": book_id,
            "rating": 1,
            "comment": "Delete me",
        }, headers=user_auth_headers)
        review_id = create_res.json()["id"]
        response = await client.delete(f"/reviews/{review_id}", headers=user_auth_headers)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_review_not_found(self, client: AsyncClient, user_auth_headers: dict):
        """DELETE /reviews/{id} for non-existent review returns 404."""
        response = await client.delete("/reviews/99999", headers=user_auth_headers)
        assert response.status_code == 404


# ── Duplicate Review Guard ───────────────────────────────────────────────────

class TestReviewDuplicate:
    """Tests for duplicate review prevention."""

    @pytest.mark.asyncio
    async def test_duplicate_review_same_book(self, client: AsyncClient, admin_auth_headers: dict, user_auth_headers: dict):
        """POST /reviews twice for same book by same user returns 409."""
        book_id = await _setup_book(client, admin_auth_headers)
        await client.post("/reviews", json={
            "book_id": book_id,
            "rating": 5,
            "comment": "First",
        }, headers=user_auth_headers)
        response = await client.post("/reviews", json={
            "book_id": book_id,
            "rating": 3,
            "comment": "Second attempt",
        }, headers=user_auth_headers)
        assert response.status_code == 409
