import os
import sys
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import pytest_asyncio
from alembic import command
from alembic.config import Config

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


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(ven.router, prefix="/vens", tags=["VENs"])
    app.include_router(event.router, prefix="/events", tags=["Events"])
    return app

app = create_app()

BASE_DIR = os.path.dirname(__file__)
db_file = os.path.join(BASE_DIR, "test.db")
DATABASE_URL = f"sqlite+aiosqlite:///{db_file}"


@pytest_asyncio.fixture(scope="module")
async def async_client():
    if os.path.exists(db_file):
        os.remove(db_file)
    engine = create_async_engine(DATABASE_URL, future=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    from app.db import database as db
    db.engine = engine

    alembic_cfg = Config(os.path.join(BASE_DIR, "..", "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(BASE_DIR, "..", "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    async def override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()
    if os.path.exists(db_file):
        os.remove(db_file)

@pytest.mark.asyncio
async def test_health(async_client):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_ven_endpoints(async_client):
    ven_payload = {"name": "Test VEN", "location": {"lat": 1.23, "lon": 4.56}}
    resp = await async_client.post("/vens/", json=ven_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == ven_payload["name"]
    new_id = data["id"]

    resp = await async_client.get("/vens/")
    assert resp.status_code == 200
    assert any(v["id"] == new_id for v in resp.json())

@pytest.mark.asyncio
async def test_event_endpoints(async_client):
    event_payload = {
        "startTime": "2024-01-01T00:00:00Z",
        "endTime": "2024-01-01T01:00:00Z",
        "requestedReductionKw": 1.5,
    }
    resp = await async_client.post("/events/", json=event_payload)
    assert resp.status_code == 201
    event = resp.json()
    event_id = event["id"]

    resp = await async_client.get("/events/")
    assert resp.status_code == 200
    assert any(e["id"] == event_id for e in resp.json())

    resp = await async_client.get(f"/events/{event_id}")
    assert resp.status_code == 200

    resp = await async_client.delete(f"/events/{event_id}")
    assert resp.status_code == 204

    resp = await async_client.get(f"/events/{event_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_ven(async_client):
    ven_payload = {"name": "Delete VEN", "location": {"lat": 0.0, "lon": 0.0}}
    resp = await async_client.post("/vens/", json=ven_payload)
    assert resp.status_code == 201
    ven_id = resp.json()["id"]

    resp = await async_client.delete(f"/vens/{ven_id}")
    assert resp.status_code == 204

    resp = await async_client.get("/vens/")
    assert all(v["id"] != ven_id for v in resp.json())

