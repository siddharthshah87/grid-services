from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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


class CircuitCurtailment(BaseModel):
    """Details about a specific circuit that was curtailed."""
    id: str
    name: str
    breaker_amps: int
    original_kw: float
    curtailed_kw: float
    final_kw: float
    critical: bool


class VenEventAck(BaseModel):
    """VEN acknowledgment of a DR event."""
    id: int
    venId: str
    eventId: str
    correlationId: Optional[str] = None
    op: str
    status: str
    timestamp: datetime
    requestedShedKw: Optional[float] = None
    actualShedKw: Optional[float] = None
    circuitsCurtailed: Optional[list[CircuitCurtailment]] = None


class CircuitSnapshot(BaseModel):
    """Historical snapshot of a circuit/load at a specific time."""
    timestamp: datetime
    loadId: str
    name: Optional[str] = None
    type: Optional[str] = None
    capacityKw: Optional[float] = None
    currentPowerKw: Optional[float] = None
    shedCapabilityKw: Optional[float] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None


class CircuitHistoryResponse(BaseModel):
    """Time-series data for one or more circuits."""
    venId: str
    loadId: Optional[str] = None  # If querying single circuit
    snapshots: list[CircuitSnapshot]
    totalCount: int
