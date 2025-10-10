import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
import pytest
from hypothesis import given, strategies as st
from app.models.telemetry import VenStatus
from app.crud import latest_status_map
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime, timezone

from hypothesis import settings

@settings(max_examples=5)
@given(
    ven_id=st.text(min_size=1, max_size=10),
    status=st.text(min_size=1, max_size=10),
    current_power_kw=st.one_of(st.none(), st.floats(min_value=-10000, max_value=10000)),
    shed_availability_kw=st.one_of(st.none(), st.floats(min_value=0, max_value=10000)),
    active_event_id=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    raw_payload=st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.integers())),
    created_at=st.datetimes(),
    timestamp=st.datetimes()
)
@pytest.mark.asyncio
async def test_latest_status_map_property(
    ven_id,
    status,
    current_power_kw,
    shed_availability_kw,
    active_event_id,
    raw_payload,
    created_at,
    timestamp
):
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: c.execute(text('''
            CREATE TABLE ven_status (
                id INTEGER PRIMARY KEY,
                ven_id VARCHAR NOT NULL,
                timestamp DATETIME NOT NULL,
                status VARCHAR NOT NULL,
                current_power_kw FLOAT,
                shed_availability_kw FLOAT,
                active_event_id VARCHAR,
                raw_payload JSON,
                created_at DATETIME NOT NULL
            )
        ''')))
    async with AsyncSessionLocal() as db_session:
        # Insert two status rows for the same VEN, with different timestamps
        vs1 = VenStatus(
            ven_id=ven_id,
            timestamp=timestamp,
            status=status,
            current_power_kw=current_power_kw,
            shed_availability_kw=shed_availability_kw,
            active_event_id=active_event_id,
            raw_payload=raw_payload,
            created_at=created_at
        )
        vs2 = VenStatus(
            ven_id=ven_id,
            timestamp=timestamp.replace(year=timestamp.year + 1),
            status=status,
            current_power_kw=current_power_kw,
            shed_availability_kw=shed_availability_kw,
            active_event_id=active_event_id,
            raw_payload=raw_payload,
            created_at=created_at
        )
        db_session.add(vs1)
        db_session.add(vs2)
        await db_session.commit()
        result = await latest_status_map(db_session, ven_ids=[ven_id])
        assert ven_id in result
        # Should return the row with the latest timestamp
        assert result[ven_id].timestamp == vs2.timestamp
