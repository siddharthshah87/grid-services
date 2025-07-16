from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CircuitBase(BaseModel):
    name: str
    description: Optional[str] = None

class CircuitCreate(CircuitBase):
    pass

class CircuitRead(CircuitBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
