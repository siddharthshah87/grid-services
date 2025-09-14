from __future__ import annotations

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

