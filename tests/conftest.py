import pytest_asyncio
import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import Base, get_async_session

# in-memory sqlite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine_test, expire_on_commit=False, class_=AsyncSession)


# Используем pytest_asyncio.fixture для async fixtures
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client):
    user = {"username": "testuser", "password": "password123"}
    r = await client.post("/auth/register", json=user)
    assert r.status_code in (200, 201)
    r2 = await client.post("/auth/token", data={"username": user["username"], "password": user["password"]})
    assert r2.status_code == 200
    token = r2.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}
