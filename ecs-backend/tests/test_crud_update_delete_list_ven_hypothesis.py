import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from hypothesis import given, strategies as st, settings
from app.models.ven import VEN
from app.crud import create_ven, update_ven, delete_ven, list_vens
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime

@settings(max_examples=10)
@given(
    ven_id=st.text(min_size=1, max_size=10),
    name=st.text(min_size=1, max_size=20),
    status=st.text(min_size=1, max_size=10),
    registration_id=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    latitude=st.one_of(st.none(), st.floats(min_value=-90, max_value=90)),
    longitude=st.one_of(st.none(), st.floats(min_value=-180, max_value=180)),
    new_name=st.text(min_size=1, max_size=20),
    new_status=st.text(min_size=1, max_size=10)
)
@pytest.mark.asyncio
async def test_update_delete_list_ven_property(
    ven_id,
    name,
    status,
    registration_id,
    latitude,
    longitude,
    new_name,
    new_status
):
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: c.execute(text('''
            CREATE TABLE vens (
                ven_id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                registration_id VARCHAR,
                latitude FLOAT,
                longitude FLOAT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')))
    async with AsyncSessionLocal() as db_session:
        ven = await create_ven(
            db_session,
            ven_id=ven_id,
            name=name,
            status=status,
            registration_id=registration_id,
            latitude=latitude,
            longitude=longitude
        )
        # Update VEN
        updated = await update_ven(db_session, ven, {"name": new_name, "status": new_status})
        assert updated.name == new_name
        assert updated.status == new_status
        # List VENs
        vens = await list_vens(db_session)
        assert any(v.ven_id == ven_id for v in vens)
        # Delete VEN
        await delete_ven(db_session, ven)
        vens_after = await list_vens(db_session)
        assert all(v.ven_id != ven_id for v in vens_after)
