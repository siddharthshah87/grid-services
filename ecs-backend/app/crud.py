"""Shared database helpers for FastAPI routers."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.ven import VEN
from app.models.event import Event


# ---------------------------------------------------------------------------
# VEN helpers
# ---------------------------------------------------------------------------

async def list_vens(session: AsyncSession) -> Sequence[VEN]:
    """Return all VEN records."""

    result = await session.execute(select(VEN))
    return result.scalars().all()


async def create_ven(session: AsyncSession, ven_data: dict) -> VEN:
    """Create a new VEN and persist it."""

    ven = VEN(**ven_data)
    session.add(ven)
    await session.commit()
    await session.refresh(ven)
    return ven


async def get_ven(session: AsyncSession, ven_id: str) -> VEN | None:
    """Retrieve a VEN by its identifier."""

    result = await session.execute(select(VEN).where(VEN.ven_id == ven_id))
    return result.scalar_one_or_none()


async def update_ven(session: AsyncSession, ven_id: str, updates: dict) -> VEN | None:
    """Update an existing VEN."""

    ven = await get_ven(session, ven_id)
    if not ven:
        return None

    for key, value in updates.items():
        setattr(ven, key, value)

    await session.commit()
    await session.refresh(ven)
    return ven


async def delete_ven(session: AsyncSession, ven_id: str) -> bool:
    """Delete a VEN if it exists."""

    ven = await get_ven(session, ven_id)
    if not ven:
        return False

    await session.delete(ven)
    await session.commit()
    return True


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------

async def list_events(session: AsyncSession) -> Sequence[Event]:
    """Return all Event records."""

    result = await session.execute(select(Event))
    return result.scalars().all()


async def list_events_for_ven(session: AsyncSession, ven_id: str) -> Sequence[Event]:
    result = await session.execute(select(Event).where(Event.ven_id == ven_id))
    return result.scalars().all()


async def create_event(session: AsyncSession, event_data: dict) -> Event:
    event = Event(**event_data)
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def get_event(session: AsyncSession, event_id: str) -> Event | None:
    result = await session.execute(select(Event).where(Event.event_id == event_id))
    return result.scalar_one_or_none()


async def update_event(session: AsyncSession, event_id: str, updates: dict) -> Event | None:
    event = await get_event(session, event_id)
    if not event:
        return None

    for key, value in updates.items():
        setattr(event, key, value)

    await session.commit()
    await session.refresh(event)
    return event


async def delete_event(session: AsyncSession, event_id: str) -> bool:
    event = await get_event(session, event_id)
    if not event:
        return False

    await session.delete(event)
    await session.commit()
    return True


async def get_current_event(session: AsyncSession) -> Event | None:
    """Return the most recent event by start time."""

    result = await session.execute(
        select(Event).order_by(Event.start_time.desc())
    )
    return result.scalars().first()
