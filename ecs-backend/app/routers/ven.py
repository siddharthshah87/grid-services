from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.dependencies import get_session
from app.models import VenLoadSample
from app.schemas.api_models import (
    HistoryResponse,
    Load,
    ShedCommand,
    TimeseriesPoint,
    Ven,
    VenCreate,
    VenSummary,
    VenUpdate,
)
from app.data.dummy import (
    list_vens,
    get_ven as get_dummy_ven,
    upsert_ven as upsert_dummy_ven,
    ven_summaries,
)

from .utils import format_timestamp, parse_granularity, parse_timestamp


router = APIRouter()


@router.get("/", response_model=List[Ven])
async def list_vens_v2():
    return list_vens()


@router.post("/", response_model=Ven, status_code=201)
async def create_ven_v2(payload: VenCreate):
    new_id = f"ven-{100 + len(list_vens()) + 1}"
    ven = Ven(
        id=new_id,
        name=payload.name,
        status="online",
        location=payload.location,
        loads=[],
        metrics={"currentPowerKw": 0.0, "shedAvailabilityKw": 0.0, "activeEventId": None, "shedLoadIds": []},
    )
    return upsert_dummy_ven(ven)


@router.get("/summary", response_model=List[VenSummary])
async def list_vens_summary():
    """Summarized VEN data tailored for the current UI list view."""
    return ven_summaries()


@router.get("/{ven_id}", response_model=Ven)
async def get_ven_v2(ven_id: str):
    ven = get_dummy_ven(ven_id)
    if not ven:
        raise HTTPException(status_code=404, detail="VEN not found")
    return ven


@router.patch("/{ven_id}", response_model=Ven)
async def patch_ven_v2(ven_id: str, update: VenUpdate):
    ven = get_dummy_ven(ven_id)
    if not ven:
        raise HTTPException(status_code=404, detail="VEN not found")
    data = ven.model_copy(update={k: v for k, v in update.model_dump(exclude_unset=True).items()})
    return upsert_dummy_ven(data)


@router.delete("/{ven_id}", status_code=204)
async def delete_ven_v2(ven_id: str):
    from app.data.dummy import VENS
    if ven_id not in VENS:
        raise HTTPException(status_code=404, detail="VEN not found")
    del VENS[ven_id]
    return {"status": "deleted"}


@router.get("/{ven_id}/loads", response_model=List[Load])
async def list_ven_loads(ven_id: str, session: AsyncSession = Depends(get_session)):
    if not await crud.ven_exists(session, ven_id):
        raise HTTPException(status_code=404, detail="VEN not found")
    samples = await crud.latest_load_samples_for_ven(session, ven_id)
    return [_to_load_model(sample) for sample in samples]


@router.get("/{ven_id}/loads/{load_id}", response_model=Load)
async def get_ven_load(ven_id: str, load_id: str, session: AsyncSession = Depends(get_session)):
    if not await crud.ven_exists(session, ven_id):
        raise HTTPException(status_code=404, detail="VEN not found")
    sample = await crud.latest_load_sample(session, ven_id, load_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Load not found")
    return _to_load_model(sample)


@router.patch("/{ven_id}/loads/{load_id}", response_model=Load)
async def update_ven_load(ven_id: str, load_id: str, update: dict):
    ven = get_dummy_ven(ven_id)
    if not ven:
        raise HTTPException(status_code=404, detail="VEN not found")
    updated = None
    new_loads: List[Load] = []
    for l in ven.loads:
        if l.id == load_id:
            data = l.model_dump()
            data.update({k: v for k, v in update.items() if k in data})
            updated = Load(**data)
            new_loads.append(updated)
        else:
            new_loads.append(l)
    if not updated:
        raise HTTPException(status_code=404, detail="Load not found")
    upsert_dummy_ven(ven.model_copy(update={"loads": new_loads}))
    return updated


@router.post("/{ven_id}/loads/{load_id}/commands/shed", status_code=202)
async def shed_ven_load(ven_id: str, load_id: str, cmd: ShedCommand):
    ven = get_dummy_ven(ven_id)
    if not ven:
        raise HTTPException(status_code=404, detail="VEN not found")
    return {"status": "accepted", "venId": ven_id, "loadId": load_id, "amountKw": cmd.amountKw}


@router.get("/{ven_id}/history", response_model=HistoryResponse)
async def ven_history(
    ven_id: str,
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    granularity: str | None = Query(default="5m"),
    session: AsyncSession = Depends(get_session),
):
    if not await crud.ven_exists(session, ven_id):
        raise HTTPException(status_code=404, detail="VEN not found")

    start_dt = parse_timestamp(start) if start else None
    end_dt = parse_timestamp(end) if end else None
    interval = parse_granularity(granularity)

    rows = await crud.telemetry_history(session, ven_id=ven_id, start=start_dt, end=end_dt)
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


@router.get("/{ven_id}/loads/{load_id}/history", response_model=HistoryResponse)
async def ven_load_history(
    ven_id: str,
    load_id: str,
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    granularity: str | None = Query(default="5m"),
    session: AsyncSession = Depends(get_session),
):
    if not await crud.ven_exists(session, ven_id):
        raise HTTPException(status_code=404, detail="VEN not found")

    sample = await crud.latest_load_sample(session, ven_id, load_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Load not found")

    start_dt = parse_timestamp(start) if start else None
    end_dt = parse_timestamp(end) if end else None
    interval = parse_granularity(granularity)

    rows = await crud.telemetry_history(
        session,
        ven_id=ven_id,
        load_id=load_id,
        start=start_dt,
        end=end_dt,
    )
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


def _to_load_model(sample: VenLoadSample) -> Load:
    payload = sample.payload if isinstance(sample.payload, dict) else {}
    shed_capability = (
        sample.shed_capability_kw if sample.shed_capability_kw is not None else sample.shed_power_kw or 0.0
    )
    capacity = sample.capacity_kw
    if capacity is None:
        capacity = (sample.used_power_kw or 0.0) + (shed_capability or 0.0)

    return Load(
        id=sample.load_id,
        type=sample.load_type or payload.get("type", "unknown"),
        capacityKw=float(capacity or 0.0),
        shedCapabilityKw=float(shed_capability or 0.0),
        currentPowerKw=float(sample.used_power_kw or 0.0),
        name=payload.get("name"),
    )
