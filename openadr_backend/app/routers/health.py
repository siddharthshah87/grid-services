from fastapi import APIRouter
from sqlalchemy import text

from app.db.database import engine

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/db-check")
async def db_check():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}
