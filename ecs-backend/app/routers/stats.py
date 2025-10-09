from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import crud
from app.dependencies import get_session
from app.models.telemetry import VenTelemetry
from app.routers.utils import (
    aggregate_load_stats,
    aggregate_network_stats,
    build_history_response,
)
from app.schemas.api_models import HistoryResponse, LoadTypeStats, NetworkStats

router = APIRouter()


@router.get("/network", response_model=NetworkStats)
async def stats_network(session: AsyncSession = Depends(get_session)):
    vens = await crud.list_vens(session)
    ven_ids = [ven.ven_id for ven in vens]
    statuses = await crud.latest_status_map(session, ven_ids)
    telemetry = await crud.latest_telemetry_map(session, ven_ids)
    return aggregate_network_stats(vens, statuses, telemetry)


@router.get("/loads", response_model=list[LoadTypeStats])
async def stats_loads(session: AsyncSession = Depends(get_session)):
    ven_ids = [ven.ven_id for ven in await crud.list_vens(session)]
    telemetry = await crud.latest_telemetry_map(session, ven_ids)
    stats = aggregate_load_stats(telemetry.values())
    return [
        LoadTypeStats(
            type=load_type,
            totalCapacityKw=round(values["capacity"], 3),
            totalShedCapabilityKw=round(values["shed"], 3),
            currentUsageKw=round(values["usage"], 3),
        )
        for load_type, values in sorted(stats.items())
    ]


@router.get("/network/history", response_model=HistoryResponse)
async def stats_network_history(
    session: AsyncSession = Depends(get_session),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    granularity: str | None = Query(default="5m"),
):
    stmt = select(VenTelemetry).options(selectinload(VenTelemetry.loads))
    if start is not None:
        stmt = stmt.where(VenTelemetry.timestamp >= start)
    else:
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        stmt = stmt.where(VenTelemetry.timestamp >= cutoff)
    if end is not None:
        stmt = stmt.where(VenTelemetry.timestamp <= end)
    stmt = stmt.order_by(VenTelemetry.timestamp.asc())
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return build_history_response(rows, granularity)
