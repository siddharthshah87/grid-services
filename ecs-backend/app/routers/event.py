from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.dependencies import get_session
from app.schemas.event import EventCreate, EventMetrics, EventRead, EventWithMetrics


router = APIRouter()


@router.get("/", response_model=List[EventRead])
async def list_events_v2(session: AsyncSession = Depends(get_session)):
    return await crud.list_events(session)


@router.get("/current", response_model=EventWithMetrics | None)
async def current_event_v2(session: AsyncSession = Depends(get_session)):
    event = await crud.get_current_event(session)
    if not event:
        return None

    data = EventWithMetrics.model_validate(event)
    return data.model_copy(
        update={
            "current_reduction_kw": data.current_reduction_kw or 0.0,
            "vens_responding": data.vens_responding or 0,
            "avg_response_ms": data.avg_response_ms or 0,
        }
    )


@router.get("/history", response_model=List[EventRead])
async def history_events_v2(
    start: str | None = None,
    end: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    # Filtering by time range is not yet implemented.
    return await crud.list_events(session)


@router.post("/", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event_v2(payload: EventCreate, session: AsyncSession = Depends(get_session)):
    return await crud.create_event(session, payload.model_dump())


@router.get("/{event_id}", response_model=EventRead)
async def get_event_v2(event_id: str, session: AsyncSession = Depends(get_session)):
    event = await crud.get_event(session, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.get("/ven/{ven_id}", response_model=List[EventRead])
async def get_events_for_ven(ven_id: str, session: AsyncSession = Depends(get_session)):
    return await crud.list_events_for_ven(session, ven_id)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_v2(event_id: str, session: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_event(session, event_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")


@router.post("/{event_id}/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_event_v2(event_id: str, session: AsyncSession = Depends(get_session)):
    event = await crud.get_event(session, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return {"status": "stopping", "eventId": event_id}


@router.get("/{event_id}/metrics", response_model=EventMetrics)
async def event_metrics_v2(event_id: str, session: AsyncSession = Depends(get_session)):
    event = await crud.get_event(session, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventMetrics(current_reduction_kw=0.0, vens_responding=0, avg_response_ms=0)
