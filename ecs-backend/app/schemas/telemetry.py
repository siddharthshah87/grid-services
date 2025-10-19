from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TelemetryLoadPayload(BaseModel):
    """Per-load telemetry payload published by the VEN."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    load_id: str = Field(..., alias="id")
    name: str | None = Field(None, alias="name")
    type: str | None = Field(None, alias="type")
    capacity_kw: float | None = Field(None, alias="capacityKw")
    shed_capability_kw: float | None = Field(None, alias="shedCapabilityKw")
    current_power_kw: float | None = Field(None, alias="currentPowerKw")
    enabled: bool | None = Field(None, alias="enabled")
    priority: int | None = Field(None, alias="priority")


class TelemetryPayload(BaseModel):
    """Metering payload emitted on the MQTT metering topic."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    schema_version: str | None = Field(None, alias="schemaVersion")
    ven_id: str = Field(..., alias="venId")
    timestamp: int | float | str | datetime = Field(..., alias="timestamp")
    used_power_kw: float | None = Field(None, alias="usedPowerKw")
    shed_power_kw: float | None = Field(None, alias="shedPowerKw")
    requested_reduction_kw: float | None = Field(None, alias="requestedReductionKw")
    event_id: str | None = Field(None, alias="eventId")
    battery_soc: float | None = Field(None, alias="batterySoc")
    loads: list[TelemetryLoadPayload] = Field(default_factory=list, alias="loads")
    
    # Legacy fields for backward compatibility
    legacy_power_kw: float | None = Field(None, alias="power_kw")
    legacy_shed_kw: float | None = Field(None, alias="shed_kw")
    
    # Panel information (optional, for US electrical panel-based VENs)
    panel_amperage_rating: int | None = Field(None, alias="panelAmperageRating")
    panel_voltage: int | None = Field(None, alias="panelVoltage")
    panel_max_kw: float | None = Field(None, alias="panelMaxKw")
    current_amps: float | None = Field(None, alias="currentAmps")
    panel_utilization_percent: float | None = Field(None, alias="panelUtilizationPercent")
    circuits: list[dict[str, Any]] | None = Field(None, alias="circuits")  # Circuit breaker details

    def dump_raw(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True)


class LoadSnapshotPayload(BaseModel):
    """Backend load snapshot message."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    schema_version: str | None = Field(None, alias="schemaVersion")
    ven_id: str = Field(..., alias="venId")
    timestamp: int | float | str | datetime = Field(..., alias="timestamp")
    loads: list[TelemetryLoadPayload] = Field(default_factory=list, alias="loads")

    def dump_raw(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True)
