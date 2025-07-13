from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .ven import VEN
from .event import Event

__all__ = ["Base", "VEN", "Event"]
