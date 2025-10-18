"""
Example usage of hardware interface modules.

This script demonstrates how to use the GPIO relay controller and
EVALSTPM34 meter interface for a physical VEN implementation.

Key Features Demonstrated:
- GPIO relay control for load switching
- EVALSTPM34 coherent snapshot-based measurements
- Software latch mechanism for synchronized readings
- Dual-channel power monitoring
- Integrated demand response operations

The EVALSTPM34 driver implements advanced features matching the
STMicroelectronics C HAL:
- Software latch (DSP_CR3) for coherent data snapshots
- Bulk register reads (up to 30 consecutive registers)
- Proper register mapping from DSP_REG14/15 for RMS values
- Measurement variability detection for validation

For hardware testing and validation, also see:
- test_evalstpm34_real.py: Continuous monitoring test for EVALSTPM34
"""

import time
import logging
from datetime import datetime

from hardware_interfaces import GPIORelayController, EVALSTPM34Meter, RelayConfig, RelayState, MeterConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main example function."""
    logger.info("Starting hardware interface example")
    
    # Example 1: GPIO Relay Controller
    logger.info("=== GPIO Relay Controller Example ===")
    
    # Configure relays
    relay_configs = [
        RelayConfig(
            relay_id="load_1",
            gpio_pin=18,
            name="Main Load Circuit",
            description="Primary load control relay",
            initial_state=RelayState.CLOSED
        ),
        RelayConfig(
            relay_id="load_2", 
            gpio_pin=19,
            name="Secondary Load Circuit",
            description="Secondary load control relay",
            initial_state=RelayState.CLOSED
        ),
        RelayConfig(
            relay_id="emergency",
            gpio_pin=20,
            name="Emergency Shutoff",
            description="Emergency load disconnect",
            initial_state=RelayState.CLOSED
        ),
    ]
    
    # Initialize relay controller (will use simulation mode if not on Pi)
    try:
        with GPIORelayController(relay_configs) as relay_controller:
            logger.info(f"Initialized relay controller with {len(relay_controller.list_relays())} relays")
            
            # Display relay information
            for relay_id in relay_controller.list_relays():
                info = relay_controller.get_relay_info(relay_id)
                logger.info(f"Relay {relay_id}: {info['name']} on pin {info['gpio_pin']}, state: {info['current_state']}")
            
            # Demonstrate relay operations
            logger.info("Testing relay operations...")
            
            # Turn off load_1 (open circuit)
            relay_controller.turn_off_relay("load_1")
            time.sleep(1)
            
            # Turn it back on
            relay_controller.turn_on_relay("load_1")
            time.sleep(1)
            
            # Set multiple relays
            relay_controller.set_multiple_relays({
                "load_1": RelayState.OPEN,
                "load_2": RelayState.OPEN,
            })
            time.sleep(2)
            
            # Restore all relays
            relay_controller.set_multiple_relays({
                "load_1": RelayState.CLOSED,
                "load_2": RelayState.CLOSED,
            })
            
            # Get current states
            states = relay_controller.get_all_relay_states()
            logger.info(f"Current relay states: {states}")
            
    except Exception as e:
        logger.error(f"Relay controller error: {e}")
    
    # Example 2: EVALSTPM34 Meter
    logger.info("=== EVALSTPM34 Meter Example ===")
    
    # Configure meter
    meter_config = MeterConfig(
        meter_id="meter_001",
        uart_port="/dev/ttyUSB0",  # Adjust based on actual connection
        baud_rate=9600,  # STPM34 default baud rate
        name="Main Power Meter",
        description="Primary circuit power measurement",
        voltage_calibration_ch1=1.0,
        current_calibration_ch1=1.0,
        voltage_calibration_ch2=1.0,
        current_calibration_ch2=1.0,
        voltage_range_ch1="230V",
        current_range_ch1="5A"
    )
    
    try:
        with EVALSTPM34Meter(meter_config) as meter:
            logger.info(f"Initialized meter: {meter.get_meter_info()}")
            
            # Take several readings using snapshot-based measurements
            logger.info("Taking power measurements with coherent snapshots...")
            for i in range(5):
                reading = meter.read_instantaneous_values()
                
                logger.info(f"Reading {i+1} (snapshot-synchronized):")
                logger.info(f"  CH1: {reading.voltage_ch1:.1f}V, {reading.current_ch1:.3f}A, {reading.active_power_ch1:.1f}W")
                logger.info(f"  CH2: {reading.voltage_ch2:.1f}V, {reading.current_ch2:.3f}A, {reading.active_power_ch2:.1f}W")
                logger.info(f"  Apparent Power: CH1={reading.apparent_power_ch1:.1f}VA, CH2={reading.apparent_power_ch2:.1f}VA")
                logger.info(f"  Power Factor: CH1={reading.power_factor_ch1:.3f}, CH2={reading.power_factor_ch2:.3f}")
                logger.info(f"  Frequency: {reading.frequency:.1f}Hz")
                if reading.temperature:
                    logger.info(f"  Temperature: {reading.temperature:.1f}°C")
                
                time.sleep(1)
            
            # Read energy values
            logger.info("Reading energy accumulations...")
            energy = meter.read_energy_values()
            logger.info(f"Energy CH1: {energy.active_energy_ch1:.2f}Wh, {energy.reactive_energy_ch1:.2f}VARh")
            logger.info(f"Energy CH2: {energy.active_energy_ch2:.2f}Wh, {energy.reactive_energy_ch2:.2f}VARh")
            
            # Example of using readings for demand response
            total_power = reading.active_power_ch1 + reading.active_power_ch2
            logger.info(f"Total power consumption: {total_power:.1f}W")
            
            if total_power > 1000:  # Example threshold
                logger.info("Power consumption high - would trigger demand response")
                
    except Exception as e:
        logger.error(f"Meter error: {e}")
    
    # Example 3: Integrated Operation
    logger.info("=== Integrated Operation Example ===")
    
    # This would be the core of a real VEN implementation
    try:
        # Initialize both systems
        with GPIORelayController(relay_configs) as relays, \
             EVALSTPM34Meter(meter_config) as meter:
            
            logger.info("Integrated VEN hardware interfaces ready")
            
            # Simulation of demand response event
            logger.info("Simulating demand response event...")
            
            # 1. Take baseline measurement
            baseline = meter.read_instantaneous_values()
            baseline_power = baseline.active_power_ch1 + baseline.active_power_ch2
            logger.info(f"Baseline power: {baseline_power:.1f}W")
            
            # 2. Shed load (turn off secondary circuit)
            logger.info("Shedding load...")
            relays.turn_off_relay("load_2")
            time.sleep(2)
            
            # 3. Measure load reduction
            reduced = meter.read_instantaneous_values()
            reduced_power = reduced.active_power_ch1 + reduced.active_power_ch2
            load_reduction = baseline_power - reduced_power
            logger.info(f"Reduced power: {reduced_power:.1f}W")
            logger.info(f"Load reduction achieved: {load_reduction:.1f}W")
            
            # 4. Restore load after event
            time.sleep(3)
            logger.info("Restoring load...")
            relays.turn_on_relay("load_2")
            
            # 5. Verify restoration
            restored = meter.read_instantaneous_values()
            restored_power = restored.active_power_ch1 + restored.active_power_ch2
            logger.info(f"Restored power: {restored_power:.1f}W")
            
    except Exception as e:
        logger.error(f"Integrated operation error: {e}")
    
    # Example 4: Advanced Features Demonstration
    logger.info("=== Advanced Features Demonstration ===")
    logger.info("Demonstrating snapshot-based bulk reads and continuous polling...")
    
    try:
        with EVALSTPM34Meter(meter_config) as meter:
            # Demonstrate manual snapshot read for advanced users
            logger.info("Taking manual snapshot read...")
            snapshot_data = meter.read_snapshot()
            if snapshot_data:
                logger.info(f"Snapshot captured {len(snapshot_data)} register blocks successfully")
                logger.info("Snapshot provides synchronized measurement data across all channels")
    
    except Exception as e:
        logger.error(f"Advanced features error: {e}")
    
    # Example 5: Continuous Monitoring (similar to test script)
    logger.info("=== Continuous Monitoring Example ===")
    logger.info("Demonstrating continuous data polling with measurement variability...")
    
    try:
        with EVALSTPM34Meter(meter_config) as meter:
            if meter.is_connected():
                logger.info("Starting continuous monitoring (5 samples)...")
                logger.info("Note: Current RMS may show small variations due to internal reference noise")
                
                for i in range(5):
                    readings = meter.read_instantaneous_values()
                    energy = meter.read_energy_values()
                    
                    logger.info(f"Sample {i+1} (coherent snapshot):")
                    logger.info(f"  CH1: {readings.voltage_ch1:.2f}V, {readings.current_ch1:.3f}A, {readings.active_power_ch1:.1f}W")
                    logger.info(f"  CH2: {readings.voltage_ch2:.2f}V, {readings.current_ch2:.3f}A, {readings.active_power_ch2:.1f}W")
                    logger.info(f"  Apparent Power: CH1={readings.apparent_power_ch1:.1f}VA, CH2={readings.apparent_power_ch2:.1f}VA")
                    logger.info(f"  Power Factor: CH1={readings.power_factor_ch1:.3f}, CH2={readings.power_factor_ch2:.3f}")
                    logger.info(f"  Frequency: {readings.frequency:.2f}Hz")
                    logger.info(f"  Energy: CH1={energy.active_energy_ch1:.2f}Wh, CH2={energy.active_energy_ch2:.2f}Wh")
                    
                    # Simulate a 2-second polling interval
                    if i < 4:  # Don't sleep after last iteration
                        time.sleep(2)
                
                logger.info("Continuous monitoring example completed")
            else:
                logger.error("Failed to connect to meter for continuous monitoring")
                
    except Exception as e:
        logger.error(f"Continuous monitoring error: {e}")
    
    logger.info("Hardware interface example completed")


if __name__ == "__main__":
    main()