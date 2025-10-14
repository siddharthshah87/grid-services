from __future__ import annotations

import asyncio
import json
import logging
import contextlib
import os
import tempfile
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable

import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage

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
        self._loop: asyncio.AbstractEventLoop | None = None
        self._worker: asyncio.Task[None] | None = None
        self._client: mqtt.Client | None = None
        self._started = False

    def _setup_tls_cert_file(self, cert_type: str, cert_config: str | None) -> str | None:
        """Handle TLS certificates - either file paths or PEM content from environment variables."""
        # Check for PEM content from environment variables FIRST (used in ECS with secrets)
        env_var_map = {
            "ca_cert": "CA_CERT_PEM",
            "client_cert": "CLIENT_CERT_PEM", 
            "client_key": "PRIVATE_KEY_PEM"
        }
        
        pem_env_var = env_var_map.get(cert_type)
        if pem_env_var:
            pem_content = os.getenv(pem_env_var)
            if pem_content:
                # Create temporary file with PEM content
                temp_fd, temp_path = tempfile.mkstemp(suffix=f"_{cert_type}.pem")
                try:
                    with os.fdopen(temp_fd, 'w') as temp_file:
                        temp_file.write(pem_content)
                    logger.info(f"Created temporary {cert_type} file", extra={"path": temp_path})
                    return temp_path
                except Exception as e:
                    logger.error(f"Failed to create temporary {cert_type} file", extra={"error": str(e)})
                    os.close(temp_fd)
                    return None
        
        # If no PEM env var, check if cert_config is provided
        if not cert_config:
            return None
            
        # If it's a file path that exists, use it directly
        if os.path.isfile(cert_config):
            return cert_config
                    
        # Fall back to using the config value as-is (file path)
        return cert_config

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

        # Use MQTT 3.1.1 protocol (required by AWS IoT Core)
        self._client = mqtt.Client(
            client_id=self._config.mqtt_client_id or None,
            protocol=mqtt.MQTTv311
        )
        # Enable paho-mqtt debug logging to diagnose disconnect issues
        self._client.enable_logger(logger=logger)
        
        # Configure reconnect behavior and queue limits
        self._client.reconnect_delay_set(min_delay=1, max_delay=60)
        try:
            self._client.max_inflight_messages_set(20)
            self._client.max_queued_messages_set(200)
        except Exception:
            pass  # Older paho-mqtt versions may not have these methods
        
        if self._config.mqtt_username and self._config.mqtt_password:
            self._client.username_pw_set(self._config.mqtt_username, self._config.mqtt_password)

        if self._config.mqtt_use_tls:
            import ssl
            # Handle certificates - either file paths or PEM content from env vars
            # Must do this FIRST to ensure files exist before SSL context creation
            ca_certs = self._setup_tls_cert_file("ca_cert", self._config.mqtt_ca_cert)
            certfile = self._setup_tls_cert_file("client_cert", self._config.mqtt_client_cert)
            keyfile = self._setup_tls_cert_file("client_key", self._config.mqtt_client_key)
            
            # Verify we have valid certificate files
            if not ca_certs or not certfile or not keyfile:
                raise MQTTConsumerError("TLS certificates not properly configured")
            
            # Configure SNI for TLS when connecting to VPC endpoints
            # The VPC endpoint DNS name won't match the IoT Core certificate, so we use SNI
            # to tell AWS IoT which certificate to present
            manual_hostname_override = (
                self._config.mqtt_tls_server_name 
                and self._config.mqtt_tls_server_name != self._config.mqtt_host
            )
            
            if manual_hostname_override:
                logger.info(
                    "Configuring TLS with SNI override",
                    extra={
                        "connect_host": self._config.mqtt_host,
                        "sni_hostname": self._config.mqtt_tls_server_name,
                        "ca_file": ca_certs,
                        "cert_file": certfile,
                        "key_file": keyfile
                    }
                )
                # Create custom SSL context with SNI override
                # This allows connecting to VPC endpoints while validating against IoT Core certificate
                ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_certs)
                ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
                
                # Enforce TLS 1.2+
                try:
                    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
                except Exception:
                    pass
                
                # Monkey-patch wrap_socket to force server_hostname to the SNI value
                orig_wrap = ctx.wrap_socket
                sni_hostname = self._config.mqtt_tls_server_name
                
                def _wrap_socket_with_sni(sock, *args, **kwargs):
                    kwargs["server_hostname"] = sni_hostname
                    return orig_wrap(sock, *args, **kwargs)
                
                ctx.wrap_socket = _wrap_socket_with_sni
                ctx.check_hostname = True
                ctx.verify_mode = ssl.CERT_REQUIRED
                
                self._client.tls_set_context(ctx)
                # Only disable paho's hostname check for VPC endpoints
                # Public endpoints need proper hostname verification
                is_vpc_endpoint = "vpce" in self._config.mqtt_host
                if is_vpc_endpoint:
                    self._client.tls_insecure_set(True)
            else:
                # Standard TLS configuration
                self._client.tls_set(
                    ca_certs=ca_certs,
                    certfile=certfile,
                    keyfile=keyfile,
                )

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.on_log = lambda client, userdata, level, buf: logger.info(f"PAHO: {buf}")

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
            "Starting MQTT consumer",
            extra={"client_id": self._config.mqtt_client_id, "host": self._config.mqtt_host}
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

    def _on_connect(
        self, client: mqtt.Client, _userdata: Any, _flags: dict[str, Any], rc: int
    ) -> None:
        if rc != 0:
            logger.error("MQTT client failed to connect", extra={"rc": rc})
            return
        assert self._config.mqtt_topics  # guard above ensures not empty
        for topic in self._config.mqtt_topics:
            client.subscribe(topic)
        logger.info(
            "MQTT client subscribed",
            extra={"topics": self._config.mqtt_topics}
        )

    def _on_disconnect(self, _client: mqtt.Client, _userdata: Any, rc: int) -> None:
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnect with rc={rc} ({mqtt.error_string(rc)})")
        else:
            logger.info("MQTT client disconnected cleanly")

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

        # Validate basic structure for demo reliability
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
                # Enhanced logging for demo troubleshooting
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
            await generator.aclose()

    async def _persist_metering(self, payload: dict[str, Any]) -> None:
        model = TelemetryPayload.model_validate(payload)
        timestamp = _coerce_timestamp(model.timestamp)
        if not timestamp:
            logger.warning("Telemetry payload missing timestamp", extra={"ven": model.ven_id})
            return

        # Auto-register VEN if it doesn't exist
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
                        latitude=37.7749,  # Default San Francisco coordinates
                        longitude=-122.4194,
                    )
                    logger.info("Successfully auto-registered VEN", extra={"ven_id": model.ven_id})
                except Exception as e:
                    logger.error("Failed to auto-register VEN", extra={"ven_id": model.ven_id, "error": str(e)})
                    return

        used_kw = model.used_power_kw
        if used_kw is None:
            used_kw = model.legacy_power_kw

        shed_kw = model.shed_power_kw
        if shed_kw is None:
            shed_kw = model.legacy_shed_kw

        reading = VenTelemetry(
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
