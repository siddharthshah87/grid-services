from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.device import DeviceCreate, DeviceRead
from app.models.device import Device
from app.db.database import get_session
from app.core.security import get_current_user

router = APIRouter()


@router.post("/", response_model=DeviceRead)
async def register_device(
    device: DeviceCreate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    db_device = Device(**device.dict())
    session.add(db_device)
    await session.commit()
    await session.refresh(db_device)
    return db_device


@router.get("/", response_model=list[DeviceRead])
async def list_devices(
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    result = await session.execute(select(Device))
    return result.scalars().all()
