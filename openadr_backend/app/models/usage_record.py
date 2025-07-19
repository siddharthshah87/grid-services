from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from datetime import datetime

from . import Base

class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.device_id"), index=True)
    circuit_id = Column(Integer, ForeignKey("circuits.id"), nullable=True, index=True)
    timestamp = Column(DateTime)
    consumption = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
