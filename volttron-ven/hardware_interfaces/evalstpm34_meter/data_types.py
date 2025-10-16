"""
Data Types for EVALSTPM34 Meter

Defines data structures for meter readings and calibration data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class MeterChannel(Enum):
    """Meter channel identifiers."""
    CHANNEL_1 = "ch1"
    CHANNEL_2 = "ch2"


class PowerType(Enum):
    """Power measurement types."""
    ACTIVE = "active"
    REACTIVE = "reactive"
    APPARENT = "apparent"


@dataclass
class MeterReading:
    """
    Complete meter reading from EVALSTPM34.
    
    Contains voltage, current, power, energy, and frequency measurements
    for both channels.
    """
    timestamp: datetime
    meter_id: str
    
    # Channel 1 measurements
    voltage_ch1: float  # RMS voltage in V
    current_ch1: float  # RMS current in A
    active_power_ch1: float  # Active power in W
    reactive_power_ch1: float  # Reactive power in VAR
    apparent_power_ch1: float  # Apparent power in VA
    power_factor_ch1: float  # Power factor
    energy_ch1: float  # Accumulated energy in Wh
    
    # Channel 2 measurements
    voltage_ch2: float  # RMS voltage in V
    current_ch2: float  # RMS current in A
    active_power_ch2: float  # Active power in W
    reactive_power_ch2: float  # Reactive power in VAR
    apparent_power_ch2: float  # Apparent power in VA
    power_factor_ch2: float  # Power factor
    energy_ch2: float  # Accumulated energy in Wh
    
    # Common measurements
    frequency: float  # Line frequency in Hz
    temperature: Optional[float] = None  # Temperature in °C
    
    # Data quality indicators
    data_valid: bool = True
    error_flags: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reading to dictionary format."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "meter_id": self.meter_id,
            "channel_1": {
                "voltage": self.voltage_ch1,
                "current": self.current_ch1,
                "active_power": self.active_power_ch1,
                "reactive_power": self.reactive_power_ch1,
                "apparent_power": self.apparent_power_ch1,
                "power_factor": self.power_factor_ch1,
                "energy": self.energy_ch1,
            },
            "channel_2": {
                "voltage": self.voltage_ch2,
                "current": self.current_ch2,
                "active_power": self.active_power_ch2,
                "reactive_power": self.reactive_power_ch2,
                "apparent_power": self.apparent_power_ch2,
                "power_factor": self.power_factor_ch2,
                "energy": self.energy_ch2,
            },
            "frequency": self.frequency,
            "temperature": self.temperature,
            "data_valid": self.data_valid,
            "error_flags": self.error_flags,
        }


@dataclass
class CalibrationData:
    """
    Calibration parameters for EVALSTPM34 meter.
    
    Contains calibration coefficients and reference values used
    for accurate measurements.
    """
    meter_id: str
    calibration_date: datetime
    
    # Voltage calibration
    voltage_gain_ch1: float
    voltage_offset_ch1: float
    voltage_gain_ch2: float
    voltage_offset_ch2: float
    
    # Current calibration  
    current_gain_ch1: float
    current_offset_ch1: float
    current_gain_ch2: float
    current_offset_ch2: float
    
    # Power calibration
    power_gain_ch1: float
    power_offset_ch1: float
    power_gain_ch2: float
    power_offset_ch2: float
    
    # Phase calibration
    phase_compensation_ch1: float
    phase_compensation_ch2: float
    
    # Reference values used during calibration
    reference_voltage: float
    reference_current: float
    reference_frequency: float
    
    # Calibration metadata
    calibrated_by: str
    calibration_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert calibration data to dictionary format."""
        return {
            "meter_id": self.meter_id,
            "calibration_date": self.calibration_date.isoformat(),
            "voltage_calibration": {
                "ch1_gain": self.voltage_gain_ch1,
                "ch1_offset": self.voltage_offset_ch1,
                "ch2_gain": self.voltage_gain_ch2,
                "ch2_offset": self.voltage_offset_ch2,
            },
            "current_calibration": {
                "ch1_gain": self.current_gain_ch1,
                "ch1_offset": self.current_offset_ch1,
                "ch2_gain": self.current_gain_ch2,
                "ch2_offset": self.current_offset_ch2,
            },
            "power_calibration": {
                "ch1_gain": self.power_gain_ch1,
                "ch1_offset": self.power_offset_ch1,
                "ch2_gain": self.power_gain_ch2,
                "ch2_offset": self.power_offset_ch2,
            },
            "phase_calibration": {
                "ch1_compensation": self.phase_compensation_ch1,
                "ch2_compensation": self.phase_compensation_ch2,
            },
            "reference_values": {
                "voltage": self.reference_voltage,
                "current": self.reference_current,
                "frequency": self.reference_frequency,
            },
            "metadata": {
                "calibrated_by": self.calibrated_by,
                "notes": self.calibration_notes,
            }
        }


@dataclass
class MeterConfig:
    """Configuration for an EVALSTPM34 meter."""
    meter_id: str
    uart_port: str
    baud_rate: int = 115200
    timeout: float = 1.0
    name: str = ""
    description: str = ""
    
    # Hardware configuration
    channels_enabled: int = 0x03  # Both channels enabled by default
    sampling_rate: int = 4000  # Sampling rate in Hz
    
    # Communication settings
    retry_count: int = 3
    command_delay: float = 0.1  # Delay between commands in seconds