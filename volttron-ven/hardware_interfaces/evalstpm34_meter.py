"""
EVALSTPM34 Energy Meter Interface

This module provides an interface for communicating with STMicroelectronics
EVALSTPM34 energy metering evaluation board via UART.

The STPM34 is a dual-channel energy metering ASIC that provides:
- Voltage and current measurement on 2 channels
- Active, reactive, and apparent energy calculation
- RMS voltage and current values
- Power factor calculation
- Frequency measurement
- Temperature measurement

Communication Protocol:
- UART interface (typically 115200 baud)
- 8-bit data frames with specific command structure
- CRC-8 checksum for data integrity
"""

import serial
import time
import struct
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class STPM34Command(Enum):
    """STPM34 UART command codes"""
    # Read commands
    READ_STATUS = 0x48
    READ_CH1_RMS_VOLTAGE = 0x49
    READ_CH1_RMS_CURRENT = 0x4A
    READ_CH1_ACTIVE_POWER = 0x4B
    READ_CH1_REACTIVE_POWER = 0x4C
    READ_CH1_APPARENT_POWER = 0x4D
    READ_CH2_RMS_VOLTAGE = 0x4E
    READ_CH2_RMS_CURRENT = 0x4F
    READ_CH2_ACTIVE_POWER = 0x50
    READ_CH2_REACTIVE_POWER = 0x51
    READ_CH2_APPARENT_POWER = 0x52
    READ_FREQUENCY = 0x53
    READ_TEMPERATURE = 0x54
    READ_ENERGY_CH1 = 0x55
    READ_ENERGY_CH2 = 0x56
    
    # Write/Configuration commands
    RESET = 0x70
    START_MEASUREMENT = 0x71
    STOP_MEASUREMENT = 0x72
    CALIBRATION_MODE = 0x73
    READ_CONFIG = 0x74
    WRITE_CONFIG = 0x75

class STPM34Status(Enum):
    """STPM34 status flags"""
    MEASUREMENT_READY = 0x01
    CALIBRATION_MODE = 0x02
    TEMPERATURE_READY = 0x04
    FREQUENCY_READY = 0x08
    ENERGY_OVERFLOW = 0x10
    COMMUNICATION_ERROR = 0x20

@dataclass
class MeterConfig:
    """Configuration for EVALSTPM34 meter"""
    meter_id: str
    uart_port: str = "/dev/ttyUSB0"
    baud_rate: int = 115200
    timeout: float = 1.0
    name: str = "EVALSTPM34"
    description: str = "EVALSTPM34 Energy Meter"
    # Calibration coefficients (set during factory calibration)
    voltage_calibration_ch1: float = 1.0
    current_calibration_ch1: float = 1.0
    voltage_calibration_ch2: float = 1.0
    current_calibration_ch2: float = 1.0
    # Measurement configuration
    voltage_range_ch1: str = "230V"  # "110V", "230V", "400V"
    voltage_range_ch2: str = "230V"
    current_range_ch1: str = "5A"    # "1A", "5A", "10A", "20A"
    current_range_ch2: str = "5A"

@dataclass
class InstantaneousValues:
    """Container for instantaneous meter readings"""
    timestamp: float
    # Channel 1 measurements
    voltage_ch1: float  # V RMS
    current_ch1: float  # A RMS
    active_power_ch1: float  # W
    reactive_power_ch1: float  # VAR
    apparent_power_ch1: float  # VA
    power_factor_ch1: float  # 0.0 to 1.0
    
    # Channel 2 measurements
    voltage_ch2: float  # V RMS
    current_ch2: float  # A RMS
    active_power_ch2: float  # W
    reactive_power_ch2: float  # VAR
    apparent_power_ch2: float  # VA
    power_factor_ch2: float  # 0.0 to 1.0
    
    # Common measurements
    frequency: float  # Hz
    temperature: Optional[float] = None  # °C

@dataclass
class EnergyValues:
    """Container for energy accumulation readings"""
    timestamp: float
    # Channel 1 energy
    active_energy_ch1: float  # Wh
    reactive_energy_ch1: float  # VARh
    
    # Channel 2 energy
    active_energy_ch2: float  # Wh
    reactive_energy_ch2: float  # VARh

class EVALSTPM34Meter:
    """
    Interface for EVALSTPM34 energy meter evaluation board.
    
    This class provides methods to communicate with the STPM34 energy metering
    ASIC via UART and retrieve power measurements.
    """
    
    def __init__(self, config: MeterConfig):
        """
        Initialize the EVALSTPM34 meter interface.
        
        Args:
            config: Meter configuration parameters
        """
        self.config = config
        self.serial_port: Optional[serial.Serial] = None
        self._lock = threading.Lock()
        self._is_measuring = False
        self._last_error: Optional[str] = None
        
        logger.info(f"Initializing EVALSTPM34 meter {config.meter_id}")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def connect(self) -> bool:
        """
        Establish UART connection to the meter.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.serial_port = serial.Serial(
                port=self.config.uart_port,
                baudrate=self.config.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.config.timeout,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # Clear any pending data
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            
            # Test communication with status read
            status = self._read_status()
            if status is not None:
                logger.info(f"Successfully connected to EVALSTPM34 on {self.config.uart_port}")
                
                # Initialize measurement mode
                self._send_command(STPM34Command.START_MEASUREMENT)
                self._is_measuring = True
                
                return True
            else:
                logger.error("Failed to communicate with EVALSTPM34 after connection")
                self.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to EVALSTPM34: {e}")
            self._last_error = str(e)
            return False

    def disconnect(self):
        """Close UART connection"""
        if self.serial_port and self.serial_port.is_open:
            try:
                # Stop measurements before disconnecting
                if self._is_measuring:
                    self._send_command(STPM34Command.STOP_MEASUREMENT)
                    self._is_measuring = False
                
                self.serial_port.close()
                logger.info("Disconnected from EVALSTPM34")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
        
        self.serial_port = None

    def is_connected(self) -> bool:
        """Check if meter is connected and responsive"""
        if not self.serial_port or not self.serial_port.is_open:
            return False
        
        try:
            status = self._read_status()
            return status is not None
        except:
            return False

    def get_meter_info(self) -> Dict[str, Any]:
        """
        Get meter information and configuration.
        
        Returns:
            Dictionary containing meter information
        """
        return {
            "meter_id": self.config.meter_id,
            "name": self.config.name,
            "description": self.config.description,
            "uart_port": self.config.uart_port,
            "baud_rate": self.config.baud_rate,
            "connected": self.is_connected(),
            "measuring": self._is_measuring,
            "voltage_range_ch1": self.config.voltage_range_ch1,
            "voltage_range_ch2": self.config.voltage_range_ch2,
            "current_range_ch1": self.config.current_range_ch1,
            "current_range_ch2": self.config.current_range_ch2,
            "last_error": self._last_error
        }

    def read_instantaneous_values(self) -> InstantaneousValues:
        """
        Read all instantaneous power measurements.
        
        Returns:
            InstantaneousValues object with current measurements
            
        Raises:
            RuntimeError: If meter is not connected or communication fails
        """
        if not self.is_connected():
            raise RuntimeError("Meter not connected")
        
        with self._lock:
            try:
                timestamp = time.time()
                
                # Read Channel 1 measurements
                voltage_ch1 = self._read_voltage(channel=1)
                current_ch1 = self._read_current(channel=1)
                active_power_ch1 = self._read_active_power(channel=1)
                reactive_power_ch1 = self._read_reactive_power(channel=1)
                apparent_power_ch1 = self._read_apparent_power(channel=1)
                
                # Calculate power factor for CH1
                if apparent_power_ch1 > 0:
                    power_factor_ch1 = abs(active_power_ch1) / apparent_power_ch1
                else:
                    power_factor_ch1 = 0.0
                
                # Read Channel 2 measurements
                voltage_ch2 = self._read_voltage(channel=2)
                current_ch2 = self._read_current(channel=2)
                active_power_ch2 = self._read_active_power(channel=2)
                reactive_power_ch2 = self._read_reactive_power(channel=2)
                apparent_power_ch2 = self._read_apparent_power(channel=2)
                
                # Calculate power factor for CH2
                if apparent_power_ch2 > 0:
                    power_factor_ch2 = abs(active_power_ch2) / apparent_power_ch2
                else:
                    power_factor_ch2 = 0.0
                
                # Read common measurements
                frequency = self._read_frequency()
                temperature = self._read_temperature()
                
                return InstantaneousValues(
                    timestamp=timestamp,
                    voltage_ch1=voltage_ch1,
                    current_ch1=current_ch1,
                    active_power_ch1=active_power_ch1,
                    reactive_power_ch1=reactive_power_ch1,
                    apparent_power_ch1=apparent_power_ch1,
                    power_factor_ch1=power_factor_ch1,
                    voltage_ch2=voltage_ch2,
                    current_ch2=current_ch2,
                    active_power_ch2=active_power_ch2,
                    reactive_power_ch2=reactive_power_ch2,
                    apparent_power_ch2=apparent_power_ch2,
                    power_factor_ch2=power_factor_ch2,
                    frequency=frequency,
                    temperature=temperature
                )
                
            except Exception as e:
                logger.error(f"Failed to read instantaneous values: {e}")
                self._last_error = str(e)
                raise RuntimeError(f"Failed to read meter values: {e}")

    def read_energy_values(self) -> EnergyValues:
        """
        Read accumulated energy values.
        
        Returns:
            EnergyValues object with energy accumulations
            
        Raises:
            RuntimeError: If meter is not connected or communication fails
        """
        if not self.is_connected():
            raise RuntimeError("Meter not connected")
        
        with self._lock:
            try:
                timestamp = time.time()
                
                # Read energy accumulations
                active_energy_ch1, reactive_energy_ch1 = self._read_energy(channel=1)
                active_energy_ch2, reactive_energy_ch2 = self._read_energy(channel=2)
                
                return EnergyValues(
                    timestamp=timestamp,
                    active_energy_ch1=active_energy_ch1,
                    reactive_energy_ch1=reactive_energy_ch1,
                    active_energy_ch2=active_energy_ch2,
                    reactive_energy_ch2=reactive_energy_ch2
                )
                
            except Exception as e:
                logger.error(f"Failed to read energy values: {e}")
                self._last_error = str(e)
                raise RuntimeError(f"Failed to read energy values: {e}")

    def reset_energy_counters(self) -> bool:
        """
        Reset energy accumulation counters.
        
        Returns:
            True if reset successful, False otherwise
        """
        try:
            with self._lock:
                # Send reset command
                response = self._send_command(STPM34Command.RESET)
                if response:
                    # Restart measurements
                    time.sleep(0.1)  # Allow reset to complete
                    self._send_command(STPM34Command.START_MEASUREMENT)
                    logger.info("Energy counters reset successfully")
                    return True
                else:
                    logger.error("Failed to reset energy counters")
                    return False
        except Exception as e:
            logger.error(f"Error resetting energy counters: {e}")
            self._last_error = str(e)
            return False

    # Private methods for UART communication

    def _send_command(self, command: STPM34Command, data: bytes = b'') -> Optional[bytes]:
        """
        Send command to STPM34 and receive response.
        
        Args:
            command: Command to send
            data: Optional data payload
            
        Returns:
            Response data or None if failed
        """
        if not self.serial_port or not self.serial_port.is_open:
            return None
        
        try:
            # Build command frame: [STX][CMD][LEN][DATA][CRC][ETX]
            stx = 0x02  # Start of text
            etx = 0x03  # End of text
            cmd = command.value
            length = len(data)
            
            # Calculate CRC-8 for command and data
            crc_data = bytes([cmd, length]) + data
            crc = self._calculate_crc8(crc_data)
            
            # Build complete frame
            frame = bytes([stx, cmd, length]) + data + bytes([crc, etx])
            
            # Send command
            self.serial_port.write(frame)
            self.serial_port.flush()
            
            # Read response
            response = self._read_response()
            return response
            
        except Exception as e:
            logger.error(f"Command send failed: {e}")
            return None

    def _read_response(self) -> Optional[bytes]:
        """
        Read response from STPM34.
        
        Returns:
            Response data or None if failed
        """
        try:
            # Wait for STX
            stx = self.serial_port.read(1)
            if not stx or stx[0] != 0x02:
                return None
            
            # Read status byte
            status = self.serial_port.read(1)
            if not status:
                return None
            
            # Read length
            length_byte = self.serial_port.read(1)
            if not length_byte:
                return None
            
            length = length_byte[0]
            
            # Read data
            data = b''
            if length > 0:
                data = self.serial_port.read(length)
                if len(data) != length:
                    return None
            
            # Read CRC and ETX
            crc_etx = self.serial_port.read(2)
            if len(crc_etx) != 2:
                return None
            
            crc_received = crc_etx[0]
            etx = crc_etx[1]
            
            if etx != 0x03:
                return None
            
            # Verify CRC
            crc_data = status + length_byte + data
            crc_calculated = self._calculate_crc8(crc_data)
            
            if crc_received != crc_calculated:
                logger.warning("CRC mismatch in response")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Response read failed: {e}")
            return None

    def _calculate_crc8(self, data: bytes) -> int:
        """
        Calculate CRC-8 checksum.
        
        Args:
            data: Data to calculate CRC for
            
        Returns:
            CRC-8 value
        """
        crc = 0x00
        polynomial = 0x07  # CRC-8-CCITT polynomial
        
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc <<= 1
                crc &= 0xFF
        
        return crc

    def _read_status(self) -> Optional[int]:
        """Read meter status"""
        response = self._send_command(STPM34Command.READ_STATUS)
        if response and len(response) >= 1:
            return response[0]
        return None

    def _read_voltage(self, channel: int) -> float:
        """Read RMS voltage for specified channel"""
        if channel == 1:
            command = STPM34Command.READ_CH1_RMS_VOLTAGE
            cal_factor = self.config.voltage_calibration_ch1
        else:
            command = STPM34Command.READ_CH2_RMS_VOLTAGE
            cal_factor = self.config.voltage_calibration_ch2
        
        response = self._send_command(command)
        if response and len(response) >= 4:
            # Convert 32-bit response to float voltage
            raw_value = struct.unpack('<I', response[:4])[0]
            voltage = (raw_value / 65536.0) * 400.0 * cal_factor  # Scale to voltage range
            return round(voltage, 2)
        return 0.0

    def _read_current(self, channel: int) -> float:
        """Read RMS current for specified channel"""
        if channel == 1:
            command = STPM34Command.READ_CH1_RMS_CURRENT
            cal_factor = self.config.current_calibration_ch1
        else:
            command = STPM34Command.READ_CH2_RMS_CURRENT
            cal_factor = self.config.current_calibration_ch2
        
        response = self._send_command(command)
        if response and len(response) >= 4:
            # Convert 32-bit response to float current
            raw_value = struct.unpack('<I', response[:4])[0]
            current = (raw_value / 65536.0) * 20.0 * cal_factor  # Scale to current range
            return round(current, 3)
        return 0.0

    def _read_active_power(self, channel: int) -> float:
        """Read active power for specified channel"""
        if channel == 1:
            command = STPM34Command.READ_CH1_ACTIVE_POWER
        else:
            command = STPM34Command.READ_CH2_ACTIVE_POWER
        
        response = self._send_command(command)
        if response and len(response) >= 4:
            # Convert 32-bit signed response to float power
            raw_value = struct.unpack('<i', response[:4])[0]  # Signed integer
            power = raw_value / 1000.0  # Convert to watts
            return round(power, 1)
        return 0.0

    def _read_reactive_power(self, channel: int) -> float:
        """Read reactive power for specified channel"""
        if channel == 1:
            command = STPM34Command.READ_CH1_REACTIVE_POWER
        else:
            command = STPM34Command.READ_CH2_REACTIVE_POWER
        
        response = self._send_command(command)
        if response and len(response) >= 4:
            # Convert 32-bit signed response to float power
            raw_value = struct.unpack('<i', response[:4])[0]  # Signed integer
            power = raw_value / 1000.0  # Convert to VAR
            return round(power, 1)
        return 0.0

    def _read_apparent_power(self, channel: int) -> float:
        """Read apparent power for specified channel"""
        if channel == 1:
            command = STPM34Command.READ_CH1_APPARENT_POWER
        else:
            command = STPM34Command.READ_CH2_APPARENT_POWER
        
        response = self._send_command(command)
        if response and len(response) >= 4:
            # Convert 32-bit response to float power
            raw_value = struct.unpack('<I', response[:4])[0]
            power = raw_value / 1000.0  # Convert to VA
            return round(power, 1)
        return 0.0

    def _read_frequency(self) -> float:
        """Read line frequency"""
        response = self._send_command(STPM34Command.READ_FREQUENCY)
        if response and len(response) >= 4:
            # Convert 32-bit response to frequency
            raw_value = struct.unpack('<I', response[:4])[0]
            frequency = raw_value / 1000.0  # Convert to Hz
            return round(frequency, 2)
        return 50.0  # Default frequency

    def _read_temperature(self) -> Optional[float]:
        """Read internal temperature"""
        response = self._send_command(STPM34Command.READ_TEMPERATURE)
        if response and len(response) >= 2:
            # Convert 16-bit response to temperature
            raw_value = struct.unpack('<H', response[:2])[0]
            # Temperature conversion formula from datasheet
            temperature = (raw_value - 1708) / 5.336  # Convert to Celsius
            return round(temperature, 1)
        return None

    def _read_energy(self, channel: int) -> Tuple[float, float]:
        """Read energy accumulation for specified channel"""
        if channel == 1:
            command = STPM34Command.READ_ENERGY_CH1
        else:
            command = STPM34Command.READ_ENERGY_CH2
        
        response = self._send_command(command)
        if response and len(response) >= 8:
            # Response contains active and reactive energy (32-bit each)
            active_raw = struct.unpack('<I', response[:4])[0]
            reactive_raw = struct.unpack('<I', response[4:8])[0]
            
            # Convert to Wh and VARh
            active_energy = active_raw / 1000.0
            reactive_energy = reactive_raw / 1000.0
            
            return round(active_energy, 2), round(reactive_energy, 2)
        
        return 0.0, 0.0

    def start_measurements(self) -> bool:
        """Start continuous measurements"""
        try:
            response = self._send_command(STPM34Command.START_MEASUREMENT)
            if response is not None:
                self._is_measuring = True
                logger.info("Measurements started")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to start measurements: {e}")
            return False

    def stop_measurements(self) -> bool:
        """Stop measurements"""
        try:
            response = self._send_command(STPM34Command.STOP_MEASUREMENT)
            if response is not None:
                self._is_measuring = False
                logger.info("Measurements stopped")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to stop measurements: {e}")
            return False

    def get_last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self._last_error

    def clear_last_error(self):
        """Clear the last error message"""
        self._last_error = None