from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VENBase(BaseModel):
    ven_id: str
    name: str
    registration_id: str | None = None
    status: str = "active"
    latitude: float | None = None
    longitude: float | None = None

    model_config = ConfigDict(from_attributes=True)


class VENCreate(VENBase):
    pass


class VENUpdate(BaseModel):
    registration_id: str | None = None
    name: str | None = None
    status: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class VENRead(VENBase):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
