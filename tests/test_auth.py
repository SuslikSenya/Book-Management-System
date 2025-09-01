# tests/test_auth.py
import pytest

@pytest.mark.asyncio
async def test_register_and_login(client):
    data = {"username": "newuser", "password": "verysecure"}
    # регистрация
    r = await client.post("/auth/register", json=data)
    assert r.status_code in (200, 201)
    # логин
    r2 = await client.post("/auth/token", data={"username": data["username"], "password": data["password"]})
    assert r2.status_code == 200
    assert "access_token" in r2.json()
