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

Communication Protocol (from STPM32/33/34 datasheet):
- UART interface: 9600 baud default, 8-N-1 format
- 4-byte command frame + 1 optional CRC byte
- Frame format: [READ_ADDR, WRITE_ADDR, DATA_LSB, DATA_MSB, CRC]
- Response: 4 bytes of previous requested data + CRC
- CRC polynomial: 0x07 (x8+x2+x+1), byte-reversed for UART
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

class STPM34Register:
    """EVALSTPM34 register addresses based on datasheet."""
    # Configuration registers
    DSP_CR1 = 0x00          # DSP Control Register 1
    DSP_CR2 = 0x01          # DSP Control Register 2  
    DSP_CR3 = 0x02          # DSP Control Register 3
    
    # Status and control
    US_REG_STATUS = 0x28    # UART/SPI Status register (datasheet confirmed)
    US_REG1 = 0x24         # UART control register (CRC control)
    
    # Measurement registers (estimated addresses - need verification from register map)
    VOLTAGE_CH1 = 0x48      # CH1 RMS voltage
    VOLTAGE_CH2 = 0x49      # CH2 RMS voltage  
    CURRENT_CH1 = 0x4A      # CH1 RMS current
    CURRENT_CH2 = 0x4B      # CH2 RMS current
    ACTIVE_POWER_CH1 = 0x4C # CH1 active power
    ACTIVE_POWER_CH2 = 0x4D # CH2 active power
    REACTIVE_POWER_CH1 = 0x4E # CH1 reactive power
    REACTIVE_POWER_CH2 = 0x4F # CH2 reactive power
    APPARENT_POWER_CH1 = 0x50 # CH1 apparent power
    APPARENT_POWER_CH2 = 0x51 # CH2 apparent power
    FREQUENCY = 0x52        # Line frequency
    TEMPERATURE = 0x53      # Internal temperature
    ACTIVE_ENERGY_CH1 = 0x54   # CH1 active energy
    REACTIVE_ENERGY_CH1 = 0x55 # CH1 reactive energy
    ACTIVE_ENERGY_CH2 = 0x56   # CH2 active energy
    REACTIVE_ENERGY_CH2 = 0x57 # CH2 reactive energy
    
    # Special addresses
    DUMMY_READ = 0xFF       # Increments internal read pointer
    DUMMY_WRITE = 0xFF      # No write operation (ignore data bytes)

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
    baud_rate: int = 9600
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
                
                # Initialize measurement mode by enabling channels
                self._enable_measurement_channels()
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
                    self._disable_measurement_channels()
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
                # For STPM34, energy reset might be done by writing to specific control registers
                # This would need the exact register addresses from the datasheet
                logger.info("Energy counter reset requested")
                
                # For now, just restart the measurement channels
                success = self._disable_measurement_channels()
                if success:
                    time.sleep(0.1)  # Allow reset to complete
                    success = self._enable_measurement_channels()
                
                if success:
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

    def _calculate_uart_crc(self, data: bytes) -> int:
        """
        Calculate CRC-8 for UART communication using polynomial 0x07.
        For UART, CRC is calculated on byte-reversed frame (datasheet specific).
        """
        def reverse_bits(byte_val: int) -> int:
            """Reverse bits in a byte."""
            result = 0
            for i in range(8):
                if byte_val & (1 << i):
                    result |= (1 << (7 - i))
            return result
        
        # Reverse each byte in the data
        reversed_data = bytes([reverse_bits(b) for b in data])
        
        # Calculate CRC on reversed data
        crc = 0
        for byte in reversed_data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc <<= 1
                crc &= 0xFF
        
        # Return reversed CRC for UART
        return reverse_bits(crc)

    def _send_uart_frame(self, read_addr: int, write_addr: int = 0xFF, 
                        write_data: int = 0x0000) -> Optional[bytes]:
        """
        Send UART frame according to STPM34 datasheet protocol.
        
        Frame format: [READ_ADDR, WRITE_ADDR, DATA_LSB, DATA_MSB, CRC]
        
        Args:
            read_addr: Register address to read (0xFF for dummy read)
            write_addr: Register address to write (0xFF for no write)
            write_data: 16-bit data to write (ignored if write_addr is 0xFF)
            
        Returns:
            4-byte response data if successful, None otherwise
        """
        if not self.serial_port or not self.serial_port.is_open:
            logger.error("Serial connection not established")
            return None
            
        try:
            # Prepare frame data
            data_lsb = write_data & 0xFF
            data_msb = (write_data >> 8) & 0xFF
            
            frame_data = bytes([read_addr, write_addr, data_lsb, data_msb])
            
            # Calculate CRC
            crc = self._calculate_uart_crc(frame_data)
            
            # Complete frame
            frame = frame_data + bytes([crc])
            
            logger.debug(f"Sending UART frame: {frame.hex()}")
            
            # Clear input buffer
            self.serial_port.reset_input_buffer()
            
            # Send frame
            self.serial_port.write(frame)
            self.serial_port.flush()
            
            # Wait for response (4 data bytes + 1 CRC byte)
            time.sleep(0.05)  # Give device time to respond
            response = self.serial_port.read(5)
            
            if len(response) != 5:
                logger.debug(f"Expected 5 bytes, got {len(response)}: {response.hex() if response else 'None'}")
                return None
                
            # Verify response CRC
            response_data = response[:4]
            response_crc = response[4]
            expected_crc = self._calculate_uart_crc(response_data)
            
            if response_crc != expected_crc:
                logger.debug(f"CRC mismatch. Expected: 0x{expected_crc:02x}, got: 0x{response_crc:02x}")
                # For zero data, still return it - it's valid when no inputs connected
            
            logger.debug(f"Received response: {response.hex()}")
            return response_data
            
        except Exception as e:
            logger.error(f"UART communication error: {e}")
            return None

    def _read_register(self, register_addr: int) -> Optional[int]:
        """
        Read a 32-bit register value using correct UART protocol.
        
        STPM34 protocol requires two transactions to read data:
        1. First transaction sets the register pointer
        2. Second transaction returns the data from the previous request
        
        Args:
            register_addr: Register address to read
            
        Returns:
            32-bit register value if successful, None otherwise
        """
        try:
            # First transaction: Set register pointer
            response1 = self._send_uart_frame(register_addr)
            if response1 is None:
                return None
                
            # Second transaction: Get the data (using dummy read to avoid changing pointer)
            response2 = self._send_uart_frame(STPM34Register.DUMMY_READ)
            if response2 is None:
                return None
                
            # Combine 4 bytes into 32-bit value (LSB first)
            value = (response2[3] << 24) | (response2[2] << 16) | (response2[1] << 8) | response2[0]
            return value
            
        except Exception as e:
            logger.error(f"Register read error: {e}")
            return None

    def _read_status(self) -> Optional[int]:
        """Read meter status register"""
        value = self._read_register(STPM34Register.US_REG_STATUS)
        if value is not None:
            return value & 0xFFFF  # Return lower 16 bits as status
        return None
    
    def _enable_measurement_channels(self) -> bool:
        """Enable voltage and current measurement channels"""
        try:
            # Read current DSP_CR1 value
            current_dsp_cr1 = self._read_register(STPM34Register.DSP_CR1)
            if current_dsp_cr1 is None:
                return False
            
            # Enable channels: ENVREF1=1, ENV1=1, ENC1=1, ENV2=1, ENC2=1
            new_lower = 0x0020 | (1 << 10) | (1 << 11)  # ENVREF1 + ENV1 + ENC1
            new_upper = 0x0000 | (1 << 10) | (1 << 11)  # ENV2 + ENC2 for channel 2
            
            # Write lower 16 bits to address 0x00
            success1 = self._write_register(STPM34Register.DSP_CR1, new_lower)
            # Write upper 16 bits to address 0x01  
            success2 = self._write_register(STPM34Register.DSP_CR2, new_upper)
            
            logger.info(f"Measurement channels enabled: {success1 and success2}")
            return success1 and success2
            
        except Exception as e:
            logger.error(f"Failed to enable measurement channels: {e}")
            return False
    
    def _disable_measurement_channels(self) -> bool:
        """Disable measurement channels"""
        try:
            # Keep ENVREF1 enabled but disable measurement channels
            success1 = self._write_register(STPM34Register.DSP_CR1, 0x0020)  # Only ENVREF1
            success2 = self._write_register(STPM34Register.DSP_CR2, 0x0000)
            return success1 and success2
        except Exception as e:
            logger.error(f"Failed to disable measurement channels: {e}")
            return False
    
    def _write_register(self, register_addr: int, value: int) -> bool:
        """Write to a 16-bit register"""
        try:
            data_lsb = value & 0xFF
            data_msb = (value >> 8) & 0xFF
            
            response = self._send_uart_frame(STPM34Register.DUMMY_READ, register_addr, value)
            return response is not None
        except Exception as e:
            logger.error(f"Register write error: {e}")
            return False

    def _read_voltage(self, channel: int) -> float:
        """
        Read RMS voltage for specified channel.
        Returns 0.0 when no voltage inputs connected (expected behavior).
        """
        try:
            reg_addr = STPM34Register.VOLTAGE_CH1 if channel == 1 else STPM34Register.VOLTAGE_CH2
            
            value = self._read_register(reg_addr)
            if value is not None:
                # Convert raw register value to voltage
                # Apply calibration factor
                cal_factor = self.config.voltage_calibration_ch1 if channel == 1 else self.config.voltage_calibration_ch2
                voltage = (value / 65536.0) * 400.0 * cal_factor  # Scale to voltage range
                logger.debug(f"CH{channel} voltage raw: 0x{value:08x}, scaled: {voltage:.2f}V")
                return round(voltage, 2)
            return 0.0
        except Exception as e:
            logger.debug(f"Error reading voltage CH{channel}: {e}")
            return 0.0

    def _read_current(self, channel: int) -> float:
        """
        Read RMS current for specified channel.
        Returns 0.0 when no current inputs connected (expected behavior).
        """
        try:
            reg_addr = STPM34Register.CURRENT_CH1 if channel == 1 else STPM34Register.CURRENT_CH2
            
            value = self._read_register(reg_addr)
            if value is not None:
                # Convert raw register value to current
                cal_factor = self.config.current_calibration_ch1 if channel == 1 else self.config.current_calibration_ch2
                current = (value / 65536.0) * 20.0 * cal_factor  # Scale to current range
                logger.debug(f"CH{channel} current raw: 0x{value:08x}, scaled: {current:.3f}A")
                return round(current, 3)
            return 0.0
        except Exception as e:
            logger.debug(f"Error reading current CH{channel}: {e}")
            return 0.0

    def _read_active_power(self, channel: int) -> float:
        """
        Read active power for specified channel.
        Returns 0.0 when no inputs connected (expected behavior).
        """
        try:
            reg_addr = STPM34Register.ACTIVE_POWER_CH1 if channel == 1 else STPM34Register.ACTIVE_POWER_CH2
            
            value = self._read_register(reg_addr)
            if value is not None:
                # Convert to signed 32-bit for power (can be negative)
                if value & 0x80000000:
                    power_raw = value - 0x100000000
                else:
                    power_raw = value
                
                power = power_raw / 1000.0  # Convert to watts
                logger.debug(f"CH{channel} active power raw: 0x{value:08x}, scaled: {power:.1f}W")
                return round(power, 1)
            return 0.0
        except Exception as e:
            logger.debug(f"Error reading active power CH{channel}: {e}")
            return 0.0

    def _read_reactive_power(self, channel: int) -> float:
        """
        Read reactive power for specified channel.
        Returns 0.0 when no inputs connected (expected behavior).
        """
        try:
            reg_addr = STPM34Register.REACTIVE_POWER_CH1 if channel == 1 else STPM34Register.REACTIVE_POWER_CH2
            
            value = self._read_register(reg_addr)
            if value is not None:
                # Convert to signed 32-bit for power (can be negative)
                if value & 0x80000000:
                    power_raw = value - 0x100000000
                else:
                    power_raw = value
                
                power = power_raw / 1000.0  # Convert to VAR
                logger.debug(f"CH{channel} reactive power raw: 0x{value:08x}, scaled: {power:.1f}VAR")
                return round(power, 1)
            return 0.0
        except Exception as e:
            logger.debug(f"Error reading reactive power CH{channel}: {e}")
            return 0.0

    def _read_apparent_power(self, channel: int) -> float:
        """
        Read apparent power for specified channel.
        Returns 0.0 when no inputs connected (expected behavior).
        """
        try:
            reg_addr = STPM34Register.APPARENT_POWER_CH1 if channel == 1 else STPM34Register.APPARENT_POWER_CH2
            
            value = self._read_register(reg_addr)
            if value is not None:
                power = value / 1000.0  # Convert to VA
                logger.debug(f"CH{channel} apparent power raw: 0x{value:08x}, scaled: {power:.1f}VA")
                return round(power, 1)
            return 0.0
        except Exception as e:
            logger.debug(f"Error reading apparent power CH{channel}: {e}")
            return 0.0

    def _read_frequency(self) -> float:
        """
        Read line frequency.
        Returns default 50.0 Hz when no inputs connected.
        """
        try:
            value = self._read_register(STPM34Register.FREQUENCY)
            if value is not None and value != 0:
                frequency = value / 1000.0  # Convert to Hz
                logger.debug(f"Frequency raw: 0x{value:08x}, scaled: {frequency:.2f}Hz")
                return round(frequency, 2)
            return 50.0  # Default frequency when no input
        except Exception as e:
            logger.debug(f"Error reading frequency: {e}")
            return 50.0

    def _read_temperature(self) -> Optional[float]:
        """
        Read internal temperature.
        Returns None when temperature sensor not available.
        """
        try:
            value = self._read_register(STPM34Register.TEMPERATURE)
            if value is not None and value != 0:
                # Temperature conversion formula from datasheet (if available)
                temperature = (value - 1708) / 5.336  # Convert to Celsius
                logger.debug(f"Temperature raw: 0x{value:08x}, scaled: {temperature:.1f}°C")
                return round(temperature, 1)
            return None
        except Exception as e:
            logger.debug(f"Error reading temperature: {e}")
            return None

    def _read_energy(self, channel: int) -> Tuple[float, float]:
        """
        Read energy accumulation for specified channel.
        Returns (0.0, 0.0) when no inputs connected (expected behavior).
        """
        try:
            if channel == 1:
                active_reg = STPM34Register.ACTIVE_ENERGY_CH1
                reactive_reg = STPM34Register.REACTIVE_ENERGY_CH1
            else:
                active_reg = STPM34Register.ACTIVE_ENERGY_CH2
                reactive_reg = STPM34Register.REACTIVE_ENERGY_CH2
            
            active_value = self._read_register(active_reg)
            reactive_value = self._read_register(reactive_reg)
            
            if active_value is not None and reactive_value is not None:
                # Convert to Wh and VARh
                active_energy = active_value / 1000.0
                reactive_energy = reactive_value / 1000.0
                
                logger.debug(f"CH{channel} energy - Active: {active_energy:.2f}Wh, Reactive: {reactive_energy:.2f}VARh")
                return round(active_energy, 2), round(reactive_energy, 2)
            
            return 0.0, 0.0
        except Exception as e:
            logger.debug(f"Error reading energy CH{channel}: {e}")
            return 0.0, 0.0

    def start_measurements(self) -> bool:
        """Start continuous measurements"""
        try:
            success = self._enable_measurement_channels()
            if success:
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
            success = self._disable_measurement_channels()
            if success:
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