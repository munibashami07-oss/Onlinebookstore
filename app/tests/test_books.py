"""Tests for Book catalog endpoints: /books."""

import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _create_genre(client: AsyncClient, headers: dict, name: str = "Fiction") -> dict:
    """Helper to create a genre and return its response dict."""
    res = await client.post("/genres", json={"name": name, "description": f"{name} genre"}, headers=headers)
    return res.json()


async def _create_book(client: AsyncClient, headers: dict, genre_id: int, **overrides) -> dict:
    """Helper to create a book and return its response dict."""
    payload = {
        "title": overrides.get("title", "Test Book"),
        "author": overrides.get("author", "Author One"),
        "isbn": overrides.get("isbn", "9780131103627"),
        "price": overrides.get("price", 19.99),
        "genre_id": genre_id,
    }
    res = await client.post("/books", json=payload, headers=headers)
    return res.json()


# ── Public Read Endpoints ────────────────────────────────────────────────────

class TestBooksPublic:
    """Tests for public book browsing and search."""

    @pytest.mark.asyncio
    async def test_list_books_empty(self, client: AsyncClient):
        """GET /books on empty catalog returns empty list."""
        response = await client.get("/books")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_books_with_data(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /books returns created books."""
        genre = await _create_genre(client, admin_auth_headers)
        await _create_book(client, admin_auth_headers, genre["id"])
        response = await client.get("/books")
        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_list_books_pagination(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /books?page=1&page_size=1 returns single result."""
        genre = await _create_genre(client, admin_auth_headers)
        await _create_book(client, admin_auth_headers, genre["id"], isbn="1111111111")
        await _create_book(client, admin_auth_headers, genre["id"], isbn="2222222222", title="Second Book")
        response = await client.get("/books?page=1&page_size=1")
        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_search_books(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /books/search?q=Test returns matching books."""
        genre = await _create_genre(client, admin_auth_headers)
        await _create_book(client, admin_auth_headers, genre["id"])
        response = await client.get("/books/search?q=Test")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    @pytest.mark.asyncio
    async def test_search_books_no_match(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /books/search?q=ZZZZZ returns empty list."""
        genre = await _create_genre(client, admin_auth_headers)
        await _create_book(client, admin_auth_headers, genre["id"])
        response = await client.get("/books/search?q=ZZZZZ")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_book_details(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /books/{id} returns book details."""
        genre = await _create_genre(client, admin_auth_headers)
        book = await _create_book(client, admin_auth_headers, genre["id"])
        response = await client.get(f"/books/{book['id']}")
        assert response.status_code == 200
        assert response.json()["title"] == "Test Book"

    @pytest.mark.asyncio
    async def test_get_book_not_found(self, client: AsyncClient):
        """GET /books/{id} with invalid ID returns 404."""
        response = await client.get("/books/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_books_by_genre(self, client: AsyncClient, admin_auth_headers: dict):
        """GET /books/genre/{genre_id} returns filtered books."""
        genre = await _create_genre(client, admin_auth_headers)
        await _create_book(client, admin_auth_headers, genre["id"])
        response = await client.get(f"/books/genre/{genre['id']}")
        assert response.status_code == 200
        assert len(response.json()) == 1


# ── Admin CRUD Endpoints ────────────────────────────────────────────────────

class TestBooksAdmin:
    """Tests for admin book CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_book_as_admin(self, client: AsyncClient, admin_auth_headers: dict):
        """POST /books as admin returns 201."""
        genre = await _create_genre(client, admin_auth_headers)
        response = await client.post("/books", json={
            "title": "Admin Book",
            "author": "Admin Author",
            "isbn": "9876543210",
            "price": 25.99,
            "genre_id": genre["id"],
        }, headers=admin_auth_headers)
        assert response.status_code == 201
        assert response.json()["title"] == "Admin Book"

    @pytest.mark.asyncio
    async def test_create_book_as_customer(self, client: AsyncClient, user_auth_headers: dict):
        """POST /books as customer returns 403."""
        response = await client.post("/books", json={
            "title": "Fail Book",
            "author": "Fail",
            "isbn": "1111111111",
            "price": 10.0,
            "genre_id": 1,
        }, headers=user_auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_book_no_auth(self, client: AsyncClient):
        """POST /books without auth returns 401."""
        response = await client.post("/books", json={
            "title": "NoAuth",
            "author": "NA",
            "isbn": "1111111111",
            "price": 10.0,
            "genre_id": 1,
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_book_duplicate_isbn(self, client: AsyncClient, admin_auth_headers: dict):
        """POST /books with duplicate ISBN returns 409."""
        genre = await _create_genre(client, admin_auth_headers)
        await _create_book(client, admin_auth_headers, genre["id"], isbn="5555555555")
        response = await client.post("/books", json={
            "title": "Dup",
            "author": "Dup",
            "isbn": "5555555555",
            "price": 5.0,
            "genre_id": genre["id"],
        }, headers=admin_auth_headers)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_book_invalid_price(self, client: AsyncClient, admin_auth_headers: dict):
        """POST /books with zero price returns 422."""
        genre = await _create_genre(client, admin_auth_headers)
        response = await client.post("/books", json={
            "title": "Free",
            "author": "Free",
            "isbn": "0000000000",
            "price": 0,
            "genre_id": genre["id"],
        }, headers=admin_auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_book_as_admin(self, client: AsyncClient, admin_auth_headers: dict):
        """PUT /books/{id} as admin returns updated book."""
        genre = await _create_genre(client, admin_auth_headers)
        book = await _create_book(client, admin_auth_headers, genre["id"])
        response = await client.put(f"/books/{book['id']}", json={
            "title": "Updated Title",
        }, headers=admin_auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_book_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """PUT /books/{id} for non-existent ID returns 404."""
        response = await client.put("/books/99999", json={"title": "X"}, headers=admin_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_book_as_admin(self, client: AsyncClient, admin_auth_headers: dict):
        """DELETE /books/{id} as admin returns 204."""
        genre = await _create_genre(client, admin_auth_headers)
        book = await _create_book(client, admin_auth_headers, genre["id"])
        response = await client.delete(f"/books/{book['id']}", headers=admin_auth_headers)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_book_as_customer(self, client: AsyncClient, user_auth_headers: dict, admin_auth_headers: dict):
        """DELETE /books/{id} as customer returns 403."""
        genre = await _create_genre(client, admin_auth_headers)
        book = await _create_book(client, admin_auth_headers, genre["id"])
        response = await client.delete(f"/books/{book['id']}", headers=user_auth_headers)
        assert response.status_code == 403
