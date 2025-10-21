"""
VEN Heartbeat Monitor

Periodically checks for VENs that haven't sent telemetry recently
and marks them as offline.
"""
import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.models.ven import VEN as VENModel

logger = logging.getLogger(__name__)

# VEN is considered offline if no heartbeat for this many seconds
DEFAULT_HEARTBEAT_TIMEOUT = 60  # 1 minute


class VenHeartbeatMonitor:
    """
    Monitors VEN heartbeats and marks stale VENs as offline.
    
    VENs send telemetry every 5 seconds. If we don't receive telemetry
    for HEARTBEAT_TIMEOUT seconds, we mark the VEN as offline.
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        config: Settings | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._config = config or settings
        self._monitor_task: asyncio.Task | None = None
        self._started = False
        
        # Configurable heartbeat timeout (default 60 seconds)
        self._heartbeat_timeout = int(
            self._config.ven_heartbeat_timeout_s 
            if hasattr(self._config, 'ven_heartbeat_timeout_s') 
            else DEFAULT_HEARTBEAT_TIMEOUT
        )
        
        # How often to check for stale VENs (default 30 seconds)
        self._check_interval = int(
            self._config.ven_heartbeat_check_interval_s
            if hasattr(self._config, 'ven_heartbeat_check_interval_s')
            else 30
        )

    async def start(self) -> None:
        """Start the heartbeat monitor."""
        if self._started:
            logger.warning("VEN heartbeat monitor already started")
            return

        self._started = True
        logger.info(
            f"Starting VEN heartbeat monitor "
            f"(timeout: {self._heartbeat_timeout}s, check interval: {self._check_interval}s)"
        )
        
        # Start the monitoring loop
        self._monitor_task = asyncio.create_task(self._monitor_heartbeats())

    async def stop(self) -> None:
        """Stop the heartbeat monitor."""
        if not self._started:
            return

        logger.info("Stopping VEN heartbeat monitor")
        self._started = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _monitor_heartbeats(self) -> None:
        """Main monitoring loop."""
        while self._started:
            try:
                await asyncio.sleep(self._check_interval)
                await self._check_stale_vens()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat monitoring loop: {e}", exc_info=True)

    async def _check_stale_vens(self) -> None:
        """Check for VENs that haven't sent telemetry recently and mark them offline."""
        async with self._session_factory() as session:
            # Calculate cutoff time
            cutoff_time = datetime.now(UTC) - timedelta(seconds=self._heartbeat_timeout)
            
            # Find VENs that are marked online but haven't sent heartbeat recently
            stmt = select(VENModel).where(
                VENModel.status == "online",
                VENModel.last_heartbeat.isnot(None),
                VENModel.last_heartbeat < cutoff_time
            )
            
            result = await session.execute(stmt)
            stale_vens = result.scalars().all()
            
            if stale_vens:
                logger.info(f"Found {len(stale_vens)} stale VENs, marking as offline")
                
                for ven in stale_vens:
                    time_since_heartbeat = (datetime.now(UTC) - ven.last_heartbeat).total_seconds()
                    logger.info(
                        f"Marking VEN {ven.ven_id} as offline "
                        f"(last heartbeat: {time_since_heartbeat:.0f}s ago)"
                    )
                    ven.status = "offline"
                
                await session.commit()
            
            # Also find VENs marked online but with no heartbeat at all (legacy data)
            stmt_no_heartbeat = select(VENModel).where(
                VENModel.status == "online",
                VENModel.last_heartbeat.is_(None)
            )
            
            result_no_heartbeat = await session.execute(stmt_no_heartbeat)
            no_heartbeat_vens = result_no_heartbeat.scalars().all()
            
            if no_heartbeat_vens:
                logger.info(
                    f"Found {len(no_heartbeat_vens)} VENs without heartbeat data, "
                    f"marking as offline (legacy data)"
                )
                
                for ven in no_heartbeat_vens:
                    logger.info(f"Marking VEN {ven.ven_id} as offline (no heartbeat data)")
                    ven.status = "offline"
                
                await session.commit()
