"""
EVALSTPM34 Device Manager for Multiple Meter Identification

Handles reliable identification of multiple EVALSTPM34 meters connected via USB hub
using hardware-based USB paths and device validation.
"""

import os
import glob
import re
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .evalstpm34_meter import EVALSTPM34Meter, MeterConfig

logger = logging.getLogger(__name__)

@dataclass
class DeviceIdentity:
    """Device identification information."""
    usb_path: str          # e.g., "1-1.2:1.0"
    device_path: str       # e.g., "/dev/ttyUSB0"  
    persistent_path: str   # e.g., "/dev/serial/by-path/..."
    physical_location: str # e.g., "Hub Port 2"
    meter_name: str        # User-defined name

class EVALSTPM34DeviceManager:
    """Manages multiple EVALSTPM34 devices with reliable identification."""
    
    def __init__(self):
        self.devices: Dict[str, DeviceIdentity] = {}
        self.meters: Dict[str, EVALSTPM34Meter] = {}
        
    def discover_devices(self) -> List[DeviceIdentity]:
        """Discover all connected EVALSTPM34-compatible USB serial devices."""
        devices = []
        
        # Method 1: Use persistent device paths
        persistent_devices = glob.glob("/dev/serial/by-path/*")
        for persistent_path in persistent_devices:
            if self._is_usb_serial_device(persistent_path):
                device_path = os.path.realpath(persistent_path)
                usb_path = self._extract_usb_path(persistent_path)
                
                device = DeviceIdentity(
                    usb_path=usb_path,
                    device_path=device_path,
                    persistent_path=persistent_path,
                    physical_location=self._describe_location(usb_path),
                    meter_name=""  # To be assigned by user
                )
                devices.append(device)
                
        return devices
    
    def _is_usb_serial_device(self, path: str) -> bool:
        """Check if device is a USB serial device suitable for STPM34."""
        try:
            # Check if it's a USB device with serial interface
            return ("usb" in path.lower() and 
                    os.path.exists(os.path.realpath(path)))
        except:
            return False
    
    def _extract_usb_path(self, persistent_path: str) -> str:
        """Extract USB path from persistent device path."""
        # Example: /dev/serial/by-path/pci-0000:00:14.0-usb-0:1.2:1.0-port0
        # Extract: 1.2:1.0
        match = re.search(r'usb-\d+:([^-]+)', persistent_path)
        return match.group(1) if match else "unknown"
    
    def _describe_location(self, usb_path: str) -> str:
        """Convert USB path to human-readable location."""
        # USB path format: bus.port.subport:config.interface
        # Example: "1.2:1.0" = Bus 1, Port 2, Config 1, Interface 0
        parts = usb_path.split(':')[0].split('.')
        if len(parts) >= 2:
            bus, port = parts[0], parts[1]
            return f"USB Hub Port {port}"
        return f"USB Path {usb_path}"
    
    def assign_device_names(self, device_mapping: Dict[str, str]) -> bool:
        """
        Assign names to devices based on their persistent paths.
        
        Args:
            device_mapping: Dict mapping persistent_path -> meter_name
            Example: {
                "/dev/serial/by-path/...usb-0:1.2:1.0...": "main_panel",
                "/dev/serial/by-path/...usb-0:1.3:1.0...": "solar_meter"
            }
        """
        devices = self.discover_devices()
        
        for device in devices:
            if device.persistent_path in device_mapping:
                device.meter_name = device_mapping[device.persistent_path]
                self.devices[device.meter_name] = device
                logger.info(f"Assigned '{device.meter_name}' to {device.physical_location}")
            else:
                logger.warning(f"Unassigned device at {device.physical_location}")
        
        return len(self.devices) > 0
    
    def create_meters(self) -> Dict[str, EVALSTPM34Meter]:
        """Create EVALSTPM34Meter instances for all assigned devices."""
        for name, device in self.devices.items():
            try:
                config = MeterConfig(
                    meter_id=name,
                    uart_port=device.persistent_path,  # Use persistent path!
                    baud_rate=9600,
                    name=f"{name} ({device.physical_location})"
                )
                
                meter = EVALSTPM34Meter(config)
                if meter.connect():
                    self.meters[name] = meter
                    logger.info(f"Connected meter '{name}' at {device.physical_location}")
                else:
                    logger.error(f"Failed to connect meter '{name}'")
                    
            except Exception as e:
                logger.error(f"Error creating meter '{name}': {e}")
        
        return self.meters
    
    def validate_device_assignment(self) -> bool:
        """Validate that all meters are responding correctly."""
        for name, meter in self.meters.items():
            try:
                # Try to read data to confirm device is working
                values = meter.read_instantaneous_values()
                logger.info(f"Meter '{name}' validation: {values.voltage_ch1:.2f}V")
            except Exception as e:
                logger.error(f"Meter '{name}' validation failed: {e}")
                return False
        return True
    
    def get_device_info(self) -> Dict[str, Dict]:
        """Get detailed information about all devices."""
        info = {}
        for name, device in self.devices.items():
            info[name] = {
                "meter_name": device.meter_name,
                "physical_location": device.physical_location,
                "usb_path": device.usb_path,
                "device_path": device.device_path,
                "persistent_path": device.persistent_path,
                "connected": name in self.meters
            }
        return info