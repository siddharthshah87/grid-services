from sqlalchemy import Column, String, DateTime
from datetime import datetime

from . import Base


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
