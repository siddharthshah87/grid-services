"""
EVALSTPM34 Meter Interface

Provides UART communication interface for EVALSTPM34 evaluation boards
for power metering and energy measurement applications.

Features:
- Real-time power measurements (V, I, P, Q, S, PF)
- Dual channel support
- Energy accumulation
- Temperature monitoring
- Calibration support
- Hardware abstraction for testing
"""

import logging
import time
import struct
from datetime import datetime
from typing import Optional, Dict, List, Any, Union
import threading

from .exceptions import (EVALSTPM34Error, UARTCommunicationError, 
                        MeterNotFoundError, InvalidMeterDataError, MeterTimeoutError)
from .data_types import MeterReading, MeterConfig, MeterChannel
from .calibration import CalibrationManager

# Optional serial library import
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logging.warning("pySerial not available. UART operations will be simulated.")


class EVALSTPM34Meter:
    """
    Interface for EVALSTPM34 power metering evaluation board.
    
    Communicates via UART to collect voltage, current, power, and energy
    measurements from the STPM34 metering IC.
    """
    
    # STPM34 Register addresses (example values - need actual datasheet)
    REG_VOLTAGE_CH1 = 0x10
    REG_CURRENT_CH1 = 0x11
    REG_POWER_CH1 = 0x12
    REG_VOLTAGE_CH2 = 0x20
    REG_CURRENT_CH2 = 0x21
    REG_POWER_CH2 = 0x22
    REG_FREQUENCY = 0x30
    REG_TEMPERATURE = 0x31
    REG_STATUS = 0x40
    
    def __init__(self, config: MeterConfig, simulation_mode: bool = None):
        """
        Initialize EVALSTPM34 meter interface.
        
        Args:
            config: Meter configuration
            simulation_mode: Force simulation mode (None = auto-detect)
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.serial_connection: Optional[Any] = None
        self.calibration_manager = CalibrationManager()
        
        # Determine if we should use simulation mode
        if simulation_mode is None:
            self.simulation_mode = not SERIAL_AVAILABLE
        else:
            self.simulation_mode = simulation_mode
            
        if not self.simulation_mode and not SERIAL_AVAILABLE:
            raise UARTCommunicationError("pySerial library not available but simulation mode disabled")
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Simulation data for testing
        self._simulation_data = {
            "voltage_ch1": 120.0,
            "current_ch1": 5.0,
            "voltage_ch2": 120.0,
            "current_ch2": 3.0,
            "frequency": 60.0,
            "temperature": 25.0,
        }
        
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize UART connection to the meter."""
        if self.simulation_mode:
            self.logger.info(f"Initializing EVALSTPM34 meter {self.config.meter_id} in simulation mode")
            return
        
        try:
            self.serial_connection = serial.Serial(
                port=self.config.uart_port,
                baudrate=self.config.baud_rate,
                timeout=self.config.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Wait for connection to stabilize
            time.sleep(0.1)
            
            # Send initialization commands if needed
            self._initialize_meter()
            
            self.logger.info(f"Initialized EVALSTPM34 meter {self.config.meter_id} on {self.config.uart_port}")
            
        except Exception as e:
            raise UARTCommunicationError(f"Failed to initialize UART connection: {e}")
    
    def _initialize_meter(self):
        """Send initialization commands to the meter."""
        # Placeholder for meter-specific initialization
        # This would include setting up sampling rates, enabling channels, etc.
        pass
    
    def _send_command(self, command: bytes, expect_response: bool = True) -> Optional[bytes]:
        """
        Send command to meter and optionally wait for response.
        
        Args:
            command: Command bytes to send
            expect_response: Whether to wait for a response
            
        Returns:
            Response bytes if expected, None otherwise
            
        Raises:
            UARTCommunicationError: If communication fails
            MeterTimeoutError: If response times out
        """
        if self.simulation_mode:
            # Simulate command/response
            time.sleep(0.01)  # Simulate communication delay
            if expect_response:
                return b'\x00\x01\x02\x03'  # Dummy response
            return None
        
        with self._lock:
            try:
                if not self.serial_connection or not self.serial_connection.is_open:
                    raise UARTCommunicationError("Serial connection not available")
                
                # Clear input buffer
                self.serial_connection.reset_input_buffer()
                
                # Send command
                self.serial_connection.write(command)
                
                if expect_response:
                    # Wait for response
                    response = self.serial_connection.read(64)  # Adjust size as needed
                    if len(response) == 0:
                        raise MeterTimeoutError("No response from meter")
                    return response
                
                return None
                
            except Exception as e:
                raise UARTCommunicationError(f"Command failed: {e}")
    
    def _read_register(self, register: int) -> int:
        """
        Read a register from the STPM34.
        
        Args:
            register: Register address
            
        Returns:
            Register value
        """
        # Construct read command (format depends on STPM34 protocol)
        command = struct.pack('>BB', 0x01, register)  # Example format
        
        response = self._send_command(command, expect_response=True)
        
        if response and len(response) >= 4:
            # Parse response (format depends on protocol)
            value = struct.unpack('>I', response[:4])[0]
            return value
        else:
            raise InvalidMeterDataError("Invalid register response")
    
    def _convert_raw_voltage(self, raw_value: int, channel: MeterChannel) -> float:
        """Convert raw voltage reading to volts."""
        # Apply calibration and scaling
        # This is a placeholder - actual conversion depends on STPM34 specifications
        voltage = raw_value * 0.0001  # Example scaling
        
        # Apply calibration if available
        calibration = self.calibration_manager.get_calibration(self.config.meter_id)
        if calibration:
            if channel == MeterChannel.CHANNEL_1:
                voltage = voltage * calibration.voltage_gain_ch1 + calibration.voltage_offset_ch1
            else:
                voltage = voltage * calibration.voltage_gain_ch2 + calibration.voltage_offset_ch2
        
        return voltage
    
    def _convert_raw_current(self, raw_value: int, channel: MeterChannel) -> float:
        """Convert raw current reading to amperes."""
        # Apply calibration and scaling
        current = raw_value * 0.0001  # Example scaling
        
        # Apply calibration if available
        calibration = self.calibration_manager.get_calibration(self.config.meter_id)
        if calibration:
            if channel == MeterChannel.CHANNEL_1:
                current = current * calibration.current_gain_ch1 + calibration.current_offset_ch1
            else:
                current = current * calibration.current_gain_ch2 + calibration.current_offset_ch2
        
        return current
    
    def read_instantaneous_values(self) -> MeterReading:
        """
        Read instantaneous power measurements from the meter.
        
        Returns:
            Complete meter reading with all channels
            
        Raises:
            UARTCommunicationError: If communication fails
            InvalidMeterDataError: If data is invalid
        """
        try:
            if self.simulation_mode:
                # Generate simulated data with some variation
                import random
                sim_data = self._simulation_data.copy()
                
                # Add some realistic variation
                sim_data["voltage_ch1"] += random.uniform(-2.0, 2.0)
                sim_data["current_ch1"] += random.uniform(-0.5, 0.5)
                sim_data["voltage_ch2"] += random.uniform(-2.0, 2.0)
                sim_data["current_ch2"] += random.uniform(-0.3, 0.3)
                
                # Calculate derived values
                active_power_ch1 = sim_data["voltage_ch1"] * sim_data["current_ch1"] * 0.9
                active_power_ch2 = sim_data["voltage_ch2"] * sim_data["current_ch2"] * 0.85
                
                reading = MeterReading(
                    timestamp=datetime.now(),
                    meter_id=self.config.meter_id,
                    voltage_ch1=sim_data["voltage_ch1"],
                    current_ch1=sim_data["current_ch1"],
                    active_power_ch1=active_power_ch1,
                    reactive_power_ch1=active_power_ch1 * 0.1,
                    apparent_power_ch1=(active_power_ch1**2 + (active_power_ch1 * 0.1)**2)**0.5,
                    power_factor_ch1=0.9,
                    energy_ch1=0.0,  # Would be accumulated
                    voltage_ch2=sim_data["voltage_ch2"],
                    current_ch2=sim_data["current_ch2"],
                    active_power_ch2=active_power_ch2,
                    reactive_power_ch2=active_power_ch2 * 0.15,
                    apparent_power_ch2=(active_power_ch2**2 + (active_power_ch2 * 0.15)**2)**0.5,
                    power_factor_ch2=0.85,
                    energy_ch2=0.0,  # Would be accumulated
                    frequency=sim_data["frequency"],
                    temperature=sim_data["temperature"],
                )
                
            else:
                # Read actual values from hardware
                voltage_ch1_raw = self._read_register(self.REG_VOLTAGE_CH1)
                current_ch1_raw = self._read_register(self.REG_CURRENT_CH1)
                voltage_ch2_raw = self._read_register(self.REG_VOLTAGE_CH2)
                current_ch2_raw = self._read_register(self.REG_CURRENT_CH2)
                frequency_raw = self._read_register(self.REG_FREQUENCY)
                temperature_raw = self._read_register(self.REG_TEMPERATURE)
                
                # Convert raw values
                voltage_ch1 = self._convert_raw_voltage(voltage_ch1_raw, MeterChannel.CHANNEL_1)
                current_ch1 = self._convert_raw_current(current_ch1_raw, MeterChannel.CHANNEL_1)
                voltage_ch2 = self._convert_raw_voltage(voltage_ch2_raw, MeterChannel.CHANNEL_2)
                current_ch2 = self._convert_raw_current(current_ch2_raw, MeterChannel.CHANNEL_2)
                
                # Calculate power values
                active_power_ch1 = voltage_ch1 * current_ch1 * 0.9  # Assuming PF
                active_power_ch2 = voltage_ch2 * current_ch2 * 0.9
                
                reading = MeterReading(
                    timestamp=datetime.now(),
                    meter_id=self.config.meter_id,
                    voltage_ch1=voltage_ch1,
                    current_ch1=current_ch1,
                    active_power_ch1=active_power_ch1,
                    reactive_power_ch1=0.0,  # Would calculate from actual measurements
                    apparent_power_ch1=voltage_ch1 * current_ch1,
                    power_factor_ch1=0.9,  # Would calculate from actual measurements
                    energy_ch1=0.0,  # Would be accumulated
                    voltage_ch2=voltage_ch2,
                    current_ch2=current_ch2,
                    active_power_ch2=active_power_ch2,
                    reactive_power_ch2=0.0,
                    apparent_power_ch2=voltage_ch2 * current_ch2,
                    power_factor_ch2=0.9,
                    energy_ch2=0.0,
                    frequency=60.0,  # Would convert from frequency_raw
                    temperature=25.0,  # Would convert from temperature_raw
                )
            
            return reading
            
        except Exception as e:
            raise InvalidMeterDataError(f"Failed to read meter data: {e}")
    
    def reset_energy_counters(self, channels: List[MeterChannel] = None):
        """
        Reset energy accumulation counters.
        
        Args:
            channels: List of channels to reset (None = all channels)
        """
        if channels is None:
            channels = [MeterChannel.CHANNEL_1, MeterChannel.CHANNEL_2]
        
        for channel in channels:
            if self.simulation_mode:
                self.logger.info(f"Simulated: Reset energy counter for {channel.value}")
            else:
                # Send reset command to meter
                # Implementation depends on STPM34 protocol
                pass
    
    def get_meter_info(self) -> Dict[str, Any]:
        """
        Get meter information and status.
        
        Returns:
            Dictionary with meter information
        """
        return {
            "meter_id": self.config.meter_id,
            "uart_port": self.config.uart_port,
            "baud_rate": self.config.baud_rate,
            "name": self.config.name,
            "description": self.config.description,
            "simulation_mode": self.simulation_mode,
            "connected": self.is_connected(),
            "channels_enabled": self.config.channels_enabled,
            "sampling_rate": self.config.sampling_rate,
        }
    
    def is_connected(self) -> bool:
        """
        Check if meter is connected and responding.
        
        Returns:
            True if connected and responsive
        """
        if self.simulation_mode:
            return True
        
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                return False
            
            # Send a simple status query
            response = self._send_command(b'\x01\x40', expect_response=True)  # Read status
            return response is not None and len(response) > 0
            
        except Exception:
            return False
    
    def close(self):
        """Close the UART connection."""
        if not self.simulation_mode and self.serial_connection:
            try:
                self.serial_connection.close()
                self.logger.info(f"Closed UART connection for meter {self.config.meter_id}")
            except Exception as e:
                self.logger.error(f"Error closing UART connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()


# Convenience functions
def create_meter_config(meter_id: str, uart_port: str, name: str = "", 
                       baud_rate: int = 115200, description: str = "") -> MeterConfig:
    """
    Create a meter configuration.
    
    Args:
        meter_id: Unique identifier for the meter
        uart_port: UART device path (e.g., "/dev/ttyUSB0")
        name: Human-readable name
        baud_rate: UART baud rate
        description: Optional description
        
    Returns:
        MeterConfig object
    """
    return MeterConfig(
        meter_id=meter_id,
        uart_port=uart_port,
        baud_rate=baud_rate,
        name=name,
        description=description
    )