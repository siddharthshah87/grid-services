from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.ven import VEN
from app.models.event import Event

async def create_ven(session: AsyncSession, ven: VEN):
    session.add(ven)
    await session.commit()
    await session.refresh(ven)
    return ven

async def get_ven(session: AsyncSession, ven_id: str):
    result = await session.execute(select(VEN).where(VEN.ven_id == ven_id))
    return result.scalar_one_or_none()
