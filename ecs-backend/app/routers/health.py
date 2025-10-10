from fastapi import APIRouter

# from app.db.database import engine

router = APIRouter()


@router.get("")
async def health_check():
    """Report basic service health.

    Returns:
        A simple status message.
    """
    return {"status": "ok"}


@router.get("/db-check")
async def db_check():
    """Verify database connectivity and required tables.

    Returns:
        Status details indicating database health.
    """
    '''
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
    '''
    return {"status": "disabled", "details": "Database check is currently disabled."}
