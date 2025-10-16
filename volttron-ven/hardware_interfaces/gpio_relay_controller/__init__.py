"""
GPIO Relay Controller Module

This module provides an interface for controlling normally closed (NC) relays
connected to GPIO pins on a Raspberry Pi. Used for load switching in demand
response scenarios.
"""

__version__ = "0.1.0"

from .controller import GPIORelayController
from .exceptions import GPIORelayError, RelayNotFoundError

__all__ = [
    "GPIORelayController",
    "GPIORelayError", 
    "RelayNotFoundError",
]