from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class VEN(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ven_id: str
    name: Optional[str] = None
    registered_at: datetime = Field(default_factory=datetime.utcnow)

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str
    ven_id: int = Field(foreign_key="ven.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
