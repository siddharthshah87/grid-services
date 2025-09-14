from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.api_models import Ven, VenCreate, VenUpdate, Load, HistoryResponse, ShedCommand
from app.data.dummy import list_vens, get_ven as get_dummy_ven, upsert_ven as upsert_dummy_ven, sample_history_points


router = APIRouter()


@router.get("/", response_model=List[Ven])
async def list_vens_v2():
    return list_vens()


@router.post("/", response_model=Ven)
async def create_ven_v2(payload: VenCreate):
    # Create a simple ID
    new_id = f"ven-{100 + len(list_vens()) + 1}"
    ven = Ven(
        id=new_id,
        name=payload.name,
        status="active",
        location=payload.location,
        loads=[],
        metrics={"currentPowerKw": 0.0, "shedAvailabilityKw": 0.0, "activeEventId": None, "shedLoadIds": []},
    )
    return upsert_dummy_ven(ven)


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


@router.get("/{ven_id}/loads", response_model=List[Load])
async def list_ven_loads(ven_id: str):
    ven = get_dummy_ven(ven_id)
    if not ven:
        raise HTTPException(status_code=404, detail="VEN not found")
    return ven.loads


@router.get("/{ven_id}/loads/{load_id}", response_model=Load)
async def get_ven_load(ven_id: str, load_id: str):
    ven = get_dummy_ven(ven_id)
    if not ven:
        raise HTTPException(status_code=404, detail="VEN not found")
    for l in ven.loads:
        if l.id == load_id:
            return l
    raise HTTPException(status_code=404, detail="Load not found")


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
    # No-op in dummy mode; accept command
    return {"status": "accepted", "venId": ven_id, "loadId": load_id, "amountKw": cmd.amountKw}


@router.get("/{ven_id}/history", response_model=HistoryResponse)
async def ven_history(ven_id: str):
    if not get_dummy_ven(ven_id):
        raise HTTPException(status_code=404, detail="VEN not found")
    return sample_history_points()


@router.get("/{ven_id}/loads/{load_id}/history", response_model=HistoryResponse)
async def ven_load_history(ven_id: str, load_id: str):
    ven = get_dummy_ven(ven_id)
    if not ven or not any(l.id == load_id for l in ven.loads):
        raise HTTPException(status_code=404, detail="Not found")
    return sample_history_points()

