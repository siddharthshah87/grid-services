from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UsageRecordBase(BaseModel):
    device_id: str
    circuit_id: Optional[int] = None
    timestamp: datetime
    consumption: float

class UsageRecordCreate(UsageRecordBase):
    pass

class UsageRecordRead(UsageRecordBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
