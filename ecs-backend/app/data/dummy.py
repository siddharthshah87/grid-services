from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.schemas.api_models import (
    Ven,
    VenMetrics,
    Location,
    Load,
    NetworkStats,
    LoadTypeStats,
    HistoryResponse,
    TimeseriesPoint,
    Event,
    VenSummary,
    EventMetrics,
)


# Static dummy VENs
VENS: Dict[str, Ven] = {}
VEN_META: Dict[str, dict] = {}


def _init_vens() -> None:
    global VENS
    if VENS:
        return
    VENS = {
        "ven-101": Ven(
            id="ven-101",
            name="Main Street Facility",
            status="online",
            location=Location(lat=37.42, lon=-122.08),
            loads=[
                Load(id="ld-101-a", type="hvac", capacityKw=7.5, shedCapabilityKw=3.0, currentPowerKw=4.2),
                Load(id="ld-101-b", type="ev", capacityKw=11.0, shedCapabilityKw=6.0, currentPowerKw=8.0),
            ],
            metrics=VenMetrics(currentPowerKw=12.4, shedAvailabilityKw=5.0, activeEventId=None, shedLoadIds=[]),
        ),
        "ven-102": Ven(
            id="ven-102",
            name="Riverside Plant",
            status="online",
            location=Location(lat=47.61, lon=-122.33),
            loads=[
                Load(id="ld-102-a", type="washer_dryer", capacityKw=2.5, shedCapabilityKw=1.5, currentPowerKw=1.1),
                Load(id="ld-102-b", type="ac", capacityKw=5.0, shedCapabilityKw=2.0, currentPowerKw=2.6),
            ],
            metrics=VenMetrics(currentPowerKw=3.7, shedAvailabilityKw=2.5, activeEventId=None, shedLoadIds=[]),
        ),
        "ven-103": Ven(
            id="ven-103",
            name="Hilltop Campus",
            status="maintenance",
            location=Location(lat=34.05, lon=-118.24),
            loads=[
                Load(id="ld-103-a", type="pool_heater", capacityKw=9.0, shedCapabilityKw=4.5, currentPowerKw=3.0),
                Load(id="ld-103-b", type="solar", capacityKw=15.0, shedCapabilityKw=0.0, currentPowerKw=-4.5),
            ],
            metrics=VenMetrics(currentPowerKw=-1.5, shedAvailabilityKw=4.5, activeEventId=None, shedLoadIds=[]),
        ),
    }
    global VEN_META
    VEN_META = {
        "ven-101": {
            "address": "123 Main St, Grid Sector 1",
            "locationLabel": "Downtown District",
            "lastSeen": "PT2M",  # ISO-8601 duration or humanized string
            "responseTimeMs": 145,
        },
        "ven-102": {
            "address": "456 Commerce Ave, Grid Sector 2",
            "locationLabel": "Business District",
            "lastSeen": "PT1M",
            "responseTimeMs": 89,
        },
        "ven-103": {
            "address": "789 Industrial Blvd, Grid Sector 3",
            "locationLabel": "Manufacturing Zone",
            "lastSeen": "PT15M",
            "responseTimeMs": 0,
        },
    }


_init_vens()


# Simple in-memory events timeline
EVENTS: Dict[str, Event] = {
    "evt-1": Event(
        id="evt-1",
        status="scheduled",
        startTime="2024-07-10T15:00:00Z",
        endTime="2024-07-10T17:00:00Z",
        requestedReductionKw=500,
        actualReductionKw=0,
    )
}


def list_vens() -> List[Ven]:
    return list(VENS.values())


def get_ven(ven_id: str) -> Optional[Ven]:
    return VENS.get(ven_id)


def upsert_ven(ven: Ven) -> Ven:
    VENS[ven.id] = ven
    return ven


def get_network_stats() -> NetworkStats:
    vens = list_vens()
    ven_count = len(vens)
    controllable = sum(v.metrics.shedAvailabilityKw for v in vens)
    potential = sum(sum(l.shedCapabilityKw for l in v.loads) for v in vens)
    household = sum(max(0.0, v.metrics.currentPowerKw) for v in vens)
    # Extended fields for UI
    online_vens = sum(1 for v in vens if v.status == "online")
    # Event-based reduction (dummy)
    evt = current_event()
    current_reduction_kw = 0.0
    if evt and evt.status == "active":
        current_reduction_kw = min(evt.requestedReductionKw, controllable)
    return NetworkStats(
        venCount=ven_count,
        controllablePowerKw=round(controllable, 2),
        potentialLoadReductionKw=round(potential, 2),
        householdUsageKw=round(household, 2),
        onlineVens=online_vens,
        currentLoadReductionKw=round(current_reduction_kw, 2),
        networkEfficiency=94.2,
        averageHousePower=3.2,
        totalHousePowerToday=1247.6,
    )


def get_load_type_stats() -> List[LoadTypeStats]:
    agg: Dict[str, LoadTypeStats] = {}
    for v in list_vens():
        for l in v.loads:
            if l.type not in agg:
                agg[l.type] = LoadTypeStats(
                    type=l.type, totalCapacityKw=0.0, totalShedCapabilityKw=0.0, currentUsageKw=0.0
                )
            entry = agg[l.type]
            entry.totalCapacityKw += l.capacityKw
            entry.totalShedCapabilityKw += l.shedCapabilityKw
            entry.currentUsageKw += max(0.0, l.currentPowerKw)
    # Round for nicer output
    for k, v in agg.items():
        v.totalCapacityKw = round(v.totalCapacityKw, 2)
        v.totalShedCapabilityKw = round(v.totalShedCapabilityKw, 2)
        v.currentUsageKw = round(v.currentUsageKw, 2)
    return list(agg.values())


def sample_history_points(start: Optional[str] = None, end: Optional[str] = None, step: str = "5m") -> HistoryResponse:
    now = datetime.utcnow().replace(microsecond=0)
    points: List[TimeseriesPoint] = []
    for i in range(6):
        ts = now - timedelta(minutes=5 * (5 - i))
        points.append(
            TimeseriesPoint(
                timestamp=ts.isoformat() + "Z",
                usedPowerKw=round(5.0 + (i * 0.2), 2),
                shedPowerKw=0.0,
            )
        )
    return HistoryResponse(points=points)


def list_events() -> List[Event]:
    return list(EVENTS.values())


def get_event(event_id: str) -> Optional[Event]:
    return EVENTS.get(event_id)


def set_event(evt: Event) -> Event:
    EVENTS[evt.id] = evt
    return evt


def current_event() -> Optional[Event]:
    # Return the first active event if any; else scheduled soonest
    active = [e for e in EVENTS.values() if e.status == "active"]
    if active:
        return active[0]
    scheduled = [e for e in EVENTS.values() if e.status == "scheduled"]
    return scheduled[0] if scheduled else None


def ven_summaries() -> list[VenSummary]:
    out: list[VenSummary] = []
    for v in list_vens():
        meta = VEN_META.get(v.id, {})
        out.append(
            VenSummary(
                id=v.id,
                name=v.name,
                location=meta.get("locationLabel", f"{v.location.lat:.2f},{v.location.lon:.2f}"),
                status=v.status,
                controllablePower=max(0.0, v.metrics.shedAvailabilityKw),
                currentPower=max(0.0, v.metrics.currentPowerKw),
                address=meta.get("address", ""),
                lastSeen=meta.get("lastSeen", "PT1M"),
                responseTime=meta.get("responseTimeMs", 0),
            )
        )
    return out


def event_metrics(event_id: str) -> EventMetrics | None:
    evt = get_event(event_id)
    if not evt:
        return None
    # Dummy progress: 40% of requested reduction, 238 VENS responding, 142ms avg
    return EventMetrics(
        currentReductionKw=round(evt.requestedReductionKw * 0.4, 2),
        vensResponding=238,
        avgResponseMs=142,
    )
