"""
VEN Acknowledgment Model

Stores acknowledgments from VENs when they respond to DR events.
Includes detailed circuit curtailment information.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from . import Base


class VenAck(Base):
    """
    VEN acknowledgment response to a DR event command.
    
    Stores the detailed response from a VEN including which circuits
    were curtailed and by how much.
    """
    __tablename__ = "ven_acks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ven_id = Column(String(255), nullable=False, index=True)
    event_id = Column(String(255), nullable=False, index=True)
    correlation_id = Column(String(255), nullable=True, index=True)
    
    # ACK metadata
    op = Column(String(50), nullable=False)  # "event", "restore", "ping"
    status = Column(String(50), nullable=False)  # "accepted", "rejected", "success"
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Shed information
    requested_shed_kw = Column(Float, nullable=True)
    actual_shed_kw = Column(Float, nullable=True)
    
    # Circuit details (JSON array)
    # Each entry: {id, name, breaker_amps, original_kw, curtailed_kw, final_kw, critical}
    circuits_curtailed = Column(JSON, nullable=True)
    
    # Full ACK payload for debugging
    raw_payload = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return (
            f"<VenAck(id={self.id}, ven_id={self.ven_id}, event_id={self.event_id}, "
            f"status={self.status}, actual_shed_kw={self.actual_shed_kw})>"
        )
