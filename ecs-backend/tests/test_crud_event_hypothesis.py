import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st, settings
from app.models.event import Event
from app.crud import create_event, get_event, update_event, delete_event, list_events
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime, timedelta

@settings(max_examples=5)
@given(
    event_id=st.text(min_size=1, max_size=10),
    status=st.text(min_size=1, max_size=10),
    start_time=st.datetimes(),
    end_time=st.datetimes(),
    requested_reduction_kw=st.one_of(st.none(), st.floats(min_value=0, max_value=10000)),
    ven_id=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    signal_name=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    signal_type=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    signal_payload=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    response_required=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    raw=st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.integers()))
)
@pytest.mark.asyncio
async def test_event_crud_property(
    event_id,
    status,
    start_time,
    end_time,
    requested_reduction_kw,
    ven_id,
    signal_name,
    signal_type,
    signal_payload,
    response_required,
    raw
):
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: c.execute(text('''
            CREATE TABLE events (
                event_id VARCHAR PRIMARY KEY,
                status VARCHAR NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                requested_reduction_kw FLOAT,
                ven_id VARCHAR,
                signal_name VARCHAR,
                signal_type VARCHAR,
                signal_payload VARCHAR,
                response_required VARCHAR,
                raw JSON
                    , created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')))
    async with AsyncSessionLocal() as db_session:
        # Create event
        evt = await create_event(
            db_session,
            event_id=event_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
            requested_reduction_kw=requested_reduction_kw,
            ven_id=ven_id,
            signal_name=signal_name,
            signal_type=signal_type,
            signal_payload=signal_payload,
            response_required=response_required,
            raw=raw
        )
        assert evt.event_id == event_id
        assert evt.status == status
        # Get event
        evt_fetched = await get_event(db_session, event_id)
        assert evt_fetched is not None
        assert evt_fetched.event_id == event_id
        # Update event
        new_status = "updated"
        updated = await update_event(db_session, evt, {"status": new_status})
        assert updated.status == new_status
        # List events
        events = await list_events(db_session)
        assert any(e.event_id == event_id for e in events)
        # Delete event
        await delete_event(db_session, evt)
        events_after = await list_events(db_session)
        assert all(e.event_id != event_id for e in events_after)
