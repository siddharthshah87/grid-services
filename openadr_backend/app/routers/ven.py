from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.schemas.ven import VENCreate, VENRead
from app.models.ven import VEN
from app.db.database import get_session

router = APIRouter()

@router.post("/", response_model=VENRead)
async def register_ven(
    ven: VENCreate,
    session: AsyncSession = Depends(get_session),
):
    db_ven = VEN(**ven.dict())
    session.add(db_ven)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        if "registration_id" in str(e.orig):
            raise HTTPException(status_code=409, detail="registration_id already exists")
        raise
    await session.refresh(db_ven)
    return db_ven

@router.get("/", response_model=list[VENRead])
async def list_vens(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(VEN))
    return result.scalars().all()
