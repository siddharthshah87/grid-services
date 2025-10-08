from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import Mapped, relationship

from . import Base


class TelemetryReading(Base):
    """A single telemetry datapoint emitted by a VEN."""

    __tablename__ = "telemetry_readings"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    ven_id: Mapped[str] = Column(String, index=True, nullable=False)
    timestamp: Mapped[datetime] = Column(DateTime(timezone=True), index=True, nullable=False)
    used_power_kw: Mapped[float | None] = Column(Float)
    shed_power_kw: Mapped[float | None] = Column(Float)
    requested_reduction_kw: Mapped[float | None] = Column(Float)
    event_id: Mapped[str | None] = Column(String)
    battery_soc: Mapped[float | None] = Column(Float)
    raw_payload: Mapped[dict | None] = Column(JSON)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, nullable=False)

    loads: Mapped[list[TelemetryLoad]] = relationship(
        "TelemetryLoad",
        back_populates="telemetry",
        cascade="all, delete-orphan",
    )


class TelemetryLoad(Base):
    """Per-load telemetry as part of a reading."""

    __tablename__ = "telemetry_loads"

    id: Mapped[int] = Column(Integer, primary_key=True)
    telemetry_id: Mapped[int] = Column(
        Integer,
        ForeignKey("telemetry_readings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    load_id: Mapped[str] = Column(String, nullable=False)
    name: Mapped[str | None] = Column(String)
    type: Mapped[str | None] = Column(String)
    capacity_kw: Mapped[float | None] = Column(Float)
    current_power_kw: Mapped[float | None] = Column(Float)
    shed_capability_kw: Mapped[float | None] = Column(Float)
    enabled: Mapped[bool | None] = Column(Boolean)
    priority: Mapped[int | None] = Column(Integer)
    raw_payload: Mapped[dict | None] = Column(JSON)

    telemetry: Mapped[TelemetryReading] = relationship("TelemetryReading", back_populates="loads")


class LoadSnapshot(Base):
    """Snapshot of a VEN's controllable loads."""

    __tablename__ = "load_snapshots"

    id: Mapped[int] = Column(Integer, primary_key=True)
    ven_id: Mapped[str] = Column(String, index=True, nullable=False)
    timestamp: Mapped[datetime] = Column(DateTime(timezone=True), index=True, nullable=False)
    load_id: Mapped[str] = Column(String, nullable=False)
    name: Mapped[str | None] = Column(String)
    type: Mapped[str | None] = Column(String)
    capacity_kw: Mapped[float | None] = Column(Float)
    current_power_kw: Mapped[float | None] = Column(Float)
    shed_capability_kw: Mapped[float | None] = Column(Float)
    enabled: Mapped[bool | None] = Column(Boolean)
    priority: Mapped[int | None] = Column(Integer)
    raw_payload: Mapped[dict | None] = Column(JSON)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, nullable=False)
