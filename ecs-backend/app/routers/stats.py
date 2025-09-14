from fastapi import APIRouter, Query

from app.schemas.api_models import NetworkStats, LoadTypeStats, HistoryResponse
from app.data.dummy import get_network_stats, get_load_type_stats, sample_history_points


router = APIRouter()


@router.get("/network", response_model=NetworkStats)
async def stats_network():
    return get_network_stats()


@router.get("/loads", response_model=list[LoadTypeStats])
async def stats_loads():
    return get_load_type_stats()


@router.get("/network/history", response_model=HistoryResponse)
async def stats_network_history(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    granularity: str | None = Query(default="5m"),
):
    return sample_history_points(start, end, granularity or "5m")

