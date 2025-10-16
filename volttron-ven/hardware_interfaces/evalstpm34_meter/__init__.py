"""
EVALSTPM34 Meter Interface Module

This module provides an interface for communicating with EVALSTPM34 evaluation
boards via UART for power metering, current/voltage sensing, and calibration.
"""

__version__ = "0.1.0"

from .meter import EVALSTPM34Meter
from .exceptions import EVALSTPM34Error, CalibrationError, UARTCommunicationError
from .calibration import CalibrationManager
from .data_types import MeterReading, CalibrationData

__all__ = [
    "EVALSTPM34Meter",
    "EVALSTPM34Error",
    "CalibrationError", 
    "UARTCommunicationError",
    "CalibrationManager",
    "MeterReading",
    "CalibrationData",
]