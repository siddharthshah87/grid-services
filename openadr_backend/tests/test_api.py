import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DB_HOST", "test")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_TIMEOUT", "30")

os.environ.setdefault("DB_NAME", "test")

# Allow importing the `app` package when tests are executed without
# installing the project by adding the parent directory to ``sys.path``.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from app.routers import health, ven, event
from app.db.database import get_session
from app.models import Base


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(ven.router, prefix="/vens", tags=["VENs"])
    app.include_router(event.router, prefix="/events", tags=["Events"])
    return app

app = create_app()

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

import pytest_asyncio


@pytest_asyncio.fixture(scope="module")
async def async_client():
    engine = create_async_engine(DATABASE_URL, future=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()

@pytest.mark.asyncio
async def test_health(async_client):
    resp = await async_client.get("/health/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_ven_endpoints(async_client):
    ven_payload = {"ven_id": "ven123", "registration_id": "reg123"}
    resp = await async_client.post("/vens/", json=ven_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ven_id"] == ven_payload["ven_id"]

    resp = await async_client.get("/vens/")
    assert resp.status_code == 200
    assert any(v["ven_id"] == ven_payload["ven_id"] for v in resp.json())

@pytest.mark.asyncio
async def test_event_endpoints(async_client):
    event_payload = {
        "event_id": "evt1",
        "ven_id": "ven123",
        "signal_name": "simple",
        "signal_type": "level",
        "signal_payload": "1",
        "start_time": "2024-01-01T00:00:00Z",
        "response_required": "always",
        "raw": {"a": "b"},
    }
    resp = await async_client.post("/events/", json=event_payload)
    assert resp.status_code == 200
    event = resp.json()
    assert event["event_id"] == event_payload["event_id"]

    resp = await async_client.get("/events/")
    assert resp.status_code == 200
    assert any(e["event_id"] == event_payload["event_id"] for e in resp.json())

    resp = await async_client.get(f"/events/{event_payload['event_id']}")
    assert resp.status_code == 200

    resp = await async_client.get(f"/events/ven/{event_payload['ven_id']}")
    assert resp.status_code == 200
    assert any(e["event_id"] == event_payload["event_id"] for e in resp.json())

