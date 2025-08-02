from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VENBase(BaseModel):
    ven_id: str
    registration_id: str
    status: Optional[str] = "active"

class VENCreate(VENBase):
    pass

class VENRead(VENBase):
    created_at: datetime

    class Config:
        orm_mode = True
