from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.dependencies import get_session
from app.schemas.api_models import Load, HistoryResponse, ShedCommand, VenSummary
from app.schemas.ven import VENCreate, VENRead, VENUpdate


router = APIRouter()


@router.get("/", response_model=List[VENRead])
async def list_vens_v2(session: AsyncSession = Depends(get_session)):
    return await crud.list_vens(session)


@router.post("/", response_model=VENRead, status_code=status.HTTP_201_CREATED)
async def create_ven_v2(payload: VENCreate, session: AsyncSession = Depends(get_session)):
    ven = await crud.create_ven(session, payload.model_dump())
    return ven


@router.get("/summary", response_model=List[VenSummary])
async def list_vens_summary(session: AsyncSession = Depends(get_session)):
    """Summarized VEN data tailored for the current UI list view."""

    # Summary information is not yet stored in the database, so return an empty list
    # until the backing data model is expanded.
    await crud.list_vens(session)
    return []


@router.get("/{ven_id}", response_model=VENRead)
async def get_ven_v2(ven_id: str, session: AsyncSession = Depends(get_session)):
    ven = await crud.get_ven(session, ven_id)
    if not ven:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VEN not found")
    return ven


@router.patch("/{ven_id}", response_model=VENRead)
async def patch_ven_v2(ven_id: str, update: VENUpdate, session: AsyncSession = Depends(get_session)):
    ven = await crud.update_ven(session, ven_id, update.model_dump(exclude_unset=True, exclude_none=True))
    if not ven:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VEN not found")
    return ven


@router.delete("/{ven_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ven_v2(ven_id: str, session: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_ven(session, ven_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VEN not found")


@router.get("/{ven_id}/loads", response_model=List[Load])
async def list_ven_loads(ven_id: str, session: AsyncSession = Depends(get_session)):
    ven = await crud.get_ven(session, ven_id)
    if not ven:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VEN not found")
    return []


@router.get("/{ven_id}/loads/{load_id}", response_model=Load)
async def get_ven_load(ven_id: str, load_id: str, session: AsyncSession = Depends(get_session)):
    ven = await crud.get_ven(session, ven_id)
    if not ven:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VEN not found")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")


@router.patch("/{ven_id}/loads/{load_id}", response_model=Load)
async def update_ven_load(ven_id: str, load_id: str, update: dict, session: AsyncSession = Depends(get_session)):
    ven = await crud.get_ven(session, ven_id)
    if not ven:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VEN not found")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")


@router.post("/{ven_id}/loads/{load_id}/commands/shed", status_code=status.HTTP_202_ACCEPTED)
async def shed_ven_load(ven_id: str, load_id: str, cmd: ShedCommand, session: AsyncSession = Depends(get_session)):
    ven = await crud.get_ven(session, ven_id)
    if not ven:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VEN not found")
    return {"status": "accepted", "venId": ven_id, "loadId": load_id, "amountKw": cmd.amountKw}


@router.get("/{ven_id}/history", response_model=HistoryResponse)
async def ven_history(ven_id: str, session: AsyncSession = Depends(get_session)):
    ven = await crud.get_ven(session, ven_id)
    if not ven:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VEN not found")
    return HistoryResponse(points=[])


@router.get("/{ven_id}/loads/{load_id}/history", response_model=HistoryResponse)
async def ven_load_history(ven_id: str, load_id: str, session: AsyncSession = Depends(get_session)):
    ven = await crud.get_ven(session, ven_id)
    if not ven:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VEN not found")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")
