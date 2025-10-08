from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class EventBase(BaseModel):
    event_id: str
    ven_id: str
    signal_name: str
    signal_type: str
    signal_payload: str
    start_time: datetime
    response_required: str
    raw: Optional[dict] = None


class EventCreate(EventBase):
    model_config = ConfigDict(extra="forbid")


class EventUpdate(BaseModel):
    ven_id: Optional[str] = None
    signal_name: Optional[str] = None
    signal_type: Optional[str] = None
    signal_payload: Optional[str] = None
    start_time: Optional[datetime] = None
    response_required: Optional[str] = None
    raw: Optional[dict] = None

    model_config = ConfigDict(extra="forbid")


class EventRead(EventBase):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventMetrics(BaseModel):
    current_reduction_kw: float
    vens_responding: int
    avg_response_ms: int


class EventWithMetrics(EventRead):
    current_reduction_kw: Optional[float] = None
    vens_responding: Optional[int] = None
    avg_response_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
