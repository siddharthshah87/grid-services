from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from typing import List, Optional


class Location(BaseModel):
    lat: float
    lon: float


class Load(BaseModel):
    id: str
    type: str
    capacityKw: float
    shedCapabilityKw: float
    currentPowerKw: float
    name: Optional[str] = None


class VenMetrics(BaseModel):
    currentPowerKw: float
    shedAvailabilityKw: float
    activeEventId: Optional[str] = None
    shedLoadIds: List[str] = []


class Ven(BaseModel):
    id: str
    name: str
    status: str
    location: Location
    loads: List[Load]
    metrics: VenMetrics


class VenCreate(BaseModel):
    name: str
    location: Location


class VenUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    location: Optional[Location] = None


class NetworkStats(BaseModel):
    venCount: int
    controllablePowerKw: float
    potentialLoadReductionKw: float
    householdUsageKw: float
    # Extended fields to support current UI without frontend refactors
    onlineVens: int | None = None
    currentLoadReductionKw: float | None = None
    networkEfficiency: float | None = None
    averageHousePower: float | None = None
    totalHousePowerToday: float | None = None


class LoadTypeStats(BaseModel):
    type: str
    totalCapacityKw: float
    totalShedCapabilityKw: float
    currentUsageKw: float


class TimeseriesPoint(BaseModel):
    timestamp: str
    usedPowerKw: float
    shedPowerKw: float
    eventId: Optional[str] = None
    requestedReductionKw: Optional[float] = None


class HistoryResponse(BaseModel):
    points: List[TimeseriesPoint]


class Event(BaseModel):
    id: str
    status: str
    startTime: str
    endTime: str
    requestedReductionKw: float
    actualReductionKw: float = 0


class EventCreate(BaseModel):
    startTime: str
    endTime: str
    requestedReductionKw: float


class ShedCommand(BaseModel):
    amountKw: float = Field(..., description="Kilowatts to shed")


class VenSummary(BaseModel):
    id: str
    name: str
    location: str  # label for UI
    status: str  # online | offline | maintenance
    controllablePower: float  # kW
    currentPower: float  # kW
    address: str
    lastSeen: str
    responseTime: int  # ms


class EventMetrics(BaseModel):
    currentReductionKw: float
    vensResponding: int
    avgResponseMs: int


class EventWithMetrics(Event):
    currentReductionKw: Optional[float] = None
    vensResponding: Optional[int] = None
    avgResponseMs: Optional[int] = None


class VenTelemetryRecord(BaseModel):
    venId: str = Field(alias="ven_id")
    timestamp: datetime
    usedPowerKw: float = Field(alias="used_power_kw")
    shedPowerKw: float = Field(alias="shed_power_kw")
    payload: Optional[dict] = None

    model_config = {"populate_by_name": True}


class VenLoadSampleRecord(BaseModel):
    venId: str = Field(alias="ven_id")
    loadId: str = Field(alias="load_id")
    timestamp: datetime
    loadType: Optional[str] = Field(default=None, alias="load_type")
    usedPowerKw: float = Field(alias="used_power_kw")
    shedPowerKw: float = Field(alias="shed_power_kw")
    capacityKw: Optional[float] = Field(default=None, alias="capacity_kw")
    shedCapabilityKw: Optional[float] = Field(default=None, alias="shed_capability_kw")
    payload: Optional[dict] = None

    model_config = {"populate_by_name": True}


class VenStatusRecord(BaseModel):
    venId: str = Field(alias="ven_id")
    status: str
    recordedAt: datetime = Field(alias="recorded_at")
    details: Optional[dict] = None

    model_config = {"populate_by_name": True}
