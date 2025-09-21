from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.api_models import Event, EventCreate, EventMetrics
from app.data.dummy import (
    list_events,
    get_event as get_dummy_event,
    set_event as set_dummy_event,
    current_event as get_current_event,
    event_metrics as calc_event_metrics,
)


router = APIRouter()


@router.get("/", response_model=List[Event])
async def list_events_v2():
    return list_events()


@router.post("/", response_model=Event, status_code=201)
async def create_event_v2(payload: EventCreate):
    new_id = f"evt-{len(list_events()) + 1}"
    evt = Event(
        id=new_id,
        status="scheduled",
        startTime=payload.startTime,
        endTime=payload.endTime,
        requestedReductionKw=payload.requestedReductionKw,
        actualReductionKw=0,
    )
    return set_dummy_event(evt)


@router.get("/{event_id}", response_model=Event)
async def get_event_v2(event_id: str):
    evt = get_dummy_event(event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    return evt


@router.delete("/{event_id}", status_code=204)
async def delete_event_v2(event_id: str):
    evt = get_dummy_event(event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    from app.data.dummy import EVENTS

    if event_id in EVENTS:
        del EVENTS[event_id]
    return {"status": "deleted"}


@router.post("/{event_id}/stop", status_code=202)
async def stop_event_v2(event_id: str):
    evt = get_dummy_event(event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    evt.status = "completed"
    set_dummy_event(evt)
    return {"status": "stopping", "eventId": event_id}


@router.get("/current", response_model=Event | None)
async def current_event_v2():
    evt = get_current_event()
    if not evt:
        return None
    metrics = calc_event_metrics(evt.id)
    # Enrich the response with metrics for the UI
    data = evt.model_dump()
    if metrics:
        data.update(
            {
                "currentReductionKw": metrics.currentReductionKw,
                "vensResponding": metrics.vensResponding,
                "avgResponseMs": metrics.avgResponseMs,
            }
        )
    return data


@router.get("/history", response_model=List[Event])
async def history_events_v2(start: str | None = None, end: str | None = None):
    return list_events()


@router.get("/{event_id}/metrics", response_model=EventMetrics)
async def event_metrics_v2(event_id: str):
    metrics = calc_event_metrics(event_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Event not found")
    return metrics
