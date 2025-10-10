"""Shared utilities for API routers."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Iterable, Sequence

from app.models.telemetry import VenStatus, VenTelemetry
from app.models.ven import VEN
from app.schemas.api_models import (
    HistoryResponse,
    Load,
    Location,
    NetworkStats,
    TimeseriesPoint,
    Ven,
    VenMetrics,
)


def _granularity_to_timedelta(value: str | None) -> timedelta:
    if not value:
        return timedelta(minutes=5)
    value = value.strip().lower()
    if not value:
        return timedelta(minutes=5)
    if value.endswith("ms"):
        try:
            amount = int(value[:-2])
        except ValueError:
            return timedelta(minutes=5)
        return timedelta(milliseconds=amount)
    unit = value[-1]
    try:
        amount = int(value[:-1])
    except ValueError:
        return timedelta(minutes=5)
    if unit == "m":
        return timedelta(minutes=amount)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "d":
        return timedelta(days=amount)
    return timedelta(minutes=5)


def build_ven_payload(
    ven: VEN,
    status: VenStatus | None,
    telemetry: VenTelemetry | None,
    *,
    include_loads: bool = False,
) -> Ven:
    """Convert ORM rows into an API response object."""

    location = Location(lat=ven.latitude or 0.0, lon=ven.longitude or 0.0)

    # Get current power from status or telemetry
    current_power = (
        status.current_power_kw if status and status.current_power_kw is not None
        else telemetry.used_power_kw if telemetry and telemetry.used_power_kw is not None
        else 0.0
    )

    # Get shed availability from status or telemetry
    shed_availability = (
        status.shed_availability_kw if status and status.shed_availability_kw is not None
        else telemetry.shed_power_kw if telemetry and telemetry.shed_power_kw is not None
        else 0.0
    )

    # Get active event ID from status or telemetry
    active_event = (
        status.active_event_id if status and status.active_event_id
        else (telemetry.event_id if telemetry and telemetry.event_id else None)
    )

    metrics = VenMetrics(
        currentPowerKw=current_power,
        shedAvailabilityKw=shed_availability,
        activeEventId=active_event,
        shedLoadIds=[
            load.load_id
            for load in (telemetry.loads if telemetry else [])
            if load.shed_capability_kw and load.shed_capability_kw > 0
        ],
    )

    status_value = status.status if status else ven.status or "unknown"

    created_at = ven.created_at or datetime.now(UTC)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)

    loads = None
    if include_loads and telemetry:
        loads = [
            Load(
                id=sample.load_id,
                type=sample.type or "unknown",
                capacityKw=sample.capacity_kw or 0.0,
                shedCapabilityKw=sample.shed_capability_kw or 0.0,
                currentPowerKw=sample.current_power_kw or 0.0,
                name=sample.name,
            )
            for sample in telemetry.loads
        ]

    return Ven(
        id=ven.ven_id,
        name=ven.name,
        status=status_value,
        location=location,
        metrics=metrics,
        createdAt=created_at,
        loads=loads,
    )


def build_history_response(
    telemetries: Sequence[VenTelemetry],
    granularity: str | None,
) -> HistoryResponse:
    """Bucket telemetry points into the requested granularity."""

    if not telemetries:
        return HistoryResponse(points=[])

    bucket = _granularity_to_timedelta(granularity)
    bucket_seconds = max(int(bucket.total_seconds()), 1)

    aggregates: dict[datetime, dict[str, list[float] | str | None]] = {}

    for row in telemetries:
        ts = row.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        epoch = int(ts.timestamp())
        bucket_epoch = (epoch // bucket_seconds) * bucket_seconds
        bucket_ts = datetime.fromtimestamp(bucket_epoch, tz=ts.tzinfo)

        entry = aggregates.setdefault(
            bucket_ts,
            {
                "used": [],
                "shed": [],
                "requested": [],
                "event": None,
            },
        )
        if row.used_power_kw is not None:
            entry["used"].append(row.used_power_kw)
        if row.shed_power_kw is not None:
            entry["shed"].append(row.shed_power_kw)
        if row.requested_reduction_kw is not None:
            entry["requested"].append(row.requested_reduction_kw)
        if row.event_id:
            entry["event"] = row.event_id

    points: list[TimeseriesPoint] = []
    for bucket_ts in sorted(aggregates.keys()):
        entry = aggregates[bucket_ts]
        used = sum(entry["used"]) / len(entry["used"]) if entry["used"] else 0.0
        shed = sum(entry["shed"]) / len(entry["shed"]) if entry["shed"] else 0.0
        requested = (
            sum(entry["requested"]) / len(entry["requested"])
            if entry["requested"]
            else None
        )
        points.append(
            TimeseriesPoint(
                timestamp=bucket_ts,
                usedPowerKw=used,
                shedPowerKw=shed,
                requestedReductionKw=requested,
                eventId=entry["event"],
            )
        )

    return HistoryResponse(points=points)


def aggregate_network_stats(
    vens: Sequence[VEN],
    statuses: dict[str, VenStatus],
    telemetries: dict[str, VenTelemetry],
) -> NetworkStats:
    """Build network statistics from stored telemetry."""

    controllable = 0.0
    potential = 0.0
    household = 0.0
    current_reduction = 0.0
    online = 0

    for ven in vens:
        status = statuses.get(ven.ven_id)
        telemetry = telemetries.get(ven.ven_id)
        if status and status.current_power_kw is not None:
            household += status.current_power_kw
        elif telemetry and telemetry.used_power_kw is not None:
            household += telemetry.used_power_kw

        if status and status.shed_availability_kw is not None:
            controllable += status.shed_availability_kw
            potential += status.shed_availability_kw
        elif telemetry and telemetry.shed_power_kw is not None:
            controllable += telemetry.shed_power_kw
            potential += telemetry.shed_power_kw

        if telemetry and telemetry.shed_power_kw is not None:
            current_reduction += telemetry.shed_power_kw

        if (status and status.status.lower() == "online") or ven.status.lower() == "online":
            online += 1

    return NetworkStats(
        venCount=len(vens),
        controllablePowerKw=round(controllable, 3),
        potentialLoadReductionKw=round(potential, 3),
        householdUsageKw=round(household, 3),
        onlineVens=online,
        currentLoadReductionKw=round(current_reduction, 3),
    )


def aggregate_load_stats(telemetries: Iterable[VenTelemetry]) -> dict[str, dict[str, float]]:
    """Aggregate load metrics by type from telemetry samples."""

    stats: dict[str, dict[str, float]] = defaultdict(lambda: {
        "capacity": 0.0,
        "shed": 0.0,
        "usage": 0.0,
    })

    for telemetry in telemetries:
        for load in telemetry.loads:
            load_type = load.type or "unknown"
            if load.capacity_kw:
                stats[load_type]["capacity"] += load.capacity_kw
            if load.shed_capability_kw:
                stats[load_type]["shed"] += load.shed_capability_kw
            if load.current_power_kw is not None:
                stats[load_type]["usage"] += load.current_power_kw

    return stats
