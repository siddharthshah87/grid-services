"""
GPIO Relay Controller

Manages normally closed (NC) relays connected to GPIO pins for load control
in demand response applications.

Features:
- Individual relay control (on/off)
- Bulk relay operations
- Status monitoring
- Safe initialization and cleanup
- Hardware abstraction for testing
"""

import logging
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .exceptions import GPIORelayError, RelayNotFoundError, GPIOInitializationError, RelayOperationError

# Optional GPIO library import for Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO not available. GPIO operations will be simulated.")


class RelayState(Enum):
    """Relay states for normally closed relays."""
    CLOSED = "closed"  # Relay closed, current flows (GPIO LOW for NC)
    OPEN = "open"      # Relay open, current blocked (GPIO HIGH for NC)


@dataclass
class RelayConfig:
    """Configuration for a single relay."""
    relay_id: str
    gpio_pin: int
    name: str
    description: str = ""
    initial_state: RelayState = RelayState.CLOSED


class GPIORelayController:
    """
    Controller for GPIO-based relay switching.
    
    Manages normally closed (NC) relays where:
    - LOW signal = relay closed = current flows
    - HIGH signal = relay open = current blocked
    """
    
    def __init__(self, relays: List[RelayConfig], simulation_mode: bool = None):
        """
        Initialize the GPIO relay controller.
        
        Args:
            relays: List of relay configurations
            simulation_mode: Force simulation mode (None = auto-detect)
        """
        self.logger = logging.getLogger(__name__)
        self.relays = {relay.relay_id: relay for relay in relays}
        self.relay_states: Dict[str, RelayState] = {}
        
        # Determine if we should use simulation mode
        if simulation_mode is None:
            self.simulation_mode = not GPIO_AVAILABLE
        else:
            self.simulation_mode = simulation_mode
            
        if not self.simulation_mode and not GPIO_AVAILABLE:
            raise GPIOInitializationError("GPIO library not available but simulation mode disabled")
        
        self._initialize_gpio()
        
    def _initialize_gpio(self):
        """Initialize GPIO pins and set initial states."""
        if self.simulation_mode:
            self.logger.info("Initializing GPIO relay controller in simulation mode")
            # Simulate GPIO initialization
            for relay_id, relay in self.relays.items():
                self.relay_states[relay_id] = relay.initial_state
                self.logger.info(f"Simulated: Initialized relay {relay_id} on pin {relay.gpio_pin}")
        else:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                
                for relay_id, relay in self.relays.items():
                    GPIO.setup(relay.gpio_pin, GPIO.OUT)
                    initial_gpio_state = GPIO.LOW if relay.initial_state == RelayState.CLOSED else GPIO.HIGH
                    GPIO.output(relay.gpio_pin, initial_gpio_state)
                    self.relay_states[relay_id] = relay.initial_state
                    self.logger.info(f"Initialized relay {relay_id} on pin {relay.gpio_pin}")
                    
            except Exception as e:
                raise GPIOInitializationError(f"Failed to initialize GPIO: {e}")
    
    def set_relay_state(self, relay_id: str, state: RelayState) -> bool:
        """
        Set the state of a specific relay.
        
        Args:
            relay_id: ID of the relay to control
            state: Desired relay state
            
        Returns:
            True if operation successful
            
        Raises:
            RelayNotFoundError: If relay_id doesn't exist
            RelayOperationError: If the operation fails
        """
        if relay_id not in self.relays:
            raise RelayNotFoundError(f"Relay {relay_id} not found")
        
        relay = self.relays[relay_id]
        
        try:
            if self.simulation_mode:
                # Simulate relay operation
                self.relay_states[relay_id] = state
                self.logger.info(f"Simulated: Set relay {relay_id} to {state.value}")
            else:
                # For NC relays: LOW = closed, HIGH = open
                gpio_state = GPIO.LOW if state == RelayState.CLOSED else GPIO.HIGH
                GPIO.output(relay.gpio_pin, gpio_state)
                self.relay_states[relay_id] = state
                self.logger.info(f"Set relay {relay_id} (pin {relay.gpio_pin}) to {state.value}")
            
            return True
            
        except Exception as e:
            raise RelayOperationError(f"Failed to set relay {relay_id} to {state.value}: {e}")
    
    def get_relay_state(self, relay_id: str) -> RelayState:
        """
        Get the current state of a relay.
        
        Args:
            relay_id: ID of the relay
            
        Returns:
            Current relay state
            
        Raises:
            RelayNotFoundError: If relay_id doesn't exist
        """
        if relay_id not in self.relays:
            raise RelayNotFoundError(f"Relay {relay_id} not found")
            
        return self.relay_states[relay_id]
    
    def turn_on_relay(self, relay_id: str) -> bool:
        """
        Turn on a relay (close the circuit).
        
        Args:
            relay_id: ID of the relay
            
        Returns:
            True if successful
        """
        return self.set_relay_state(relay_id, RelayState.CLOSED)
    
    def turn_off_relay(self, relay_id: str) -> bool:
        """
        Turn off a relay (open the circuit).
        
        Args:
            relay_id: ID of the relay
            
        Returns:
            True if successful
        """
        return self.set_relay_state(relay_id, RelayState.OPEN)
    
    def set_multiple_relays(self, relay_states: Dict[str, RelayState]) -> Dict[str, bool]:
        """
        Set multiple relays simultaneously.
        
        Args:
            relay_states: Dictionary of relay_id -> desired state
            
        Returns:
            Dictionary of relay_id -> operation success
        """
        results = {}
        
        for relay_id, state in relay_states.items():
            try:
                results[relay_id] = self.set_relay_state(relay_id, state)
            except Exception as e:
                self.logger.error(f"Failed to set relay {relay_id}: {e}")
                results[relay_id] = False
                
        return results
    
    def get_all_relay_states(self) -> Dict[str, RelayState]:
        """
        Get the current state of all relays.
        
        Returns:
            Dictionary of relay_id -> current state
        """
        return self.relay_states.copy()
    
    def emergency_all_off(self) -> Dict[str, bool]:
        """
        Emergency function to turn off all relays (open all circuits).
        
        Returns:
            Dictionary of relay_id -> operation success
        """
        self.logger.warning("Emergency all relays OFF initiated")
        
        all_off_states = {relay_id: RelayState.OPEN for relay_id in self.relays.keys()}
        return self.set_multiple_relays(all_off_states)
    
    def get_relay_info(self, relay_id: str) -> Dict:
        """
        Get detailed information about a relay.
        
        Args:
            relay_id: ID of the relay
            
        Returns:
            Dictionary with relay information
            
        Raises:
            RelayNotFoundError: If relay_id doesn't exist
        """
        if relay_id not in self.relays:
            raise RelayNotFoundError(f"Relay {relay_id} not found")
        
        relay = self.relays[relay_id]
        current_state = self.relay_states[relay_id]
        
        return {
            "relay_id": relay_id,
            "gpio_pin": relay.gpio_pin,
            "name": relay.name,
            "description": relay.description,
            "current_state": current_state.value,
            "simulation_mode": self.simulation_mode
        }
    
    def list_relays(self) -> List[str]:
        """
        Get a list of all configured relay IDs.
        
        Returns:
            List of relay IDs
        """
        return list(self.relays.keys())
    
    def cleanup(self):
        """
        Clean up GPIO resources.
        Call this when shutting down the controller.
        """
        if not self.simulation_mode:
            try:
                GPIO.cleanup()
                self.logger.info("GPIO cleanup completed")
            except Exception as e:
                self.logger.error(f"Error during GPIO cleanup: {e}")
        else:
            self.logger.info("Simulation mode cleanup completed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()


# Convenience functions for common operations
def create_relay_config(relay_id: str, gpio_pin: int, name: str, 
                       description: str = "", initial_state: RelayState = RelayState.CLOSED) -> RelayConfig:
    """
    Create a relay configuration.
    
    Args:
        relay_id: Unique identifier for the relay
        gpio_pin: GPIO pin number (BCM numbering)
        name: Human-readable name
        description: Optional description
        initial_state: Initial relay state
        
    Returns:
        RelayConfig object
    """
    return RelayConfig(
        relay_id=relay_id,
        gpio_pin=gpio_pin,
        name=name,
        description=description,
        initial_state=initial_state
    )