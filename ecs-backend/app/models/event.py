from sqlalchemy import Column, String, DateTime, JSON
from datetime import datetime

from . import Base

class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)
    ven_id = Column(String, index=True)
    signal_name = Column(String)
    signal_type = Column(String)
    signal_payload = Column(String)
    start_time = Column(DateTime)
    response_required = Column(String)
    raw = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
