from __future__ import annotations
# BaseSettings moved to the pydantic-settings package in Pydantic v2
from collections.abc import Iterable
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


def _unique(iterable: Iterable[str | None]) -> list[str]:
    """Return a list of non-empty unique strings preserving order."""

    seen: set[str] = set()
    ordered: list[str] = []
    for value in iterable:
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    db_host: str = Field(alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    db_user: str = Field(alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")
    db_name: str = Field(alias="DB_NAME")
    db_timeout: int = Field(30, alias="DB_TIMEOUT")

    mqtt_enabled: bool = Field(False, alias="MQTT_ENABLED")
    mqtt_host: str | None = Field(None, alias="MQTT_HOST")
    mqtt_port: int = Field(8883, alias="MQTT_PORT")
    mqtt_client_id: str | None = Field(None, alias="MQTT_CLIENT_ID")
    mqtt_username: str | None = Field(None, alias="MQTT_USERNAME")
    mqtt_password: str | None = Field(None, alias="MQTT_PASSWORD")
    mqtt_keepalive: int = Field(60, alias="MQTT_KEEPALIVE")
    mqtt_use_tls: bool = Field(True, alias="MQTT_USE_TLS")
    mqtt_tls_server_name: str | None = Field(None, alias="MQTT_TLS_SERVER_NAME")
    mqtt_ca_cert: str | None = Field(None, alias="MQTT_CA_CERT")
    mqtt_client_cert: str | None = Field(None, alias="MQTT_CLIENT_CERT")
    mqtt_client_key: str | None = Field(None, alias="MQTT_CLIENT_KEY")
    mqtt_topic_status: str | None = Field("volttron/dev", alias="MQTT_TOPIC_STATUS")
    mqtt_topic_metering: str | None = Field("volttron/metering", alias="MQTT_TOPIC_METERING")
    mqtt_topic_events: str | None = Field("openadr/event", alias="MQTT_TOPIC_EVENTS")
    mqtt_topic_responses: str | None = Field("openadr/response", alias="MQTT_TOPIC_RESPONSES")
    backend_loads_topic: str | None = Field(None, alias="BACKEND_LOADS_TOPIC")
    mqtt_additional_topics: list[str] = Field(default_factory=list, alias="MQTT_TOPICS")
    
    # Event Command Service settings
    event_command_enabled: bool = Field(True, alias="EVENT_COMMAND_ENABLED")
    iot_endpoint: str | None = Field(None, alias="IOT_ENDPOINT")

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "extra": "ignore",
        "env_nested_delimiter": "__",
    }

    @field_validator("mqtt_additional_topics", mode="before")
    @classmethod
    def _split_topics(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            parts = [part.strip() for part in value.replace("\n", ",").split(",")]
            return [part for part in parts if part]
        if isinstance(value, list):
            return [part for part in value if isinstance(part, str) and part]
        return []

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def mqtt_topics(self) -> list[str]:
        """List of topics the backend should subscribe to."""

        return _unique(
            [
                self.mqtt_topic_status,
                self.mqtt_topic_metering,
                self.mqtt_topic_events,
                self.mqtt_topic_responses,
                self.backend_loads_topic,
                *self.mqtt_additional_topics,
            ]
        )


_settings_instance = None


def get_settings():
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


# Backward compatibility: settings variable for legacy imports
settings = get_settings()
