# Hardware Interfaces

This directory contains Python modules for interfacing with physical hardware components used in the VEN (Virtual End Node) implementation.

## Modules

### 1. GPIO Relay Controller (`gpio_relay_controller/`)

Controls normally closed (NC) relays connected to GPIO pins for load switching in demand response scenarios.

**Features:**
- Individual relay control (on/off)
- Bulk relay operations
- Status monitoring
- Safe initialization and cleanup
- Hardware abstraction for testing (simulation mode)
- Emergency shutoff capability

**Hardware Requirements:**
- Raspberry Pi with GPIO pins
- Normally closed relays connected to GPIO pins
- Appropriate relay driver circuits

**Example Usage:**
```python
from hardware_interfaces.gpio_relay_controller import GPIORelayController, RelayConfig, RelayState

# Configure relays
relay_configs = [
    RelayConfig("load_1", gpio_pin=18, name="Main Load"),
    RelayConfig("load_2", gpio_pin=19, name="Secondary Load"),
]

# Initialize controller
with GPIORelayController(relay_configs) as controller:
    # Turn off a relay (open circuit)
    controller.turn_off_relay("load_1")
    
    # Turn on a relay (close circuit)
    controller.turn_on_relay("load_1")
    
    # Set multiple relays
    controller.set_multiple_relays({
        "load_1": RelayState.OPEN,
        "load_2": RelayState.CLOSED,
    })
```

### 2. EVALSTPM34 Meter Interface (`evalstpm34_meter/`)

Interfaces with EVALSTPM34 evaluation boards via UART for power metering, current/voltage sensing, and calibration.

**Features:**
- Real-time power measurements (V, I, P, Q, S, PF)
- Dual channel support
- Energy accumulation
- Temperature monitoring
- Calibration support with EOL procedures
- Hardware abstraction for testing (simulation mode)

**Hardware Requirements:**
- EVALSTPM34 evaluation board
- UART connection (USB-to-Serial adapter)
- Proper power supply and signal conditioning

**Example Usage:**
```python
from hardware_interfaces.evalstpm34_meter import EVALSTPM34Meter, MeterConfig

# Configure meter
config = MeterConfig(
    meter_id="meter_001",
    uart_port="/dev/ttyUSB0",
    baud_rate=115200,
    name="Main Power Meter"
)

# Initialize meter
with EVALSTPM34Meter(config) as meter:
    # Take a reading
    reading = meter.read_instantaneous_values()
    
    print(f"CH1: {reading.voltage_ch1:.1f}V, {reading.current_ch1:.2f}A")
    print(f"CH2: {reading.voltage_ch2:.1f}V, {reading.current_ch2:.2f}A")
    print(f"Total Power: {reading.active_power_ch1 + reading.active_power_ch2:.1f}W")
```

## Installation

1. Install required Python packages:
```bash
pip install -r requirements.txt
```

2. For Raspberry Pi GPIO support:
```bash
sudo apt-get update
sudo apt-get install python3-rpi.gpio
```

3. For UART communication:
```bash
sudo apt-get install python3-serial
```

## Simulation Mode

Both modules support simulation mode for development and testing without physical hardware:

- **GPIO Relay Controller**: Automatically detects if RPi.GPIO is available
- **EVALSTPM34 Meter**: Automatically detects if pySerial is available
- Can be forced with `simulation_mode=True` parameter

## Testing

Run the test suite:
```bash
cd volttron-ven
python -m pytest tests/hardware_interfaces/ -v
```

Run the example script:
```bash
cd volttron-ven
python example_hardware_usage.py
```

## Calibration (EVALSTPM34)

The EVALSTPM34 meter supports calibration procedures for accurate measurements:

```python
from hardware_interfaces.evalstpm34_meter.calibration import CalibrationManager

# Initialize calibration manager
cal_manager = CalibrationManager()

# Perform EOL calibration
calibration = cal_manager.perform_eol_calibration(
    meter=meter,
    reference_voltage=120.0,
    reference_current=5.0,
    calibrated_by="technician_001"
)

# Save calibration data
cal_manager.save_calibration(calibration)
```

## Integration with VEN

These hardware interfaces are designed to be integrated with the main VEN agent for demand response operations:

1. **Load Control**: Use GPIO relay controller to shed/restore loads based on OpenADR events
2. **Power Monitoring**: Use EVALSTPM34 meter to monitor baseline and real-time power consumption
3. **Measurement & Verification**: Combine both modules to measure actual load reduction

## Hardware Wiring

### GPIO Relay Controller
- Connect relay control pins to GPIO pins (18, 19, 20, etc.)
- Use appropriate relay driver circuits (transistors, optocouplers)
- Ensure proper isolation between control and power circuits
- Consider using relay modules with built-in drivers

### EVALSTPM34 Meter
- Connect UART pins (TX, RX, GND) to USB-Serial adapter
- Connect power supply (typically 3.3V or 5V)
- Connect current transformers and voltage dividers as per datasheet
- Ensure proper grounding and isolation

## Safety Considerations

⚠️ **WARNING**: These modules control electrical loads and measure live power circuits.

- Always follow electrical safety practices
- Use proper isolation and protection circuits
- Test thoroughly in simulation mode before connecting to real hardware
- Have qualified personnel review hardware connections
- Include emergency shutoff mechanisms
- Consider fail-safe designs (normally closed relays for critical loads)

## Future Enhancements

- Support for additional relay types (normally open, latching)
- Multiple EVALSTPM34 meter support
- Enhanced calibration procedures
- Integration with cloud-based calibration databases
- Support for other power metering ICs
- Advanced fault detection and diagnostics