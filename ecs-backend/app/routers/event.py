from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.dependencies import get_session
from app.models.event import Event as EventModel
from app.models.telemetry import VenTelemetry
from app.schemas.api_models import Event, EventCreate, EventMetrics, EventWithMetrics, EventDetail, VenParticipation

router = APIRouter()


async def _ensure_event(session: AsyncSession, event_id: str) -> EventModel:
    event = await crud.get_event(session, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


def _event_to_api(event: EventModel, reduction: float = 0.0) -> Event:
    return Event(
        id=event.event_id,
        status=event.status,
        startTime=event.start_time,
        endTime=event.end_time,
        requestedReductionKw=event.requested_reduction_kw,
        actualReductionKw=reduction,
    )


async def _reduction_map(session: AsyncSession, event_ids: list[str]) -> dict[str, float]:
    if not event_ids:
        return {}
    stmt = (
        select(VenTelemetry.event_id, func.coalesce(func.sum(VenTelemetry.shed_power_kw), 0.0))
        .where(VenTelemetry.event_id.in_(event_ids))
        .group_by(VenTelemetry.event_id)
    )
    result = await session.execute(stmt)
    return {row[0]: float(row[1] or 0.0) for row in result.all()}


async def _event_metrics(session: AsyncSession, event_id: str) -> EventMetrics:
    stmt = (
        select(
            func.coalesce(func.sum(VenTelemetry.shed_power_kw), 0.0),
            func.count(func.distinct(VenTelemetry.ven_id)),
        )
        .where(VenTelemetry.event_id == event_id)
    )
    result = await session.execute(stmt)
    total, responding = result.one_or_none() or (0.0, 0)
    return EventMetrics(
        currentReductionKw=float(total or 0.0),
        vensResponding=int(responding or 0),
        avgResponseMs=0,
    )


async def _ven_participation(session: AsyncSession, event_id: str) -> list[VenParticipation]:
    """Get VEN participation details for an event."""
    from app.models.ven import VEN as VenModel
    
    # Aggregate shed power per VEN for this event
    stmt = (
        select(
            VenTelemetry.ven_id,
            func.coalesce(func.sum(VenTelemetry.shed_power_kw), 0.0).label('total_shed'),
        )
        .where(VenTelemetry.event_id == event_id)
        .group_by(VenTelemetry.ven_id)
    )
    result = await session.execute(stmt)
    shed_map = {row[0]: float(row[1]) for row in result.all()}
    
    # Get VEN details
    if not shed_map:
        return []
    
    ven_stmt = select(VenModel).where(VenModel.ven_id.in_(list(shed_map.keys())))
    ven_result = await session.execute(ven_stmt)
    vens = ven_result.scalars().all()
    
    participation = []
    for ven in vens:
        participation.append(VenParticipation(
            venId=ven.ven_id,
            venName=ven.name,
            shedKw=shed_map.get(ven.ven_id, 0.0),
            status="responded",  # Could be enhanced with actual status tracking
        ))
    
    return participation


@router.get("/", response_model=list[Event])
async def list_events_v2(session: AsyncSession = Depends(get_session)):
    events = await crud.list_events(session)
    reductions = await _reduction_map(session, [event.event_id for event in events])
    return [_event_to_api(event, reductions.get(event.event_id, 0.0)) for event in events]


@router.get("/current", response_model=EventWithMetrics | None)
async def current_event_v2(session: AsyncSession = Depends(get_session)):
    now = datetime.now(UTC)
    stmt = (
        select(EventModel)
        .where(EventModel.status.in_(["active", "in_progress"]))
        .order_by(EventModel.start_time.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    event = result.scalar_one_or_none()
    if event is None:
        stmt = (
            select(EventModel)
            .where(EventModel.start_time <= now, EventModel.end_time >= now)
            .order_by(EventModel.start_time.asc())
            .limit(1)
        )
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()
    if event is None:
        return None
    metrics = await _event_metrics(session, event.event_id)
    base = _event_to_api(event, metrics.currentReductionKw)
    return EventWithMetrics(**base.model_dump(), **metrics.model_dump())


@router.get("/history", response_model=list[Event])
async def history_events_v2(
    session: AsyncSession = Depends(get_session),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
):
    stmt = select(EventModel)
    if start is not None:
        stmt = stmt.where(EventModel.start_time >= start)
    if end is not None:
        stmt = stmt.where(EventModel.start_time <= end)
    stmt = stmt.order_by(EventModel.start_time.asc())
    result = await session.execute(stmt)
    events = result.scalars().all()
    reductions = await _reduction_map(session, [event.event_id for event in events])
    return [_event_to_api(event, reductions.get(event.event_id, 0.0)) for event in events]


@router.post("/", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event_v2(payload: EventCreate, session: AsyncSession = Depends(get_session)):
    event_id = f"evt-{uuid4().hex[:8]}"
    event = await crud.create_event(
        session,
        event_id=event_id,
        status=payload.status or "scheduled",
        start_time=payload.startTime,
        end_time=payload.endTime,
        requested_reduction_kw=payload.requestedReductionKw,
    )
    reduction = (await _reduction_map(session, [event.event_id])).get(event.event_id, 0.0)
    return _event_to_api(event, reduction)


@router.get("/{event_id}", response_model=EventDetail)
async def get_event_v2(event_id: str, session: AsyncSession = Depends(get_session)):
    event = await _ensure_event(session, event_id)
    metrics = await _event_metrics(session, event.event_id)
    ven_participation = await _ven_participation(session, event.event_id)
    base = _event_to_api(event, metrics.currentReductionKw)
    return EventDetail(
        **base.model_dump(),
        currentReductionKw=metrics.currentReductionKw,
        vensResponding=metrics.vensResponding,
        avgResponseMs=metrics.avgResponseMs,
        vens=ven_participation if ven_participation else None,
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_v2(event_id: str, session: AsyncSession = Depends(get_session)):
    event = await _ensure_event(session, event_id)
    await crud.delete_event(session, event)
    return None


@router.post("/{event_id}/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_event_v2(event_id: str, session: AsyncSession = Depends(get_session)):
    event = await _ensure_event(session, event_id)
    updated = await crud.update_event(session, event, {"status": "completed"})
    return {"status": "stopping", "eventId": updated.event_id}


@router.get("/{event_id}/metrics", response_model=EventMetrics)
async def event_metrics_v2(event_id: str, session: AsyncSession = Depends(get_session)):
    await _ensure_event(session, event_id)
    return await _event_metrics(session, event_id)
