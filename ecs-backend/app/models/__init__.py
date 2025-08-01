from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .ven import VEN  # noqa: E402
from .event import Event  # noqa: E402

__all__ = ["Base", "VEN", "Event"]
