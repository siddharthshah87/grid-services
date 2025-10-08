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
from app import crud
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
    app.state.test_session_factory = async_session

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
    if hasattr(app.state, "test_session_factory"):
        delattr(app.state, "test_session_factory")
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
    ven_payload = {"ven_id": "ven123", "registration_id": "reg123"}
    resp = await async_client.post("/vens/", json=ven_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["ven_id"] == ven_payload["ven_id"]
    assert data["registration_id"] == ven_payload["registration_id"]
    assert "created_at" in data

    resp = await async_client.get("/vens/")
    assert resp.status_code == 200
    all_vens = resp.json()
    assert any(v["ven_id"] == ven_payload["ven_id"] for v in all_vens)

    async with app.state.test_session_factory() as session:
        db_ven = await crud.get_ven(session, ven_payload["ven_id"])
        assert db_ven is not None

@pytest.mark.asyncio
async def test_event_endpoints(async_client):
    ven_payload = {"ven_id": "ven_event", "registration_id": "reg_event"}
    resp = await async_client.post("/vens/", json=ven_payload)
    assert resp.status_code == 201

    event_payload = {
        "event_id": "evt1",
        "ven_id": ven_payload["ven_id"],
        "signal_name": "simple",
        "signal_type": "level",
        "signal_payload": "1",
        "start_time": "2024-01-01T00:00:00Z",
        "response_required": "always",
        "raw": {"a": "b"},
    }
    resp = await async_client.post("/events/", json=event_payload)
    assert resp.status_code == 201
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

    resp = await async_client.delete(f"/events/{event_payload['event_id']}")
    assert resp.status_code == 204

    resp = await async_client.get(f"/events/{event_payload['event_id']}")
    assert resp.status_code == 404

    async with app.state.test_session_factory() as session:
        db_event = await crud.get_event(session, event_payload["event_id"])
        assert db_event is None


@pytest.mark.asyncio
async def test_delete_ven(async_client):
    ven_payload = {"ven_id": "ven_del", "registration_id": "reg_del"}
    resp = await async_client.post("/vens/", json=ven_payload)
    assert resp.status_code == 201

    resp = await async_client.delete(f"/vens/{ven_payload['ven_id']}")
    assert resp.status_code == 204

    resp = await async_client.get("/vens/")
    assert all(v["ven_id"] != ven_payload["ven_id"] for v in resp.json())

    async with app.state.test_session_factory() as session:
        db_ven = await crud.get_ven(session, ven_payload["ven_id"])
        assert db_ven is None

