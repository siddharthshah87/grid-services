"""Tests for VEN router endpoints."""
import pytest
from datetime import datetime, timedelta, UTC
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_list_vens_empty(client: AsyncClient):
    """Test listing VENs when database is empty."""
    response = await client.get("/api/vens/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_ven(client: AsyncClient):
    """Test creating a new VEN."""
    payload = {
        "name": "Test VEN",
        "location": {"lat": 37.7749, "lon": -122.4194},
        "registrationId": "test-reg-123",
        "status": "active"
    }
    
    response = await client.post("/api/vens/", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "Test VEN"
    assert data["status"] == "active"
    assert "id" in data
    assert data["id"].startswith("ven-")
    assert data["location"]["lat"] == 37.7749
    assert data["location"]["lon"] == -122.4194


@pytest.mark.asyncio
async def test_list_vens_with_data(client: AsyncClient):
    """Test listing VENs after creating some."""
    # Create two VENs
    for i in range(2):
        payload = {
            "name": f"Test VEN {i}",
            "location": {"lat": 37.0 + i, "lon": -122.0 - i},
            "registrationId": f"reg-{i}",
        }
        await client.post("/api/vens/", json=payload)
    
    response = await client.get("/api/vens/")
    assert response.status_code == 200
    vens = response.json()
    assert len(vens) == 2


@pytest.mark.asyncio
async def test_get_ven(client: AsyncClient):
    """Test getting a specific VEN by ID."""
    payload = {
        "name": "Specific VEN",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "registrationId": "specific-reg",
    }
    
    # Create VEN
    create_response = await client.post("/api/vens/", json=payload)
    ven_id = create_response.json()["id"]
    
    # Get VEN
    response = await client.get(f"/api/vens/{ven_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == ven_id
    assert data["name"] == "Specific VEN"


@pytest.mark.asyncio
async def test_get_ven_not_found(client: AsyncClient):
    """Test getting a non-existent VEN returns 404."""
    response = await client.get("/api/vens/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "VEN not found"


@pytest.mark.asyncio
async def test_patch_ven(client: AsyncClient):
    """Test updating a VEN."""
    payload = {
        "name": "Original Name",
        "location": {"lat": 37.0, "lon": -122.0},
        "registrationId": "orig-reg",
    }
    
    # Create VEN
    create_response = await client.post("/api/vens/", json=payload)
    ven_id = create_response.json()["id"]
    
    # Update VEN
    update_payload = {"name": "Updated Name", "status": "maintenance"}
    response = await client.patch(f"/api/vens/{ven_id}", json=update_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["status"] == "maintenance"


@pytest.mark.asyncio
async def test_patch_ven_location(client: AsyncClient):
    """Test updating VEN location."""
    payload = {
        "name": "Mobile VEN",
        "location": {"lat": 37.0, "lon": -122.0},
        "registrationId": "mobile-reg",
    }
    
    create_response = await client.post("/api/vens/", json=payload)
    ven_id = create_response.json()["id"]
    
    # Update location
    update_payload = {"location": {"lat": 38.0, "lon": -123.0}}
    response = await client.patch(f"/api/vens/{ven_id}", json=update_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["location"]["lat"] == 38.0
    assert data["location"]["lon"] == -123.0


@pytest.mark.asyncio
async def test_delete_ven(client: AsyncClient):
    """Test deleting a VEN."""
    payload = {
        "name": "Temporary VEN",
        "location": {"lat": 37.0, "lon": -122.0},
        "registrationId": "temp-reg",
    }
    
    # Create VEN
    create_response = await client.post("/api/vens/", json=payload)
    ven_id = create_response.json()["id"]
    
    # Delete VEN
    response = await client.delete(f"/api/vens/{ven_id}")
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = await client.get(f"/api/vens/{ven_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_vens_summary(client: AsyncClient):
    """Test getting VEN summary list."""
    # Create VEN
    payload = {
        "name": "Summary VEN",
        "location": {"lat": 37.5, "lon": -122.5},
        "registrationId": "summary-reg",
    }
    await client.post("/api/vens/", json=payload)
    
    response = await client.get("/api/vens/summary")
    assert response.status_code == 200
    summaries = response.json()
    
    assert len(summaries) == 1
    summary = summaries[0]
    assert "id" in summary
    assert "name" in summary
    assert "location" in summary
    assert "status" in summary
    assert "controllablePower" in summary
    assert "currentPower" in summary


@pytest.mark.asyncio
async def test_list_ven_loads_empty(client: AsyncClient):
    """Test listing loads for a VEN with no telemetry."""
    payload = {
        "name": "No Loads VEN",
        "location": {"lat": 37.0, "lon": -122.0},
        "registrationId": "no-loads-reg",
    }
    
    create_response = await client.post("/api/vens/", json=payload)
    ven_id = create_response.json()["id"]
    
    response = await client.get(f"/api/vens/{ven_id}/loads")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_ven_loads_with_telemetry(client: AsyncClient, test_session: AsyncSession):
    """Test listing loads for a VEN with telemetry data."""
    from app import crud
    from app.models.telemetry import VenTelemetry, VenLoadSample
    
    # Create VEN
    ven = await crud.create_ven(
        test_session,
        ven_id="ven-with-loads",
        name="VEN with Loads",
        status="active",
        registration_id="loads-reg",
        latitude=37.0,
        longitude=-122.0,
    )
    
    # Create telemetry with loads
    now = datetime.now(UTC)
    telemetry = VenTelemetry(
        ven_id=ven.ven_id,
        timestamp=now,
        used_power_kw=5.0,
        shed_power_kw=2.0,
    )
    test_session.add(telemetry)
    await test_session.flush()
    
    load = VenLoadSample(
        telemetry_id=telemetry.id,
        load_id="load-1",
        name="HVAC",
        type="hvac",
        capacity_kw=10.0,
        shed_capability_kw=3.0,
        current_power_kw=4.0,
    )
    test_session.add(load)
    await test_session.commit()
    
    response = await client.get(f"/api/vens/{ven.ven_id}/loads")
    assert response.status_code == 200
    loads = response.json()
    
    assert len(loads) == 1
    assert loads[0]["id"] == "load-1"
    assert loads[0]["type"] == "hvac"
    assert loads[0]["capacityKw"] == 10.0


@pytest.mark.asyncio
async def test_ven_last_seen_field(client: AsyncClient, test_session: AsyncSession):
    """Test that lastSeen field is populated from telemetry timestamp."""
    from app import crud
    from app.models.telemetry import VenTelemetry
    
    # Create VEN
    ven = await crud.create_ven(
        test_session,
        ven_id="ven-lastseen-test",
        name="VEN LastSeen Test",
        status="active",
        registration_id="lastseen-reg",
        latitude=37.0,
        longitude=-122.0,
    )
    
    # Create telemetry
    now = datetime.now(UTC)
    telemetry = VenTelemetry(
        ven_id=ven.ven_id,
        timestamp=now,
        used_power_kw=5.0,
        shed_power_kw=2.0,
    )
    test_session.add(telemetry)
    await test_session.commit()
    
    # Get VEN and verify lastSeen is set
    response = await client.get(f"/api/vens/{ven.ven_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert "lastSeen" in data
    assert data["lastSeen"] is not None
    # Verify it's a valid ISO datetime string
    last_seen_dt = datetime.fromisoformat(data["lastSeen"].replace('Z', '+00:00'))
    assert isinstance(last_seen_dt, datetime)


@pytest.mark.asyncio
async def test_ven_last_seen_none_without_telemetry(client: AsyncClient):
    """Test that lastSeen is None when VEN has no telemetry."""
    payload = {
        "name": "No Telemetry VEN",
        "location": {"lat": 37.0, "lon": -122.0},
        "registrationId": "no-telem-reg",
    }
    
    create_response = await client.post("/api/vens/", json=payload)
    ven_id = create_response.json()["id"]
    
    response = await client.get(f"/api/vens/{ven_id}")
    assert response.status_code == 200
    data = response.json()
    
    # lastSeen should be None when no telemetry exists
    assert "lastSeen" in data
    assert data["lastSeen"] is None


@pytest.mark.asyncio
async def test_get_ven_load(client: AsyncClient, test_session: AsyncSession):
    """Test getting a specific load for a VEN."""
    from app import crud
    from app.models.telemetry import VenTelemetry, VenLoadSample
    
    # Create VEN
    ven = await crud.create_ven(
        test_session,
        ven_id="ven-specific-load",
        name="VEN",
        status="active",
        registration_id="load-reg",
        latitude=37.0,
        longitude=-122.0,
    )
    
    # Create telemetry with load
    now = datetime.now(UTC)
    telemetry = VenTelemetry(
        ven_id=ven.ven_id,
        timestamp=now,
        used_power_kw=5.0,
        shed_power_kw=2.0,
    )
    test_session.add(telemetry)
    await test_session.flush()
    
    load = VenLoadSample(
        telemetry_id=telemetry.id,
        load_id="specific-load",
        name="EV Charger",
        type="ev",
        capacity_kw=7.2,
        shed_capability_kw=7.2,
        current_power_kw=6.0,
    )
    test_session.add(load)
    await test_session.commit()
    
    response = await client.get(f"/api/vens/{ven.ven_id}/loads/specific-load")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == "specific-load"
    assert data["type"] == "ev"
    assert data["name"] == "EV Charger"


@pytest.mark.asyncio
async def test_get_ven_load_not_found(client: AsyncClient):
    """Test getting non-existent load returns 404."""
    payload = {
        "name": "VEN",
        "location": {"lat": 37.0, "lon": -122.0},
        "registrationId": "reg",
    }
    
    create_response = await client.post("/api/vens/", json=payload)
    ven_id = create_response.json()["id"]
    
    response = await client.get(f"/api/vens/{ven_id}/loads/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_shed_ven_load(client: AsyncClient):
    """Test shedding a load (stub implementation)."""
    payload = {
        "name": "VEN",
        "location": {"lat": 37.0, "lon": -122.0},
        "registrationId": "reg",
    }
    
    create_response = await client.post("/api/vens/", json=payload)
    ven_id = create_response.json()["id"]
    
    shed_payload = {"amountKw": 2.5}
    response = await client.post(
        f"/api/vens/{ven_id}/loads/load-1/commands/shed",
        json=shed_payload
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert data["venId"] == ven_id
    assert data["amountKw"] == 2.5


@pytest.mark.asyncio
async def test_ven_history(client: AsyncClient, test_session: AsyncSession):
    """Test getting VEN history."""
    from app import crud
    from app.models.telemetry import VenTelemetry
    
    # Create VEN
    ven = await crud.create_ven(
        test_session,
        ven_id="ven-history",
        name="VEN",
        status="active",
        registration_id="hist-reg",
        latitude=37.0,
        longitude=-122.0,
    )
    
    # Create telemetry data points
    now = datetime.now(UTC)
    for i in range(3):
        telemetry = VenTelemetry(
            ven_id=ven.ven_id,
            timestamp=now - timedelta(minutes=i*5),
            used_power_kw=5.0 + i,
            shed_power_kw=1.0,
        )
        test_session.add(telemetry)
    await test_session.commit()
    
    response = await client.get(f"/api/vens/{ven.ven_id}/history")
    assert response.status_code == 200
    data = response.json()
    
    assert "points" in data
    assert isinstance(data["points"], list)
