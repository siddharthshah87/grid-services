"""CRUD helpers shared by routers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy import Select, delete, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.telemetry import VenStatus, VenTelemetry
from app.models.ven import VEN


# ---------------------------------------------------------------------------
# VEN helpers


async def list_vens(session: AsyncSession) -> list[VEN]:
    """Return all VENs ordered by creation time."""

    stmt: Select[tuple[VEN]] = select(VEN).order_by(VEN.created_at.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_ven(session: AsyncSession, ven_id: str) -> VEN | None:
    stmt: Select[tuple[VEN]] = select(VEN).where(VEN.ven_id == ven_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_ven(
    session: AsyncSession,
    *,
    ven_id: str,
    name: str,
    status: str,
    registration_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> VEN:
    ven = VEN(
        ven_id=ven_id,
        name=name,
        status=status,
        registration_id=registration_id,
        latitude=latitude,
        longitude=longitude,
    )
    session.add(ven)
    await session.commit()
    await session.refresh(ven)
    return ven


async def update_ven(session: AsyncSession, ven: VEN, data: dict[str, Any]) -> VEN:
    for key, value in data.items():
        setattr(ven, key, value)
    await session.commit()
    await session.refresh(ven)
    return ven


async def delete_ven(session: AsyncSession, ven: VEN) -> None:
    await session.delete(ven)
    await session.commit()


# ---------------------------------------------------------------------------
# Event helpers


async def list_events(session: AsyncSession) -> list[Event]:
    stmt: Select[tuple[Event]] = select(Event).order_by(Event.start_time.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_event(session: AsyncSession, event_id: str) -> Event | None:
    stmt: Select[tuple[Event]] = select(Event).where(Event.event_id == event_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_event(
    session: AsyncSession,
    *,
    event_id: str,
    status: str,
    start_time,
    end_time,
    requested_reduction_kw: float | None = None,
    ven_id: str | None = None,
    signal_name: str | None = None,
    signal_type: str | None = None,
    signal_payload: str | None = None,
    response_required: str | None = None,
    raw: dict[str, Any] | None = None,
) -> Event:
    event = Event(
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
        raw=raw,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def update_event(session: AsyncSession, event: Event, data: dict[str, Any]) -> Event:
    for key, value in data.items():
        setattr(event, key, value)
    await session.commit()
    await session.refresh(event)
    return event


async def delete_event(session: AsyncSession, event: Event) -> None:
    await session.delete(event)
    await session.commit()


# ---------------------------------------------------------------------------
# Telemetry helpers


async def latest_status_map(
    session: AsyncSession,
    ven_ids: Iterable[str] | None = None,
) -> dict[str, VenStatus]:
    """Return latest status row for each VEN."""

    subquery = (
        select(
            VenStatus.ven_id.label("ven_id"),
            func.max(VenStatus.timestamp).label("max_timestamp"),
        )
    )
    if ven_ids:
        subquery = subquery.where(VenStatus.ven_id.in_(list(ven_ids)))
    subquery = subquery.group_by(VenStatus.ven_id).subquery()

    stmt = (
        select(VenStatus)
        .join(
            subquery,
            (VenStatus.ven_id == subquery.c.ven_id)
            & (VenStatus.timestamp == subquery.c.max_timestamp),
        )
    )
    result = await session.execute(stmt)
    statuses = result.scalars().all()
    return {row.ven_id: row for row in statuses}


async def latest_telemetry_map(
    session: AsyncSession,
    ven_ids: Iterable[str] | None = None,
) -> dict[str, VenTelemetry]:
    """Return latest telemetry sample for each VEN."""

    subquery = (
        select(
            VenTelemetry.ven_id.label("ven_id"),
            func.max(VenTelemetry.timestamp).label("max_timestamp"),
        )
        .group_by(VenTelemetry.ven_id)
    )
    if ven_ids:
        subquery = subquery.where(VenTelemetry.ven_id.in_(list(ven_ids)))
    subquery = subquery.subquery()

    stmt = (
        select(VenTelemetry)
        .options(selectinload(VenTelemetry.loads))
        .join(
            subquery,
            (VenTelemetry.ven_id == subquery.c.ven_id)
            & (VenTelemetry.timestamp == subquery.c.max_timestamp),
        )
    )
    result = await session.execute(stmt)
    rows = result.scalars().unique().all()
    return {row.ven_id: row for row in rows}


async def telemetry_for_ven(
    session: AsyncSession,
    ven_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[VenTelemetry]:
    stmt = (
        select(VenTelemetry)
        .options(selectinload(VenTelemetry.loads))
        .where(VenTelemetry.ven_id == ven_id)
    )
    if start is not None:
        stmt = stmt.where(VenTelemetry.timestamp >= start)
    if end is not None:
        stmt = stmt.where(VenTelemetry.timestamp <= end)
    stmt = stmt.order_by(VenTelemetry.timestamp.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_telemetry_for_event(session: AsyncSession, event_id: str) -> None:
    await session.execute(delete(VenTelemetry).where(VenTelemetry.event_id == event_id))
    await session.commit()
