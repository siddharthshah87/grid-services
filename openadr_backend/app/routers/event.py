from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.event import EventCreate, EventRead
from app.models.event import Event
from app.db.database import get_session

router = APIRouter()

@router.post("/", response_model=EventRead)
async def create_event(
    event: EventCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new event.

    Parameters:
        event: Event data to store.
        session: Database session dependency.

    Returns:
        The persisted event.
    """
    db_event = Event(**event.model_dump())
    session.add(db_event)
    await session.commit()
    await session.refresh(db_event)
    return db_event

@router.get("/", response_model=list[EventRead])
async def list_events(session: AsyncSession = Depends(get_session)):
    """List all events.

    Parameters:
        session: Database session dependency.

    Returns:
        All events in the system.
    """
    result = await session.execute(select(Event))
    return result.scalars().all()


@router.get("/ven/{ven_id}", response_model=list[EventRead])
async def list_events_by_ven(
    ven_id: str,
    session: AsyncSession = Depends(get_session),
):
    """List events associated with a VEN.

    Parameters:
        ven_id: Identifier of the VEN.
        session: Database session dependency.

    Returns:
        Events tied to the specified VEN.
    """
    result = await session.execute(select(Event).where(Event.ven_id == ven_id))
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventRead)
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve a specific event by ID.

    Parameters:
        event_id: Identifier of the event.
        session: Database session dependency.

    Returns:
        The requested event or raises 404 if not found.
    """
    result = await session.execute(select(Event).where(Event.event_id == event_id))
    row = result.scalars().first()
    if row:
        return row
    raise HTTPException(status_code=404, detail="Event not found")


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Remove an event by ID.

    Parameters:
        event_id: Identifier of the event to delete.
        session: Database session dependency.

    Returns:
        HTTP 204 status code on success.
    """
    result = await session.execute(select(Event).where(Event.event_id == event_id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await session.delete(event)
    await session.commit()
    return Response(status_code=204)
