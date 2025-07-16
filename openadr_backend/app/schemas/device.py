from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class DeviceBase(BaseModel):
    device_id: str
    name: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceRead(DeviceBase):
    created_at: datetime

    class Config:
        orm_mode = True
