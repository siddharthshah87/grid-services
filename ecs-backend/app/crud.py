from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import VEN, VenLoadSample, VenStatus, VenTelemetry


async def create_ven(session: AsyncSession, ven: VEN) -> VEN:
    session.add(ven)
    await session.commit()
    await session.refresh(ven)
    return ven


async def get_ven(session: AsyncSession, ven_id: str) -> Optional[VEN]:
    result = await session.execute(select(VEN).where(VEN.ven_id == ven_id))
    return result.scalar_one_or_none()


async def ven_exists(session: AsyncSession, ven_id: str) -> bool:
    result = await session.execute(select(func.count()).select_from(VEN).where(VEN.ven_id == ven_id))
    return (result.scalar_one() or 0) > 0


async def latest_network_telemetry(session: AsyncSession) -> list[VenTelemetry]:
    """Return the most recent telemetry row per VEN."""

    latest_subquery = (
        select(
            VenTelemetry.ven_id.label("ven_id"),
            func.max(VenTelemetry.timestamp).label("max_ts"),
        )
        .group_by(VenTelemetry.ven_id)
        .subquery()
    )

    stmt = (
        select(VenTelemetry)
        .join(
            latest_subquery,
            and_(
                VenTelemetry.ven_id == latest_subquery.c.ven_id,
                VenTelemetry.timestamp == latest_subquery.c.max_ts,
            ),
        )
    )

    result = await session.execute(stmt)
    return result.scalars().all()


async def compute_network_stats(session: AsyncSession) -> dict[str, object]:
    """Aggregate the latest telemetry for all VENs into summary metrics."""

    telemetry_rows = await latest_network_telemetry(session)
    ven_count_result = await session.execute(select(func.count(VEN.ven_id)))
    ven_count = ven_count_result.scalar() or 0

    used_total = sum(row.used_power_kw or 0.0 for row in telemetry_rows)
    shed_total = sum(row.shed_power_kw or 0.0 for row in telemetry_rows)

    statuses = await latest_status_by_ven(session)
    online_vens = sum(1 for status in statuses.values() if status.status == "online")

    average_house_power = used_total / ven_count if ven_count else None

    return {
        "venCount": ven_count,
        "controllablePowerKw": round(shed_total, 3),
        "potentialLoadReductionKw": round(shed_total, 3),
        "householdUsageKw": round(used_total, 3),
        "onlineVens": online_vens if ven_count else 0,
        "currentLoadReductionKw": round(shed_total, 3),
        "networkEfficiency": None,
        "averageHousePower": round(average_house_power, 3) if average_house_power is not None else None,
        "totalHousePowerToday": None,
    }


async def latest_status_by_ven(session: AsyncSession) -> dict[str, VenStatus]:
    latest_subquery = (
        select(
            VenStatus.ven_id.label("ven_id"),
            func.max(VenStatus.recorded_at).label("max_ts"),
        )
        .group_by(VenStatus.ven_id)
        .subquery()
    )

    stmt = (
        select(VenStatus)
        .join(
            latest_subquery,
            and_(
                VenStatus.ven_id == latest_subquery.c.ven_id,
                VenStatus.recorded_at == latest_subquery.c.max_ts,
            ),
        )
    )

    result = await session.execute(stmt)
    return {status.ven_id: status for status in result.scalars().all()}


async def latest_load_samples_for_ven(session: AsyncSession, ven_id: str) -> list[VenLoadSample]:
    latest_subquery = (
        select(
            VenLoadSample.ven_id.label("ven_id"),
            VenLoadSample.load_id.label("load_id"),
            func.max(VenLoadSample.timestamp).label("max_ts"),
        )
        .where(VenLoadSample.ven_id == ven_id)
        .group_by(VenLoadSample.ven_id, VenLoadSample.load_id)
        .subquery()
    )

    stmt = (
        select(VenLoadSample)
        .join(
            latest_subquery,
            and_(
                VenLoadSample.ven_id == latest_subquery.c.ven_id,
                VenLoadSample.load_id == latest_subquery.c.load_id,
                VenLoadSample.timestamp == latest_subquery.c.max_ts,
            ),
        )
        .order_by(VenLoadSample.load_id)
    )

    result = await session.execute(stmt)
    return result.scalars().all()


async def aggregate_load_type_stats(session: AsyncSession) -> list[dict[str, float | str]]:
    latest_subquery = (
        select(
            VenLoadSample.ven_id.label("ven_id"),
            VenLoadSample.load_id.label("load_id"),
            func.max(VenLoadSample.timestamp).label("max_ts"),
        )
        .group_by(VenLoadSample.ven_id, VenLoadSample.load_id)
        .subquery()
    )

    stmt = (
        select(VenLoadSample)
        .join(
            latest_subquery,
            and_(
                VenLoadSample.ven_id == latest_subquery.c.ven_id,
                VenLoadSample.load_id == latest_subquery.c.load_id,
                VenLoadSample.timestamp == latest_subquery.c.max_ts,
            ),
        )
    )

    result = await session.execute(stmt)
    rows = result.scalars().all()

    by_type: dict[str, dict[str, float | str]] = {}
    for sample in rows:
        load_type = sample.load_type or "unknown"
        entry = by_type.setdefault(
            load_type,
            {
                "type": load_type,
                "totalCapacityKw": 0.0,
                "totalShedCapabilityKw": 0.0,
                "currentUsageKw": 0.0,
            },
        )

        capacity = sample.capacity_kw
        if capacity is None:
            shed_capability = sample.shed_capability_kw if sample.shed_capability_kw is not None else sample.shed_power_kw
            capacity = (sample.used_power_kw or 0.0) + (shed_capability or 0.0)
        entry["totalCapacityKw"] = float(entry["totalCapacityKw"]) + (capacity or 0.0)

        shed_capability_value = sample.shed_capability_kw if sample.shed_capability_kw is not None else sample.shed_power_kw
        entry["totalShedCapabilityKw"] = float(entry["totalShedCapabilityKw"]) + (shed_capability_value or 0.0)
        entry["currentUsageKw"] = float(entry["currentUsageKw"]) + max(sample.used_power_kw or 0.0, 0.0)

    for entry in by_type.values():
        entry["totalCapacityKw"] = round(float(entry["totalCapacityKw"]), 3)
        entry["totalShedCapabilityKw"] = round(float(entry["totalShedCapabilityKw"]), 3)
        entry["currentUsageKw"] = round(float(entry["currentUsageKw"]), 3)

    return list(by_type.values())


async def latest_load_sample(session: AsyncSession, ven_id: str, load_id: str) -> Optional[VenLoadSample]:
    stmt = (
        select(VenLoadSample)
        .where(and_(VenLoadSample.ven_id == ven_id, VenLoadSample.load_id == load_id))
        .order_by(desc(VenLoadSample.timestamp))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def telemetry_history(
    session: AsyncSession,
    *,
    ven_id: Optional[str] = None,
    load_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> list[VenTelemetry | VenLoadSample]:
    """Fetch telemetry rows filtered by VEN/load/time."""

    if load_id:
        stmt = select(VenLoadSample).where(
            and_(
                VenLoadSample.ven_id == ven_id,
                VenLoadSample.load_id == load_id,
            )
        )
        if start:
            stmt = stmt.where(VenLoadSample.timestamp >= start)
        if end:
            stmt = stmt.where(VenLoadSample.timestamp <= end)
        stmt = stmt.order_by(VenLoadSample.timestamp)
        result = await session.execute(stmt)
        return result.scalars().all()

    stmt = select(VenTelemetry)

    if ven_id:
        stmt = stmt.where(VenTelemetry.ven_id == ven_id)
    if start:
        stmt = stmt.where(VenTelemetry.timestamp >= start)
    if end:
        stmt = stmt.where(VenTelemetry.timestamp <= end)

    stmt = stmt.order_by(VenTelemetry.timestamp)

    result = await session.execute(stmt)
    return result.scalars().all()


async def network_history(
    session: AsyncSession,
    *,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> list[VenTelemetry]:
    stmt = select(VenTelemetry)
    if start:
        stmt = stmt.where(VenTelemetry.timestamp >= start)
    if end:
        stmt = stmt.where(VenTelemetry.timestamp <= end)

    stmt = stmt.order_by(VenTelemetry.timestamp)

    result = await session.execute(stmt)
    return result.scalars().all()


def bucketize_telemetry(
    rows: Iterable[VenTelemetry | VenLoadSample],
    *,
    interval: timedelta,
) -> list[dict[str, object]]:
    """Aggregate telemetry rows into time buckets."""

    if interval <= timedelta(0):
        raise ValueError("Interval must be positive")

    bucket_map: defaultdict[datetime, dict[str, float]] = defaultdict(lambda: {"used": 0.0, "shed": 0.0})

    for row in rows:
        timestamp: datetime = getattr(row, "timestamp")
        bucket = _truncate_timestamp(timestamp, interval)
        bucket_map[bucket]["used"] += float(getattr(row, "used_power_kw", 0.0) or 0.0)
        bucket_map[bucket]["shed"] += float(getattr(row, "shed_power_kw", 0.0) or 0.0)

    return [
        {
            "timestamp": bucket,
            "used_power_kw": values["used"],
            "shed_power_kw": values["shed"],
        }
        for bucket, values in sorted(bucket_map.items())
    ]


def _truncate_timestamp(ts: datetime, interval: timedelta) -> datetime:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)

    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = ts - epoch
    seconds = int(interval.total_seconds())
    bucket_seconds = int(delta.total_seconds()) // seconds * seconds
    return epoch + timedelta(seconds=bucket_seconds)
