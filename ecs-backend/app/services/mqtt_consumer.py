from __future__ import annotations

import asyncio
import json
import logging
import os
import ssl
import tempfile
import time
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable

import gmqtt
from gmqtt.mqtt.constants import MQTTv311
import gmqtt
from app.core.config import Settings, settings
from app.models import LoadSnapshot, VenLoadSample, VenTelemetry
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
        self._worker: asyncio.Task[None] | None = None
        self._client: gmqtt.Client | None = None
        self._started = False

    def _setup_tls_cert_file(self, cert_type: str) -> str | None:
        """Handle TLS certificates - either file paths or PEM content from environment variables."""
        env_var_map = {
            "ca_cert": ("CA_CERT_PEM", self._config.mqtt_ca_cert),
            "client_cert": ("CLIENT_CERT_PEM", self._config.mqtt_client_cert),
            "client_key": ("PRIVATE_KEY_PEM", self._config.mqtt_client_key),
        }
        
        pem_env_var, config_path = env_var_map.get(cert_type, (None, None))
        
        # Prefer PEM content from environment variables (used in ECS with secrets)
        if pem_env_var:
            pem_content = os.getenv(pem_env_var)
            if pem_content:
                try:
                    # Create temporary file with PEM content
                    temp_fd, temp_path = tempfile.mkstemp(suffix=f"_{cert_type}.pem")
                    with os.fdopen(temp_fd, 'w') as temp_file:
                        temp_file.write(pem_content)
                    logger.info(f"Created temporary {cert_type} file", extra={"path": temp_path})
                    return temp_path
                except Exception as e:
                    logger.error(f"Failed to create temporary {cert_type} file", extra={"error": str(e)})
                    if 'temp_fd' in locals() and temp_fd is not None:
                        os.close(temp_fd)
                    return None

        # If no PEM env var, check if config_path is a valid file
        if config_path and os.path.isfile(config_path):
            return config_path
        
        # Fallback for cases where the config value might be a path that doesn't exist yet
        # or is not a file.
        return config_path

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

        self._queue = asyncio.Queue()
        self._worker = asyncio.create_task(self._process_queue())

        client_id = self._config.mqtt_client_id or gmqtt.client.get_client_id()
        self._client = gmqtt.Client(client_id)

        # Assign callbacks
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._client.on_subscribe = self._on_subscribe

        # Set will message
        # self._client.set_will_message(will_message)

        if self._config.mqtt_username and self._config.mqtt_password:
            self._client.set_auth_credentials(self._config.mqtt_username, self._config.mqtt_password)

        ssl_context = None
        if self._config.mqtt_use_tls:
            ca_certs = self._setup_tls_cert_file("ca_cert")
            certfile = self._setup_tls_cert_file("client_cert")
            keyfile = self._setup_tls_cert_file("client_key")

            if not ca_certs or not certfile or not keyfile:
                raise MQTTConsumerError("TLS certificates not properly configured")

            server_hostname = self._config.mqtt_tls_server_name or self._config.mqtt_host
            
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_certs)
            ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
            try:
                ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            except AttributeError:
                pass # some older python versions dont have this
            
            # For gmqtt, we pass the server_hostname directly to the connect call
            # and set check_hostname in the SSL context.
            ssl_context.check_hostname = True
            
            logger.info(
                "Configuring TLS",
                extra={
                    "connect_host": self._config.mqtt_host,
                    "server_hostname": server_hostname,
                    "ca_file": ca_certs,
                }
            )

        try:
            await self._client.connect(
                self._config.mqtt_host,
                self._config.mqtt_port,
                ssl=ssl_context or self._config.mqtt_use_tls,
                keepalive=self._config.mqtt_keepalive,
                version=MQTTv311
            )
        except (OSError, Exception) as exc:
            raise MQTTConsumerError(f"Failed to connect to MQTT broker: {exc}") from exc

        self._started = True
        logger.info(
            "Starting MQTT consumer",
            extra={"client_id": client_id, "host": self._config.mqtt_host}
        )

    async def stop(self) -> None:
        if not self._started or not self._client:
            return
        try:
            await self._client.disconnect()
        except Exception:
            logger.exception("Error stopping MQTT client")
        
        if self._worker:
            self._worker.cancel()
            with suppress(asyncio.CancelledError):
                await self._worker
        
        self._worker = None
        self._client = None
        self._queue = None
        self._started = False
        logger.info("MQTT consumer stopped")

    def _on_connect(self, client: gmqtt.Client, flags: dict[str, Any], rc: int, properties: Any) -> None:
        if rc != 0:
            logger.error("MQTT client failed to connect", extra={"rc": rc, "error": gmqtt.constants.CONNACK_RETURN_CODES.get(rc)})
            return
        
        assert self._config.mqtt_topics
        for topic in self._config.mqtt_topics:
            client.subscribe(topic, qos=1)

    def _on_subscribe(self, client: gmqtt.Client, mid: int, qos: list[int], properties: Any) -> None:
        logger.info("MQTT client subscribed", extra={"mid": mid, "qos": qos})

    def _on_disconnect(self, client: gmqtt.Client, packet: Any, exc: Exception | None = None) -> None:
        if exc:
            logger.warning("Unexpected MQTT disconnect", extra={"exception": str(exc)})
        else:
            logger.info("MQTT client disconnected cleanly")

    def _on_message(self, client: gmqtt.Client, topic: str, payload: bytes, qos: int, properties: Any) -> int:
        if not self._queue:
            logger.warning("Received MQTT message before consumer initialisation")
            return 0
        
        self._queue.put_nowait(_QueuedMessage(topic=topic, payload=payload))
        return 0

    async def handle_message(self, topic: str, payload: bytes) -> None:
        try:
            decoded = payload.decode("utf-8")
        except UnicodeDecodeError:
            logger.warning(
                "Received non-UTF8 payload",
                extra={"topic": topic, "payload_preview": payload[:100]}
            )
            return

        try:
            data = json.loads(decoded)
        except json.JSONDecodeError as e:
            logger.warning(
                "Discarding invalid JSON payload",
                extra={
                    "topic": topic,
                    "error": str(e),
                    "payload_preview": decoded[:200]
                }
            )
            return

        if not isinstance(data, dict):
            logger.warning(
                "Payload is not a JSON object",
                extra={"topic": topic, "type": type(data).__name__}
            )
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
            except Exception as e:
                logger.exception(
                    "Failed to process MQTT message",
                    extra={
                        "topic": message.topic,
                        "payload_size": len(message.payload),
                        "error": str(e)
                    }
                )
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
            with suppress(StopAsyncIteration):
                await generator.aclose()

    async def _persist_metering(self, payload: dict[str, Any]) -> None:
        try:
            model = TelemetryPayload.model_validate(payload)
        except Exception as e:
            logger.warning("Failed to validate telemetry payload", extra={"error": str(e), "payload": payload})
            return

        timestamp = _coerce_timestamp(model.timestamp)
        if not timestamp:
            logger.warning("Telemetry payload missing timestamp", extra={"ven": model.ven_id})
            return

        async with self._session_scope() as session:
            from app import crud
            ven = await crud.get_ven(session, model.ven_id)
            if ven is None:
                logger.info("Auto-registering new VEN", extra={"ven_id": model.ven_id})
                try:
                    await crud.create_ven(
                        session,
                        ven_id=model.ven_id,
                        name=f"Auto-registered VEN {model.ven_id}",
                        status="online",
                        registration_id=model.ven_id,
                    )
                except Exception as e:
                    logger.error("Failed to auto-register VEN", extra={"ven_id": model.ven_id, "error": str(e)})
                    return

        reading = VenTelemetry(
            ven_id=model.ven_id,
            timestamp=timestamp,
            used_power_kw=model.used_power_kw,
            shed_power_kw=model.shed_power_kw,
            requested_reduction_kw=model.requested_reduction_kw,
            event_id=model.event_id,
            battery_soc=model.battery_soc,
            raw_payload=payload,
        )

        for load in model.loads:
            reading.loads.append(
                VenLoadSample(
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
        try:
            model = LoadSnapshotPayload.model_validate(payload)
        except Exception as e:
            logger.warning("Failed to validate load snapshot payload", extra={"error": str(e), "payload": payload})
            return
            
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
            return

        async with self._session_scope() as session:
            session.add_all(records)

        logger.debug("Persisted load snapshot", extra={"ven": model.ven_id, "count": len(records)})


def _coerce_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None
