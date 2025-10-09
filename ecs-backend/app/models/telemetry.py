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
from sqlalchemy.sql import func

from . import Base


class VenTelemetry(Base):
    """A single telemetry datapoint emitted by a VEN."""

    __tablename__ = "ven_telemetry"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    ven_id: Mapped[str] = Column(
        String,
        ForeignKey("vens.ven_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    timestamp: Mapped[datetime] = Column(DateTime(timezone=True), index=True, nullable=False)
    used_power_kw: Mapped[float | None] = Column(Float)
    shed_power_kw: Mapped[float | None] = Column(Float)
    requested_reduction_kw: Mapped[float | None] = Column(Float)
    event_id: Mapped[str | None] = Column(
        String,
        ForeignKey("events.event_id", ondelete="SET NULL"),
        index=True,
    )
    battery_soc: Mapped[float | None] = Column(Float)
    raw_payload: Mapped[dict | None] = Column(JSON)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    loads: Mapped[list[VenLoadSample]] = relationship(
        "VenLoadSample",
        back_populates="telemetry",
        cascade="all, delete-orphan",
    )


class VenLoadSample(Base):
    """Per-load telemetry captured as part of a VEN telemetry sample."""

    __tablename__ = "ven_load_samples"

    id: Mapped[int] = Column(Integer, primary_key=True)
    telemetry_id: Mapped[int] = Column(
        Integer,
        ForeignKey("ven_telemetry.id", ondelete="CASCADE"),
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

    telemetry: Mapped[VenTelemetry] = relationship("VenTelemetry", back_populates="loads")


class VenStatus(Base):
    """Latest status values reported by a VEN."""

    __tablename__ = "ven_status"

    id: Mapped[int] = Column(Integer, primary_key=True)
    ven_id: Mapped[str] = Column(
        String,
        ForeignKey("vens.ven_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = Column(DateTime(timezone=True), index=True, nullable=False)
    status: Mapped[str] = Column(String, nullable=False)
    current_power_kw: Mapped[float | None] = Column(Float)
    shed_availability_kw: Mapped[float | None] = Column(Float)
    active_event_id: Mapped[str | None] = Column(
        String,
        ForeignKey("events.event_id", ondelete="SET NULL"),
        index=True,
    )
    raw_payload: Mapped[dict | None] = Column(JSON)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


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
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
