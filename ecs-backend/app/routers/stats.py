from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.dependencies import get_session
from app.schemas.api_models import HistoryResponse, LoadTypeStats, NetworkStats, TimeseriesPoint
from .utils import format_timestamp, parse_granularity, parse_timestamp


router = APIRouter()


@router.get("/network", response_model=NetworkStats)
async def stats_network(session: AsyncSession = Depends(get_session)):
    payload = await crud.compute_network_stats(session)
    return NetworkStats(**payload)


@router.get("/loads", response_model=list[LoadTypeStats])
async def stats_loads(session: AsyncSession = Depends(get_session)):
    rows = await crud.aggregate_load_type_stats(session)
    return [LoadTypeStats(**row) for row in rows]


@router.get("/network/history", response_model=HistoryResponse)
async def stats_network_history(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    granularity: str | None = Query(default="5m"),
    session: AsyncSession = Depends(get_session),
):
    interval = parse_granularity(granularity)
    start_dt = parse_timestamp(start) if start else None
    end_dt = parse_timestamp(end) if end else None

    rows = await crud.network_history(session, start=start_dt, end=end_dt)
    bucketed = crud.bucketize_telemetry(rows, interval=interval) if rows else []

    points = [
        TimeseriesPoint(
            timestamp=format_timestamp(entry["timestamp"]),
            usedPowerKw=round(float(entry["used_power_kw"]), 3),
            shedPowerKw=round(float(entry["shed_power_kw"]), 3),
        )
        for entry in bucketed
    ]

    return HistoryResponse(points=points)

