from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException


def parse_timestamp(value: str) -> datetime:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp: {value}") from exc


def parse_granularity(value: str | None, *, default: timedelta = timedelta(minutes=5)) -> timedelta:
    if not value:
        return default

    try:
        unit = value[-1]
        amount = int(value[:-1])
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid granularity: {value}") from exc

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Granularity must be positive")

    if unit == "m":
        return timedelta(minutes=amount)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "s":
        return timedelta(seconds=amount)

    raise HTTPException(status_code=400, detail=f"Unsupported granularity unit: {unit}")


def format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")
