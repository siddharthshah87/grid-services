import asyncio
import json
import os
import sys

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DB_HOST", "test")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_TIMEOUT", "30")
os.environ.setdefault("DB_NAME", "test")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import Settings  # noqa: E402  pylint: disable=wrong-import-position
from app.models import LoadSnapshot, TelemetryLoad, TelemetryReading  # noqa: E402
from app.services import MQTTConsumer  # noqa: E402


@pytest_asyncio.fixture(scope="module")
async def db_fixture(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("mqtt_tests")
    db_file = tmp_dir / "test.db"
    database_url = f"sqlite+aiosqlite:///{db_file}"

    engine = create_async_engine(database_url, future=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    from app.db import database as db

    db.engine = engine
    db.async_session = async_session

    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    async def session_dependency():
        async with async_session() as session:
            yield session

    yield async_session, session_dependency

    await engine.dispose()
    if db_file.exists():
        db_file.unlink()


def build_settings(**overrides) -> Settings:
    base = dict(
        db_host="unused",
        db_port=5432,
        db_user="unused",
        db_password="unused",
        db_name="unused",
        db_timeout=30,
        mqtt_enabled=True,
        mqtt_host="localhost",
        mqtt_port=1883,
        mqtt_use_tls=False,
        backend_loads_topic="ven/loads/test",
    )
    base.update(overrides)
    return Settings(**base)


@pytest.mark.asyncio
async def test_metering_message_persists_records(db_fixture):
    session_factory, dependency = db_fixture
    config = build_settings()
    consumer = MQTTConsumer(config=config, session_factory=dependency)

    payload = {
        "venId": "ven-1",
        "timestamp": 1700000000,
        "power_kw": 3.2,
        "shedPowerKw": 0.6,
        "requestedReductionKw": 1.5,
        "eventId": "evt-1",
        "batterySoc": 0.42,
        "loads": [
            {
                "id": "load-1",
                "type": "hvac",
                "capacityKw": 5.0,
                "currentPowerKw": 2.5,
                "shedCapabilityKw": 1.0,
                "enabled": True,
                "priority": 1,
            }
        ],
    }

    await consumer.handle_message(config.mqtt_topic_metering, json.dumps(payload).encode())

    async with session_factory() as session:
        telemetry_rows = (await session.execute(select(TelemetryReading))).scalars().all()
        assert len(telemetry_rows) == 1
        reading = telemetry_rows[0]
        assert reading.ven_id == "ven-1"
        assert reading.used_power_kw == pytest.approx(3.2)
        assert reading.shed_power_kw == pytest.approx(0.6)
        assert reading.requested_reduction_kw == pytest.approx(1.5)
        assert reading.event_id == "evt-1"
        assert reading.battery_soc == pytest.approx(0.42)

        load_rows = (await session.execute(select(TelemetryLoad))).scalars().all()
        assert len(load_rows) == 1
        load = load_rows[0]
        assert load.load_id == "load-1"
        assert load.type == "hvac"
        assert load.current_power_kw == pytest.approx(2.5)
        assert load.shed_capability_kw == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_load_snapshot_persists_rows(db_fixture):
    session_factory, dependency = db_fixture
    config = build_settings()
    consumer = MQTTConsumer(config=config, session_factory=dependency)

    payload = {
        "venId": "ven-2",
        "timestamp": "2024-05-01T12:00:00Z",
        "loads": [
            {
                "id": "load-10",
                "type": "ev",
                "capacityKw": 7.2,
                "currentPowerKw": 3.1,
                "shedCapabilityKw": 2.0,
                "enabled": False,
                "priority": 2,
            },
            {
                "id": "load-11",
                "type": "battery",
                "capacityKw": 10.0,
                "currentPowerKw": -1.2,
                "shedCapabilityKw": 0.0,
                "enabled": True,
                "priority": 1,
            },
        ],
    }

    await consumer.handle_message(config.backend_loads_topic, json.dumps(payload).encode())

    async with session_factory() as session:
        rows = (await session.execute(select(LoadSnapshot))).scalars().all()
        assert len(rows) == 2
        ids = {row.load_id for row in rows}
        assert ids == {"load-10", "load-11"}
        ven_ids = {row.ven_id for row in rows}
        assert ven_ids == {"ven-2"}

