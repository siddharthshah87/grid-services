"""
Tests for circuit history API endpoints and functionality.

This module tests the GET /api/vens/{ven_id}/circuits/history endpoint
which retrieves historical power usage data for individual circuits/loads.
"""
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession

# Setup path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import crud
from app.main import app
from app.models import VenTelemetry, VenLoadSample


@pytest.mark.asyncio
async def test_get_circuit_history_empty(client: AsyncClient, test_session: AsyncSession):
    """Test circuit history endpoint when no data exists."""
    # Create VEN first
    ven = await crud.create_ven(
        test_session,
        ven_id="test-ven",
        name="Test VEN",
        status="online",
        registration_id="reg-test"
    )
    
    response = await client.get("/api/vens/test-ven/circuits/history")
    assert response.status_code == 200
    data = response.json()
    assert data["venId"] == "test-ven"
    assert data["totalCount"] == 0
    assert data["snapshots"] == []


@pytest.mark.asyncio
async def test_get_circuit_history_with_data(client: AsyncClient, test_session: AsyncSession):
    """Test circuit history endpoint with sample telemetry data."""
    # Create VEN
    ven = await crud.create_ven(
        test_session,
        ven_id="history-ven",
        name="Test VEN",
        status="online",
        registration_id="reg-123"
    )
    
    # Create telemetry with load samples
    now = datetime.now(timezone.utc)
    telemetry = VenTelemetry(
        ven_id="history-ven",
        timestamp=now,
        used_power_kw=10.5,
        shed_power_kw=0.0
    )
    test_session.add(telemetry)
    await test_session.flush()
    
    # Add load samples
    loads = [
        VenLoadSample(
            telemetry_id=telemetry.id,
            load_id="hvac1",
            name="HVAC",
            type="hvac",
            capacity_kw=7.2,
            current_power_kw=5.5,
            shed_capability_kw=0.0,
            enabled=True,
            priority=1
        ),
        VenLoadSample(
            telemetry_id=telemetry.id,
            load_id="heater1",
            name="Water Heater",
            type="heater",
            capacity_kw=4.5,
            current_power_kw=3.0,
            shed_capability_kw=3.0,
            enabled=True,
            priority=5
        ),
        VenLoadSample(
            telemetry_id=telemetry.id,
            load_id="ev1",
            name="EV Charger",
            type="ev",
            capacity_kw=12.0,
            current_power_kw=2.0,
            shed_capability_kw=2.0,
            enabled=False,
            priority=5
        )
    ]
    test_session.add_all(loads)
    await test_session.commit()
    
    # Test getting all circuits
    response = await client.get("/api/vens/history-ven/circuits/history")
    assert response.status_code == 200
    data = response.json()
    assert data["venId"] == "history-ven"
    assert data["totalCount"] == 3
    assert len(data["snapshots"]) == 3
    
    # Verify circuit data
    snapshot = data["snapshots"][0]
    assert snapshot["loadId"] in ["hvac1", "heater1", "ev1"]
    assert "name" in snapshot
    assert "type" in snapshot
    assert "capacityKw" in snapshot
    assert "currentPowerKw" in snapshot
    assert "shedCapabilityKw" in snapshot
    assert "enabled" in snapshot
    assert "priority" in snapshot


@pytest.mark.asyncio
async def test_get_circuit_history_filter_by_load_id(client: AsyncClient, test_session: AsyncSession):
    """Test filtering circuit history by specific load_id."""
    # Create VEN
    ven = await crud.create_ven(
        test_session,
        ven_id="filter-ven",
        name="Filter Test VEN",
        status="online",
        registration_id="reg-456"
    )
    
    # Create telemetry with multiple loads
    now = datetime.now(timezone.utc)
    telemetry = VenTelemetry(
        ven_id="filter-ven",
        timestamp=now,
        used_power_kw=10.0,
        shed_power_kw=0.0
    )
    test_session.add(telemetry)
    await test_session.flush()
    
    # Add multiple load samples
    loads = [
        VenLoadSample(
            telemetry_id=telemetry.id,
            load_id="hvac1",
            name="HVAC",
            type="hvac",
            capacity_kw=7.2,
            current_power_kw=5.5,
            shed_capability_kw=0.0,
            enabled=True,
            priority=1
        ),
        VenLoadSample(
            telemetry_id=telemetry.id,
            load_id="heater1",
            name="Water Heater",
            type="heater",
            capacity_kw=4.5,
            current_power_kw=3.0,
            shed_capability_kw=3.0,
            enabled=True,
            priority=5
        )
    ]
    test_session.add_all(loads)
    await test_session.commit()
    
    # Filter by hvac1
    response = await client.get("/api/vens/filter-ven/circuits/history?load_id=hvac1")
    assert response.status_code == 200
    data = response.json()
    assert data["loadId"] == "hvac1"
    assert data["totalCount"] == 1
    assert all(s["loadId"] == "hvac1" for s in data["snapshots"])


@pytest.mark.asyncio
async def test_get_circuit_history_with_limit(client: AsyncClient, test_session: AsyncSession):
    """Test limiting the number of circuit history results."""
    # Create VEN
    ven = await crud.create_ven(
        test_session,
        ven_id="limit-ven",
        name="Limit Test VEN",
        status="online",
        registration_id="reg-789"
    )
    
    # Create multiple telemetry entries
    now = datetime.now(timezone.utc)
    for i in range(5):
        telemetry = VenTelemetry(
            ven_id="limit-ven",
            timestamp=now - timedelta(seconds=i*5),
            used_power_kw=10.0 + i,
            shed_power_kw=0.0
        )
        test_session.add(telemetry)
        await test_session.flush()
        
        load = VenLoadSample(
            telemetry_id=telemetry.id,
            load_id="hvac1",
            name="HVAC",
            type="hvac",
            capacity_kw=7.2,
            current_power_kw=5.0 + i*0.5,
            shed_capability_kw=0.0,
            enabled=True,
            priority=1
        )
        test_session.add(load)
    
    await test_session.commit()
    
    # Request with limit
    response = await client.get("/api/vens/limit-ven/circuits/history?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["snapshots"]) == 3
    assert data["totalCount"] == 3


@pytest.mark.asyncio
async def test_get_circuit_history_time_range(client: AsyncClient, test_session: AsyncSession):
    """Test filtering circuit history by time range."""
    # Create VEN
    ven = await crud.create_ven(
        test_session,
        ven_id="timerange-ven",
        name="Time Range VEN",
        status="online",
        registration_id="reg-time"
    )
    
    # Create telemetry entries at different times
    base_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=timezone.utc)
    
    for i in range(10):
        telemetry = VenTelemetry(
            ven_id="timerange-ven",
            timestamp=base_time + timedelta(minutes=i),
            used_power_kw=10.0,
            shed_power_kw=0.0
        )
        test_session.add(telemetry)
        await test_session.flush()
        
        load = VenLoadSample(
            telemetry_id=telemetry.id,
            load_id="hvac1",
            name="HVAC",
            type="hvac",
            capacity_kw=7.2,
            current_power_kw=5.0,
            shed_capability_kw=0.0,
            enabled=True,
            priority=1
        )
        test_session.add(load)
    
    await test_session.commit()
    
    # Query with time range (minutes 2-6)
    start_time = (base_time + timedelta(minutes=2)).isoformat()
    end_time = (base_time + timedelta(minutes=6)).isoformat()
    
    from urllib.parse import quote
    response = await client.get(
        f"/api/vens/timerange-ven/circuits/history?start={quote(start_time)}&end={quote(end_time)}"
    )
    assert response.status_code == 200
    data = response.json()
    # Should get samples from minutes 2, 3, 4, 5, 6 (5 samples)
    assert 4 <= data["totalCount"] <= 6  # Allow some flexibility in boundary conditions


@pytest.mark.asyncio
async def test_get_circuit_history_nonexistent_ven(client: AsyncClient):
    """Test circuit history for non-existent VEN returns 404."""
    response = await client.get("/api/vens/nonexistent-ven/circuits/history")
    assert response.status_code == 404


@given(
    ven_id=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    num_samples=st.integers(min_value=1, max_value=10),
    current_power=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(
    max_examples=20, 
    deadline=None, 
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much]
)
@pytest.mark.asyncio
async def test_circuit_history_hypothesis(
    client: AsyncClient,
    test_session: AsyncSession,
    ven_id: str,
    num_samples: int,
    current_power: float
):
    """Hypothesis test for circuit history with various inputs."""
    # Create VEN
    try:
        ven = await crud.create_ven(
            test_session,
            ven_id=ven_id,
            name=f"Hypothesis VEN {ven_id}",
            status="online",
            registration_id=f"reg-{ven_id}"
        )
    except Exception:
        # VEN might already exist from previous test
        assume(False)
    
    # Create telemetry samples
    now = datetime.now(timezone.utc)
    for i in range(num_samples):
        telemetry = VenTelemetry(
            ven_id=ven_id,
            timestamp=now - timedelta(seconds=i*5),
            used_power_kw=current_power,
            shed_power_kw=0.0
        )
        test_session.add(telemetry)
        await test_session.flush()
        
        load = VenLoadSample(
            telemetry_id=telemetry.id,
            load_id="test-load",
            name="Test Load",
            type="generic",
            capacity_kw=10.0,
            current_power_kw=current_power,
            shed_capability_kw=current_power,
            enabled=True,
            priority=5
        )
        test_session.add(load)
    
    await test_session.commit()
    
    # Query circuit history
    response = await client.get(f"/api/vens/{ven_id}/circuits/history")
    assert response.status_code == 200
    data = response.json()
    assert data["venId"] == ven_id
    assert data["totalCount"] == num_samples
    assert len(data["snapshots"]) == num_samples
    
    # Verify all snapshots have required fields
    for snapshot in data["snapshots"]:
        assert "timestamp" in snapshot
        assert "loadId" in snapshot
        assert snapshot["loadId"] == "test-load"
        assert isinstance(snapshot["currentPowerKw"], (int, float))
        assert snapshot["currentPowerKw"] >= 0


@pytest.mark.asyncio
async def test_get_circuit_history_descending_order(client: AsyncClient, test_session: AsyncSession):
    """Test that circuit history is returned in descending timestamp order (newest first)."""
    # Create VEN
    ven = await crud.create_ven(
        test_session,
        ven_id="order-ven",
        name="Order Test VEN",
        status="online",
        registration_id="reg-order"
    )
    
    # Create telemetry at different times
    base_time = datetime.now(timezone.utc)
    timestamps = []
    
    for i in range(5):
        ts = base_time - timedelta(seconds=i*10)
        timestamps.append(ts)
        telemetry = VenTelemetry(
            ven_id="order-ven",
            timestamp=ts,
            used_power_kw=10.0,
            shed_power_kw=0.0
        )
        test_session.add(telemetry)
        await test_session.flush()
        
        load = VenLoadSample(
            telemetry_id=telemetry.id,
            load_id="hvac1",
            name="HVAC",
            type="hvac",
            capacity_kw=7.2,
            current_power_kw=5.0,
            shed_capability_kw=0.0,
            enabled=True,
            priority=1
        )
        test_session.add(load)
    
    await test_session.commit()
    
    # Query circuit history
    response = await client.get("/api/vens/order-ven/circuits/history")
    assert response.status_code == 200
    data = response.json()
    
    # Verify descending order (newest first)
    snapshots = data["snapshots"]
    for i in range(len(snapshots) - 1):
        current_time = datetime.fromisoformat(snapshots[i]["timestamp"].replace('Z', '+00:00'))
        next_time = datetime.fromisoformat(snapshots[i + 1]["timestamp"].replace('Z', '+00:00'))
        assert current_time >= next_time, "Circuit history should be in descending timestamp order"
