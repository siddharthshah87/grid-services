from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventBase(BaseModel):
    event_id: str
    status: str = "scheduled"
    start_time: datetime | None = None
    end_time: datetime | None = None
    requested_reduction_kw: float | None = None
    ven_id: str | None = None
    signal_name: str | None = None
    signal_type: str | None = None
    signal_payload: str | None = None
    response_required: str | None = None
    raw: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    status: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    requested_reduction_kw: float | None = None
    ven_id: str | None = None
    signal_name: str | None = None
    signal_type: str | None = None
    signal_payload: str | None = None
    response_required: str | None = None
    raw: dict | None = None


class EventRead(EventBase):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
