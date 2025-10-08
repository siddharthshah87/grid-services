from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, JSON
from sqlalchemy.sql import func

from . import Base


class VenTelemetry(Base):
    """Aggregated telemetry received from VEN MQTT payloads."""

    __tablename__ = "ven_telemetry"

    id = Column(Integer, primary_key=True)
    ven_id = Column(String, ForeignKey("vens.ven_id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    used_power_kw = Column(Float, nullable=False)
    shed_power_kw = Column(Float, nullable=False, default=0.0)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VenLoadSample(Base):
    """Per-load telemetry sample for a VEN."""

    __tablename__ = "ven_load_samples"

    id = Column(Integer, primary_key=True)
    ven_id = Column(String, ForeignKey("vens.ven_id", ondelete="CASCADE"), nullable=False, index=True)
    load_id = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    load_type = Column(String, nullable=True)
    used_power_kw = Column(Float, nullable=False)
    shed_power_kw = Column(Float, nullable=False, default=0.0)
    capacity_kw = Column(Float, nullable=True)
    shed_capability_kw = Column(Float, nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VenStatus(Base):
    """Tracks status transitions for a VEN."""

    __tablename__ = "ven_statuses"

    id = Column(Integer, primary_key=True)
    ven_id = Column(String, ForeignKey("vens.ven_id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
