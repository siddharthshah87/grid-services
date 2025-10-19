import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st, settings
from app.models.telemetry import VenTelemetry, VenLoadSample
from app.crud import latest_telemetry_map
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime, timezone, timedelta

@settings(max_examples=10)
@given(
    ven_id=st.text(min_size=1, max_size=10),
    used_power_kw=st.one_of(st.none(), st.floats(min_value=-10000, max_value=10000)),
    shed_power_kw=st.one_of(st.none(), st.floats(min_value=0, max_value=10000)),
    event_id=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    created_at=st.datetimes(),
    timestamp=st.datetimes()
)
@pytest.mark.asyncio
async def test_latest_telemetry_map_property(
    ven_id,
    used_power_kw,
    shed_power_kw,
    event_id,
    created_at,
    timestamp
):
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: c.execute(text('''
            CREATE TABLE ven_telemetry (
                id INTEGER PRIMARY KEY,
                ven_id VARCHAR NOT NULL,
                timestamp DATETIME NOT NULL,
                used_power_kw FLOAT,
                shed_power_kw FLOAT,
                requested_reduction_kw FLOAT,
                event_id VARCHAR,
                battery_soc FLOAT,
                raw_payload JSON,
                created_at DATETIME NOT NULL
            )
        ''')))
        await conn.run_sync(lambda c: c.execute(text('''
            CREATE TABLE ven_load_samples (
                id INTEGER PRIMARY KEY,
                telemetry_id INTEGER NOT NULL,
                load_id VARCHAR NOT NULL,
                name VARCHAR,
                type VARCHAR,
                capacity_kw FLOAT,
                current_power_kw FLOAT,
                shed_capability_kw FLOAT,
                enabled BOOLEAN,
                priority INTEGER,
                raw_payload JSON
            )
        ''')))
    async with AsyncSessionLocal() as db_session:
        # Insert two telemetry rows for the same VEN, with different timestamps
        vt1 = VenTelemetry(
            id=1,
            ven_id=ven_id,
            timestamp=timestamp,
            used_power_kw=used_power_kw,
            shed_power_kw=shed_power_kw,
            requested_reduction_kw=None,
            event_id=event_id,
            battery_soc=None,
            raw_payload=None,
            created_at=created_at,
            loads=[]
        )
        vt2 = VenTelemetry(
            id=2,
            ven_id=ven_id,
            timestamp=timestamp + timedelta(days=365),  # Add 365 days instead of 1 year to avoid leap year issues
            used_power_kw=used_power_kw,
            shed_power_kw=shed_power_kw,
            requested_reduction_kw=None,
            event_id=event_id,
            battery_soc=None,
            raw_payload=None,
            created_at=created_at,
            loads=[]
        )
        db_session.add(vt1)
        db_session.add(vt2)
        await db_session.commit()
        result = await latest_telemetry_map(db_session, ven_ids=[ven_id])
        assert ven_id in result
        # Should return the row with the latest timestamp
        assert result[ven_id].timestamp == vt2.timestamp
