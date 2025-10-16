"""
EVALSTPM34 Meter Exceptions

Custom exceptions for EVALSTPM34 meter operations.
"""


class EVALSTPM34Error(Exception):
    """Base exception for EVALSTPM34 meter operations."""
    pass


class UARTCommunicationError(EVALSTPM34Error):
    """Raised when UART communication fails."""
    pass


class CalibrationError(EVALSTPM34Error):
    """Raised when calibration operations fail."""
    pass


class MeterNotFoundError(EVALSTPM34Error):
    """Raised when attempting to operate on a meter that doesn't exist."""
    pass


class InvalidMeterDataError(EVALSTPM34Error):
    """Raised when meter returns invalid or corrupted data."""
    pass


class MeterTimeoutError(EVALSTPM34Error):
    """Raised when meter communication times out."""
    pass