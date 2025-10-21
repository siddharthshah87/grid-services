from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.sql import func

from . import Base


class VEN(Base):
    __tablename__ = "vens"

    ven_id = Column(String, primary_key=True, index=True)
    registration_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=False)
    status = Column(String, default="active")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)  # Updated when telemetry received
