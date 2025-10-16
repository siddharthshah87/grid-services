"""
Hardware Interfaces Package

This package contains hardware interface modules for the physical VEN implementation:
- gpio_relay_controller: Controls GPIO-based relays for load switching
- evalstpm34_meter: Interfaces with EVALSTPM34 metering boards via UART
"""

__version__ = "0.1.0"
__author__ = "Grid Services Team"

# Import main classes for easy access
from .gpio_relay_controller import GPIORelayController
from .evalstpm34_meter import EVALSTPM34Meter

__all__ = [
    "GPIORelayController",
    "EVALSTPM34Meter",
]