from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy.sql import func

from . import Base


class VenTelemetry(Base):
    """Aggregated telemetry received from VEN MQTT payloads."""

    __tablename__ = "ven_telemetry"
    __table_args__ = (
        Index("ix_ven_telemetry_ven_id_timestamp", "ven_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True)
    ven_id = Column(
        String,
        ForeignKey("vens.ven_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    used_power_kw = Column(Float, nullable=False)
    shed_power_kw = Column(Float, nullable=False, default=0.0)
    payload = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class VenLoadSample(Base):
    """Per-load telemetry sample for a VEN."""

    __tablename__ = "ven_load_samples"
    __table_args__ = (
        Index(
            "ix_ven_load_samples_ven_id_load_id_timestamp",
            "ven_id",
            "load_id",
            "timestamp",
        ),
    )

    id = Column(Integer, primary_key=True)
    ven_id = Column(
        String,
        ForeignKey("vens.ven_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    load_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    load_type = Column(String, nullable=True)
    used_power_kw = Column(Float, nullable=False)
    shed_power_kw = Column(Float, nullable=False, default=0.0)
    capacity_kw = Column(Float, nullable=True)
    shed_capability_kw = Column(Float, nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class VenStatus(Base):
    """Tracks status transitions for a VEN."""

    __tablename__ = "ven_statuses"
    __table_args__ = (
        Index("ix_ven_statuses_ven_id_recorded_at", "ven_id", "recorded_at"),
    )

    id = Column(Integer, primary_key=True)
    ven_id = Column(
        String,
        ForeignKey("vens.ven_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String, nullable=False)
    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    details = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
