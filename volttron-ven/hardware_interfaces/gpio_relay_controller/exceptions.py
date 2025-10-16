"""
GPIO Relay Controller Exceptions

Custom exceptions for GPIO relay operations.
"""


class GPIORelayError(Exception):
    """Base exception for GPIO relay operations."""
    pass


class RelayNotFoundError(GPIORelayError):
    """Raised when attempting to operate on a relay that doesn't exist."""
    pass


class GPIOInitializationError(GPIORelayError):
    """Raised when GPIO initialization fails."""
    pass


class RelayOperationError(GPIORelayError):
    """Raised when relay operation (on/off) fails."""
    pass