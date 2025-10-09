from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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
    currentPowerKw: float = 0.0
    shedAvailabilityKw: float = 0.0
    activeEventId: Optional[str] = None
    shedLoadIds: list[str] = Field(default_factory=list)


class Ven(BaseModel):
    id: str
    name: str
    status: str
    location: Location
    metrics: VenMetrics
    createdAt: datetime
    loads: list[Load] | None = None


class VenCreate(BaseModel):
    name: str
    location: Location
    status: Optional[str] = "active"
    registrationId: Optional[str] = None


class VenUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    location: Optional[Location] = None
    registrationId: Optional[str] = None


class NetworkStats(BaseModel):
    venCount: int
    controllablePowerKw: float
    potentialLoadReductionKw: float
    householdUsageKw: float
    onlineVens: int = 0
    currentLoadReductionKw: float = 0.0
    networkEfficiency: float | None = None
    averageHousePower: float | None = None
    totalHousePowerToday: float | None = None


class LoadTypeStats(BaseModel):
    type: str
    totalCapacityKw: float
    totalShedCapabilityKw: float
    currentUsageKw: float


class TimeseriesPoint(BaseModel):
    timestamp: datetime
    usedPowerKw: float
    shedPowerKw: float
    eventId: Optional[str] = None
    requestedReductionKw: Optional[float] = None


class HistoryResponse(BaseModel):
    points: list[TimeseriesPoint]


class Event(BaseModel):
    id: str
    status: str
    startTime: Optional[datetime]
    endTime: Optional[datetime]
    requestedReductionKw: Optional[float]
    actualReductionKw: float = 0.0


class EventCreate(BaseModel):
    startTime: datetime
    endTime: datetime
    requestedReductionKw: float
    status: Optional[str] = "scheduled"


class ShedCommand(BaseModel):
    amountKw: float = Field(..., description="Kilowatts to shed")


class VenSummary(BaseModel):
    id: str
    name: str
    location: str
    status: str
    controllablePower: float
    currentPower: float
    address: str
    lastSeen: str
    responseTime: int


class EventMetrics(BaseModel):
    currentReductionKw: float
    vensResponding: int
    avgResponseMs: int


class EventWithMetrics(Event):
    currentReductionKw: Optional[float] = None
    vensResponding: Optional[int] = None
    avgResponseMs: Optional[int] = None
