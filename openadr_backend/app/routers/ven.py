from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.ven import VENCreate, VENRead
from app.models.ven import VEN
from app.db.database import get_session

router = APIRouter()

@router.post("/", response_model=VENRead)
async def register_ven(
    ven: VENCreate,
    session: AsyncSession = Depends(get_session),
):
    db_ven = VEN(**ven.model_dump())
    session.add(db_ven)
    await session.commit()
    await session.refresh(db_ven)
    return db_ven

@router.get("/", response_model=list[VENRead])
async def list_vens(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(VEN))
    return result.scalars().all()


@router.delete("/{ven_id}", status_code=204)
async def delete_ven(
    ven_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(VEN).where(VEN.ven_id == ven_id))
    ven = result.scalars().first()
    if not ven:
        raise HTTPException(status_code=404, detail="VEN not found")
    await session.delete(ven)
    await session.commit()
    return Response(status_code=204)
