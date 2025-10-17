# Hardware Interfaces for Physical VEN Implementation

This package provides hardware interface modules for implementing physical Virtual End Node (VEN) demand response systems. It includes drivers for power measurement and load control hardware commonly used in grid-interactive applications.

## Overview

The hardware interfaces support two main categories of devices:
1. **Load Control**: GPIO-based relay controllers for switching electrical loads
2. **Power Measurement**: Energy meters for monitoring power consumption and generation

## Module Structure

Both hardware interfaces are implemented as single-file modules for consistency and ease of use:

- **`gpio_relay_controller.py`** - Complete GPIO relay control implementation
- **`evalstpm34_meter.py`** - Complete EVALSTPM34 energy meter implementation

## Modules

### GPIO Relay Controller (`gpio_relay_controller.py`)

Controls electrical relays via Raspberry Pi GPIO pins for load shedding and switching operations.

**Features:**
- Multiple relay control with individual configuration
- Thread-safe operations with proper resource management
- Context manager support for automatic cleanup
- Comprehensive error handling with custom exceptions
- Emergency safety functions

**Hardware Requirements:**
- Raspberry Pi (any model with GPIO)
- Relay modules (5V or 3.3V logic compatible)  
- Proper electrical isolation and safety measures
- RPi.GPIO Python library (`pip install RPi.GPIO`)

### EVALSTPM34 Energy Meter (`evalstpm34_meter.py`)

Interface for STMicroelectronics EVALSTPM34 energy metering evaluation board via UART.

**Features:**
- Dual-channel power measurement (voltage, current, power, energy)
- Real-time monitoring of electrical parameters
- Energy accumulation with reset capability
- Temperature and frequency measurement
- CRC-protected UART communication
- Configurable measurement ranges and calibration

**Hardware Requirements:**
- EVALSTPM34 evaluation board
- UART connection (USB-to-Serial adapter or built-in UART)
- Proper current and voltage sensor connections
- pyserial Python library (`pip install pyserial`)

## Quick Start

### Basic Relay Control

```python
from hardware_interfaces import GPIORelayController, RelayConfig, RelayState

# Configure relays
relays = [
    RelayConfig("load1", gpio_pin=18, name="Main Load"),
    RelayConfig("load2", gpio_pin=19, name="Secondary Load")
]

# Use relay controller
with GPIORelayController(relays) as controller:
    # Turn off a load
    controller.turn_off_relay("load1")
    
    # Set multiple relays
    controller.set_multiple_relays({
        "load1": RelayState.OPEN,
        "load2": RelayState.CLOSED
    })
    
    # Get current states
    states = controller.get_all_relay_states()
    print(f"Current states: {states}")
```

### Basic Power Measurement

```python
from hardware_interfaces import EVALSTPM34Meter, MeterConfig

# Configure meter
config = MeterConfig(
    meter_id="main_meter",
    uart_port="/dev/ttyUSB0",
    baud_rate=9600,  # STPM34 default baud rate
    voltage_range_ch1="230V",
    current_range_ch1="5A"
)

# Read power measurements
with EVALSTPM34Meter(config) as meter:
    # Get instantaneous values
    reading = meter.read_instantaneous_values()
    print(f"Power: {reading.active_power_ch1:.1f}W")
    print(f"Voltage: {reading.voltage_ch1:.1f}V")
    print(f"Current: {reading.current_ch1:.2f}A")
    
    # Get energy accumulations
    energy = meter.read_energy_values()
    print(f"Energy consumed: {energy.active_energy_ch1:.2f}Wh")
```

### Integrated Demand Response

```python
from hardware_interfaces import GPIORelayController, EVALSTPM34Meter
from hardware_interfaces.gpio_relay_controller import RelayConfig, RelayState
from hardware_interfaces.evalstpm34_meter import MeterConfig

# Setup configurations
relay_config = [RelayConfig("load1", gpio_pin=18, name="Controllable Load")]
meter_config = MeterConfig("meter1", uart_port="/dev/ttyUSB0")

# Implement demand response logic
with GPIORelayController(relay_config) as relays, \
     EVALSTPM34Meter(meter_config) as meter:
    
    # Monitor power consumption
    baseline = meter.read_instantaneous_values()
    baseline_power = baseline.active_power_ch1
    
    # Check if demand response is needed
    if baseline_power > 1500:  # 1.5kW threshold
        print("High power consumption detected - shedding load")
        relays.turn_off_relay("load1")
        
        # Verify load reduction
        time.sleep(2)
        reduced = meter.read_instantaneous_values()
        reduction = baseline_power - reduced.active_power_ch1
        print(f"Load reduced by {reduction:.1f}W")
```

## EVALSTPM34 Meter Details

### Communication Protocol

The EVALSTPM34 uses UART communication with the following frame structure:
- **Frame Format**: `[READ_ADDR][WRITE_ADDR][DATA_LSB][DATA_MSB][CRC]`
- **Baud Rate**: 9600 (default, configurable)
- **Data Bits**: 8
- **Parity**: None
- **Stop Bits**: 1
- **CRC**: CRC-8 with polynomial 0x07, byte-reversed for UART
- **Protocol**: Two-transaction sequence (set pointer, then read data)

### Measurement Capabilities

**Channel 1 & 2 (Dual Channel)**:
- RMS Voltage (V)
- RMS Current (A) 
- Active Power (W)
- Reactive Power (VAR)
- Apparent Power (VA)
- Power Factor

**Common Measurements**:
- Line Frequency (Hz)
- Internal Temperature (°C)
- Energy Accumulation (Wh, VARh)

### Configuration Options

```python
config = MeterConfig(
    meter_id="meter_001",
    uart_port="/dev/ttyUSB0",
    baud_rate=9600,  # STPM34 default
    timeout=1.0,
    
    # Calibration factors (set during installation)
    voltage_calibration_ch1=1.0,
    current_calibration_ch1=1.0,
    voltage_calibration_ch2=1.0, 
    current_calibration_ch2=1.0,
    
    # Measurement ranges
    voltage_range_ch1="230V",  # "110V", "230V", "400V"
    current_range_ch1="5A",    # "1A", "5A", "10A", "20A"
    voltage_range_ch2="230V",
    current_range_ch2="5A"
)
```

### Error Handling

Both interfaces provide comprehensive error handling:
- Connection monitoring and automatic recovery
- CRC verification for meter communications
- Thread-safe operations with proper locking
- Detailed logging for debugging

## Installation Requirements

```bash
# For GPIO control on Raspberry Pi
pip install RPi.GPIO

# For UART communication
pip install pyserial

# Standard requirements
pip install dataclasses typing
```

## Hardware Setup

### GPIO Relays
1. Connect relay modules to Raspberry Pi GPIO pins
2. Ensure proper voltage levels (3.3V or 5V logic)
3. Use optical isolation for high-voltage switching
4. Follow electrical safety guidelines

### EVALSTPM34 Meter
1. Connect EVALSTPM34 board to system via USB-UART adapter
2. Configure current transformers and voltage dividers
3. Set appropriate measurement ranges in software
4. Perform calibration for accurate measurements

## Safety Considerations

⚠️ **ELECTRICAL SAFETY WARNING**
- Always follow electrical safety codes and regulations
- Use proper isolation and protection devices
- Ensure qualified personnel perform electrical connections
- Test all safety systems before deployment
- Consider fail-safe operation modes for critical systems

## Integration with VEN Agent

These hardware interfaces are designed to integrate with the VOLTTRON VEN agent:

```python
# In ven_agent.py, add hardware interface support
from hardware_interfaces import GPIORelayController, EVALSTPM34Meter

class PhysicalVEN:
    def __init__(self):
        self.relays = GPIORelayController(relay_configs)
        self.meter = EVALSTPM34Meter(meter_config)
    
    def shed_load(self, load_id: str, amount_kw: float):
        """Implement actual load shedding"""
        self.relays.turn_off_relay(load_id)
    
    def get_power_measurement(self) -> float:
        """Get real power measurement"""
        reading = self.meter.read_instantaneous_values()
        return reading.active_power_ch1 + reading.active_power_ch2
```

## Testing Hardware Interfaces

### Test Scripts

A comprehensive test script is provided for validating EVALSTPM34 meter functionality:

```bash
# Run the high-level driver test with continuous monitoring
python3 test_evalstpm34_real.py
```

**Test Script Features:**
- High-level driver communication validation
- Continuous data polling with real-time display  
- Formatted output showing all measurement parameters
- Connection status monitoring
- Graceful shutdown with Ctrl+C

**Expected Output (USB-only connection):**
```
EVALSTPM34 Energy Meter - Live Data (Sample #1)
Timestamp: 2025-10-17 20:15:22
======================================================================
Parameter            Channel 1       Channel 2       Unit      
----------------------------------------------------------------------
Voltage RMS          3.55            3.55            V         
Current RMS          2.374           1.583           A         
Active Power         -0.0            -0.0            W         
Reactive Power       -0.0            -0.0            VAR       
Apparent Power       8.4             5.6             VA        
Power Factor         0.000           0.000                     
```

**Note**: Small voltage and current readings are normal when only USB is connected. Real measurements appear when AC voltage and current inputs are properly connected.

### Validation Checklist

**EVALSTPM34 Meter**:
- [ ] UART communication established (✓ connection message)
- [ ] Consistent measurement readings (non-zero, stable values)
- [ ] Realistic voltage/current ranges for your setup
- [ ] Proper scaling and unit conversions
- [ ] Error-free continuous operation

**GPIO Relay Controller**:
- [ ] Individual relay control working
- [ ] Multiple relay operations
- [ ] Emergency shutdown functions
- [ ] State reporting accuracy
- [ ] Thread-safe operations

## Troubleshooting

### GPIO Issues
- Check that script runs with sufficient privileges (`sudo`)
- Verify GPIO pin assignments don't conflict
- Test individual pins with simple blink programs

### UART/Meter Issues
- Verify UART device path (`/dev/ttyUSB0`, `/dev/ttyAMA0`, etc.)
- Check baud rate and communication parameters
- Test basic serial communication with terminal programs
- Ensure proper hardware connections and power supply

### Performance Optimization
- Use appropriate polling intervals for measurements
- Implement caching for frequently accessed values
- Consider separate threads for continuous monitoring

## License

This hardware interface package is part of the Grid Services Infrastructure project and follows the same licensing terms.