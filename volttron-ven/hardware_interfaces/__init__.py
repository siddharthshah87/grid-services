"""
Hardware interfaces for physical VEN implementations.

This package provides interfaces for controlling hardware components
commonly used in Virtual End Node (VEN) demand response systems.
"""

from .gpio_relay_controller import (
    GPIORelayController,
    RelayConfig,
    RelayState,
    GPIORelayError,
    RelayNotFoundError,
    GPIOInitializationError,
    RelayOperationError,
    create_relay_config
)

from .evalstpm34_meter import (
    EVALSTPM34Meter,
    MeterConfig,
    InstantaneousValues,
    EnergyValues,
    STPM34Command,
    STPM34Status
)

__all__ = [
    'GPIORelayController',
    'RelayConfig', 
    'RelayState',
    'GPIORelayError',
    'RelayNotFoundError',
    'GPIOInitializationError',
    'RelayOperationError',
    'create_relay_config',
    'EVALSTPM34Meter',
    'MeterConfig',
    'InstantaneousValues',
    'EnergyValues',
    'STPM34Command',
    'STPM34Status'
]

__version__ = '1.0.0'