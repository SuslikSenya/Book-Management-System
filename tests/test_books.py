# tests/test_books.py
import pytest


@pytest.mark.asyncio
async def test_create_book(client, auth_headers):
    payload = {"title": "Test Book", "author": "John Doe", "genre": "Fiction", "published_year": 2020}
    r = await client.post("/books/", json=payload, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == payload["title"]
    assert body["author"]["name"] == payload["author"]


@pytest.mark.asyncio
async def test_read_books(client):
    r = await client.get("/books/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_recommend_books(client, auth_headers):
    # создаём книгу, чтобы получить id
    payload = {"title": "Rec Book", "author": "Jane Doe", "genre": "Science", "published_year": 2021}
    create = await client.post("/books/", json=payload, headers=auth_headers)
    assert create.status_code == 200
    book_id = create.json()["id"]

    # вызываем recommend
    r = await client.get(f"/books/{book_id}/recommend")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
