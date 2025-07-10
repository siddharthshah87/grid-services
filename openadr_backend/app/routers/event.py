from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.schemas.event import EventCreate, EventRead
from app.models.event import Event
from app.db.database import database

router = APIRouter()

@router.post("/", response_model=EventRead)
async def create_event(event: EventCreate):
    query = Event.__table__.insert().values(**event.dict())
    await database.execute(query)
    return event

@router.get("/", response_model=list[EventRead])
async def list_events():
    query = select(Event)
    return await database.fetch_all(query)


@router.get("/ven/{ven_id}", response_model=list[EventRead])
async def list_events_by_ven(ven_id: str):
    query = select(Event).where(Event.ven_id == ven_id)
    return await database.fetch_all(query)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: str):
    query = select(Event).where(Event.event_id == event_id)
    row = await database.fetch_one(query)
    if row:
        return row
    raise HTTPException(status_code=404, detail="Event not found")
