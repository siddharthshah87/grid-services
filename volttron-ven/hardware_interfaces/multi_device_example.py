#!/usr/bin/env python3
"""
Multi-Device Hardware Interface Example

This script demonstrates how to use multiple EVALSTPM34 meters 
and multiple GPIO relay controllers simultaneously for a 
comprehensive physical VEN implementation.

Key Features:
- Multiple EVALSTPM34 meters on different USB ports
- Multiple relay groups with configurable GPIO pins
- Integrated demand response operations
- Real-time monitoring and control
"""

import time
import logging
from typing import Dict, List
from datetime import datetime

# Import hardware interfaces
from evalstpm34_meter import EVALSTPM34Meter, MeterConfig
from gpio_relay_controller import GPIORelayController, RelayConfig, RelayState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def multi_meter_example():
    """Example showing multiple EVALSTPM34 meters."""
    logger.info("=== Multiple EVALSTPM34 Meters Example ===")
    
    # Configuration for multiple meters on different USB ports
    meter_configs = [
        MeterConfig(
            meter_id="main_panel",
            uart_port="/dev/ttyUSB0",
            name="Main Panel Meter",
            description="Primary building electrical panel"
        ),
        MeterConfig(
            meter_id="solar_inverter", 
            uart_port="/dev/ttyUSB1",
            name="Solar Inverter Meter",
            description="Solar PV inverter output measurement"
        ),
        MeterConfig(
            meter_id="hvac_unit",
            uart_port="/dev/ttyUSB2", 
            name="HVAC Unit Meter",
            description="Air conditioning unit power measurement"
        )
    ]
    
    try:
        # Initialize all meters
        meters = {}
        for config in meter_configs:
            try:
                meter = EVALSTPM34Meter(config)
                if meter.connect():
                    meters[config.meter_id] = meter
                    logger.info(f"✓ Connected to {config.name}")
                else:
                    logger.warning(f"✗ Failed to connect to {config.name}")
            except Exception as e:
                logger.error(f"✗ Error initializing {config.name}: {e}")
        
        if not meters:
            logger.error("No meters connected successfully")
            return
        
        # Take measurements from all connected meters
        logger.info("Taking measurements from all meters...")
        for meter_id, meter in meters.items():
            try:
                readings = meter.read_instantaneous_values()
                total_power = readings.active_power_ch1 + readings.active_power_ch2
                
                logger.info(f"{meter_id}:")
                logger.info(f"  Total Power: {total_power:.1f}W")
                logger.info(f"  CH1: {readings.voltage_ch1:.1f}V, {readings.current_ch1:.2f}A")
                logger.info(f"  CH2: {readings.voltage_ch2:.1f}V, {readings.current_ch2:.2f}A")
                
            except Exception as e:
                logger.error(f"Error reading from {meter_id}: {e}")
        
        # Cleanup
        for meter in meters.values():
            meter.disconnect()
            
    except Exception as e:
        logger.error(f"Multi-meter example error: {e}")


def multi_relay_example():
    """Example showing multiple relay groups."""
    logger.info("=== Multiple GPIO Relay Groups Example ===")
    
    # Configuration for different relay groups
    hvac_relays = [
        RelayConfig("hvac_main", gpio_pin=18, name="HVAC Main Unit"),
        RelayConfig("hvac_fan", gpio_pin=19, name="HVAC Fan"),
        RelayConfig("hvac_heat", gpio_pin=20, name="HVAC Heating")
    ]
    
    lighting_relays = [
        RelayConfig("light_zone1", gpio_pin=21, name="Lighting Zone 1"),
        RelayConfig("light_zone2", gpio_pin=22, name="Lighting Zone 2"),
        RelayConfig("light_zone3", gpio_pin=23, name="Lighting Zone 3")
    ]
    
    appliance_relays = [
        RelayConfig("water_heater", gpio_pin=24, name="Water Heater"),
        RelayConfig("pool_pump", gpio_pin=25, name="Pool Pump"),
        RelayConfig("ev_charger", gpio_pin=26, name="EV Charger")
    ]
    
    try:
        # Initialize separate controllers for each group
        with GPIORelayController(hvac_relays) as hvac_controller, \
             GPIORelayController(lighting_relays) as light_controller, \
             GPIORelayController(appliance_relays) as appliance_controller:
            
            logger.info("✓ All relay controllers initialized")
            
            # Display initial states
            controllers = {
                "HVAC": hvac_controller,
                "Lighting": light_controller, 
                "Appliances": appliance_controller
            }
            
            for name, controller in controllers.items():
                states = controller.get_all_relay_states()
                logger.info(f"{name} relays: {states}")
            
            # Demonstrate group operations
            logger.info("Demonstrating group relay operations...")
            
            # Turn off all HVAC except main unit
            hvac_controller.set_multiple_relays({
                "hvac_fan": RelayState.OPEN,
                "hvac_heat": RelayState.OPEN
            })
            logger.info("HVAC: Turned off fan and heating, kept main unit")
            
            # Turn on half the lighting
            light_controller.set_multiple_relays({
                "light_zone1": RelayState.CLOSED,
                "light_zone2": RelayState.OPEN,
                "light_zone3": RelayState.CLOSED
            })
            logger.info("Lighting: Zone 1 and 3 on, Zone 2 off")
            
            # Turn off all appliances  
            appliance_controller.turn_off_all_relays()
            logger.info("Appliances: All turned off")
            
            time.sleep(2)
            
            # Restore all relays
            for controller in controllers.values():
                controller.turn_on_all_relays()
            logger.info("All relays restored to ON state")
            
    except Exception as e:
        logger.error(f"Multi-relay example error: {e}")


def integrated_demand_response_example():
    """Example showing integrated demand response with multiple devices."""
    logger.info("=== Integrated Multi-Device Demand Response Example ===")
    
    # Simplified configuration for demo
    meter_config = MeterConfig(
        meter_id="main_meter",
        uart_port="/dev/ttyUSB0",
        name="Main Panel Meter"
    )
    
    load_relays = [
        RelayConfig("critical_load", gpio_pin=18, name="Critical Load"),
        RelayConfig("hvac", gpio_pin=19, name="HVAC System"),
        RelayConfig("water_heater", gpio_pin=20, name="Water Heater"),
        RelayConfig("ev_charger", gpio_pin=21, name="EV Charger")
    ]
    
    try:
        with EVALSTPM34Meter(meter_config) as meter, \
             GPIORelayController(load_relays) as load_controller:
            
            if not meter.is_connected():
                logger.error("Meter not connected - skipping integrated example")
                return
                
            logger.info("✓ Integrated system ready")
            
            # Simulate demand response event
            logger.info("Simulating demand response event...")
            
            # 1. Baseline measurement
            baseline = meter.read_instantaneous_values()
            baseline_power = baseline.active_power_ch1 + baseline.active_power_ch2
            logger.info(f"Baseline power: {baseline_power:.1f}W")
            
            # 2. Check if demand response needed (example threshold)
            demand_limit = 2000  # Watts
            if baseline_power > demand_limit:
                logger.info(f"Power {baseline_power:.1f}W exceeds limit {demand_limit}W")
                logger.info("Executing load shedding sequence...")
                
                # Shed non-critical loads in priority order
                shed_sequence = ["ev_charger", "water_heater", "hvac"]
                
                for load_id in shed_sequence:
                    logger.info(f"Shedding load: {load_id}")
                    load_controller.turn_off_relay(load_id)
                    time.sleep(1)
                    
                    # Check power reduction
                    current = meter.read_instantaneous_values()
                    current_power = current.active_power_ch1 + current.active_power_ch2
                    reduction = baseline_power - current_power
                    
                    logger.info(f"Power now: {current_power:.1f}W, reduction: {reduction:.1f}W")
                    
                    if current_power <= demand_limit:
                        logger.info("Target power level achieved")
                        break
            else:
                logger.info("Power consumption within limits - no action needed")
            
            # 3. Monitor for restoration opportunity
            logger.info("Monitoring for restoration opportunity...")
            time.sleep(5)
            
            # 4. Restore loads
            logger.info("Restoring loads...")
            load_controller.turn_on_all_relays()
            
            # Final measurement
            final = meter.read_instantaneous_values()
            final_power = final.active_power_ch1 + final.active_power_ch2
            logger.info(f"Final power: {final_power:.1f}W")
            
    except Exception as e:
        logger.error(f"Integrated example error: {e}")


def main():
    """Main function demonstrating all multi-device scenarios."""
    logger.info("Multi-Device Hardware Interface Examples")
    logger.info("=" * 50)
    
    try:
        # Run examples (comment out as needed for testing)
        multi_meter_example()
        time.sleep(2)
        
        multi_relay_example() 
        time.sleep(2)
        
        integrated_demand_response_example()
        
    except KeyboardInterrupt:
        logger.info("Examples interrupted by user")
    except Exception as e:
        logger.error(f"Example execution error: {e}")
    
    logger.info("Multi-device examples completed")


if __name__ == "__main__":
    main()