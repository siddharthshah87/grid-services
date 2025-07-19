from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.usage import UsageRecordCreate, UsageRecordRead
from app.models.usage_record import UsageRecord
from app.db.database import get_session

router = APIRouter()

@router.post("/", response_model=UsageRecordRead)
async def create_usage(record: UsageRecordCreate, session: AsyncSession = Depends(get_session)):
    db_record = UsageRecord(**record.model_dump())
    session.add(db_record)
    await session.commit()
    await session.refresh(db_record)
    return db_record

@router.get("/", response_model=list[UsageRecordRead])
async def list_usage(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(UsageRecord))
    return result.scalars().all()
