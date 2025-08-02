from sqlalchemy import Column, String, DateTime
from datetime import datetime

from . import Base

class VEN(Base):
    __tablename__ = "vens"

    ven_id = Column(String, primary_key=True, index=True)
    registration_id = Column(String, unique=True, index=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
