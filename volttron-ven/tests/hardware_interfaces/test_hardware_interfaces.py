"""
Tests for hardware interface modules.
"""

import pytest
import sys
import os

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from hardware_interfaces.gpio_relay_controller import GPIORelayController, RelayConfig, RelayState
from hardware_interfaces.evalstpm34_meter import EVALSTPM34Meter, MeterConfig


class TestGPIORelayController:
    """Tests for GPIO relay controller."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.relay_configs = [
            RelayConfig("test_relay_1", 18, "Test Relay 1"),
            RelayConfig("test_relay_2", 19, "Test Relay 2"),
        ]
    
    def test_initialization_simulation_mode(self):
        """Test controller initialization in simulation mode."""
        controller = GPIORelayController(self.relay_configs, simulation_mode=True)
        
        assert len(controller.list_relays()) == 2
        assert "test_relay_1" in controller.list_relays()
        assert "test_relay_2" in controller.list_relays()
        
        controller.cleanup()
    
    def test_relay_operations(self):
        """Test basic relay operations."""
        with GPIORelayController(self.relay_configs, simulation_mode=True) as controller:
            # Test turning relay off
            result = controller.turn_off_relay("test_relay_1")
            assert result is True
            assert controller.get_relay_state("test_relay_1") == RelayState.OPEN
            
            # Test turning relay on
            result = controller.turn_on_relay("test_relay_1")
            assert result is True
            assert controller.get_relay_state("test_relay_1") == RelayState.CLOSED
    
    def test_multiple_relay_operations(self):
        """Test multiple relay operations."""
        with GPIORelayController(self.relay_configs, simulation_mode=True) as controller:
            states = {
                "test_relay_1": RelayState.OPEN,
                "test_relay_2": RelayState.OPEN,
            }
            
            results = controller.set_multiple_relays(states)
            
            assert all(results.values())
            assert controller.get_relay_state("test_relay_1") == RelayState.OPEN
            assert controller.get_relay_state("test_relay_2") == RelayState.OPEN
    
    def test_relay_info(self):
        """Test getting relay information."""
        with GPIORelayController(self.relay_configs, simulation_mode=True) as controller:
            info = controller.get_relay_info("test_relay_1")
            
            assert info["relay_id"] == "test_relay_1"
            assert info["gpio_pin"] == 18
            assert info["name"] == "Test Relay 1"
            assert info["simulation_mode"] is True
    
    def test_emergency_all_off(self):
        """Test emergency all off function."""
        with GPIORelayController(self.relay_configs, simulation_mode=True) as controller:
            results = controller.emergency_all_off()
            
            assert all(results.values())
            states = controller.get_all_relay_states()
            assert all(state == RelayState.OPEN for state in states.values())


class TestEVALSTPM34Meter:
    """Tests for EVALSTPM34 meter interface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.meter_config = MeterConfig(
            meter_id="test_meter",
            uart_port="/dev/ttyUSB0",
            name="Test Meter"
        )
    
    def test_initialization_simulation_mode(self):
        """Test meter initialization in simulation mode."""
        meter = EVALSTPM34Meter(self.meter_config, simulation_mode=True)
        
        assert meter.config.meter_id == "test_meter"
        assert meter.simulation_mode is True
        assert meter.is_connected() is True
        
        meter.close()
    
    def test_meter_reading(self):
        """Test taking meter readings."""
        with EVALSTPM34Meter(self.meter_config, simulation_mode=True) as meter:
            reading = meter.read_instantaneous_values()
            
            assert reading.meter_id == "test_meter"
            assert reading.voltage_ch1 > 0
            assert reading.current_ch1 > 0
            assert reading.voltage_ch2 > 0
            assert reading.current_ch2 > 0
            assert reading.frequency > 0
            assert reading.data_valid is True
    
    def test_meter_info(self):
        """Test getting meter information."""
        with EVALSTPM34Meter(self.meter_config, simulation_mode=True) as meter:
            info = meter.get_meter_info()
            
            assert info["meter_id"] == "test_meter"
            assert info["uart_port"] == "/dev/ttyUSB0"
            assert info["simulation_mode"] is True
            assert info["connected"] is True
    
    def test_reading_to_dict(self):
        """Test converting readings to dictionary."""
        with EVALSTPM34Meter(self.meter_config, simulation_mode=True) as meter:
            reading = meter.read_instantaneous_values()
            reading_dict = reading.to_dict()
            
            assert "timestamp" in reading_dict
            assert "meter_id" in reading_dict
            assert "channel_1" in reading_dict
            assert "channel_2" in reading_dict
            assert "voltage" in reading_dict["channel_1"]
            assert "current" in reading_dict["channel_1"]


if __name__ == "__main__":
    pytest.main([__file__])