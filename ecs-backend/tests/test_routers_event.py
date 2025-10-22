"""Tests for event router endpoints."""
import pytest
from datetime import datetime, timedelta, UTC
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base
from app.dependencies import get_session


@pytest.fixture
async def test_engine():
    """Create in-memory test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(test_session):
    """Create test HTTP client with database override."""
    async def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_events_empty(client: AsyncClient):
    """Test listing events when database is empty."""
    response = await client.get("/api/events/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_event(client: AsyncClient):
    """Test creating a new event."""
    now = datetime.now(UTC)
    payload = {
        "startTime": now.isoformat(),
        "endTime": (now + timedelta(hours=2)).isoformat(),
        "requestedReductionKw": 50.0,
        "status": "scheduled"
    }
    
    response = await client.post("/api/events/", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["status"] == "scheduled"
    assert data["requestedReductionKw"] == 50.0
    assert data["actualReductionKw"] == 0.0
    assert "id" in data
    assert data["id"].startswith("evt-")


@pytest.mark.asyncio
async def test_list_events_with_data(client: AsyncClient):
    """Test listing events after creating some."""
    now = datetime.now(UTC)
    
    # Create two events
    for i in range(2):
        payload = {
            "startTime": (now + timedelta(hours=i)).isoformat(),
            "endTime": (now + timedelta(hours=i+1)).isoformat(),
            "requestedReductionKw": 25.0 * (i + 1),
            "status": "scheduled"
        }
        await client.post("/api/events/", json=payload)
    
    response = await client.get("/api/events/")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2


@pytest.mark.asyncio
async def test_get_event(client: AsyncClient):
    """Test getting a specific event by ID."""
    now = datetime.now(UTC)
    payload = {
        "startTime": now.isoformat(),
        "endTime": (now + timedelta(hours=1)).isoformat(),
        "requestedReductionKw": 30.0,
        "status": "scheduled"
    }
    
    # Create event
    create_response = await client.post("/api/events/", json=payload)
    event_id = create_response.json()["id"]
    
    # Get event
    response = await client.get(f"/api/events/{event_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event_id
    assert data["requestedReductionKw"] == 30.0


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient):
    """Test getting a non-existent event returns 404."""
    response = await client.get("/api/events/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


@pytest.mark.asyncio
async def test_delete_event(client: AsyncClient):
    """Test deleting an event."""
    now = datetime.now(UTC)
    payload = {
        "startTime": now.isoformat(),
        "endTime": (now + timedelta(hours=1)).isoformat(),
        "requestedReductionKw": 20.0,
    }
    
    # Create event
    create_response = await client.post("/api/events/", json=payload)
    event_id = create_response.json()["id"]
    
    # Delete event
    response = await client.delete(f"/api/events/{event_id}")
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = await client.get(f"/api/events/{event_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_event_not_found(client: AsyncClient):
    """Test deleting a non-existent event returns 404."""
    response = await client.delete("/api/events/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stop_event(client: AsyncClient):
    """Test stopping an active event."""
    now = datetime.now(UTC)
    payload = {
        "startTime": now.isoformat(),
        "endTime": (now + timedelta(hours=1)).isoformat(),
        "requestedReductionKw": 40.0,
        "status": "active"
    }
    
    # Create active event
    create_response = await client.post("/api/events/", json=payload)
    event_id = create_response.json()["id"]
    
    # Stop event
    response = await client.post(f"/api/events/{event_id}/stop")
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "stopping"
    assert data["eventId"] == event_id


@pytest.mark.asyncio
async def test_current_event_none(client: AsyncClient):
    """Test getting current event when none exist."""
    response = await client.get("/api/events/current")
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_current_event_active(client: AsyncClient):
    """Test getting current event when one is active."""
    now = datetime.now(UTC)
    payload = {
        "startTime": (now - timedelta(minutes=30)).isoformat(),
        "endTime": (now + timedelta(minutes=30)).isoformat(),
        "requestedReductionKw": 60.0,
        "status": "active"
    }
    
    create_response = await client.post("/api/events/", json=payload)
    event_id = create_response.json()["id"]
    
    response = await client.get("/api/events/current")
    assert response.status_code == 200
    data = response.json()
    assert data is not None
    assert data["id"] == event_id
    assert data["status"] == "active"
    assert "currentReductionKw" in data
    assert "vensResponding" in data


@pytest.mark.asyncio
async def test_event_metrics(client: AsyncClient):
    """Test getting metrics for an event."""
    now = datetime.now(UTC)
    payload = {
        "startTime": now.isoformat(),
        "endTime": (now + timedelta(hours=1)).isoformat(),
        "requestedReductionKw": 35.0,
    }
    
    create_response = await client.post("/api/events/", json=payload)
    event_id = create_response.json()["id"]
    
    response = await client.get(f"/api/events/{event_id}/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "currentReductionKw" in data
    assert "vensResponding" in data
    assert "avgResponseMs" in data
    assert data["currentReductionKw"] == 0.0
    assert data["vensResponding"] == 0


@pytest.mark.asyncio
async def test_history_events_no_filter(client: AsyncClient):
    """Test getting event history without filters."""
    now = datetime.now(UTC)
    
    # Create past event
    payload = {
        "startTime": (now - timedelta(days=1)).isoformat(),
        "endTime": (now - timedelta(days=1, hours=-1)).isoformat(),
        "requestedReductionKw": 20.0,
    }
    await client.post("/api/events/", json=payload)
    
    response = await client.get("/api/events/history")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1


@pytest.mark.asyncio
async def test_history_events_with_date_filter(client: AsyncClient):
    """Test getting event history with date range filter."""
    now = datetime.now(UTC)
    
    # Create events in different time periods
    old_payload = {
        "startTime": (now - timedelta(days=10)).isoformat(),
        "endTime": (now - timedelta(days=10, hours=-1)).isoformat(),
        "requestedReductionKw": 15.0,
    }
    recent_payload = {
        "startTime": (now - timedelta(hours=2)).isoformat(),
        "endTime": (now - timedelta(hours=1)).isoformat(),
        "requestedReductionKw": 25.0,
    }
    
    await client.post("/api/events/", json=old_payload)
    await client.post("/api/events/", json=recent_payload)
    
    # Query recent events only
    start = (now - timedelta(days=1)).isoformat()
    response = await client.get(f"/api/events/history?start={start}")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["requestedReductionKw"] == 25.0
