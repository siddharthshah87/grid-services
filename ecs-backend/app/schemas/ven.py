from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class VENBase(BaseModel):
    ven_id: str
    registration_id: str
    status: Optional[str] = "active"


class VENCreate(VENBase):
    model_config = ConfigDict(extra="forbid")


class VENUpdate(BaseModel):
    registration_id: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class VENRead(VENBase):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
