from sqlalchemy import Column, DateTime, Float, JSON, String
from sqlalchemy.sql import func

from . import Base


class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)
    ven_id = Column(String, index=True, nullable=True)
    status = Column(String, default="scheduled", nullable=False)
    signal_name = Column(String, nullable=True)
    signal_type = Column(String, nullable=True)
    signal_payload = Column(String, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    requested_reduction_kw = Column(Float, nullable=True)
    response_required = Column(String, nullable=True)
    raw = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
