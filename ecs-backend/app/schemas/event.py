from pydantic import BaseModel
from datetime import datetime

class EventBase(BaseModel):
    event_id: str
    ven_id: str
    signal_name: str
    signal_type: str
    signal_payload: str
    start_time: datetime
    response_required: str
    raw: dict

class EventCreate(EventBase):
    pass

class EventRead(EventBase):
    created_at: datetime

    class Config:
        orm_mode = True
