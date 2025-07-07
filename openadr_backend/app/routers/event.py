from fastapi import APIRouter
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
