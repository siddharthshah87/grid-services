from fastapi import APIRouter
from sqlalchemy import text

from app.db.database import engine

router = APIRouter()

@router.get("/")
async def health_check():
    return {"status": "ok"}


@router.get("/health")
async def health_alias():
    return await health_check()


@router.get("/db-check")
async def db_check():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            tables = ["vens", "events"]
            for table in tables:
                result = await conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.tables "
                        "WHERE table_schema='public' AND table_name=:t"
                    ),
                    {"t": table},
                )
                if result.scalar() is None:
                    return {"status": "error", "details": f"table '{table}' missing"}
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}
