import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-thirty-two-characters"
os.environ["CORS_ORIGINS"] = "http://localhost:43123,http://127.0.0.1:43123"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"email": "alfredo@example.com", "password": "secure-password"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
