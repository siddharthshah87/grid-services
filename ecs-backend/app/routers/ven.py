from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.dependencies import get_session
from app.routers.utils import build_history_response, build_ven_payload
from app.schemas.api_models import (
    HistoryResponse,
    Load,
    ShedCommand,
    Ven,
    VenCreate,
    VenSummary,
    VenUpdate,
)

router = APIRouter()


async def _ensure_ven(session: AsyncSession, ven_id: str):
    ven = await crud.get_ven(session, ven_id)
    if ven is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VEN not found")
    return ven


def _load_from_sample(sample) -> Load:
    return Load(
        id=sample.load_id,
        type=sample.type or "unknown",
        capacityKw=sample.capacity_kw or 0.0,
        shedCapabilityKw=sample.shed_capability_kw or 0.0,
        currentPowerKw=sample.current_power_kw or 0.0,
        name=sample.name,
    )


@router.get("/", response_model=list[Ven])
async def list_vens_v2(session: AsyncSession = Depends(get_session)):
    vens = await crud.list_vens(session)
    ven_ids = [ven.ven_id for ven in vens]
    statuses = await crud.latest_status_map(session, ven_ids)
    telemetry = await crud.latest_telemetry_map(session, ven_ids)
    return [
        build_ven_payload(ven, statuses.get(ven.ven_id), telemetry.get(ven.ven_id))
        for ven in vens
    ]


@router.post("/", response_model=Ven, status_code=status.HTTP_201_CREATED)
async def create_ven_v2(payload: VenCreate, session: AsyncSession = Depends(get_session)):
    ven_id = f"ven-{uuid4().hex[:8]}"
    ven = await crud.create_ven(
        session,
        ven_id=ven_id,
        name=payload.name,
        status=payload.status or "active",
        registration_id=payload.registrationId,
        latitude=payload.location.lat,
        longitude=payload.location.lon,
    )
    statuses = await crud.latest_status_map(session, [ven.ven_id])
    telemetry = await crud.latest_telemetry_map(session, [ven.ven_id])
    return build_ven_payload(ven, statuses.get(ven.ven_id), telemetry.get(ven.ven_id))


@router.get("/summary", response_model=list[VenSummary])
async def list_vens_summary(session: AsyncSession = Depends(get_session)):
    vens = await crud.list_vens(session)
    ven_ids = [ven.ven_id for ven in vens]
    statuses = await crud.latest_status_map(session, ven_ids)
    telemetry = await crud.latest_telemetry_map(session, ven_ids)
    summaries: list[VenSummary] = []
    for ven in vens:
        status = statuses.get(ven.ven_id)
        telem = telemetry.get(ven.ven_id)
        payload = build_ven_payload(ven, status, telem)
        last_seen = None
        if telem:
            ts = telem.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            last_seen = ts.isoformat()
        summaries.append(
            VenSummary(
                id=payload.id,
                name=payload.name,
                location=f"{payload.location.lat:.3f}, {payload.location.lon:.3f}",
                status=payload.status,
                controllablePower=round(payload.metrics.shedAvailabilityKw, 3),
                currentPower=round(payload.metrics.currentPowerKw, 3),
                address=f"Lat {payload.location.lat:.3f} / Lon {payload.location.lon:.3f}",
                lastSeen=last_seen or payload.createdAt.isoformat(),
                responseTime=0,
            )
        )
    return summaries


@router.get("/{ven_id}", response_model=Ven)
async def get_ven_v2(ven_id: str, session: AsyncSession = Depends(get_session)):
    ven = await _ensure_ven(session, ven_id)
    statuses = await crud.latest_status_map(session, [ven_id])
    telemetry = await crud.latest_telemetry_map(session, [ven_id])
    return build_ven_payload(ven, statuses.get(ven_id), telemetry.get(ven_id), include_loads=True)


@router.patch("/{ven_id}", response_model=Ven)
async def patch_ven_v2(
    ven_id: str,
    update: VenUpdate,
    session: AsyncSession = Depends(get_session),
):
    ven = await _ensure_ven(session, ven_id)
    data = update.model_dump(exclude_unset=True)
    location = data.pop("location", None)
    if location:
        data["latitude"] = location.lat
        data["longitude"] = location.lon
    registration = data.pop("registrationId", None)
    if registration is not None:
        data["registration_id"] = registration
    if data:
        ven = await crud.update_ven(session, ven, data)
    statuses = await crud.latest_status_map(session, [ven_id])
    telemetry = await crud.latest_telemetry_map(session, [ven_id])
    return build_ven_payload(ven, statuses.get(ven_id), telemetry.get(ven_id), include_loads=True)


@router.delete("/{ven_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ven_v2(ven_id: str, session: AsyncSession = Depends(get_session)):
    ven = await _ensure_ven(session, ven_id)
    await crud.delete_ven(session, ven)
    return None


@router.get("/{ven_id}/loads", response_model=list[Load])
async def list_ven_loads(ven_id: str, session: AsyncSession = Depends(get_session)):
    await _ensure_ven(session, ven_id)
    telemetry = await crud.latest_telemetry_map(session, [ven_id])
    latest = telemetry.get(ven_id)
    if not latest:
        return []
    return [_load_from_sample(sample) for sample in latest.loads]


@router.get("/{ven_id}/loads/{load_id}", response_model=Load)
async def get_ven_load(ven_id: str, load_id: str, session: AsyncSession = Depends(get_session)):
    await _ensure_ven(session, ven_id)
    telemetry = await crud.latest_telemetry_map(session, [ven_id])
    latest = telemetry.get(ven_id)
    if not latest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")
    for sample in latest.loads:
        if sample.load_id == load_id:
            return _load_from_sample(sample)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")


@router.patch("/{ven_id}/loads/{load_id}", response_model=Load)
async def update_ven_load(ven_id: str, load_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Load updates not yet supported")


@router.post("/{ven_id}/loads/{load_id}/commands/shed", status_code=status.HTTP_202_ACCEPTED)
async def shed_ven_load(ven_id: str, load_id: str, cmd: ShedCommand):
    return {"status": "accepted", "venId": ven_id, "loadId": load_id, "amountKw": cmd.amountKw}


@router.get("/{ven_id}/history", response_model=HistoryResponse)
async def ven_history(
    ven_id: str,
    session: AsyncSession = Depends(get_session),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    granularity: str | None = Query(default="5m"),
):
    await _ensure_ven(session, ven_id)
    telemetries = await crud.telemetry_for_ven(session, ven_id, start=start, end=end)
    return build_history_response(telemetries, granularity)


@router.get("/{ven_id}/loads/{load_id}/history", response_model=HistoryResponse)
async def ven_load_history(
    ven_id: str,
    load_id: str,
    session: AsyncSession = Depends(get_session),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    granularity: str | None = Query(default="5m"),
):
    await _ensure_ven(session, ven_id)
    telemetries = await crud.telemetry_for_ven(session, ven_id, start=start, end=end)
    filtered = []
    for telem in telemetries:
        loads = [load for load in telem.loads if load.load_id == load_id]
        if loads:
            filtered.append(
                SimpleNamespace(
                    timestamp=telem.timestamp,
                    used_power_kw=sum(load.current_power_kw or 0.0 for load in loads),
                    shed_power_kw=sum(load.shed_capability_kw or 0.0 for load in loads),
                    requested_reduction_kw=telem.requested_reduction_kw,
                    event_id=telem.event_id,
                )
            )
    return build_history_response(filtered, granularity)
