from fastapi import APIRouter, HTTPException, Depends
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
    db_event = Event(**event.dict())
    session.add(db_event)
    await session.commit()
    await session.refresh(db_event)
    return db_event

@router.get("/", response_model=list[EventRead])
async def list_events(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Event))
    return result.scalars().all()


@router.get("/ven/{ven_id}", response_model=list[EventRead])
async def list_events_by_ven(
    ven_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Event).where(Event.ven_id == ven_id))
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventRead)
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Event).where(Event.event_id == event_id))
    row = result.scalars().first()
    if row:
        return row
    raise HTTPException(status_code=404, detail="Event not found")
