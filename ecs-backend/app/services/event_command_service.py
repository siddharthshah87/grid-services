"""
Event Command Service

Monitors active events and automatically dispatches MQTT commands to VENs
when events start, progress, or end.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, AsyncIterator, Callable
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.models.event import Event as EventModel
from app.models.ven import VEN as VENModel

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AsyncIterator[Any]]


class EventCommandServiceError(RuntimeError):
    """Raised when the Event Command Service cannot be started."""


class EventCommandService:
    """
    Background service that monitors events and dispatches MQTT commands to VENs.
    
    When an event becomes active, it:
    1. Fetches all registered VENs
    2. Calculates requested reduction per VEN
    3. Publishes `shedPanel` or `event` command via AWS IoT Core
    4. Tracks acknowledgments
    
    When an event completes:
    1. Publishes restore commands to VENs
    2. Updates event status
    """

    def __init__(
        self,
        config: Settings | None = None,
        session_factory: SessionFactory | None = None,
    ) -> None:
        self._config = config or settings
        if session_factory is None:
            from app.dependencies import get_session
            self._session_factory = get_session
        else:
            self._session_factory = session_factory

        self._monitor_task: asyncio.Task[None] | None = None
        self._started = False
        self._iot_client = None
        
        # Track events we've already dispatched commands for
        self._dispatched_events: set[str] = set()
        self._completed_events: set[str] = set()

    async def start(self) -> None:
        """Start the event monitoring service."""
        if self._started:
            return
        
        # Check if event command service is enabled
        if not self._config.event_command_enabled:
            logger.info("Event command service disabled via configuration")
            return
        
        # Get AWS region
        aws_region = os.getenv("AWS_REGION", "us-west-2")
        iot_endpoint = self._config.iot_endpoint
        
        if not iot_endpoint:
            logger.warning("IOT_ENDPOINT not configured, event command service disabled")
            return
        
        try:
            # Initialize AWS IoT Data client
            self._iot_client = boto3.client(
                'iot-data',
                region_name=aws_region,
                endpoint_url=f"https://{iot_endpoint}"
            )
            logger.info(f"Initialized AWS IoT Data client for {iot_endpoint}")
        except Exception as e:
            raise EventCommandServiceError(f"Failed to initialize IoT client: {e}") from e
        
        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_events())
        self._started = True
        logger.info("Event command service started")

    async def stop(self) -> None:
        """Stop the event monitoring service."""
        if not self._started:
            return
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        self._monitor_task = None
        self._iot_client = None
        self._started = False
        logger.info("Event command service stopped")

    async def _monitor_events(self) -> None:
        """Main monitoring loop - checks for events that need commands."""
        logger.info("Starting event monitoring loop")
        
        while True:
            try:
                await self._check_events()
                await asyncio.sleep(5)  # Check every 5 seconds
            except asyncio.CancelledError:
                logger.info("Event monitoring loop cancelled")
                break
            except Exception as e:
                logger.exception(f"Error in event monitoring loop: {e}")
                await asyncio.sleep(10)  # Back off on error

    async def _check_events(self) -> None:
        """Check for events that need command dispatch."""
        async with self._session_scope() as session:
            now = datetime.now(UTC)
            
            # Find events that should be active now
            stmt = (
                select(EventModel)
                .where(
                    EventModel.start_time <= now,
                    EventModel.end_time >= now,
                    EventModel.status.in_(["scheduled", "active", "in_progress"])
                )
            )
            result = await session.execute(stmt)
            active_events = result.scalars().all()
            
            for event in active_events:
                # Check if we need to start this event
                if event.event_id not in self._dispatched_events:
                    logger.info(f"Event {event.event_id} is starting, dispatching commands")
                    await self._dispatch_event_start(session, event)
                    self._dispatched_events.add(event.event_id)
                    
                    # Update event status to active
                    if event.status == "scheduled":
                        event.status = "active"
                        await session.commit()
            
            # Find events that have ended and need cleanup
            stmt_ended = (
                select(EventModel)
                .where(
                    EventModel.end_time < now,
                    EventModel.status.in_(["active", "in_progress"])
                )
            )
            result_ended = await session.execute(stmt_ended)
            ended_events = result_ended.scalars().all()
            
            for event in ended_events:
                if event.event_id not in self._completed_events:
                    logger.info(f"Event {event.event_id} has ended, dispatching restore commands")
                    await self._dispatch_event_stop(session, event)
                    self._completed_events.add(event.event_id)
                    
                    # Update event status to completed
                    event.status = "completed"
                    await session.commit()

    async def _dispatch_event_start(self, session: AsyncSession, event: EventModel) -> None:
        """Dispatch shedPanel commands when an event starts."""
        # Fetch all active VENs
        stmt = select(VENModel).where(VENModel.status == "online")
        result = await session.execute(stmt)
        vens = result.scalars().all()
        
        if not vens:
            logger.warning(f"No online VENs found for event {event.event_id}")
            return
        
        # Calculate reduction per VEN (equal distribution for now)
        # TODO: Could be weighted by VEN capacity in the future
        reduction_per_ven = event.requested_reduction_kw / len(vens)
        
        logger.info(
            f"Dispatching event {event.event_id} to {len(vens)} VENs "
            f"({reduction_per_ven:.2f} kW per VEN)"
        )
        
        # Dispatch command to each VEN
        for ven in vens:
            try:
                await self._send_shed_panel_command(
                    ven_id=ven.registration_id,
                    event_id=event.event_id,
                    requested_reduction_kw=reduction_per_ven,
                    duration_s=int((event.end_time - event.start_time).total_seconds()),
                )
                logger.info(f"Dispatched shedPanel command to VEN {ven.registration_id}")
            except Exception as e:
                logger.error(f"Failed to dispatch command to VEN {ven.registration_id}: {e}")

    async def _dispatch_event_stop(self, session: AsyncSession, event: EventModel) -> None:
        """Dispatch restore commands when an event ends."""
        # Fetch all VENs that might have participated
        stmt = select(VENModel)
        result = await session.execute(stmt)
        vens = result.scalars().all()
        
        logger.info(f"Dispatching restore commands for event {event.event_id} to {len(vens)} VENs")
        
        # Dispatch restore command to each VEN
        for ven in vens:
            try:
                await self._send_restore_command(
                    ven_id=ven.registration_id,
                    event_id=event.event_id,
                )
                logger.info(f"Dispatched restore command to VEN {ven.registration_id}")
            except Exception as e:
                logger.error(f"Failed to dispatch restore to VEN {ven.registration_id}: {e}")

    async def _send_shed_panel_command(
        self,
        ven_id: str,
        event_id: str,
        requested_reduction_kw: float,
        duration_s: int,
    ) -> None:
        """
        Send a shedPanel command to a VEN via AWS IoT Core.
        
        This publishes to topic: ven/cmd/{venId}
        """
        command = {
            "op": "event",  # Using 'event' op instead of 'shedPanel' for compatibility
            "correlationId": f"evt-{event_id}-{uuid4().hex[:8]}",
            "venId": ven_id,
            "event_id": event_id,
            "shed_kw": requested_reduction_kw,
            "duration_sec": duration_s,
            "data": {
                "event_id": event_id,
                "requestedReductionKw": requested_reduction_kw,
                "duration_s": duration_s,
            }
        }
        
        await self._publish_command(ven_id, command)

    async def _send_restore_command(
        self,
        ven_id: str,
        event_id: str,
    ) -> None:
        """
        Send a restore command to a VEN via AWS IoT Core.
        
        This publishes to topic: ven/cmd/{venId}
        """
        command = {
            "op": "restore",
            "correlationId": f"restore-{event_id}-{uuid4().hex[:8]}",
            "venId": ven_id,
            "event_id": event_id,
            "data": {
                "event_id": event_id,
            }
        }
        
        await self._publish_command(ven_id, command)

    async def _publish_command(self, ven_id: str, command: dict) -> None:
        """
        Publish a command to a VEN via AWS IoT Core MQTT.
        
        Uses boto3 iot-data client to publish to ven/cmd/{venId} topic.
        """
        if not self._iot_client:
            raise EventCommandServiceError("IoT client not initialized")
        
        topic = f"ven/cmd/{ven_id}"
        payload = json.dumps(command)
        
        try:
            # Run boto3 call in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._iot_client.publish(
                    topic=topic,
                    qos=1,
                    payload=payload
                )
            )
            logger.debug(f"Published command to {topic}: {command['op']}")
        except ClientError as e:
            logger.error(f"AWS IoT publish failed: {e}")
            raise EventCommandServiceError(f"Failed to publish command: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error publishing command: {e}")
            raise

    @asynccontextmanager
    async def _session_scope(self):
        """Create a database session context."""
        async with self._session_factory() as session:
            yield session
