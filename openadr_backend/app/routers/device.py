from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.device import DeviceCreate, DeviceRead
from app.models.device import Device
from app.db.database import get_session

router = APIRouter()

@router.post("/", response_model=DeviceRead)
async def create_device(device: DeviceCreate, session: AsyncSession = Depends(get_session)):
    db_device = Device(**device.model_dump())
    session.add(db_device)
    await session.commit()
    await session.refresh(db_device)
    return db_device

@router.get("/", response_model=list[DeviceRead])
async def list_devices(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Device))
    return result.scalars().all()
