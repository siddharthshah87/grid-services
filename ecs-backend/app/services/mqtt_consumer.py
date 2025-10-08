from __future__ import annotations

import asyncio
import json
import logging
import contextlib
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable

import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage

from app.core.config import Settings, settings
from app.models import LoadSnapshot, TelemetryLoad, TelemetryReading
from app.schemas.telemetry import LoadSnapshotPayload, TelemetryPayload

logger = logging.getLogger(__name__)


class MQTTConsumerError(RuntimeError):
    """Raised when the MQTT consumer cannot be started."""


SessionFactory = Callable[[], AsyncIterator[Any]]


@dataclass(slots=True)
class _QueuedMessage:
    topic: str
    payload: bytes


class MQTTConsumer:
    """Background task that persists MQTT telemetry into the database."""

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

        self._queue: asyncio.Queue[_QueuedMessage] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._worker: asyncio.Task[None] | None = None
        self._client: mqtt.Client | None = None
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        if not self._config.mqtt_enabled:
            logger.info("MQTT consumer disabled via configuration")
            return
        if not self._config.mqtt_host:
            raise MQTTConsumerError("MQTT_HOST must be provided when MQTT_ENABLED is true")
        topics = self._config.mqtt_topics
        if not topics:
            raise MQTTConsumerError("At least one MQTT topic must be configured")

        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue()
        self._worker = asyncio.create_task(self._process_queue())

        self._client = mqtt.Client(client_id=self._config.mqtt_client_id or None)
        if self._config.mqtt_username and self._config.mqtt_password:
            self._client.username_pw_set(self._config.mqtt_username, self._config.mqtt_password)

        if self._config.mqtt_use_tls:
            self._client.tls_set(
                ca_certs=self._config.mqtt_ca_cert,
                certfile=self._config.mqtt_client_cert,
                keyfile=self._config.mqtt_client_key,
            )

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        try:
            await asyncio.to_thread(
                self._client.connect,
                self._config.mqtt_host,
                self._config.mqtt_port,
                self._config.mqtt_keepalive,
            )
        except OSError as exc:  # pragma: no cover - connection failures in prod
            raise MQTTConsumerError(f"Failed to connect to MQTT broker: {exc}") from exc

        self._client.loop_start()
        self._started = True
        logger.info(
            "MQTT consumer connected", extra={"topics": topics, "host": self._config.mqtt_host}
        )

    async def stop(self) -> None:
        if not self._started:
            return
        if self._client:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:  # pragma: no cover - defensive
                logger.exception("Error stopping MQTT client")
        if self._worker:
            self._worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker
        self._worker = None
        self._client = None
        self._queue = None
        self._started = False

    def _on_connect(self, client: mqtt.Client, _userdata: Any, _flags: dict[str, Any], rc: int) -> None:
        if rc != 0:
            logger.error("MQTT client failed to connect", extra={"rc": rc})
            return
        assert self._config.mqtt_topics  # guard above ensures not empty
        for topic in self._config.mqtt_topics:
            client.subscribe(topic)
        logger.info("MQTT client subscribed", extra={"topics": self._config.mqtt_topics})

    def _on_disconnect(self, _client: mqtt.Client, _userdata: Any, rc: int) -> None:
        if rc != 0:
            logger.warning("Unexpected MQTT disconnect", extra={"rc": rc})
        else:
            logger.info("MQTT client disconnected")

    def _on_message(self, _client: mqtt.Client, _userdata: Any, msg: MQTTMessage) -> None:
        if not self._queue or not self._loop:
            logger.warning("Received MQTT message before consumer initialisation")
            return
        payload = msg.payload or b""
        asyncio.run_coroutine_threadsafe(
            self._queue.put(_QueuedMessage(topic=msg.topic, payload=payload)),
            self._loop,
        )

    async def handle_message(self, topic: str, payload: bytes) -> None:
        try:
            decoded = payload.decode("utf-8")
        except UnicodeDecodeError:
            logger.warning("Received non-UTF8 payload", extra={"topic": topic})
            return

        try:
            data = json.loads(decoded)
        except json.JSONDecodeError:
            logger.warning("Discarding invalid JSON payload", extra={"topic": topic})
            return

        if topic == self._config.mqtt_topic_metering:
            await self._persist_metering(data)
        elif topic == self._config.backend_loads_topic:
            await self._persist_load_snapshot(data)
        else:
            logger.debug("Unhandled MQTT topic", extra={"topic": topic})

    async def _process_queue(self) -> None:
        assert self._queue is not None
        while True:
            message = await self._queue.get()
            try:
                await self.handle_message(message.topic, message.payload)
            except Exception:  # pragma: no cover - logged for investigation
                logger.exception("Failed to process MQTT message", extra={"topic": message.topic})
            finally:
                self._queue.task_done()

    @asynccontextmanager
    async def _session_scope(self):
        generator = self._session_factory()
        session = await generator.__anext__()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await generator.aclose()

    async def _persist_metering(self, payload: dict[str, Any]) -> None:
        model = TelemetryPayload.model_validate(payload)
        timestamp = _coerce_timestamp(model.timestamp)
        if not timestamp:
            logger.warning("Telemetry payload missing timestamp", extra={"ven": model.ven_id})
            return

        used_kw = model.used_power_kw
        if used_kw is None:
            used_kw = model.legacy_power_kw

        shed_kw = model.shed_power_kw
        if shed_kw is None:
            shed_kw = model.legacy_shed_kw

        reading = TelemetryReading(
            ven_id=model.ven_id,
            timestamp=timestamp,
            used_power_kw=used_kw,
            shed_power_kw=shed_kw,
            requested_reduction_kw=model.requested_reduction_kw,
            event_id=model.event_id,
            battery_soc=model.battery_soc,
            raw_payload=model.dump_raw(),
        )

        for load in model.loads:
            reading.loads.append(
                TelemetryLoad(
                    load_id=load.load_id,
                    name=load.name,
                    type=load.type,
                    capacity_kw=load.capacity_kw,
                    current_power_kw=load.current_power_kw,
                    shed_capability_kw=load.shed_capability_kw,
                    enabled=load.enabled,
                    priority=load.priority,
                    raw_payload=load.model_dump(mode="json", by_alias=True),
                )
            )

        async with self._session_scope() as session:
            session.add(reading)

        logger.debug("Persisted telemetry", extra={"ven": model.ven_id, "timestamp": timestamp.isoformat()})

    async def _persist_load_snapshot(self, payload: dict[str, Any]) -> None:
        model = LoadSnapshotPayload.model_validate(payload)
        timestamp = _coerce_timestamp(model.timestamp)
        if not timestamp:
            logger.warning("Load snapshot missing timestamp", extra={"ven": model.ven_id})
            return

        records = [
            LoadSnapshot(
                ven_id=model.ven_id,
                timestamp=timestamp,
                load_id=load.load_id,
                name=load.name,
                type=load.type,
                capacity_kw=load.capacity_kw,
                current_power_kw=load.current_power_kw,
                shed_capability_kw=load.shed_capability_kw,
                enabled=load.enabled,
                priority=load.priority,
                raw_payload=load.model_dump(mode="json", by_alias=True),
            )
            for load in model.loads
        ]

        if not records:
            logger.debug("Empty loads snapshot", extra={"ven": model.ven_id})
            return

        async with self._session_scope() as session:
            session.add_all(records)

        logger.debug("Persisted load snapshot", extra={"ven": model.ven_id, "count": len(records)})


def _coerce_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value).astimezone(timezone.utc)
        except ValueError:
            return None
    return None
