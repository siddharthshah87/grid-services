from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class VEN(Base):
    __tablename__ = "vens"

    ven_id = Column(String, primary_key=True, index=True)
    registration_id = Column(String, unique=True, index=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
