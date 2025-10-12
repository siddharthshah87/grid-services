from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.dependencies import get_session
from app import crud

router = APIRouter()


@router.get("")
async def health_check():
    """Report basic service health.

    Returns:
        A simple status message.
    """
    return {"status": "ok"}


@router.get("/db-check")
async def db_check(session: AsyncSession = Depends(get_session)):
    """Verify database connectivity and required tables.

    Returns:
        Status details indicating database health.
    """
    try:
        # Test basic connectivity
        await session.execute(text("SELECT 1"))
        
        # Check for required tables
        tables = ["vens", "events"]
        for table in tables:
            result = await session.execute(
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


@router.get("/demo-status")
async def demo_status(session: AsyncSession = Depends(get_session)):
    """Demo-specific status check with system overview."""
    try:
        # Count VENs
        vens = await crud.list_vens(session)
        ven_count = len(vens)
        
        # Count recent telemetry
        recent_telemetry = await session.execute(
            text("SELECT COUNT(*) FROM ven_telemetry WHERE timestamp > NOW() - INTERVAL '5 minutes'")
        )
        telemetry_count = recent_telemetry.scalar() or 0
        
        # Count events
        events_result = await session.execute(text("SELECT COUNT(*) FROM events"))
        event_count = events_result.scalar() or 0
        
        return {
            "status": "ok",
            "demo_ready": True,
            "metrics": {
                "ven_count": ven_count,
                "recent_telemetry_count": telemetry_count,
                "total_events": event_count
            },
            "services": {
                "database": "connected",
                "api": "operational"
            }
        }
    except Exception as e:
        return {
            "status": "error", 
            "demo_ready": False,
            "error": str(e)
        }
