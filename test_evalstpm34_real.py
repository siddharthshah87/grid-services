#!/usr/bin/env python3
"""
EVALSTPM34 High-Level Driver Test

Test script for EVALSTPM34 energy meter using the high-level driver interface.
Continuously polls measurement data and displays real-time energy readings.

Features:
- High-level driver communication test
- Continuous data polling with configurable interval
- Real-time display of all measurement parameters
- Connection status monitoring
- Graceful shutdown with Ctrl+C
"""

import sys
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def clear_screen():
    """Clear the terminal screen."""
    print('\033[2J\033[H', end='')


def format_timestamp():
    """Format current timestamp for display."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def display_measurements(values, energy_values, sample_count):
    """Display measurement data in a formatted table."""
    print(f"EVALSTPM34 Energy Meter - Live Data (Sample #{sample_count})")
    print(f"Timestamp: {format_timestamp()}")
    print("=" * 70)
    
    # Channel measurements table
    print(f"{'Parameter':<20} {'Channel 1':<15} {'Channel 2':<15} {'Unit':<10}")
    print("-" * 70)
    print(f"{'Voltage RMS':<20} {values.voltage_ch1:<15.2f} {values.voltage_ch2:<15.2f} {'V':<10}")
    print(f"{'Current RMS':<20} {values.current_ch1:<15.3f} {values.current_ch2:<15.3f} {'A':<10}")
    print(f"{'Active Power':<20} {values.active_power_ch1:<15.1f} {values.active_power_ch2:<15.1f} {'W':<10}")
    print(f"{'Reactive Power':<20} {values.reactive_power_ch1:<15.1f} {values.reactive_power_ch2:<15.1f} {'VAR':<10}")
    print(f"{'Apparent Power':<20} {values.apparent_power_ch1:<15.1f} {values.apparent_power_ch2:<15.1f} {'VA':<10}")
    print(f"{'Power Factor':<20} {values.power_factor_ch1:<15.3f} {values.power_factor_ch2:<15.3f} {'':<10}")
    
    print("\n" + "=" * 70)
    
    # Common measurements
    print(f"Frequency: {values.frequency:.2f} Hz")
    if hasattr(values, 'temperature') and values.temperature is not None:
        print(f"Temperature: {values.temperature:.1f} °C")
    else:
        print("Temperature: Not available")
    
    # Energy measurements
    if energy_values:
        print("\nEnergy Accumulation:")
        print("-" * 70)
        print(f"{'Energy Type':<20} {'Channel 1':<15} {'Channel 2':<15} {'Unit':<10}")
        print("-" * 70)
        print(f"{'Active Energy':<20} {energy_values.active_energy_ch1:<15.2f} {energy_values.active_energy_ch2:<15.2f} {'Wh':<10}")
        print(f"{'Reactive Energy':<20} {energy_values.reactive_energy_ch1:<15.2f} {energy_values.reactive_energy_ch2:<15.2f} {'VARh':<10}")
    
    print("\n" + "=" * 70)
    print("Press Ctrl+C to stop monitoring")


def main():
    """Main test function for EVALSTPM34 high-level driver."""
    print("EVALSTPM34 High-Level Driver Test")
    print("=" * 50)
    
    # Import the driver (add path if needed)
    try:
        sys.path.append('volttron-ven/hardware_interfaces')
        from evalstpm34_meter import EVALSTPM34Meter, MeterConfig
                
    except ImportError as e:
        print(f"Error importing driver: {e}")
        print("Make sure the evalstpm34_meter.py is in the correct path")
        return 1
    
    # Configuration
    polling_interval = 2.0  # seconds
    uart_port = "/dev/ttyUSB0"
    baud_rate = 9600
    
    # Create meter configuration
    config = MeterConfig(
        meter_id="test_meter_01",
        uart_port=uart_port,
        baud_rate=baud_rate,
        name="Test EVALSTPM34",
        description="EVALSTPM34 test meter for validation"
    )
    
    print(f"Connecting to EVALSTPM34 on {uart_port} at {baud_rate} baud...")
    
    try:
        with EVALSTPM34Meter(config) as meter:
            if not meter.is_connected():
                print("✗ Failed to connect to meter")
                print("Check:")
                print("- UART connection and port")
                print("- Baud rate settings") 
                print("- Power supply to EVALSTPM34")
                return 1
            
            print("✓ Successfully connected to EVALSTPM34")
            print(f"Polling interval: {polling_interval} seconds")
            print("Starting continuous monitoring...\n")
            
            sample_count = 0
            
            try:
                while True:
                    sample_count += 1
                    
                    # Read measurements
                    try:
                        values = meter.read_instantaneous_values()
                        energy_values = meter.read_energy_values()
                        
                        # Clear screen and display data
                        clear_screen()
                        display_measurements(values, energy_values, sample_count)
                        
                    except Exception as e:
                        print(f"Error reading measurements: {e}")
                        logger.error(f"Measurement error: {e}")
                    
                    # Wait for next sample
                    time.sleep(polling_interval)
                    
            except KeyboardInterrupt:
                print("\n\nStopping measurement polling...")
                print("Test completed successfully")
                
    except Exception as e:
        print(f"Driver error: {e}")
        logger.error(f"Driver initialization failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())